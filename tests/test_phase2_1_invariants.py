"""Phase 2.1 Post-Training Artifact Verification Invariant Tests.

Verifies:
1. Exact semantic parity of adapter_config.json across all 6 models (A-full, A-matched, B, C-matched, C-matched-balanced, C-full).
2. Explains and asserts that target_modules is set-identical ({"query", "value"}).
3. All 6 checkpoints match their Phase 2 SHA256 checksums.
4. Base model revision is exactly 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 in all soup_run.json files.
5. DenseRetriever loading and embedding generation produces 384-dim, unit-normalized, deterministic vectors.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from retrievers import DenseRetriever, MINILM_MODEL_ID, MINILM_REVISION

EXPECTED_BASE_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BASE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHECKPOINTS = {
    "A-full": {
        "dir": REPO_ROOT / "output_embedding",
        "weights_sha256": "4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534",
        "config_sha256": "9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670",
    },
    "A-matched": {
        "dir": REPO_ROOT / "output/adapter_exp_a_matched",
        "weights_sha256": "81c35eeda72341bd5460eb3af547e2e52e0c5829c39c59a3103a2e90c7adebb1",
        "config_sha256": "9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670",
    },
    "B": {
        "dir": REPO_ROOT / "output/adapter_exp_b",
        "weights_sha256": "7ce33a5063deaa91c8f38d2bdab96d81a196ca129a01e86515bbc69429009c8a",
        "config_sha256": "9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670",
    },
    "C-matched": {
        "dir": REPO_ROOT / "output/adapter_exp_c_matched",
        "weights_sha256": "6fe28922a98f6c13afbb3709cd9486f2b2173166802d61831852d992ba3f21b5",
        "config_sha256": "9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670",
    },
    "C-matched-balanced": {
        "dir": REPO_ROOT / "output/adapter_exp_c_matched_balanced",
        "weights_sha256": "25e0064078516ff068b6db2bface1065059f0d44a7a33592e8c0eb2094367137",
        "config_sha256": "9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670",
    },
    "C-full": {
        "dir": REPO_ROOT / "output/adapter_exp_c_full",
        "weights_sha256": "145df326e64e6043d4fa313a1ef59d7ee958a705114978d1a3eaf7cb24fc0355",
        "config_sha256": "181ca4782837c30fd0bbc336d849f1daea9d57c2c0d32053ff66858a2d49ce8b",
    },
}


@pytest.mark.parametrize("name,info", CHECKPOINTS.items())
def test_checkpoint_checksums_and_provenance(name, info):
    """Verify weights and config SHA256 checksums match expected records."""
    d = info["dir"]
    assert d.exists(), f"Missing directory: {d}"

    w_path = d / "adapter_model.safetensors"
    assert w_path.exists(), f"Missing weights: {w_path}"
    w_hash = hashlib.sha256(w_path.read_bytes()).hexdigest()
    assert w_hash == info["weights_sha256"], f"{name} weights hash mismatch: {w_hash} != {info['weights_sha256']}"

    c_path = d / "adapter_config.json"
    assert c_path.exists(), f"Missing config: {c_path}"
    c_hash = hashlib.sha256(c_path.read_bytes()).hexdigest()
    assert c_hash == info["config_sha256"], f"{name} config hash mismatch: {c_hash} != {info['config_sha256']}"

    r_path = d / "soup_run.json"
    assert r_path.exists(), f"Missing soup_run.json: {r_path}"
    with open(r_path) as f:
        run = json.load(f)
    assert run["base_model"] == BASE_MODEL_NAME
    assert run["base_revision"] == EXPECTED_BASE_REVISION
    assert run["base_revision_source"] == "hub_commit"


def test_adapter_config_semantic_parity():
    """Verify that all 6 adapter_config.json files are semantically identical."""
    loaded_configs = {}
    for name, info in CHECKPOINTS.items():
        with open(info["dir"] / "adapter_config.json") as f:
            loaded_configs[name] = json.load(f)

    # Reference is A-matched
    ref = loaded_configs["A-matched"]

    for name, cfg in loaded_configs.items():
        assert cfg["base_model_name_or_path"] == BASE_MODEL_NAME
        assert cfg["peft_type"] == "LORA"
        assert cfg["task_type"] == "FEATURE_EXTRACTION"
        assert cfg["r"] == 16
        assert cfg["lora_alpha"] == 32
        assert cfg["lora_dropout"] == 0.05
        assert cfg["bias"] == "none"
        assert cfg["modules_to_save"] is None
        assert cfg["init_lora_weights"] is True
        assert cfg["inference_mode"] is True

        # Check target_modules set equality
        assert set(cfg["target_modules"]) == {"query", "value"}

        # Compare normalized dicts (where target_modules is sorted)
        norm_ref = dict(ref, target_modules=sorted(ref["target_modules"]))
        norm_cfg = dict(cfg, target_modules=sorted(cfg["target_modules"]))
        assert norm_ref == norm_cfg, f"{name} normalized config differs from reference"


@pytest.mark.parametrize("name,info", CHECKPOINTS.items())
def test_dense_retriever_smoke_inference(name, info):
    """Verify each adapter loads cleanly via DenseRetriever and computes valid embeddings."""
    inputs = [
        "How do I configure LoRA fine-tuning for embedding models?",
        "What is the Wald sequential probability ratio test?",
    ]
    retriever = DenseRetriever(
        retriever_id=f"test_{name}",
        model_id=MINILM_MODEL_ID,
        revision=MINILM_REVISION,
        adapter_dir=str(info["dir"]),
        pooling="mean",
        device="cpu",
    )

    emb = retriever.encode(inputs)
    assert emb.shape == (2, 384)
    assert not np.isnan(emb).any()
    assert not np.isinf(emb).any()
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)

    # Determinism
    emb2 = retriever.encode(inputs)
    assert np.allclose(emb, emb2, atol=1e-6)
