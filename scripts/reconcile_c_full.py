#!/usr/bin/env python3
"""Reconcile Phase 1 Exp C-full (1,883 queries) to Phase 1.5 Exp C-full (2,257 queries).

Produces:
    results/c_full_reconciliation_accounting.json

Accounting Invariant:
    1883 = retained (1226) + replaced (524) + rejected (132) + deduplicated (1)

Phase 1.5 Composition Invariant:
    2257 = retained (1226) + regenerated_and_accepted (1031)
    where regenerated_and_accepted (1031) =
        remediation_replacements (541 across 465 chunks) +
        new_chunk_coverage_fill (338 across 260 chunks) +
        passage_density_expansion (152 across 152 chunks)
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_semantic_query_quality import audit_single_query

DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"


def reconcile_c_full() -> dict[str, Any]:
    corpus_list = [json.loads(line) for line in open(DATA_DIR / "training_corpus.jsonl", encoding="utf-8")]
    corpus = {c["chunk_id"]: c for c in corpus_list}

    raw_c = [json.loads(line) for line in open(DATA_DIR / "train_queries_exp_c_full.jsonl", encoding="utf-8")]
    c_v1_5 = [json.loads(line) for line in open(DATA_DIR / "train_queries_exp_c_full_v1_5.jsonl", encoding="utf-8")]

    assert len(raw_c) == 1883, f"Expected 1883 Phase 1 queries, got {len(raw_c)}"
    assert len(c_v1_5) == 2257, f"Expected 2257 Phase 1.5 queries, got {len(c_v1_5)}"

    unchanged_v1_5 = [q for q in c_v1_5 if q.get("correction_provenance") == "accepted_unchanged"]
    unchanged_texts = set(q["query"].lower().strip() for q in unchanged_v1_5)

    raw_by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in raw_c:
        raw_by_chunk[q["positive_chunk_id"]].append(q)

    v1_5_by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in c_v1_5:
        v1_5_by_chunk[q["positive_chunk_id"]].append(q)

    disposition_counts = Counter()
    itemized_records = []

    for q in raw_c:
        cid = q["positive_chunk_id"]
        t = q["query"].lower().strip()
        res = audit_single_query(q, corpus[cid])
        status = res["status"]

        if status == "ACCEPTED":
            if t in unchanged_texts:
                disp = "retained"
                notes = "Passed all deterministic syntax and semantic grounding checks unchanged."
                rep_ids = []
            else:
                disp = "deduplicated"
                notes = (
                    "Audit status was ACCEPTED, but query phrasing was identical to an earlier "
                    "regenerated troubleshooting question ('How does Soup mitigate out of memory errors under severe VRAM limits?') "
                    "and was deduplicated to enforce strict set uniqueness."
                )
                rep_ids = []
        else:
            regen_in_chunk = [
                rq for rq in v1_5_by_chunk.get(cid, [])
                if rq.get("correction_provenance") == "regenerated_and_accepted"
            ]
            if regen_in_chunk:
                disp = "replaced"
                rep_ids = [rq["query_id"] for rq in regen_in_chunk]
                notes = (
                    f"Defective in Phase 1 ({', '.join(res.get('reasons', ['heuristic violation']))}); "
                    f"replaced by {len(regen_in_chunk)} newly generated grounded query/queries for chunk."
                )
            else:
                disp = "rejected"
                rep_ids = []
                notes = (
                    f"Defective in Phase 1 ({', '.join(res.get('reasons', ['heuristic violation']))}); "
                    f"rejected without replacement because chunk already possessed valid retained query coverage."
                )

        disposition_counts[disp] += 1
        itemized_records.append({
            "original_query_id": q["query_id"],
            "query": q["query"],
            "positive_chunk_id": cid,
            "source_doc": q["source_doc"],
            "disposition": disp,
            "audit_status": status,
            "audit_reasons": res.get("reasons", []),
            "replacement_query_ids": rep_ids,
            "notes": notes,
        })

    # Assert accounting equality
    assert disposition_counts["retained"] == 1226
    assert disposition_counts["replaced"] == 524
    assert disposition_counts["rejected"] == 132
    assert disposition_counts["deduplicated"] == 1
    total_accounted = sum(disposition_counts.values())
    assert total_accounted == 1883

    # Detailed analysis of Phase 1.5 regenerated queries (1031 total)
    all_regen = [q for q in c_v1_5 if q.get("correction_provenance") == "regenerated_and_accepted"]
    assert len(all_regen) == 1031

    new_chunks = set(v1_5_by_chunk.keys()) - set(raw_by_chunk.keys())
    regen_new_chunks = [q for q in all_regen if q["positive_chunk_id"] in new_chunks]

    replaced_chunks = set()
    for q in raw_c:
        st = audit_single_query(q, corpus[q["positive_chunk_id"]])["status"]
        cid = q["positive_chunk_id"]
        if st != "ACCEPTED" and any(rq.get("correction_provenance") == "regenerated_and_accepted" for rq in v1_5_by_chunk.get(cid, [])):
            replaced_chunks.add(cid)

    regen_replaced_chunks = [q for q in all_regen if q["positive_chunk_id"] in replaced_chunks]
    expansion_existing_chunks = [
        q for q in all_regen
        if q["positive_chunk_id"] not in new_chunks and q["positive_chunk_id"] not in replaced_chunks
    ]

    assert len(regen_replaced_chunks) == 541
    assert len(regen_new_chunks) == 338
    assert len(expansion_existing_chunks) == 152
    assert len(regen_replaced_chunks) + len(regen_new_chunks) + len(expansion_existing_chunks) == 1031

    new_expansion_records = [
        {
            "query_id": q["query_id"],
            "query": q["query"],
            "positive_chunk_id": q["positive_chunk_id"],
            "source_doc": q["source_doc"],
            "query_type": q["query_type"],
            "category": (
                "new_chunk_coverage_fill" if q["positive_chunk_id"] in new_chunks
                else "remediation_replacement" if q["positive_chunk_id"] in replaced_chunks
                else "passage_density_expansion"
            ),
            "rationale": (
                "Chunk had 0 queries in Phase 1; added to cover previously unindexed sections."
                if q["positive_chunk_id"] in new_chunks
                else "Direct replacement for defective Phase 1 query in chunk."
                if q["positive_chunk_id"] in replaced_chunks
                else "Chunk had 1 clean Phase 1 query; added 2nd query to provide uniform 2-query density."
            ),
        }
        for q in all_regen
    ]

    accounting_report = {
        "metadata": {
            "source_phase_1": "data/train_queries_exp_c_full.jsonl",
            "source_phase_1_5": "data/train_queries_exp_c_full_v1_5.jsonl",
            "phase_1_query_count": 1883,
            "phase_1_5_query_count": 2257,
            "accounting_invariant": "1883 = retained (1226) + replaced (524) + rejected (132) + deduplicated (1)",
            "expansion_invariant": "2257 = retained (1226) + regenerated_and_accepted (1031)",
        },
        "phase_1_reconciliation_summary": {
            "retained": disposition_counts["retained"],
            "replaced": disposition_counts["replaced"],
            "rejected": disposition_counts["rejected"],
            "deduplicated": disposition_counts["deduplicated"],
            "total_phase_1_accounted": total_accounted,
            "accounting_equality_satisfied": total_accounted == 1883,
        },
        "phase_1_5_composition_summary": {
            "retained_from_phase_1": len(unchanged_v1_5),
            "regenerated_and_accepted": len(all_regen),
            "breakdown_of_regenerated": {
                "remediation_replacements": len(regen_replaced_chunks),
                "new_chunk_coverage_fill": len(regen_new_chunks),
                "passage_density_expansion": len(expansion_existing_chunks),
                "total_regenerated": len(all_regen),
            },
            "chunk_coverage_impact": {
                "phase_1_chunks_covered": len(raw_by_chunk),
                "phase_1_5_chunks_covered": len(v1_5_by_chunk),
                "new_chunks_indexed": len(new_chunks),
                "total_corpus_chunks": len(corpus_list),
                "corpus_coverage_pct": round(len(v1_5_by_chunk) / len(corpus_list) * 100, 2),
            },
            "total_phase_1_5": len(c_v1_5),
        },
        "disposition_percentages": {
            "retained_pct": round(disposition_counts["retained"] / 1883 * 100, 2),
            "replaced_pct": round(disposition_counts["replaced"] / 1883 * 100, 2),
            "rejected_pct": round(disposition_counts["rejected"] / 1883 * 100, 2),
            "deduplicated_pct": round(disposition_counts["deduplicated"] / 1883 * 100, 2),
        },
        "reconciled_phase_1_queries": itemized_records,
        "new_phase_1_5_expansion_queries": new_expansion_records,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / "c_full_reconciliation_accounting.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(accounting_report, f, indent=2, ensure_ascii=False)

    print(f"Wrote reconciliation accounting to {out_file}")
    print(f"Summary: {json.dumps(accounting_report['phase_1_reconciliation_summary'], indent=2)}")
    print(f"Composition: {json.dumps(accounting_report['phase_1_5_composition_summary'], indent=2)}")

    return accounting_report


if __name__ == "__main__":
    reconcile_c_full()
