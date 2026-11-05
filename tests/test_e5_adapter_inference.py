"""Tests for E5-small fine-tuned adapter loading, inference parity, and invariance."""

import json
import sys
from pathlib import Path
import numpy as np
import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from retrievers import (
    DenseRetriever,
    RETRIEVER_SPECS,
    build_passage_text,
    build_retriever,
    retrieve_ranked,
)
ADAPTER_DIR = REPO_ROOT / "output" / "adapter_e5_exp_b"


@pytest.fixture(scope="module")
def sample_corpus():
    return [
        {
            "chunk_id": "doc1::sec1::sub_000",
            "doc_name": "doc1",
            "heading": "Overview",
            "heading_prefix": "doc1: Overview",
            "text": "FastAPI is a modern, fast web framework for building APIs with Python.",
        },
        {
            "chunk_id": "doc1::sec2::sub_000",
            "doc_name": "doc1",
            "heading": "Routing",
            "heading_prefix": "doc1: Routing",
            "text": "Path parameters can be declared using standard Python type annotations.",
        },
    ]


def test_adapter_config_matches_training():
    cfg_file = ADAPTER_DIR / "adapter_config.json"
    assert cfg_file.exists(), f"Missing {cfg_file}"
    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))

    assert cfg["r"] == 16
    assert cfg["lora_alpha"] == 32
    assert float(cfg["lora_dropout"]) == 0.05
    assert set(cfg["target_modules"]) == {"query", "value"}
    assert cfg["base_model_name_or_path"] == "intfloat/e5-small-v2"


def test_adapter_weights_exist():
    weights_file = ADAPTER_DIR / "adapter_model.safetensors"
    assert weights_file.exists()
    assert weights_file.stat().st_size > 500_000


def test_retriever_spec_registration():
    for r_id, exp_dir in [
        ("e5_small_ft", "output/adapter_e5_exp_b"),
        ("e5_small_ft_lr2e5", "output/adapter_e5_exp_b_lr2e5"),
        ("e5_small_ft_lr2e4", "output/adapter_e5_exp_b_lr2e4"),
    ]:
        assert r_id in RETRIEVER_SPECS
        spec = RETRIEVER_SPECS[r_id]
        assert spec["model"] == "intfloat/e5-small-v2"
        assert spec["revision"] == "ffb93f3bd4047442299a41ebb6fa998a38507c52"
        assert spec["adapter_dir"] == exp_dir
        assert spec["query_prefix"] == "query: "
        assert spec["passage_prefix"] == "passage: "


def test_e5_fine_tuned_encoding():
    retriever = build_retriever("e5_small_ft", repo_root=REPO_ROOT)
    queries = ["how to declare path parameters in Python?"]
    query_vecs = retriever.encode_queries(queries)

    assert query_vecs.shape == (1, 384)
    assert np.isfinite(query_vecs).all()

    # L2 norm must be 1.0
    norm = np.linalg.norm(query_vecs[0])
    assert np.isclose(norm, 1.0, atol=1e-5)


def test_e5_fine_tuned_deterministic():
    retriever = build_retriever("e5_small_ft", repo_root=REPO_ROOT)
    queries = ["test determinism query"]
    vec1 = retriever.encode_queries(queries)
    vec2 = retriever.encode_queries(queries)
    assert np.allclose(vec1, vec2, atol=1e-6)


def test_frozen_e5_unaltered_by_fine_tuned():
    frozen_r = build_retriever("e5_small", repo_root=REPO_ROOT)
    ft_r = build_retriever("e5_small_ft", repo_root=REPO_ROOT)

    query = ["what is soup shrink?"]
    frozen_vec = frozen_r.encode_queries(query)[0]
    ft_vec = ft_r.encode_queries(query)[0]

    assert frozen_vec.shape == (384,)
    assert ft_vec.shape == (384,)
    # Verify they produce different vectors (fine-tuning altered weights)
    diff = np.max(np.abs(frozen_vec - ft_vec))
    assert diff > 1e-4, "Fine-tuned adapter has identical weights to frozen base!"


def test_e5_ft_ranked_retrieval(sample_corpus):
    retriever = build_retriever("e5_small_ft", repo_root=REPO_ROOT)
    ranked = retrieve_ranked(
        retriever,
        sample_corpus,
        ["how do path parameters work?"],
        top_k=2,
    )
    assert len(ranked) == 1
    assert len(ranked[0]) == 2
    # Verify rankings have valid chunk_id, rank, and score
    top_hit = ranked[0][0]
    assert "chunk_id" in top_hit
    assert top_hit["rank"] == 1
    assert np.isfinite(top_hit["score"])
