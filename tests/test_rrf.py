"""Unit tests for Reciprocal Rank Fusion (RRF) in scripts/fusion.py."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fusion import DEFAULT_RRF_K, fuse_per_query, reciprocal_rank_fusion


class TestReciprocalRankFusion:
    def test_hand_calculated_math_two_runs(self):
        """Verify RRF formula against exact hand-calculated fractional values."""
        # Doc A: rank 1 in run 0, rank 2 in run 1 -> 1/61 + 1/62 = 123 / 3782
        # Doc B: rank 2 in run 0, rank 1 in run 1 -> 1/62 + 1/61 = 123 / 3782
        # Doc C: rank 3 in run 0, not in run 1 -> 1/63
        # Doc D: not in run 0, rank 3 in run 1 -> 1/63
        run0 = [{"chunk_id": "docA"}, {"chunk_id": "docB"}, {"chunk_id": "docC"}]
        run1 = [{"chunk_id": "docB"}, {"chunk_id": "docA"}, {"chunk_id": "docD"}]

        fused = reciprocal_rank_fusion([run0, run1], k=60, top_k=10)

        # Expected scores
        expected_score_ab = (1.0 / 61.0) + (1.0 / 62.0)
        expected_score_cd = 1.0 / 63.0

        assert len(fused) == 4
        # Doc A and Doc B have identical scores; tie-break is chunk_id ascending ("docA" < "docB")
        assert fused[0]["chunk_id"] == "docA"
        assert fused[0]["rank"] == 1
        assert math.isclose(fused[0]["score"], expected_score_ab, rel_tol=1e-9)

        assert fused[1]["chunk_id"] == "docB"
        assert fused[1]["rank"] == 2
        assert math.isclose(fused[1]["score"], expected_score_ab, rel_tol=1e-9)

        # Doc C and Doc D have identical scores; tie-break "docC" < "docD"
        assert fused[2]["chunk_id"] == "docC"
        assert fused[2]["rank"] == 3
        assert math.isclose(fused[2]["score"], expected_score_cd, rel_tol=1e-9)

        assert fused[3]["chunk_id"] == "docD"
        assert fused[3]["rank"] == 4
        assert math.isclose(fused[3]["score"], expected_score_cd, rel_tol=1e-9)

    def test_single_retriever_appearance(self):
        """A document appearing in only one retriever still gets its proper reciprocal rank."""
        run0 = [{"chunk_id": "docA"}]
        run1 = []  # Empty

        fused = reciprocal_rank_fusion([run0, run1], k=60, top_k=5)
        assert len(fused) == 1
        assert fused[0]["chunk_id"] == "docA"
        assert math.isclose(fused[0]["score"], 1.0 / 61.0)
        assert fused[0]["component_ranks"] == {0: 1}

    def test_different_ranking_orders_reordering(self):
        """Tests that a document with strong agreement across both runs beats a top-1 doc in only one run."""
        # Doc X: rank 2 in BM25, rank 2 in E5 -> 1/62 + 1/62 = 2/62 = 1/31 ~ 0.032258
        # Doc Y: rank 1 in BM25, rank 100 in E5 -> 1/61 + 1/160 = 0.016393 + 0.00625 = 0.022643
        # Doc Z: rank 100 in BM25, rank 1 in E5 -> 1/160 + 1/61 = 0.022643
        run0 = [{"chunk_id": "docY", "rank": 1}, {"chunk_id": "docX", "rank": 2}, {"chunk_id": "docZ", "rank": 100}]
        run1 = [{"chunk_id": "docZ", "rank": 1}, {"chunk_id": "docX", "rank": 2}, {"chunk_id": "docY", "rank": 100}]

        fused = reciprocal_rank_fusion([run0, run1], k=60, top_k=3)
        assert fused[0]["chunk_id"] == "docX"
        assert fused[0]["rank"] == 1
        # docY and docZ tie in score; tie-breaker docY < docZ
        assert fused[1]["chunk_id"] == "docY"
        assert fused[2]["chunk_id"] == "docZ"

    def test_duplicate_document_handling_in_run(self):
        """Duplicates within a single run must not be counted twice; best rank is used."""
        run0 = [{"chunk_id": "docA"}, {"chunk_id": "docA"}, {"chunk_id": "docB"}]
        run1 = [{"chunk_id": "docB"}, {"chunk_id": "docB"}]

        fused = reciprocal_rank_fusion([run0, run1], k=60, top_k=5)
        assert len(fused) == 2
        # docA: rank 1 in run0 -> 1/61
        # docB: rank 2 in run0, rank 1 in run1 -> 1/62 + 1/61
        assert fused[0]["chunk_id"] == "docB"
        assert fused[1]["chunk_id"] == "docA"

    def test_deterministic_tie_breaking(self):
        """Exact score ties must be broken deterministically by chunk_id ascending."""
        run0 = ["gamma", "beta", "alpha"]
        run1 = ["delta"]  # rank 1

        # All four docs:
        # gamma: 1/61
        # beta: 1/62
        # alpha: 1/63
        # delta: 1/61
        # gamma and delta tie at 1/61. "delta" < "gamma" alphabetically.
        fused = reciprocal_rank_fusion([run0, run1], k=60, top_k=4)
        assert fused[0]["chunk_id"] == "delta"
        assert fused[1]["chunk_id"] == "gamma"
        assert fused[2]["chunk_id"] == "beta"
        assert fused[3]["chunk_id"] == "alpha"

    def test_rank_indexing_is_one_based(self):
        """Verify that the first item receives rank 1 (1/(k+1)) and not rank 0 (1/k)."""
        run = ["only_doc"]
        fused = reciprocal_rank_fusion([run], k=60, top_k=1)
        expected = 1.0 / (60 + 1)
        assert math.isclose(fused[0]["score"], expected)

    def test_empty_and_incomplete_rankings(self):
        """Empty lists should return empty output gracefully."""
        assert reciprocal_rank_fusion([], k=60) == []
        assert reciprocal_rank_fusion([[], []], k=60) == []

    def test_top_k_truncation(self):
        """Output should strictly respect top_k."""
        run = [f"doc_{i}" for i in range(50)]
        fused = reciprocal_rank_fusion([run], k=60, top_k=5)
        assert len(fused) == 5
        assert [f["rank"] for f in fused] == [1, 2, 3, 4, 5]

    def test_invalid_parameters_raise(self):
        with pytest.raises(ValueError, match="k must be a positive integer"):
            reciprocal_rank_fusion([["doc1"]], k=0)
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            reciprocal_rank_fusion([["doc1"]], top_k=0)
        with pytest.raises(ValueError, match="weights length"):
            reciprocal_rank_fusion([["doc1"], ["doc2"]], weights=[1.0])

    def test_fuse_per_query(self):
        bm25_runs = [[{"chunk_id": "doc1"}, {"chunk_id": "doc2"}]]
        dense_runs = [[{"chunk_id": "doc2"}, {"chunk_id": "doc3"}]]

        fused_per_query = fuse_per_query(bm25_runs, dense_runs, k=60, top_k=10)
        assert len(fused_per_query) == 1
        top_doc = fused_per_query[0][0]
        # doc2 was rank 2 in bm25 and rank 1 in dense -> 1/62 + 1/61 = highest score
        assert top_doc["chunk_id"] == "doc2"
