"""Phase 1.6 Invariant and Data Reconciliation Tests.

Verifies:
1. Exp C-matched-balanced v1.6 query dataset invariants (825 queries, exact query type parity with Exp B).
2. Exp C-matched-balanced v1.6 triplets and hard negative mining invariants (2,475 triplets, sibling masking).
3. Phase 1 to Phase 1.5 C-full reconciliation accounting (1,883 = 1226 + 524 + 132 + 1).
4. Semantic audit sample overlap reconciliation (396 records, 367 unique queries, 29 overlaps).
5. Frozen benchmark integrity across all 5 canonical files.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}


def test_frozen_benchmark_integrity():
    """Verify that all frozen benchmark files remain untouched with exact SHA256 hashes."""
    for fname, expected_hash in FROZEN_CHECKSUMS.items():
        file_path = DATA_DIR / fname
        assert file_path.exists(), f"Frozen file missing: {fname}"
        h = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert h == expected_hash, f"Hash mismatch for {fname}: got {h}, expected {expected_hash}"


def test_exp_c_matched_balanced_v1_6_queries():
    """Verify train_queries_exp_c_matched_balanced_v1_6.jsonl satisfies all Phase 1.6 controls."""
    q_file = DATA_DIR / "train_queries_exp_c_matched_balanced_v1_6.jsonl"
    assert q_file.exists(), f"Missing {q_file}"

    with open(q_file, "r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f]

    assert len(queries) == 825, f"Expected 825 queries, got {len(queries)}"

    q_ids = [q["query_id"] for q in queries]
    assert len(q_ids) == len(set(q_ids)), "All query_ids in C-matched-balanced must be unique"

    # Verify strict subset of C-full v1.5
    c_full_path = DATA_DIR / "train_queries_exp_c_full_v1_5.jsonl"
    with open(c_full_path, "r", encoding="utf-8") as f:
        c_full = [json.loads(line) for line in f]
    c_full_ids = {q["query_id"] for q in c_full}
    assert set(q_ids).issubset(c_full_ids), "C-matched-balanced must be a strict subset of C-full v1.5"

    # Verify query type distribution parity with Exp B v1.5
    b_path = DATA_DIR / "train_queries_exp_b_v1_5.jsonl"
    with open(b_path, "r", encoding="utf-8") as f:
        b_queries = [json.loads(line) for line in f]
    b_types = dict(Counter(q["query_type"] for q in b_queries))

    c_types = dict(Counter(q["query_type"] for q in queries))
    assert c_types == b_types, f"Distribution mismatch: expected {b_types}, got {c_types}"
    assert c_types == {
        "how_to": 327,
        "conceptual": 309,
        "parameter": 184,
        "troubleshooting": 5,
    }

    # Verify document coverage across all 31 documents
    corpus_path = DATA_DIR / "training_corpus.jsonl"
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = [json.loads(line) for line in f]
    all_docs = {c["source_file"] for c in corpus}
    assert len(all_docs) == 31

    c_docs = {q["source_doc"] for q in queries}
    assert c_docs == all_docs, f"Missing documents in C-matched-balanced: {all_docs - c_docs}"

    # Verify field integrity
    for q in queries:
        assert q["query"].strip()
        assert q["positive_chunk_id"].strip()
        assert len(q["relevant_chunk_ids"]) >= 1
        assert q["generator_model"] == "gemini-2.5-flash"
        assert q["validation_status"] == "PASSED"


def test_exp_c_matched_balanced_v1_6_triplets_and_negatives():
    """Verify triplets and hard negatives for C-matched-balanced."""
    triplets_file = DATA_DIR / "triplets_exp_c_matched_balanced_v1_6.jsonl"
    hn_file = DATA_DIR / "hard_negatives_exp_c_matched_balanced_v1_6.jsonl"

    assert triplets_file.exists(), f"Missing {triplets_file}"
    assert hn_file.exists(), f"Missing {hn_file}"

    with open(triplets_file, "r", encoding="utf-8") as f:
        triplets = [json.loads(line) for line in f]
    with open(hn_file, "r", encoding="utf-8") as f:
        hn_records = [json.loads(line) for line in f]

    assert len(triplets) == 2475, f"Expected 2475 triplets, got {len(triplets)}"
    assert len(hn_records) == 2475, f"Expected 2475 hard negatives, got {len(hn_records)}"

    query_negs = defaultdict(list)
    for r in hn_records:
        query_negs[r["query_id"]].append(r)

    assert len(query_negs) == 825, f"Expected 825 queries with negatives, got {len(query_negs)}"

    for qid, negs in query_negs.items():
        assert len(negs) == 3, f"Query {qid} must have exactly 3 negatives"
        ranks = [n["negative_rank"] for n in negs]
        assert ranks == [1, 2, 3]

        scores = [n["negative_score"] for n in negs]
        assert scores[0] >= scores[1] >= scores[2], f"Scores not descending for {qid}: {scores}"

        # Sibling masking
        pos_base = negs[0]["positive_chunk_id"].rsplit("::sub_", 1)[0]
        neg_bases = [n["negative_chunk_id"].rsplit("::sub_", 1)[0] for n in negs]
        assert len(neg_bases) == len(set(neg_bases)), f"Duplicate negative sections for {qid}"
        assert pos_base not in neg_bases, f"Negative section shares base section with positive for {qid}"

        # 0 self-negatives
        for n in negs:
            assert n["positive_chunk_id"] != n["negative_chunk_id"], "Self-negative detected!"

    for t in triplets:
        assert t["anchor"].strip()
        assert t["positive"].strip()
        assert t["negative"].strip()
        assert "\n\n" in t["positive"] or not t["positive"].startswith(" ")
        assert "\n\n" in t["negative"] or not t["negative"].startswith(" ")


def test_c_full_reconciliation_accounting():
    """Verify that results/c_full_reconciliation_accounting.json satisfies exact accounting invariants."""
    acc_file = RESULTS_DIR / "c_full_reconciliation_accounting.json"
    assert acc_file.exists(), f"Missing {acc_file}"

    with open(acc_file, "r", encoding="utf-8") as f:
        acc = json.load(f)

    p1_sum = acc["phase_1_reconciliation_summary"]
    assert p1_sum["retained"] == 1226
    assert p1_sum["replaced"] == 524
    assert p1_sum["rejected"] == 132
    assert p1_sum["deduplicated"] == 1
    assert p1_sum["total_phase_1_accounted"] == 1883
    assert p1_sum["accounting_equality_satisfied"] is True

    p1_5_sum = acc["phase_1_5_composition_summary"]
    assert p1_5_sum["retained_from_phase_1"] == 1226
    assert p1_5_sum["regenerated_and_accepted"] == 1031
    assert p1_5_sum["total_phase_1_5"] == 2257

    breakdown = p1_5_sum["breakdown_of_regenerated"]
    assert breakdown["remediation_replacements"] == 541
    assert breakdown["new_chunk_coverage_fill"] == 338
    assert breakdown["passage_density_expansion"] == 152
    assert breakdown["total_regenerated"] == 1031

    coverage = p1_5_sum["chunk_coverage_impact"]
    assert coverage["phase_1_5_chunks_covered"] == 1522
    assert coverage["total_corpus_chunks"] == 1522
    assert coverage["corpus_coverage_pct"] == 100.0


def test_audit_sample_overlap_reconciliation():
    """Verify that results/audit_sample_overlap_reconciliation.json accounts for all samples and unique IDs."""
    ov_file = RESULTS_DIR / "audit_sample_overlap_reconciliation.json"
    assert ov_file.exists(), f"Missing {ov_file}"

    with open(ov_file, "r", encoding="utf-8") as f:
        ov = json.load(f)

    counts = ov["sample_counts"]
    assert counts["exp_b_v1_5_records"] == 85
    assert counts["exp_c_matched_v1_5_records"] == 85
    assert counts["exp_c_full_v1_5_records"] == 226
    assert counts["total_audit_records_reviewed"] == 396

    accounting = ov["unique_query_accounting"]
    assert accounting["c_matched_and_c_full_shared_queries"] == 29
    assert accounting["unique_queries_across_c_family"] == 282
    assert accounting["total_unique_queries_evaluated"] == 367

    consistency = ov["overlap_consistency"]
    assert consistency["shared_query_count"] == 29
    assert consistency["status_agreement_pct"] == 100.0
    assert consistency["rubric_agreement_pct"] == 100.0
