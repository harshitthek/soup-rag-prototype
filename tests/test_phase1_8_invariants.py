"""Phase 1.8 Final Run Manifest Invariant Tests.

Verifies:
1. Frozen benchmark SHA256 integrity across all 5 canonical files.
2. A-full existing checkpoint provenance and weight checksum.
3. Training configuration files integrity, dataset linkages, and isolated output paths.
4. Exact dataloader partial batch and optimizer update arithmetic.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"
OUTPUT_DIR = REPO_ROOT / "output_embedding"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}

A_FULL_CHECKPOINT_HASH = "4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534"


def test_frozen_benchmark_integrity():
    """Verify that all frozen benchmark files remain untouched with exact SHA256 hashes."""
    for fname, expected_hash in FROZEN_CHECKSUMS.items():
        file_path = DATA_DIR / fname
        assert file_path.exists(), f"Frozen file missing: {fname}"
        h = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert h == expected_hash, f"Hash mismatch for {fname}: got {h}, expected {expected_hash}"


def test_a_full_checkpoint_provenance():
    """Verify that the existing A-full checkpoint in output_embedding is valid, intact, and matches provenance."""
    weights_path = OUTPUT_DIR / "adapter_model.safetensors"
    assert weights_path.exists(), "A-full adapter weights missing in output_embedding/"
    h = hashlib.sha256(weights_path.read_bytes()).hexdigest()
    assert h == A_FULL_CHECKPOINT_HASH, f"A-full weights hash mismatch: got {h}, expected {A_FULL_CHECKPOINT_HASH}"

    config_path = OUTPUT_DIR / "adapter_config.json"
    assert config_path.exists(), "A-full adapter config missing"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["base_model_name_or_path"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg["peft_type"] == "LORA"
    assert cfg["r"] == 16
    assert cfg["lora_alpha"] == 32
    assert set(cfg["target_modules"]) == {"query", "value"}

    run_path = OUTPUT_DIR / "soup_run.json"
    assert run_path.exists(), "A-full soup_run.json missing"
    with open(run_path, "r", encoding="utf-8") as f:
        run = json.load(f)
    assert run["run_id"] == "run_20261029_004201_f3588165"


def test_training_configs_integrity():
    """Verify all 6 experiment YAML configs exist and have consistent hyperparameters and unique outputs."""
    configs = [
        ("embedding_exp_a_full.yaml", "data/train_triplets.jsonl", "output/adapter_exp_a_full", 3234),
        ("embedding_exp_a_matched.yaml", "data/triplets_exp_a_matched_v1_5.jsonl", "output/adapter_exp_a_matched", 2475),
        ("embedding_exp_b.yaml", "data/triplets_exp_b_v1_5.jsonl", "output/adapter_exp_b", 2475),
        ("embedding_exp_c_matched.yaml", "data/triplets_exp_c_matched_v1_5.jsonl", "output/adapter_exp_c_matched", 2475),
        ("embedding_exp_c_matched_balanced.yaml", "data/triplets_exp_c_matched_balanced_v1_6.jsonl", "output/adapter_exp_c_matched_balanced", 2475),
        ("embedding_exp_c_full.yaml", "data/triplets_exp_c_full_v1_5.jsonl", "output/adapter_exp_c_full", 6771),
    ]

    seen_outputs = set()
    for cfg_name, data_path, out_dir, expected_lines in configs:
        p = CONFIG_DIR / cfg_name
        assert p.exists(), f"Config file missing: {cfg_name}"
        with open(p, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)

        assert y["base"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert y["task"] == "embedding"
        assert y["data"]["train"] == data_path
        assert y["data"]["max_length"] == 256
        assert y["training"]["epochs"] == 3
        assert float(y["training"]["lr"]) == 2e-5
        assert y["training"]["batch_size"] == 4
        assert y["training"]["gradient_accumulation_steps"] == 1
        assert y["training"]["seed"] == 42
        assert y["training"]["data_seed"] == 42
        assert y["training"]["embedding_loss"] == "triplet"
        assert y["training"]["embedding_margin"] == 0.5
        assert y["training"]["embedding_pooling"] == "mean"
        assert y["training"]["lora"]["r"] == 16
        assert y["training"]["lora"]["alpha"] == 32

        assert y["output"] == out_dir
        assert out_dir not in seen_outputs, f"Duplicate output directory detected: {out_dir}"
        seen_outputs.add(out_dir)

        # Check data file exists and line count
        data_file = REPO_ROOT / data_path
        assert data_file.exists(), f"Data file missing: {data_path}"
        line_count = sum(1 for _ in open(data_file, "r", encoding="utf-8"))
        assert line_count == expected_lines, f"Line count mismatch in {data_path}: got {line_count}, expected {expected_lines}"


def test_partial_batch_and_update_arithmetic():
    """Verify exact partial batch sizes and resulting optimizer update steps."""
    batch_size = 4
    epochs = 3

    cases = [
        ("A-full", 3234, 808, 2, 809, 2427),
        ("A-matched", 2475, 618, 3, 619, 1857),
        ("B", 2475, 618, 3, 619, 1857),
        ("C-matched", 2475, 618, 3, 619, 1857),
        ("C-matched-balanced", 2475, 618, 3, 619, 1857),
        ("C-full", 6771, 1692, 3, 1693, 5079),
    ]

    for name, n_samples, exp_full_batches, exp_partial_batch, exp_batches_per_epoch, exp_total_updates in cases:
        full_batches = n_samples // batch_size
        partial_batch = n_samples % batch_size
        batches_per_epoch = math.ceil(n_samples / batch_size)
        total_updates = batches_per_epoch * epochs

        assert full_batches == exp_full_batches, f"{name}: full batches mismatch"
        assert partial_batch == exp_partial_batch, f"{name}: partial batch mismatch"
        assert batches_per_epoch == exp_batches_per_epoch, f"{name}: batches per epoch mismatch"
        assert total_updates == exp_total_updates, f"{name}: total updates mismatch"
