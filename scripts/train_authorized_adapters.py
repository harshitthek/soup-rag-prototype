#!/usr/bin/env python3
"""Phase 2.0: Authorized Adapter Retraining Driver Script.

Executes the five authorized adapter training runs sequentially on Apple Silicon (MPS):
1. A-matched (1,857 updates)
2. B (1,857 updates)
3. C-matched (1,857 updates)
4. C-matched-balanced (1,857 updates)
5. C-full (5,079 updates)

Implements:
- Strict preflight parameter and dataset verification.
- Hub commit revision pinning check (1110a243fdf4706b3f48f1d95db1a4f5529b4d41).
- Non-destructive directory protection.
- Live console logging and persistent log saving in results/training_logs/.
- Post-training artifact verification, SHA256 checksumming, and LoRA parity assertions.
- Verification of frozen benchmark files.
"""

from __future__ import annotations

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
SOUP_BIN = "/Users/pernavjain/Documents/Soup/.venv/bin/soup"
SOUP_PYTHON = "/Users/pernavjain/Documents/Soup/.venv/bin/python"
LOGS_DIR = REPO_ROOT / "results" / "training_logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_BASE_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BASE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}

RUNS = [
    {
        "order": 1,
        "name": "A-matched",
        "config_path": "config/embedding_exp_a_matched.yaml",
        "dataset_path": "data/triplets_exp_a_matched_v1_5.jsonl",
        "expected_records": 2475,
        "expected_updates": 1857,
        "output_dir": "output/adapter_exp_a_matched",
    },
    {
        "order": 2,
        "name": "B",
        "config_path": "config/embedding_exp_b.yaml",
        "dataset_path": "data/triplets_exp_b_v1_5.jsonl",
        "expected_records": 2475,
        "expected_updates": 1857,
        "output_dir": "output/adapter_exp_b",
    },
    {
        "order": 3,
        "name": "C-matched",
        "config_path": "config/embedding_exp_c_matched.yaml",
        "dataset_path": "data/triplets_exp_c_matched_v1_5.jsonl",
        "expected_records": 2475,
        "expected_updates": 1857,
        "output_dir": "output/adapter_exp_c_matched",
    },
    {
        "order": 4,
        "name": "C-matched-balanced",
        "config_path": "config/embedding_exp_c_matched_balanced.yaml",
        "dataset_path": "data/triplets_exp_c_matched_balanced_v1_6.jsonl",
        "expected_records": 2475,
        "expected_updates": 1857,
        "output_dir": "output/adapter_exp_c_matched_balanced",
    },
    {
        "order": 5,
        "name": "C-full",
        "config_path": "config/embedding_exp_c_full.yaml",
        "dataset_path": "data/triplets_exp_c_full_v1_5.jsonl",
        "expected_records": 6771,
        "expected_updates": 5079,
        "output_dir": "output/adapter_exp_c_full",
    },
]


def compute_sha256(path: Path) -> str:
    """Compute hex SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_frozen_files():
    """Verify all frozen benchmark files match canonical checksums."""
    print("Verifying frozen benchmark file checksums...")
    for fname, expected in FROZEN_CHECKSUMS.items():
        p = REPO_ROOT / "data" / fname
        if not p.exists():
            raise FileNotFoundError(f"Frozen file missing: {p}")
        actual = compute_sha256(p)
        if actual != expected:
            raise ValueError(f"Frozen file altered: {fname} (got {actual}, expected {expected})")
    print("  ✓ All 5 frozen benchmark files match canonical SHA256 hashes.")


def verify_hub_revision() -> str:
    """Query Hugging Face Hub to verify the remote commit SHA."""
    api = HfApi()
    info = api.model_info(BASE_MODEL_NAME, timeout=10)
    sha = info.sha
    if sha != EXPECTED_BASE_REVISION:
        raise RuntimeError(
            f"Hugging Face Hub base model revision mismatch: got {sha}, expected {EXPECTED_BASE_REVISION}"
        )
    return sha


def run_preflight(run: dict) -> dict:
    """Run strict preflight checks before launching training."""
    print(f"\n[{run['name']}] Running preflight checks...")

    # 1. Dataset check
    d_path = REPO_ROOT / run["dataset_path"]
    if not d_path.exists():
        raise FileNotFoundError(f"Dataset missing: {d_path}")
    data_bytes = d_path.read_bytes()
    record_count = sum(1 for line in data_bytes.splitlines() if line.strip())
    if record_count != run["expected_records"]:
        raise ValueError(
            f"Record count mismatch in {d_path}: got {record_count}, expected {run['expected_records']}"
        )
    d_sha256 = compute_sha256(d_path)
    print(f"  ✓ Dataset: {run['dataset_path']} ({record_count} records, sha256={d_sha256[:16]}...)")

    # 2. Config check
    c_path = REPO_ROOT / run["config_path"]
    if not c_path.exists():
        raise FileNotFoundError(f"Config missing: {c_path}")
    c_sha256 = compute_sha256(c_path)
    with open(c_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 3. Hyperparameter assertions
    assert cfg["base"] == BASE_MODEL_NAME
    assert cfg["task"] == "embedding"
    assert cfg["backend"] == "transformers"
    assert cfg["training"]["epochs"] == 3
    assert float(cfg["training"]["lr"]) == 2e-5
    assert cfg["training"]["batch_size"] == 4
    assert cfg["training"]["gradient_accumulation_steps"] == 1
    assert cfg["training"]["seed"] == 42
    assert cfg["training"]["data_seed"] == 42
    assert cfg["training"]["quantization"] == "none"
    assert cfg["training"]["embedding_loss"] == "triplet"
    assert cfg["training"]["embedding_margin"] == 0.5
    assert cfg["training"]["embedding_pooling"] == "mean"

    lora = cfg["training"]["lora"]
    assert lora["r"] == 16
    assert lora["alpha"] == 32
    assert float(lora["dropout"]) == 0.05
    assert lora["target_modules"] == ["query", "value"]
    assert cfg["output"] == run["output_dir"]
    print(f"  ✓ Config: {run['config_path']} verified (sha256={c_sha256[:16]}...)")

    # 4. Output directory non-destructive check
    out_dir = REPO_ROOT / run["output_dir"]
    if out_dir.exists() and (out_dir / "adapter_model.safetensors").exists():
        raise RuntimeError(
            f"Output directory {out_dir} already contains an adapter! Refusing to overwrite."
        )
    print(f"  ✓ Output target: {run['output_dir']} (clean)")

    # 5. Base revision lock check
    hub_sha = verify_hub_revision()
    print(f"  ✓ Hub base model revision: {hub_sha} (verified)")

    return {
        "dataset_sha256": d_sha256,
        "config_sha256": c_sha256,
        "hub_sha": hub_sha,
    }


def execute_training_run(run: dict, preflight_meta: dict) -> dict:
    """Execute training using the official Soup CLI trainer and log output."""
    name = run["name"]
    cfg_path = run["config_path"]
    out_dir = REPO_ROOT / run["output_dir"]
    log_file = LOGS_DIR / f"{name.lower().replace('-', '_')}.log"

    print(f"\n[{name}] Launching training via Soup CLI...")
    cmd = [SOUP_BIN, "train", "-y", "--config", cfg_path]
    print(f"  Command: {' '.join(cmd)}")
    print(f"  Logging to: {log_file}")

    start_time = time.time()
    start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"=== SOUP TRAINING RUN: {name} ===\n")
        lf.write(f"Start timestamp: {start_iso}\n")
        lf.write(f"Command: {' '.join(cmd)}\n")
        lf.write(f"Dataset SHA256: {preflight_meta['dataset_sha256']}\n")
        lf.write(f"Config SHA256: {preflight_meta['config_sha256']}\n")
        lf.write(f"Base Revision: {preflight_meta['hub_sha']}\n")
        lf.write("=" * 60 + "\n\n")
        lf.flush()

        process = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            lf.write(line)
            lf.flush()

        retcode = process.wait()

    end_time = time.time()
    end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    duration_secs = round(end_time - start_time, 2)

    if retcode != 0:
        raise RuntimeError(f"Training run {name} failed with exit code {retcode}. Check {log_file}")

    print(f"\n[{name}] Training completed in {duration_secs}s (exit 0).")

    # Post-flight checks
    print(f"[{name}] Running post-flight artifact verification...")
    weights_path = out_dir / "adapter_model.safetensors"
    if not weights_path.exists():
        raise FileNotFoundError(f"Missing adapter weights: {weights_path}")
    weights_sha256 = compute_sha256(weights_path)
    weights_size = weights_path.stat().st_size

    adapter_cfg_path = out_dir / "adapter_config.json"
    if not adapter_cfg_path.exists():
        raise FileNotFoundError(f"Missing adapter config: {adapter_cfg_path}")
    adapter_cfg_sha256 = compute_sha256(adapter_cfg_path)
    with open(adapter_cfg_path, "r", encoding="utf-8") as f:
        acfg = json.load(f)
    assert acfg["r"] == 16
    assert acfg["lora_alpha"] == 32
    assert acfg["lora_dropout"] == 0.05
    assert set(acfg["target_modules"]) == {"query", "value"}
    assert acfg["base_model_name_or_path"] == BASE_MODEL_NAME

    soup_run_path = out_dir / "soup_run.json"
    if not soup_run_path.exists():
        raise FileNotFoundError(f"Missing soup_run.json: {soup_run_path}")
    soup_run_sha256 = compute_sha256(soup_run_path)
    with open(soup_run_path, "r", encoding="utf-8") as f:
        srun = json.load(f)
    assert srun["base_model"] == BASE_MODEL_NAME
    assert srun["base_revision"] == EXPECTED_BASE_REVISION
    assert srun["base_revision_source"] == "hub_commit"

    print(f"  ✓ Adapter weights: {weights_size:,} bytes (sha256={weights_sha256})")
    print(f"  ✓ Adapter config: sha256={adapter_cfg_sha256}")
    print(f"  ✓ Soup run metadata: base_revision={srun['base_revision']} ({srun['base_revision_source']})")

    return {
        "name": name,
        "order": run["order"],
        "status": "COMPLETED",
        "start_iso": start_iso,
        "end_iso": end_iso,
        "duration_secs": duration_secs,
        "expected_updates": run["expected_updates"],
        "config_path": run["config_path"],
        "config_sha256": preflight_meta["config_sha256"],
        "dataset_path": run["dataset_path"],
        "dataset_sha256": preflight_meta["dataset_sha256"],
        "output_dir": run["output_dir"],
        "adapter_weights_sha256": weights_sha256,
        "adapter_weights_bytes": weights_size,
        "adapter_config_sha256": adapter_cfg_sha256,
        "soup_run_sha256": soup_run_sha256,
        "run_id": srun.get("run_id"),
        "base_revision": srun.get("base_revision"),
        "base_revision_source": srun.get("base_revision_source"),
        "log_file": str(log_file.relative_to(REPO_ROOT)),
    }


def main():
    print("=" * 70)
    print("PHASE 2.0: AUTHORIZED ADAPTER RETRAINING (PATH A)")
    print(f"Execution Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 70)

    # Pre-training integrity check
    verify_frozen_files()

    results = []
    total_start = time.time()

    for run in RUNS:
        print("\n" + "#" * 70)
        print(f"STARTING RUN {run['order']}/5: {run['name']}")
        print("#" * 70)

        preflight_meta = run_preflight(run)
        run_res = execute_training_run(run, preflight_meta)
        results.append(run_res)

    total_duration = round(time.time() - total_start, 2)
    print("\n" + "=" * 70)
    print(f"ALL 5 ADAPTER TRAINING RUNS COMPLETED SUCCESSFULLY in {total_duration}s!")
    print("=" * 70)

    # Post-training integrity check
    verify_frozen_files()

    summary_file = REPO_ROOT / "results" / "phase_2_training_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "total_duration_secs": total_duration,
                "runs": results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved structured execution summary to {summary_file}")


if __name__ == "__main__":
    main()
