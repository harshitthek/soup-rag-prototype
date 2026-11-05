"""Paired document-stratified bootstrap confidence intervals (10,000 resamples, seed 42)
for:
1. Improved BM25 vs Original BM25
2. Hybrid RRF vs Frozen E5-small
3. Hybrid RRF vs Improved BM25

Strictly reports observed delta and [ci_lower, ci_upper] without p-values or significance claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from compare_retrievers import StratifiedResampler, paired_bootstrap_ci
from retrieval import compute_metrics

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
HYBRID_DIR = RESULTS_DIR / "hybrid"


def calculate_bootstrap_intervals() -> dict[str, Any]:
    per_query_path = HYBRID_DIR / "per_query_results.json"
    per_query = json.loads(per_query_path.read_text(encoding="utf-8"))
    query_docs = [pq["source_document"] for pq in per_query]

    # Exactly 10,000 resamples, seed 42
    resampler = StratifiedResampler(query_docs, n_bootstrap=10000, seed=42)

    sys_scores: dict[str, dict[str, list[float]]] = {}
    for sys_id in ["bm25_legacy", "bm25_improved", "e5_small", "hybrid_rrf"]:
        q_data = [
            {
                "query_id": pq["query_id"],
                "query": pq["query"],
                "subset": pq["subset"],
                "source_document": pq["source_document"],
                "relevant_chunk_ids": pq["relevant_chunk_ids"],
                "relevant_section_ids": pq["relevant_section_ids"],
                "ranked": pq["systems"][sys_id]["ranked_top10"],
            }
            for pq in per_query
        ]
        computed = compute_metrics(q_data)
        sys_scores[sys_id] = computed["_per_query"]

    comparisons = [
        ("improved_bm25_vs_original_bm25", "bm25_improved", "bm25_legacy"),
        ("hybrid_rrf_vs_frozen_e5", "hybrid_rrf", "e5_small"),
        ("hybrid_rrf_vs_improved_bm25", "hybrid_rrf", "bm25_improved"),
    ]

    metrics = [
        "mrr@10",
        "hit@1",
        "recall@1",
        "hit@3",
        "recall@3",
        "hit@5",
        "recall@5",
        "sec_hit@1",
        "sec_hit@3",
        "sec_recall@3",
        "sec_hit@5",
        "sec_recall@5",
        "sec_mrr@10",
    ]

    bootstrap_results: dict[str, dict[str, dict[str, float]]] = {}

    for comp_key, cand_id, base_id in comparisons:
        bootstrap_results[comp_key] = {}
        for m in metrics:
            cand_vals = sys_scores[cand_id][m]
            base_vals = sys_scores[base_id][m]
            ci = paired_bootstrap_ci(cand_vals, base_vals, resampler)
            bootstrap_results[comp_key][m] = ci

    return bootstrap_results


if __name__ == "__main__":
    results = calculate_bootstrap_intervals()
    out_path = HYBRID_DIR / "bootstrap_ci.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved bootstrap CIs -> {out_path}")

    for comp_key, comp_data in results.items():
        print(f"\n=== {comp_key} ===")
        for m in ["mrr@10", "hit@1", "recall@3", "recall@5", "sec_hit@1", "sec_mrr@10"]:
            ci = comp_data[m]
            print(f"  {m:<12}: delta = {ci['delta']:+.4f} | 95% CI: [{ci['ci_lower']:+.4f}, {ci['ci_upper']:+.4f}]")
