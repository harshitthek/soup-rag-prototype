"""Phase 2.0 Adapter Retraining Invariant Tests.

Verifies:
1. All 5 newly trained adapter checkpoints exist and contain required files.
2. Exact LoRA configuration parity across all 5 new checkpoints against adapter_config.json.
3. Base model revision provenance in soup_run.json (1110a243fdf4706b3f48f1d95db1a4f5529b4d41, hub_commit).
4. Historical A-full baseline in output_embedding remains intact and byte-identical.
5. All newly trained adapters load successfully with PeftModel and produce finite unit-length embeddings.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
import torch
from peft import PeftModel
from transformers import AutoModel, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
BASELINE_DIR = REPO_ROOT / "output_embedding"

EXPECTED_BASE_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BASE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BASELINE_A_FULL_HASH = "4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534"

NEW_CHECKPOINTS = [
    "adapter_exp_a_matched",
    "adapter_exp_b",
    "adapter_exp_c_matched",
    "adapter_exp_c_matched_balanced",
    "adapter_exp_c_full",
]


def test_baseline_a_full_preservation():
    """Verify that the immutable historical A-full baseline was NOT overwritten or modified."""
    weights_path = BASELINE_DIR / "adapter_model.safetensors"
    assert weights_path.exists(), "A-full baseline weights missing"
    h = hashlib.sha256(weights_path.read_bytes()).hexdigest()
    assert h == BASELINE_A_FULL_HASH, f"A-full weights modified! Hash: {h} != {BASELINE_A_FULL_HASH}"


@pytest.mark.parametrize("ckpt_name", NEW_CHECKPOINTS)
def test_checkpoint_files_and_config_parity(ckpt_name):
    """Verify each newly trained adapter directory contains valid weights and matching LoRA config."""
    ckpt_dir = OUTPUT_DIR / ckpt_name
    assert ckpt_dir.exists(), f"Missing checkpoint directory: {ckpt_dir}"

    weights_path = ckpt_dir / "adapter_model.safetensors"
    assert weights_path.exists(), f"Missing weights: {weights_path}"
    assert weights_path.stat().st_size > 0, f"Empty weights: {weights_path}"

    cfg_path = ckpt_dir / "adapter_config.json"
    assert cfg_path.exists(), f"Missing config: {cfg_path}"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["base_model_name_or_path"] == BASE_MODEL_NAME
    assert cfg["peft_type"] == "LORA"
    assert cfg["r"] == 16
    assert cfg["lora_alpha"] == 32
    assert cfg["lora_dropout"] == 0.05
    assert set(cfg["target_modules"]) == {"query", "value"}

    run_path = ckpt_dir / "soup_run.json"
    assert run_path.exists(), f"Missing soup_run.json: {run_path}"
    with open(run_path, "r", encoding="utf-8") as f:
        run = json.load(f)

    assert run["base_model"] == BASE_MODEL_NAME
    assert run["base_revision"] == EXPECTED_BASE_REVISION
    assert run["base_revision_source"] == "hub_commit"
    assert run["schema_version"] == 1


@pytest.mark.parametrize("ckpt_name", NEW_CHECKPOINTS)
def test_checkpoint_loadable_and_computes_embeddings(ckpt_name):
    """Verify each newly trained adapter can be loaded and executes forward pass with valid embeddings."""
    ckpt_dir = str(OUTPUT_DIR / ckpt_name)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    base = AutoModel.from_pretrained(BASE_MODEL_NAME)
    model = PeftModel.from_pretrained(base, ckpt_dir)
    model.eval()

    test_text = "Soup training pipeline evaluation for retrieval augmented generation."
    inputs = tokenizer(test_text, return_tensors="pt", max_length=128, truncation=True)

    with torch.no_grad():
        outputs = model(**inputs)
        # Mean pooling
        mask = inputs["attention_mask"].unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(outputs.last_hidden_state * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        mean_pooled = sum_embeddings / sum_mask
        normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)

    assert not torch.isnan(normalized).any(), f"NaN in embeddings for {ckpt_name}"
    assert not torch.isinf(normalized).any(), f"Inf in embeddings for {ckpt_name}"
    assert normalized.shape == (1, 384), f"Unexpected embedding shape: {normalized.shape}"
    norm = torch.norm(normalized, dim=1).item()
    assert abs(norm - 1.0) < 1e-5, f"Embedding not unit-normalized: norm={norm}"
