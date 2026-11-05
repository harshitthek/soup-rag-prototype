"""Phase 4.1: E5-Small LoRA Adapter Training Script.

Executes E5-small fine-tuning using Soup's native embedding trainer on Apple Silicon (MPS).
Matched with Experiment B hyperparameter and update budget:
- Base model: intfloat/e5-small-v2 (revision ffb93f3bd4047442299a41ebb6fa998a38507c52)
- Triplets: 2,475 (prefixed with query: and passage:)
- Epochs: 3
- Batch size: 4 (effective updates: 1,857)
- Learning rate: configurable (default 2e-5)
- Loss: Triplet Margin (margin=0.5, pooling=mean)
- LoRA: r=16, alpha=32, dropout=0.05, target_modules=["query", "value"] (294,912 trainable parameters)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import yaml
from huggingface_hub import HfApi

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from soup_cli_discovery import resolve_python_interpreter, resolve_soup_binary
except ImportError:
    from scripts.soup_cli_discovery import resolve_python_interpreter, resolve_soup_binary

SOUP_BIN = str(resolve_soup_binary(REPO_ROOT))
SOUP_PYTHON = resolve_python_interpreter()

LOGS_DIR = REPO_ROOT / "results" / "training_logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_E5_REVISION = "ffb93f3bd4047442299a41ebb6fa998a38507c52"
BASE_MODEL_NAME = "intfloat/e5-small-v2"
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "embedding_e5_exp_b.yaml"
DATASET_PATH = REPO_ROOT / "data" / "triplets_e5_exp_b.jsonl"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_e5_hub_revision() -> str:
    print(f"Querying Hugging Face Hub for {BASE_MODEL_NAME} revision...")
    api = HfApi()
    info = api.model_info(BASE_MODEL_NAME, timeout=15)
    sha = info.sha
    if sha != EXPECTED_E5_REVISION:
        raise RuntimeError(
            f"Hub revision mismatch for {BASE_MODEL_NAME}: got {sha}, expected {EXPECTED_E5_REVISION}"
        )
    print(f"  ✓ Remote Hub revision verified: {sha}")
    return sha


def run_preflight(config_path: Path) -> dict:
    print(f"\n=== Running E5-small Training Preflight Checks for {config_path.name} ===")
    assert DATASET_PATH.exists(), f"Missing dataset: {DATASET_PATH}"
    lines = [json.loads(l) for l in DATASET_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 2475, f"Expected 2475 records, got {len(lines)}"
    for idx, r in enumerate(lines[:10]):
        assert r["anchor"].startswith("query: "), f"Missing query: prefix at index {idx}"
        assert r["positive"].startswith("passage: "), f"Missing passage: prefix at index {idx}"
        assert r["negative"].startswith("passage: "), f"Missing passage: prefix at index {idx}"
    d_sha256 = compute_sha256(DATASET_PATH)
    print(f"  ✓ Dataset: {DATASET_PATH.name} (2,475 records, sha256={d_sha256})")

    assert config_path.exists(), f"Missing config: {config_path}"
    c_sha256 = compute_sha256(config_path)
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg["base"] == BASE_MODEL_NAME
    assert cfg["task"] == "embedding"
    assert cfg["backend"] == "transformers"
    assert cfg["training"]["epochs"] == 3
    assert cfg["training"]["batch_size"] == 4
    assert cfg["training"]["gradient_accumulation_steps"] == 1
    assert cfg["training"]["seed"] == 42
    assert cfg["training"]["data_seed"] == 42
    assert cfg["training"]["quantization"] == "none"
    assert cfg["training"]["embedding_loss"] == "triplet"
    assert cfg["training"]["embedding_margin"] == 0.5
    assert cfg["training"]["embedding_pooling"] == "mean"
    assert cfg["training"]["lora"]["r"] == 16
    assert cfg["training"]["lora"]["alpha"] == 32
    assert float(cfg["training"]["lora"]["dropout"]) == 0.05
    assert cfg["training"]["lora"]["target_modules"] == ["query", "value"]
    lr_val = float(cfg["training"]["lr"])
    print(f"  ✓ Config: {config_path.name} verified (lr={lr_val}, sha256={c_sha256})")

    output_dir = REPO_ROOT / cfg["output"]
    if output_dir.exists() and (output_dir / "adapter_model.safetensors").exists():
        raise RuntimeError(f"Output directory {output_dir} already contains an adapter! Refusing to overwrite.")
    print(f"  ✓ Output directory: {output_dir.name} (clean)")

    hub_sha = verify_e5_hub_revision()

    return {
        "dataset_sha256": d_sha256,
        "config_sha256": c_sha256,
        "config_path": config_path,
        "output_dir": output_dir,
        "hub_sha": hub_sha,
        "expected_updates": 1857,
        "trainable_params": 294912,
        "lr": lr_val,
    }


def execute_training(preflight_meta: dict) -> dict:
    config_path = preflight_meta["config_path"]
    output_dir = preflight_meta["output_dir"]
    stem = config_path.stem
    log_file = LOGS_DIR / f"{stem}.log"

    print(f"\n=== Launching E5-small Training via Soup CLI ({config_path.name}) ===")
    cmd = [SOUP_BIN, "train", "-y", "--config", str(config_path)]
    print(f"Command: {' '.join(cmd)}")
    print(f"Logging to: {log_file}")

    start_time = time.perf_counter()
    start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"=== SOUP EMBEDDING TRAINING RUN: {config_path.name} ===\n")
        lf.write(f"Start timestamp: {start_iso}\n")
        lf.write(f"Command: {' '.join(cmd)}\n")
        lf.write(f"Base Model: {BASE_MODEL_NAME}\n")
        lf.write(f"Base Revision: {preflight_meta['hub_sha']}\n")
        lf.write(f"Dataset SHA256: {preflight_meta['dataset_sha256']}\n")
        lf.write(f"Config SHA256: {preflight_meta['config_sha256']}\n")
        lf.write("=" * 60 + "\n\n")
        lf.flush()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

        for line in iter(proc.stdout.readline, ""):
            sys.stdout.write(line)
            sys.stdout.flush()
            lf.write(line)
            lf.flush()

        proc.stdout.close()
        retcode = proc.wait()

    end_time = time.perf_counter()
    end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    duration_secs = round(end_time - start_time, 2)

    if retcode != 0:
        raise RuntimeError(f"Training failed with exit code {retcode}. See {log_file}")

    print(f"\n✓ Training completed in {duration_secs}s ({duration_secs/60:.2f} min)")

    # Post-training artifact verification
    print("\n=== Verifying Generated Adapter Artifacts ===")
    weights_path = output_dir / "adapter_model.safetensors"
    config_out = output_dir / "adapter_config.json"
    soup_run = output_dir / "soup_run.json"

    assert weights_path.exists(), f"Missing weights: {weights_path}"
    assert config_out.exists(), f"Missing config: {config_out}"
    assert soup_run.exists(), f"Missing soup_run: {soup_run}"

    weights_sha256 = compute_sha256(weights_path)
    weights_size = weights_path.stat().st_size
    print(f"  ✓ Adapter weights: {weights_path.name} ({weights_size:,} bytes, sha256={weights_sha256})")

    acfg = json.loads(config_out.read_text(encoding="utf-8"))
    assert acfg["r"] == 16
    assert acfg["lora_alpha"] == 32
    assert set(acfg["target_modules"]) == {"query", "value"}
    assert acfg["base_model_name_or_path"] == BASE_MODEL_NAME

    # Quick forward inference test with DenseRetriever
    try:
        from retrievers import DenseRetriever
    except ImportError:
        from scripts.retrievers import DenseRetriever

    dr = DenseRetriever(
        retriever_id=f"e5_ft_{stem}",
        model_id=BASE_MODEL_NAME,
        revision=EXPECTED_E5_REVISION,
        adapter_dir=str(output_dir),
        max_length=512,
        query_prefix="query: ",
        passage_prefix="passage: ",
        device="cpu",
    )
    test_vec = dr.encode_queries(["test query"])[0]
    assert test_vec.shape == (384,)

    summary = {
        "model_name": f"E5-small ({stem})",
        "base_model": BASE_MODEL_NAME,
        "base_revision": preflight_meta["hub_sha"],
        "dataset_path": str(DATASET_PATH.relative_to(REPO_ROOT)),
        "dataset_sha256": preflight_meta["dataset_sha256"],
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "config_sha256": preflight_meta["config_sha256"],
        "lr": preflight_meta["lr"],
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_seconds": duration_secs,
        "optimizer_updates": preflight_meta["expected_updates"],
        "trainable_parameters": preflight_meta["trainable_params"],
        "adapter_weights_sha256": weights_sha256,
        "adapter_weights_bytes": weights_size,
    }

    summary_file = LOGS_DIR / f"{stem}_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"✓ Summary written to {summary_file}")
    return summary


def parse_args():
    parser = argparse.ArgumentParser(description="Train E5-small LoRA adapter with Soup CLI")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to training config YAML",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    meta = run_preflight(args.config)
    summary = execute_training(meta)
    print("\nE5 TRAINING FINISHED SUCCESSFULLY!")
