"""Tests for scripts/compare_retrievers.py (numpy required)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from compare_retrievers import (  # noqa: E402
    CAVEAT,
    StratifiedResampler,
    cluster_structure,
    failure_category_counts,
    generate_report,
    leave_one_doc_out,
    macro_metric,
    micro_metric,
    paired_bootstrap_ci,
    regression_counts,
)

METRICS = ["hit@1", "mrr@10", "sec_hit@1"]


def ranked_entry(rank, chunk_id, score=0.9):
    return {"rank": rank, "chunk_id": chunk_id, "score": score}


def make_result(
    retriever_id: str,
    query_rows: list[dict],
) -> dict:
    """query_rows: list of dicts with query_id, source_document,
    relevant_chunk_ids, relevant_section_ids, ranked, failure_category,
    subset, and per-metric score values in 'scores'."""
    scores = {m: [row["scores"][m] for row in query_rows] for m in METRICS}
    per_query_results = [
        {k: row[k] for k in (
            "query_id", "source_document", "relevant_chunk_ids",
            "relevant_section_ids", "ranked", "failure_category", "subset",
        )}
        for row in query_rows
    ]
    return {
        "retriever_id": retriever_id,
        "corpus_fingerprint": "fp",
        "query_set_fingerprint": "qfp",
        "query_count": len(query_rows),
        "_per_query_scores": scores,
        "per_query_results": per_query_results,
    }


def base_rows():
    # 2 docs x 2 queries; query 1 and 2 share a section (cluster of 2)
    return [
        dict(
            query_id="manual_001", source_document="doc_a",
            relevant_chunk_ids=["doc_a::s1::sub_000"],
            relevant_section_ids=["doc_a::s1"],
            ranked=[ranked_entry(1, "doc_a::s1::sub_000")],
            failure_category="exact_relevant_chunk_top1",
            subset="primary",
            scores={"hit@1": 1.0, "mrr@10": 1.0, "sec_hit@1": 1.0},
        ),
        dict(
            query_id="manual_002", source_document="doc_a",
            relevant_chunk_ids=["doc_a::s1::sub_001"],
            relevant_section_ids=["doc_a::s1"],
            ranked=[ranked_entry(1, "doc_a::other")],
            failure_category="wrong_section_same_document",
            subset="primary",
            scores={"hit@1": 0.0, "mrr@10": 0.0, "sec_hit@1": 0.0},
        ),
        dict(
            query_id="manual_003", source_document="doc_b",
            relevant_chunk_ids=["doc_b::x"],
            relevant_section_ids=["doc_b::x"],
            ranked=[ranked_entry(1, "doc_b::x")],
            failure_category="exact_relevant_chunk_top1",
            subset="primary",
            scores={"hit@1": 1.0, "mrr@10": 1.0, "sec_hit@1": 1.0},
        ),
        dict(
            query_id="manual_004", source_document="doc_b",
            relevant_chunk_ids=["doc_b::y"],
            relevant_section_ids=["doc_b::y"],
            ranked=[ranked_entry(1, "doc_b::x")],
            failure_category="wrong_document",
            subset="overlap",
            scores={"hit@1": 0.0, "mrr@10": 0.0, "sec_hit@1": 0.0},
        ),
    ]


@pytest.fixture
def results():
    frozen = make_result("mini_lm_frozen", base_rows())
    # soup better on the two misses, identical elsewhere
    soup_rows = base_rows()
    soup_rows[1]["scores"] = {"hit@1": 1.0, "mrr@10": 0.5, "sec_hit@1": 1.0}
    soup_rows[1]["ranked"] = [ranked_entry(1, "doc_a::s1::sub_001")]
    soup_rows[1]["failure_category"] = "exact_relevant_chunk_top1"
    soup_rows[3]["scores"] = {"hit@1": 1.0, "mrr@10": 1.0, "sec_hit@1": 1.0}
    soup_rows[3]["ranked"] = [ranked_entry(1, "doc_b::y")]
    soup_rows[3]["failure_category"] = "exact_relevant_chunk_top1"
    soup = make_result("mini_lm_soup", soup_rows)
    bm25 = make_result("bm25", base_rows())
    e5 = make_result("e5_small", base_rows())
    return {"mini_lm_frozen": frozen, "mini_lm_soup": soup, "bm25": bm25, "e5_small": e5}


def test_micro_and_macro_metric(results):
    r = results["mini_lm_frozen"]
    assert micro_metric(r, "hit@1") == pytest.approx(0.5)
    # macro: doc_a mean = 0.5, doc_b mean = 0.5 -> 0.5
    assert macro_metric(r, "hit@1") == pytest.approx(0.5)
    assert micro_metric(r, "mrr@10") == pytest.approx(0.5)
    assert macro_metric(r, "mrr@10") == pytest.approx(0.5)


def test_stratified_resampler_preserves_doc_counts():
    docs = ["a", "a", "a", "b", "b"]
    rs = StratifiedResampler(docs, n_bootstrap=5, seed=42)
    for idx in rs.iterations():
        sampled_docs = [docs[i] for i in idx]
        assert sampled_docs.count("a") == 3
        assert sampled_docs.count("b") == 2


def test_resampler_deterministic_given_seed():
    docs = ["a", "a", "b"]
    a = list(StratifiedResampler(docs, n_bootstrap=3, seed=7).iterations())
    b = list(StratifiedResampler(docs, n_bootstrap=3, seed=7).iterations())
    assert a == b


def test_paired_bootstrap_ci_positive_and_zero_deltas():
    docs = ["a", "b"]
    rs_pos = StratifiedResampler(docs, n_bootstrap=200, seed=42)
    ci = paired_bootstrap_ci([1.0, 1.0], [0.0, 0.0], rs_pos)
    assert ci["delta"] == 1.0
    assert ci["ci_lower"] == 1.0 and ci["ci_upper"] == 1.0
    rs_zero = StratifiedResampler(docs, n_bootstrap=200, seed=42)
    ci0 = paired_bootstrap_ci([0.5, 0.5], [0.5, 0.5], rs_zero)
    assert ci0["delta"] == 0.0 and ci0["ci_lower"] == 0.0 and ci0["ci_upper"] == 0.0


def test_leave_one_doc_out(results):
    query_ids = ["manual_001", "manual_002", "manual_003", "manual_004"]
    docs_per_query = ["doc_a", "doc_a", "doc_b", "doc_b"]
    loo = leave_one_doc_out(results, "hit@1", query_ids, docs_per_query)
    assert [r["dropped_document"] for r in loo["docs"]] == ["doc_a", "doc_b"]
    drop_a = loo["docs"][0]
    assert drop_a["n_kept_queries"] == 2
    assert drop_a["mini_lm_frozen_micro"] == pytest.approx(0.5)  # queries 3,4
    assert "delta_mini_lm_soup_vs_mini_lm_frozen" in drop_a


def test_cluster_structure_decision():
    rows = base_rows()
    info = cluster_structure([{k: r[k] for k in (
        "source_document", "relevant_chunk_ids")} for r in rows])
    # 3 occupied sections: doc_a::s1 (2 queries), doc_b::x (1), doc_b::y (1)
    assert info["occupied_sections"] == 3
    assert info["sections_with_multiple_queries"] == 1
    assert info["multi_query_fraction"] == 0.3333  # rounded to 4dp by the module
    assert info["cluster_bootstrap_informative"] is True

    singles = [
        {"source_document": f"d{i % 2}", "relevant_chunk_ids": [f"d{i % 2}::s{i}"]}
        for i in range(5)
    ]
    info2 = cluster_structure(singles)
    assert info2["cluster_bootstrap_informative"] is False
    assert "skipped" in info2["decision"]


def test_regression_counts_sibling_is_not_section_regression():
    a = make_result("mini_lm_frozen", base_rows()[:1])
    b_rows = base_rows()[:1]
    b_rows[0]["ranked"] = [ranked_entry(1, "doc_a::s1::sub_001")]  # sibling first
    b_rows[0]["failure_category"] = "relevant_section_unlabeled_chunk_top1"
    b = make_result("mini_lm_soup", b_rows)
    counts = regression_counts(a, b, ["manual_001"])
    assert counts["chunk_regressions"] == 1
    assert counts["section_regressions"] == 0


def test_failure_category_aggregate(results):
    counts = failure_category_counts(results["mini_lm_frozen"])
    assert counts["exact_relevant_chunk_top1"] == 2
    assert counts["wrong_section_same_document"] == 1
    assert counts["wrong_document"] == 1
    assert counts["no_relevant_result_top10"] == 2


def test_generate_report_no_p_values_and_caveats(results, tmp_path):
    out = tmp_path / "comparison.md"
    report = generate_report(results, out, n_bootstrap=50, seed=42)
    assert out.exists()
    # the only occurrence of "p-value" is the disclaimer sentence itself
    assert report.count("p-value") == 1
    assert "p_value" not in report
    assert "significance claim" not in report.lower().replace("no significance claims", "")
    assert CAVEAT in report
    assert "Section-Cluster Bootstrap Decision" in report
    assert "Overlap Subset" in report and "Primary Subset" in report
    assert "Leave-One-Document-Out Sensitivity" in report


def test_generate_report_deterministic(results, tmp_path):
    r1 = generate_report(results, tmp_path / "a.md", n_bootstrap=50, seed=42)
    r2 = generate_report(results, tmp_path / "b.md", n_bootstrap=50, seed=42)
    assert r1 == r2
