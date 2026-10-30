"""Tests for scripts/retrieval.py (stdlib-only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from retrieval import (  # noqa: E402
    FAILURE_CATEGORIES,
    NO_RELEVANT_RESULT_LEAVES,
    classify_failure,
    compute_metrics,
    compute_query_metrics,
    get_base_section,
    rank_corpus,
    section_ranking,
)


def make_ranked(pairs, section_ids=None, scores=None):
    """pairs: list of chunk_ids in rank order (rank 1 first)."""
    ranked = []
    for i, cid in enumerate(pairs, start=1):
        entry = {"rank": i, "chunk_id": cid, "score": 1.0 - 0.01 * i}
        if section_ids:
            entry["section_id"] = section_ids[cid]
        if scores:
            entry["score"] = scores[cid]
        ranked.append(entry)
    return ranked


# ---------------------------------------------------------------------------
# ranking
# ---------------------------------------------------------------------------


def test_rank_corpus_descending_and_tie_break():
    scores = [0.5, 0.9, 0.9, 0.2]
    ids = ["a::x", "b::y", "a::w", "c::z"]
    ranked = rank_corpus(scores, ids, top_k=4)
    assert [r["chunk_id"] for r in ranked] == ["a::w", "b::y", "a::x", "c::z"]
    assert [r["rank"] for r in ranked] == [1, 2, 3, 4]


def test_rank_corpus_top_k_cutoff():
    scores = [0.9, 0.8, 0.7, 0.6]
    ids = ["a", "b", "c", "d"]
    assert len(rank_corpus(scores, ids, top_k=2)) == 2


# ---------------------------------------------------------------------------
# section mapping
# ---------------------------------------------------------------------------


def test_get_base_section():
    assert get_base_section("doc::sec::sub_000") == "doc::sec"
    assert get_base_section("doc::sec::sub_042") == "doc::sec"
    assert get_base_section("doc::sec") == "doc::sec"


def test_section_ranking_dedup_preserves_first_occurrence():
    ranked = make_ranked(
        ["d::s1::sub_000", "d::s2", "d::s1::sub_001", "d::s3::sub_000"]
    )
    collapsed = section_ranking(ranked)
    assert [s["section_id"] for s in collapsed] == ["d::s1", "d::s2", "d::s3"]
    assert [s["rank"] for s in collapsed] == [1, 2, 3]
    assert collapsed[0]["chunk_id"] == "d::s1::sub_000"


# ---------------------------------------------------------------------------
# chunk metrics — the four edge cases required by the spec
# ---------------------------------------------------------------------------

def _qr(ranked_chunks, rel_chunks, rel_sections):
    return {
        "ranked": make_ranked(ranked_chunks),
        "relevant_chunk_ids": rel_chunks,
        "relevant_section_ids": rel_sections,
    }


def test_edge_single_relevant_item():
    scores = compute_query_metrics(
        _qr(["d::s1", "d::s2", "d::s3"], ["d::s1"], ["d::s1"])
    )
    assert scores["chunk"]["hit@1"] == 1.0 and scores["chunk"]["recall@1"] == 1.0
    assert scores["chunk"]["recall@3"] == 1.0
    assert scores["chunk"]["mrr@10"] == 1.0
    assert scores["section"]["sec_hit@1"] == 1.0
    assert scores["section"]["sec_recall@1"] == 1.0


def test_edge_multiple_chunks_one_section():
    ranked = ["d::s1::sub_000", "d::s1::sub_001", "d::s2"]
    rel_chunks = ["d::s1::sub_000", "d::s1::sub_001"]
    rel_sections = ["d::s1"]
    scores = compute_query_metrics(_qr(ranked, rel_chunks, rel_sections))
    # both relevant chunks in top-3 -> full chunk recall; hit binary
    assert scores["chunk"]["hit@3"] == 1.0
    assert scores["chunk"]["recall@3"] == 1.0
    # only sub_000 in top-1 -> partial recall
    assert scores["chunk"]["recall@1"] == 0.5
    # section collapses: one relevant section, present at rank 1
    assert scores["section"]["sec_hit@1"] == 1.0
    assert scores["section"]["sec_recall@1"] == 1.0


def test_edge_multiple_sections():
    ranked = ["d::s1::sub_000", "d::s2", "d::s3::sub_000"]
    rel_chunks = ["d::s1::sub_000", "d::s2", "d::s3::sub_000"]
    rel_sections = ["d::s1", "d::s2", "d::s3"]
    scores = compute_query_metrics(_qr(ranked, rel_chunks, rel_sections))
    assert scores["chunk"]["recall@3"] == 1.0
    assert scores["section"]["sec_recall@3"] == 1.0
    # top-1 unique section is s1 -> 1/3 section recall at k=1
    assert scores["section"]["sec_recall@1"] == pytest.approx(1 / 3)
    assert scores["section"]["sec_hit@1"] == 1.0


def test_edge_more_relevant_than_cutoff():
    ranked = ["d::s1::sub_000", "d::s1::sub_001", "d::s1::sub_002"]
    rel_chunks = [
        "d::s1::sub_000",
        "d::s1::sub_001",
        "d::s1::sub_002",
        "d::s1::sub_003",
    ]
    rel_sections = ["d::s1"]
    scores = compute_query_metrics(_qr(ranked, rel_chunks, rel_sections))
    assert scores["chunk"]["hit@3"] == 1.0
    assert scores["chunk"]["recall@3"] == pytest.approx(3 / 4)
    # section level: 1 relevant section present -> binary/full
    assert scores["section"]["sec_recall@3"] == 1.0


def test_mrr_first_relevant_rank():
    ranked = ["d::x", "d::y", "d::s1::sub_001", "d::s1::sub_000"]
    rel_chunks = ["d::s1::sub_000"]
    rel_sections = ["d::s1"]
    scores = compute_query_metrics(_qr(ranked, rel_chunks, rel_sections))
    assert scores["chunk"]["mrr@10"] == pytest.approx(1 / 4)
    # section d::s1 first appears at unique-section rank 3 -> sec mrr 1/3
    assert scores["section"]["sec_mrr@10"] == pytest.approx(1 / 3)


def test_miss_everything_is_zero():
    scores = compute_query_metrics(_qr(["d::x", "d::y"], ["d::s1"], ["d::s1"]))
    assert scores["chunk"]["hit@1"] == 0.0
    assert scores["chunk"]["recall@5"] == 0.0
    assert scores["chunk"]["mrr@10"] == 0.0
    assert scores["section"]["sec_hit@5"] == 0.0
    assert scores["section"]["sec_mrr@10"] == 0.0


def test_empty_relevant_raises():
    with pytest.raises(ValueError):
        compute_query_metrics(_qr(["d::x"], [], ["d::s1"]))


def test_aggregate_means():
    qrs = [
        _qr(["d::s1"], ["d::s1"], ["d::s1"]),
        _qr(["d::other"], ["d::s1"], ["d::s1"]),
    ]
    agg = compute_metrics(qrs)
    assert agg["metrics"]["hit@1"] == 0.5
    assert agg["metrics"]["sec_hit@1"] == 0.5
    assert set(agg["_per_query"]) >= {
        "hit@1", "hit@3", "hit@5", "recall@1", "recall@3", "recall@5", "mrr@10",
        "sec_hit@1", "sec_hit@3", "sec_hit@5", "sec_recall@1", "sec_recall@3",
        "sec_recall@5", "sec_mrr@10",
    }


# ---------------------------------------------------------------------------
# failure classifier — one leaf per case, plus empty-ranking handling
# ---------------------------------------------------------------------------


def _cls(ranked_chunks, rel_chunks, rel_sections, source_doc="d"):
    return classify_failure(make_ranked(ranked_chunks), rel_chunks, rel_sections, source_doc)


def test_leaf_exact_relevant_chunk_top1():
    assert _cls(["d::s1::sub_000", "d::x"], ["d::s1::sub_000"], ["d::s1"]) == "exact_relevant_chunk_top1"


def test_leaf_relevant_section_unlabeled_chunk_top1():
    # top-1 is an unlabeled sibling in a relevant section
    assert (
        _cls(["d::s1::sub_001", "d::s1::sub_000", "d::x"], ["d::s1::sub_000"], ["d::s1"])
        == "relevant_section_unlabeled_chunk_top1"
    )


def test_leaf_relevant_chunk_below_top1():
    assert (
        _cls(["d::other", "d::s1::sub_000"], ["d::s1::sub_000"], ["d::s1"])
        == "relevant_chunk_below_top1"
    )


def test_leaf_relevant_section_below_top1():
    # labeled chunk out of top-10, sibling chunk of relevant section in top-10
    ranked = ["d::other"] + [f"d::s1::sub_{i:03d}" for i in range(1, 8)]
    assert (
        _cls(ranked, ["d::s1::sub_000"], ["d::s1"])
        == "relevant_section_below_top1"
    )


def test_leaf_wrong_section_same_document():
    # top-1 in the source document, nothing relevant anywhere in top-10
    assert (
        _cls(["e::other", "e::yet_another"], ["e::s1"], ["e::s1"], source_doc="e")
        == "wrong_section_same_document"
    )


def test_leaf_wrong_document():
    assert _cls(["e::x"], ["d::s1"], ["d::s1"], source_doc="d") == "wrong_document"


def test_leaf_empty_ranking():
    assert classify_failure([], ["d::s1"], ["d::s1"], "d") == "empty_ranking"


def test_classifier_exhaustive_and_exclusive():
    # Every synthetic case maps to exactly one leaf and the leaf is in the
    # declared category set; the no_relevant aggregate covers leaves 5+6.
    rel_chunks = ["d::s1::sub_000"]
    rel_sections = ["d::s1"]
    cases = [
        [],
        ["d::s1::sub_000"],
        ["d::s1::sub_001"],
        ["d::x", "d::s1::sub_000"],
        ["d::x", "d::s1::sub_001"],
        ["d::x"],
        ["e::x"],
    ]
    leaves = {classify_failure(make_ranked(c), rel_chunks, rel_sections, "d") for c in cases}
    assert leaves == set(FAILURE_CATEGORIES)
    assert NO_RELEVANT_RESULT_LEAVES == ("wrong_section_same_document", "wrong_document")


def test_classifier_derives_section_and_doc_from_chunk_id():
    # ranked entries without section_id/doc_name still classify correctly
    ranked = [{"rank": 1, "chunk_id": "d::s1::sub_001", "score": 0.9}]
    assert (
        classify_failure(ranked, ["d::s1::sub_000"], ["d::s1"], "d")
        == "relevant_section_unlabeled_chunk_top1"
    )
