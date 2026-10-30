"""Tests for scripts/retrievers.py.

BM25 tests need ``rank_bm25``; dense-model tests need torch/transformers
(and peft for the adapter case). Tests skip when the dependency is missing
so metric-only environments stay green.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from retrievers import (  # noqa: E402
    BM25Retriever,
    DenseRetriever,
    E5_MODEL_ID,
    E5_REVISION,
    MINILM_MODEL_ID,
    MINILM_REVISION,
    RETRIEVER_SPECS,
    build_passage_text,
    build_retriever,
    retrieve_ranked,
)

rank_bm25 = pytest.importorskip("rank_bm25")


def make_chunks() -> list[dict]:
    return [
        {
            "chunk_id": "d::alpha",
            "doc_name": "d",
            "heading": "Alpha",
            "heading_prefix": "d: Alpha",
            "text": "soup adapters merge weights with ties strategy",
        },
        {
            "chunk_id": "d::beta::sub_000",
            "doc_name": "d",
            "heading": "Beta",
            "heading_prefix": "d: Beta",
            "text": "airgap bundle transfers models across networks",
        },
        {
            "chunk_id": "d::beta::sub_001",
            "doc_name": "d",
            "heading": "Beta",
            "heading_prefix": "d: Beta",
            "text": "the bundle includes config and weights",
        },
    ]


class TestBM25:
    def test_exact_term_match_ranks_first(self):
        chunks = make_chunks()
        r = BM25Retriever()
        r.fit(chunks)
        ranked = retrieve_ranked(r, chunks, ["how do i merge adapters with ties"], top_k=3)
        assert ranked[0][0]["chunk_id"] == "d::alpha"
        assert [e["rank"] for e in ranked[0]] == [1, 2, 3]

    def test_lowercasing(self):
        chunks = make_chunks()
        r = BM25Retriever()
        r.fit(chunks)
        ranked = retrieve_ranked(r, chunks, ["AIRGAP BUNDLE"], top_k=1)
        assert ranked[0][0]["chunk_id"] == "d::beta::sub_000"

    def test_deterministic(self):
        chunks = make_chunks()
        r = BM25Retriever()
        r.fit(chunks)
        a = retrieve_ranked(r, chunks, ["merge strategy"], top_k=3)
        b = retrieve_ranked(r, chunks, ["merge strategy"], top_k=3)
        assert [e["chunk_id"] for e in a[0]] == [e["chunk_id"] for e in b[0]]

    def test_config_records_fixed_parameters(self):
        cfg = BM25Retriever().config()
        assert cfg["k1"] == 1.5
        assert cfg["b"] == 0.75
        assert "tuning" in cfg and "none" in cfg["tuning"]

    def test_score_before_fit_raises(self):
        with pytest.raises(RuntimeError):
            BM25Retriever().score("x")


class TestDenseRetrieverConfig:
    def test_e5_spec_pins_revision_prefixes_and_length(self):
        spec = RETRIEVER_SPECS["e5_small"]
        assert spec["model"] == E5_MODEL_ID
        assert spec["revision"] == E5_REVISION
        assert spec["max_length"] == 512
        assert spec["query_prefix"] == "query: "
        assert spec["passage_prefix"] == "passage: "

    def test_minilm_spec_pins_revision(self):
        spec = RETRIEVER_SPECS["mini_lm_frozen"]
        assert spec["model"] == MINILM_MODEL_ID
        assert spec["revision"] == MINILM_REVISION
        assert spec["max_length"] == 256

    def test_config_available_without_loading_model(self):
        r = build_retriever("e5_small", repo_root=REPO_ROOT)
        assert isinstance(r, DenseRetriever)
        cfg = r.config()
        assert cfg["model"] == E5_MODEL_ID
        assert cfg["revision"] == E5_REVISION
        assert not r._loaded

    def test_unknown_retriever_rejected(self):
        with pytest.raises(ValueError):
            build_retriever("nope", repo_root=REPO_ROOT)

    def test_non_mean_pooling_rejected(self):
        with pytest.raises(ValueError):
            DenseRetriever("x", MINILM_MODEL_ID, pooling="cls")


class TestBuildPassageText:
    def test_prefix_plus_body(self):
        chunk = {
            "heading_prefix": "d: Alpha",
            "doc_name": "d",
            "text": "body text",
        }
        assert build_passage_text(chunk) == "d: Alpha\n\nbody text"

    def test_fallback_to_doc_name(self):
        chunk = {"heading_prefix": "", "doc_name": "d", "text": "body"}
        assert build_passage_text(chunk) == "d\n\nbody"


class TestDenseEncoding:
    """Real-model smoke tests; skipped when torch is unavailable."""

    def test_minilm_frozen_encodes_384d_unit_norm(self):
        torch = pytest.importorskip("torch")
        transformers = pytest.importorskip("transformers")
        r = DenseRetriever(
            "mini_lm_frozen",
            MINILM_MODEL_ID,
            revision=MINILM_REVISION,
            max_length=256,
        )
        vecs = r.encode(["soup train", "evaluation probes"])
        assert vecs.shape == (2, 384)
        norms = (vecs**2).sum(axis=1) ** 0.5
        assert torch.allclose(torch.tensor(norms), torch.ones(2), atol=1e-5)

    def test_e5_query_prefix_applied(self):
        r = build_retriever("e5_small", repo_root=REPO_ROOT)
        texts = ["test query"]
        assert r.query_prefix + texts[0] == "query: test query"
        assert r.passage_prefix + "doc text" == "passage: doc text"

    def test_e5_real_encode_384d_unit_norm(self):
        pytest.importorskip("torch")
        pytest.importorskip("transformers")
        r = DenseRetriever(
            "e5_small",
            E5_MODEL_ID,
            revision=E5_REVISION,
            max_length=512,
            query_prefix="query: ",
            passage_prefix="passage: ",
        )
        vecs = r.encode_queries(["what is a ship verdict", "define lora rank"])
        assert vecs.shape == (2, 384)
        norms = (vecs**2).sum(axis=1) ** 0.5
        import numpy as np

        assert np.allclose(norms, np.ones(2), atol=1e-5)
