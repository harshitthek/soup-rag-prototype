#!/usr/bin/env python3
"""Reconcile semantic audit sample overlap from Phase 1.5 audit.

Produces:
    results/audit_sample_overlap_reconciliation.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


def reconcile_audit_sample_overlap() -> dict[str, Any]:
    audit_file = RESULTS_DIR / "PHASE_1_5_QUERY_AUDIT.json"
    with open(audit_file, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    b_records = audit_data["datasets"]["exp_b_v1_5"]["audited_records"]
    c_m_records = audit_data["datasets"]["exp_c_matched_v1_5"]["audited_records"]
    c_f_records = audit_data["datasets"]["exp_c_full_v1_5"]["audited_records"]

    b_qids = [r["query_id"] for r in b_records]
    c_m_qids = [r["query_id"] for r in c_m_records]
    c_f_qids = [r["query_id"] for r in c_f_records]

    assert len(b_records) == 85
    assert len(c_m_records) == 85
    assert len(c_f_records) == 226
    assert len(set(b_qids)) == 85
    assert len(set(c_m_qids)) == 85
    assert len(set(c_f_qids)) == 226

    total_records = len(b_records) + len(c_m_records) + len(c_f_records)
    assert total_records == 396

    c_m_set = set(c_m_qids)
    c_f_set = set(c_f_qids)
    c_overlap = sorted(list(c_m_set.intersection(c_f_set)))
    assert len(c_overlap) == 29

    c_m_map = {r["query_id"]: r for r in c_m_records}
    c_f_map = {r["query_id"]: r for r in c_f_records}

    overlapping_evaluations = []
    for qid in c_overlap:
        rm = c_m_map[qid]
        rf = c_f_map[qid]
        assert rm["status"] == rf["status"], f"Status mismatch for {qid}"
        assert rm["rubric"] == rf["rubric"], f"Rubric mismatch for {qid}"
        overlapping_evaluations.append({
            "query_id": qid,
            "query": rm["query"],
            "source_doc": rm["source_doc"],
            "positive_chunk_id": rm["positive_chunk_id"],
            "status": rm["status"],
            "rubric": rm["rubric"],
        })

    all_unique_qids = set(b_qids).union(c_m_set).union(c_f_set)
    assert len(all_unique_qids) == 367
    assert len(set(b_qids).intersection(c_m_set.union(c_f_set))) == 0

    reconciliation = {
        "metadata": {
            "source_file": "results/PHASE_1_5_QUERY_AUDIT.json",
            "audit_rubric": "6-Point Quality Rubric",
            "evaluator": "Antigravity AI Agent (agentic automated evaluation)",
        },
        "sample_counts": {
            "exp_b_v1_5_records": len(b_records),
            "exp_c_matched_v1_5_records": len(c_m_records),
            "exp_c_full_v1_5_records": len(c_f_records),
            "total_audit_records_reviewed": total_records,
        },
        "unique_query_accounting": {
            "unique_exp_b_queries": len(b_records),
            "unique_exp_c_matched_queries": len(c_m_records),
            "unique_exp_c_full_queries": len(c_f_records),
            "c_matched_and_c_full_shared_queries": len(c_overlap),
            "unique_queries_across_c_family": len(c_m_set.union(c_f_set)),
            "total_unique_queries_evaluated": len(all_unique_qids),
        },
        "overlap_consistency": {
            "shared_query_count": len(c_overlap),
            "status_agreement_pct": 100.0,
            "rubric_agreement_pct": 100.0,
            "overlapping_records": overlapping_evaluations,
        },
    }

    out_file = RESULTS_DIR / "audit_sample_overlap_reconciliation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(reconciliation, f, indent=2, ensure_ascii=False)

    print(f"Wrote audit sample overlap reconciliation to {out_file}")
    print(f"Total records reviewed: {total_records}")
    print(f"Total unique queries evaluated: {len(all_unique_qids)}")
    print(f"C-matched & C-full shared queries: {len(c_overlap)} (100% agreement)")

    return reconciliation


if __name__ == "__main__":
    reconcile_audit_sample_overlap()
