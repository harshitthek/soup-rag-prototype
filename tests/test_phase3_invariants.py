"""Phase 3 Test Invariants: Multi-Retriever Benchmark Evaluation.

Verifies:
1. Frozen input benchmark files maintain bit-exact checksums.
2. All 9 retriever output JSON files exist and have complete evaluations across all 54 queries.
3. All Phase 3 summary artifacts exist and have valid structure:
   - aggregate_comparison.json
   - per_document_metrics.json
   - per_query_ranked_results.json
   - bootstrap_ci.json
   - lodo_analysis.json
   - failure_analysis.json
   - experiment_summary.json
   - manifest.sha256
4. Numeric and structural invariants on metric outputs across all slices and aggregations.
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
PHASE3_DIR = RESULTS_DIR / "phase3"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}

RETRIEVER_IDS = [
    "bm25",
    "mini_lm_frozen",
    "e5_small",
    "a_full",
    "a_matched",
    "b",
    "c_matched",
    "c_matched_balanced",
    "c_full",
]

EXPECTED_SLICES = [
    "full",
    "core_primary",
    "core_overlap",
    "candidate_clean",
    "candidate_overlap",
    "pure_held_out",
]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_frozen_benchmark_checksums_intact():
    """Verify that none of the frozen input datasets were altered."""
    for fname, expected in FROZEN_CHECKSUMS.items():
        p = DATA_DIR / fname
        assert p.exists(), f"Missing frozen file: {fname}"
        actual = compute_sha256(p)
        assert actual == expected, f"Frozen file checksum mismatch on {fname}: got {actual}"


def test_all_retriever_artifacts_exist():
    """Verify all 9 individual retriever output files exist."""
    assert PHASE3_DIR.exists(), f"Phase 3 directory does not exist: {PHASE3_DIR}"
    for rid in RETRIEVER_IDS:
        retriever_file = PHASE3_DIR / f"retriever_{rid}.json"
        assert retriever_file.exists(), f"Missing retriever output file: {retriever_file}"


def test_retriever_evaluations_completeness():
    """Verify each retriever has 54 evaluated queries, all required slices, and valid metrics."""
    for rid in RETRIEVER_IDS:
        p = PHASE3_DIR / f"retriever_{rid}.json"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["retriever_id"] == rid
        assert data["query_count"] == 54
        assert len(data["per_query_results"]) == 54

        # Verify all slices are present
        assert "slice_metrics" in data
        for s_name in EXPECTED_SLICES:
            assert s_name in data["slice_metrics"], f"Missing slice {s_name} in {rid}"
            s_data = data["slice_metrics"][s_name]
            assert "micro" in s_data
            assert "macro" in s_data
            for mode in ["micro", "macro"]:
                m = s_data[mode]
                assert 0.0 <= m["hit@1"] <= 1.0
                assert 0.0 <= m["recall@3"] <= 1.0
                assert 0.0 <= m["recall@5"] <= 1.0
                assert 0.0 <= m["mrr@10"] <= 1.0
                assert 0.0 <= m["sec_hit@1"] <= 1.0
                assert 0.0 <= m["sec_recall@3"] <= 1.0
                assert 0.0 <= m["sec_recall@5"] <= 1.0
                assert 0.0 <= m["sec_mrr@10"] <= 1.0


def test_aggregate_artifacts_exist_and_valid():
    """Verify all summary and analysis artifacts exist and contain valid fields."""
    expected_files = [
        "aggregate_comparison.json",
        "per_document_metrics.json",
        "per_query_ranked_results.json",
        "bootstrap_ci.json",
        "lodo_analysis.json",
        "failure_analysis.json",
        "experiment_summary.json",
        "manifest.sha256",
    ]
    for fname in expected_files:
        p = PHASE3_DIR / fname
        assert p.exists(), f"Missing summary artifact: {fname}"

    # Verify aggregate comparison structure
    with open(PHASE3_DIR / "aggregate_comparison.json", "r", encoding="utf-8") as f:
        agg = json.load(f)
    assert len(agg["retrievers"]) == 9
    for s_name in EXPECTED_SLICES:
        assert s_name in agg["slices"]
        assert len(agg["slices"][s_name]) == 9

    # Verify bootstrap CI structure
    with open(PHASE3_DIR / "bootstrap_ci.json", "r", encoding="utf-8") as f:
        boot = json.load(f)
    assert "hit@1" in boot
    assert "mrr@10" in boot
    for metric_k in ["hit@1", "mrr@10"]:
        assert "a_full_vs_mini_lm_frozen" in boot[metric_k]
        assert "b_vs_bm25" in boot[metric_k]
        assert "c_matched_balanced_vs_mini_lm_frozen" in boot[metric_k]

    # Verify LODO analysis structure
    with open(PHASE3_DIR / "lodo_analysis.json", "r", encoding="utf-8") as f:
        lodo = json.load(f)
    assert len(lodo["hit@1"]) == 4
    for entry in lodo["hit@1"]:
        assert "dropped_document" in entry
        assert "kept_queries" in entry
        assert "scores" in entry
        assert "deltas" in entry

    # Verify SHA256 manifest
    manifest_p = PHASE3_DIR / "manifest.sha256"
    lines = manifest_p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= len(RETRIEVER_IDS) + len(expected_files) - 1
    for line in lines:
        parts = line.split(maxsplit=1)
        assert len(parts) == 2
        file_sha, file_name = parts
        assert len(file_sha) == 64
        assert (PHASE3_DIR / file_name).exists()


def test_failure_classification_exhaustiveness_and_exclusivity():
    """Verify that failure classification is exhaustive, mutually exclusive, and accounts for all 54 queries."""
    with open(PHASE3_DIR / "per_query_ranked_results.json", "r", encoding="utf-8") as f:
        rankings = json.load(f)

    expected_rel_sec_below_top1 = {
        "bm25": "manual_006",
        "e5_small": "manual_003",
        "c_matched": "manual_004",
        "c_full": "manual_004",
    }

    declared_leaves = {
        "exact_relevant_chunk_top1",
        "relevant_section_unlabeled_chunk_top1",
        "relevant_chunk_below_top1",
        "relevant_section_below_top1",
        "wrong_section_same_document",
        "wrong_document",
    }

    for rid in RETRIEVER_IDS:
        q_list = rankings[rid]
        assert len(q_list) == 54, f"{rid} must have exactly 54 classified queries"
        query_ids = [q["query_id"] for q in q_list]
        assert len(set(query_ids)) == 54, f"{rid} has duplicate query ids"

        counts = {leaf: 0 for leaf in declared_leaves}
        for q in q_list:
            cat = q["failure_category"]
            assert cat in declared_leaves, f"Unknown leaf {cat} in {rid}"
            counts[cat] += 1

        # Invariant: 6 non-empty leaves sum to exactly 54
        total_leaves = sum(counts.values())
        assert total_leaves == 54, f"{rid} leaves sum to {total_leaves}, expected 54"

        # Invariant: 5 operational outcome categories sum to exactly 54
        # (where zero_rel_top10 = wrong_section_same_document + wrong_document)
        zero_rel_top10 = counts["wrong_section_same_document"] + counts["wrong_document"]
        five_category_sum = (
            counts["exact_relevant_chunk_top1"]
            + counts["relevant_section_unlabeled_chunk_top1"]
            + counts["relevant_chunk_below_top1"]
            + counts["relevant_section_below_top1"]
            + zero_rel_top10
        )
        assert five_category_sum == 54, f"{rid} five-category sum is {five_category_sum}, expected 54"

        # Specific query ID check for the 4 queries with relevant_section_below_top1
        if rid in expected_rel_sec_below_top1:
            target_qid = expected_rel_sec_below_top1[rid]
            matching_q = next(q for q in q_list if q["query_id"] == target_qid)
            assert matching_q["failure_category"] == "relevant_section_below_top1", (
                f"{rid} query {target_qid} expected relevant_section_below_top1, got {matching_q['failure_category']}"
            )
        else:
            assert counts["relevant_section_below_top1"] == 0, f"{rid} had unexpected relevant_section_below_top1"


def test_bootstrap_ci_coverage_and_numerical_precision():
    """Verify bootstrap CI contains all required metrics and contrasts with valid intervals."""
    with open(PHASE3_DIR / "bootstrap_ci.json", "r", encoding="utf-8") as f:
        boot = json.load(f)

    expected_metrics = [
        "hit@1", "hit@3", "recall@3", "mrr@10",
        "sec_hit@1", "sec_hit@3", "sec_recall@3", "sec_mrr@10"
    ]
    for m in expected_metrics:
        assert m in boot, f"Missing metric {m} in bootstrap_ci.json"
        contrasts = boot[m]
        assert len(contrasts) == 23, f"Expected 23 contrasts for metric {m}, got {len(contrasts)}"
        for pair_k, res in contrasts.items():
            assert "delta" in res
            assert "ci_lower" in res
            assert "ci_upper" in res
            assert res["ci_lower"] <= res["ci_upper"], f"Inverted CI in {pair_k} for {m}"

    # Verify A-matched vs B Hit@1 interval strictly excludes zero
    a_matched_vs_b_hit1 = boot["hit@1"]["a_matched_vs_b"]
    assert a_matched_vs_b_hit1["ci_lower"] == -0.2222
    assert a_matched_vs_b_hit1["ci_upper"] == -0.0370
    assert a_matched_vs_b_hit1["ci_upper"] < 0.0, "a_matched_vs_b Hit@1 upper CI bound must be strictly negative"


def test_phase3_bootstrap_protocol_implementation():
    """Verify that the bootstrap implementation strictly enforces the 4 protocol invariants:
    1. Exactly 10,000 bootstrap resamples.
    2. Random seed 42.
    3. Document-stratified paired resampling (preserving 16, 8, 17, 13 query counts).
    4. A single shared precomputed index plan whose execution reproduces saved results bit-exact.
    """
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from evaluate_phase3_retrievers import StratifiedResampler, paired_bootstrap_ci, BOOTSTRAP_N, BOOTSTRAP_SEED

    # 1. Enforce 10,000 resamples
    assert BOOTSTRAP_N == 10_000, f"Expected BOOTSTRAP_N == 10000, got {BOOTSTRAP_N}"

    # 2. Enforce random seed 42
    assert BOOTSTRAP_SEED == 42, f"Expected BOOTSTRAP_SEED == 42, got {BOOTSTRAP_SEED}"

    # Load evaluation query document assignments
    with open(DATA_DIR / "manual_queries.jsonl", "r", encoding="utf-8") as f:
        query_docs = [json.loads(line)["source_document"] for line in f]
    assert len(query_docs) == 54

    expected_doc_counts = {
        "adapters-and-governance": 16,
        "compliance": 8,
        "evaluation": 17,
        "peft-and-efficiency": 13,
    }
    actual_query_doc_counts = {}
    for d in query_docs:
        actual_query_doc_counts[d] = actual_query_doc_counts.get(d, 0) + 1
    assert actual_query_doc_counts == expected_doc_counts

    # 3. Document-stratified paired resampling plan
    resampler = StratifiedResampler(query_docs, n_bootstrap=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
    assert len(resampler.indices) == 10_000, f"Resampler must have 10,000 indices, got {len(resampler.indices)}"

    # Verify every resample keeps identical document proportions
    for idx_draw in resampler.indices:
        assert len(idx_draw) == 54
        draw_doc_counts = {}
        for i in idx_draw:
            d = query_docs[i]
            draw_doc_counts[d] = draw_doc_counts.get(d, 0) + 1
        assert draw_doc_counts == expected_doc_counts

    # 4. Single shared precomputed index plan reproducing saved bootstrap_ci.json across metrics and retrievers
    with open(PHASE3_DIR / "bootstrap_ci.json", "r", encoding="utf-8") as f:
        saved_bootstrap = json.load(f)

    retrievers_to_load = ["b", "mini_lm_frozen", "a_matched", "c_matched", "c_matched_balanced", "c_full"]
    retriever_scores = {}
    for r in retrievers_to_load:
        with open(PHASE3_DIR / f"retriever_{r}.json", "r", encoding="utf-8") as f:
            retriever_scores[r] = json.load(f)["_per_query_scores"]

    contrasts_to_verify = [
        ("mrr@10", "b", "mini_lm_frozen", "b_vs_mini_lm_frozen"),
        ("hit@1", "a_matched", "b", "a_matched_vs_b"),
        ("recall@3", "c_matched_balanced", "mini_lm_frozen", "c_matched_balanced_vs_mini_lm_frozen"),
        ("sec_mrr@10", "c_matched", "c_matched_balanced", "c_matched_vs_c_matched_balanced"),
        ("sec_hit@1", "c_full", "mini_lm_frozen", "c_full_vs_mini_lm_frozen"),
    ]

    for metric, r_a, r_b, pair_k in contrasts_to_verify:
        a_sc = retriever_scores[r_a][metric]
        b_sc = retriever_scores[r_b][metric]
        reproduced_ci = paired_bootstrap_ci(a_sc, b_sc, resampler)
        saved_ci = saved_bootstrap[metric][pair_k]
        assert reproduced_ci == saved_ci, (
            f"Reproduced CI {reproduced_ci} does not match saved CI {saved_ci} for {pair_k} on {metric}"
        )


def test_training_source_manifest_document_counts():
    """Verify training corpus document counts: 8 core + 23 candidate = 31 total training documents."""
    manifest_p = DATA_DIR / "training_source_manifest.json"
    assert manifest_p.exists(), f"Missing {manifest_p}"
    with open(manifest_p, "r", encoding="utf-8") as f:
        m = json.load(f)

    assert len(m["existing_training_docs"]) == 8, f"Expected 8 core training docs, got {len(m['existing_training_docs'])}"
    assert len(m["candidate_docs"]) == 23, f"Expected 23 candidate docs, got {len(m['candidate_docs'])}"
    assert m["total_documents"] == 31, f"Expected 31 total training docs, got {m['total_documents']}"
    assert len(m["held_out_docs_excluded"]) == 4, f"Expected 4 held-out evaluation docs, got {len(m['held_out_docs_excluded'])}"
