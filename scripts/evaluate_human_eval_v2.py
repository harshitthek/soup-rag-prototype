"""Run independent human evaluation benchmark v2 on Soup documentation corpus.

Evaluates 6 systems on the 24 frozen human queries:
1. Improved BM25 (domain-aware)
2. Frozen E5-small
3. Fine-tuned E5-small (lr=2e-5)
4. Hybrid BM25 + Frozen E5 (RRF k=60)
5. Frozen MiniLM-L6-v2
6. C-matched-balanced adapter (MiniLM)

Outputs:
- results/human_eval_v2/summary.json
- results/human_eval_v2/per_query_results.json
- results/human_eval_v2/bootstrap_intervals.json
- results/human_eval_v2/latency.json
- results/HUMAN_EVAL_V2_REPORT.md
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from compare_retrievers import StratifiedResampler, paired_bootstrap_ci
from fusion import reciprocal_rank_fusion
from retrieval import compute_metrics, rank_corpus
from retrievers import BM25Retriever, DenseRetriever
DATA_DIR = REPO_ROOT / "data"
HUMAN_EVAL_DIR = DATA_DIR / "human_eval"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"
QUERIES_PATH = HUMAN_EVAL_DIR / "human_queries_v2.jsonl"
ANNOTATIONS_PATH = HUMAN_EVAL_DIR / "relevance_annotations_v2.jsonl"
RESULTS_DIR = REPO_ROOT / "results"
OUTPUT_DIR = RESULTS_DIR / "human_eval_v2"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load corpus
    print("Loading corpus...")
    corpus = [
        json.loads(line)
        for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    chunk_ids = [c["chunk_id"] for c in corpus]
    print(f"Corpus loaded: {len(corpus)} chunks")

    # 2. Load queries and annotations
    queries_data = [
        json.loads(line)
        for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    annotations_data = [
        json.loads(line)
        for line in ANNOTATIONS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    annot_by_id = {a["query_id"]: a for a in annotations_data}

    query_items = []
    for q in queries_data:
        qid = q["query_id"]
        a = annot_by_id[qid]
        query_items.append({
            "query_id": qid,
            "query": q["query"],
            "source_file": a["source_file"],
            "source_document": a["source_file"].replace("data/raw_docs/", "").replace(".md", ""),
            "owner_reference": a["owner_reference"],
            "resolved_heading": a["resolved_heading"],
            "relevant_chunk_ids": a["relevant_chunk_ids"],
            "relevant_section_ids": a["relevant_section_ids"],
        })
    print(f"Loaded {len(query_items)} queries with resolved annotations")

    # 3. Instantiate and run retrievers with latency breakdown
    systems_ranked: dict[str, list[list[dict[str, Any]]]] = {}
    latency_stats: dict[str, dict[str, Any]] = {}

    # --- System 1: Improved BM25 ---
    print("\n[1/6] Improved BM25...")
    t0 = time.perf_counter()
    bm25 = BM25Retriever("bm25", k1=1.5, b=0.75, tokenizer="domain_aware")
    bm25_init_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    bm25.fit(corpus)
    bm25_fit_s = time.perf_counter() - t0

    bm25_query_latencies = []
    bm25_ranked = []
    for q in query_items:
        t0 = time.perf_counter()
        scores = bm25.score(q["query"])
        ranked = rank_corpus(scores, chunk_ids, top_k=10)
        dt = (time.perf_counter() - t0) * 1000.0
        bm25_query_latencies.append(dt)
        bm25_ranked.append(ranked)

    systems_ranked["bm25_improved"] = bm25_ranked
    latency_stats["bm25_improved"] = {
        "model_loading_ms": bm25_init_s * 1000.0,
        "corpus_indexing_ms": bm25_fit_s * 1000.0,
        "steady_state_query_mean_ms": float(np.mean(bm25_query_latencies)),
        "steady_state_query_median_ms": float(np.median(bm25_query_latencies)),
        "steady_state_query_p95_ms": float(np.percentile(bm25_query_latencies, 95)),
    }

    # Helper for dense retrievers
    def evaluate_dense_retriever(
        name: str,
        retriever_id: str,
        model_id: str,
        revision: str | None,
        adapter_dir: str | None,
        max_length: int,
        query_prefix: str,
        passage_prefix: str,
    ) -> None:
        print(f"\nEvaluating {name}...")
        t0 = time.perf_counter()
        retriever = DenseRetriever(
            retriever_id=retriever_id,
            model_id=model_id,
            revision=revision,
            adapter_dir=adapter_dir,
            max_length=max_length,
            query_prefix=query_prefix,
            passage_prefix=passage_prefix,
        )
        init_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        corpus_vecs = retriever.encode_corpus(corpus)
        encode_corpus_s = time.perf_counter() - t0

        query_latencies = []
        ranked_all = []
        for q in query_items:
            t0 = time.perf_counter()
            q_vec = retriever.encode_queries([q["query"]])[0]
            scores = corpus_vecs @ q_vec
            ranked = rank_corpus(scores, chunk_ids, top_k=10)
            dt = (time.perf_counter() - t0) * 1000.0
            query_latencies.append(dt)
            ranked_all.append(ranked)

        systems_ranked[name] = ranked_all
        latency_stats[name] = {
            "model_loading_ms": init_s * 1000.0,
            "corpus_indexing_ms": encode_corpus_s * 1000.0,
            "steady_state_query_mean_ms": float(np.mean(query_latencies)),
            "steady_state_query_median_ms": float(np.median(query_latencies)),
            "steady_state_query_p95_ms": float(np.percentile(query_latencies, 95)),
        }

    # --- System 2: Frozen E5-small ---
    evaluate_dense_retriever(
        name="e5_small",
        retriever_id="e5_small",
        model_id="intfloat/e5-small-v2",
        revision="ffb93f3bd4047442299a41ebb6fa998a38507c52",
        adapter_dir=None,
        max_length=512,
        query_prefix="query: ",
        passage_prefix="passage: ",
    )

    # --- System 3: Fine-tuned E5-small (lr=2e-5) ---
    evaluate_dense_retriever(
        name="e5_small_ft_lr2e5",
        retriever_id="e5_small_ft_lr2e5",
        model_id="intfloat/e5-small-v2",
        revision="ffb93f3bd4047442299a41ebb6fa998a38507c52",
        adapter_dir=str(REPO_ROOT / "output/adapter_e5_exp_b_lr2e5"),
        max_length=512,
        query_prefix="query: ",
        passage_prefix="passage: ",
    )

    # --- System 4: Hybrid RRF (BM25 + Frozen E5) ---
    print("\n[4/6] Hybrid RRF (BM25 + Frozen E5, k=60)...")
    hybrid_query_latencies = []
    hybrid_ranked = []
    for i, q in enumerate(query_items):
        t0 = time.perf_counter()
        fused = reciprocal_rank_fusion(
            [systems_ranked["bm25_improved"][i], systems_ranked["e5_small"][i]],
            k=60,
            top_k=10,
        )
        dt = (time.perf_counter() - t0) * 1000.0
        hybrid_query_latencies.append(dt)
        hybrid_ranked.append(fused)

    systems_ranked["hybrid_rrf"] = hybrid_ranked
    latency_stats["hybrid_rrf"] = {
        "model_loading_ms": latency_stats["bm25_improved"]["model_loading_ms"] + latency_stats["e5_small"]["model_loading_ms"],
        "corpus_indexing_ms": latency_stats["bm25_improved"]["corpus_indexing_ms"] + latency_stats["e5_small"]["corpus_indexing_ms"],
        "steady_state_query_mean_ms": latency_stats["bm25_improved"]["steady_state_query_mean_ms"] + latency_stats["e5_small"]["steady_state_query_mean_ms"] + float(np.mean(hybrid_query_latencies)),
        "steady_state_query_median_ms": latency_stats["bm25_improved"]["steady_state_query_median_ms"] + latency_stats["e5_small"]["steady_state_query_median_ms"] + float(np.median(hybrid_query_latencies)),
        "steady_state_query_p95_ms": latency_stats["bm25_improved"]["steady_state_query_p95_ms"] + latency_stats["e5_small"]["steady_state_query_p95_ms"] + float(np.percentile(hybrid_query_latencies, 95)),
    }

    # --- System 5: Frozen MiniLM-L6-v2 ---
    evaluate_dense_retriever(
        name="mini_lm_frozen",
        retriever_id="mini_lm_frozen",
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        adapter_dir=None,
        max_length=256,
        query_prefix="",
        passage_prefix="",
    )

    # --- System 6: C-matched-balanced adapter (MiniLM) ---
    evaluate_dense_retriever(
        name="adapter_exp_c_matched_balanced",
        retriever_id="adapter_exp_c_matched_balanced",
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        adapter_dir=str(REPO_ROOT / "output/adapter_exp_c_matched_balanced"),
        max_length=256,
        query_prefix="",
        passage_prefix="",
    )

    # 4. Compute Metrics
    print("\nComputing metrics per system...")
    summary_metrics: dict[str, dict[str, float]] = {}
    per_query_scores: dict[str, dict[str, list[float]]] = {}

    for sys_name, ranked_list in systems_ranked.items():
        q_results = [
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "relevant_chunk_ids": q["relevant_chunk_ids"],
                "relevant_section_ids": q["relevant_section_ids"],
                "ranked": ranked_list[i],
            }
            for i, q in enumerate(query_items)
        ]
        res = compute_metrics(q_results)
        summary_metrics[sys_name] = res["metrics"]
        per_query_scores[sys_name] = res["_per_query"]

    # 5. Bootstrap Confidence Intervals (10,000 resamples, seed 42)
    print("\nRunning paired document-stratified bootstrap (10,000 resamples, seed 42)...")
    query_docs = [q["source_document"] for q in query_items]
    resampler = StratifiedResampler(query_docs, n_bootstrap=10000, seed=42)

    comparisons = [
        ("hybrid_vs_frozen_e5", "hybrid_rrf", "e5_small"),
        ("ft_e5_lr2e5_vs_frozen_e5", "e5_small_ft_lr2e5", "e5_small"),
        ("c_matched_balanced_vs_frozen_minilm", "adapter_exp_c_matched_balanced", "mini_lm_frozen"),
        ("improved_bm25_vs_frozen_e5", "bm25_improved", "e5_small"),
    ]

    target_metrics = ["hit@1", "recall@3", "recall@5", "mrr@10", "sec_hit@1", "sec_mrr@10"]
    bootstrap_results: dict[str, dict[str, dict[str, float]]] = {}

    for comp_name, sys_a, sys_b in comparisons:
        comp_dict = {}
        for metric in target_metrics:
            ci = paired_bootstrap_ci(
                per_query_scores[sys_a][metric],
                per_query_scores[sys_b][metric],
                resampler=resampler,
                alpha=0.05,
            )
            comp_dict[metric] = ci
        bootstrap_results[comp_name] = comp_dict

    # 6. Save JSON artifacts
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=2)

    bootstrap_path = OUTPUT_DIR / "bootstrap_intervals.json"
    with open(bootstrap_path, "w", encoding="utf-8") as f:
        json.dump(bootstrap_results, f, indent=2)

    latency_path = OUTPUT_DIR / "latency.json"
    with open(latency_path, "w", encoding="utf-8") as f:
        json.dump(latency_stats, f, indent=2)

    # Build per-query detailed JSON
    per_query_out = []
    for i, q in enumerate(query_items):
        item = {
            "query_id": q["query_id"],
            "query": q["query"],
            "source_document": q["source_document"],
            "owner_reference": q["owner_reference"],
            "resolved_heading": q["resolved_heading"],
            "relevant_chunk_ids": q["relevant_chunk_ids"],
            "relevant_section_ids": q["relevant_section_ids"],
            "rankings": {
                sys_name: systems_ranked[sys_name][i]
                for sys_name in systems_ranked
            },
            "scores": {
                sys_name: {
                    metric: per_query_scores[sys_name][metric][i]
                    for metric in target_metrics
                }
                for sys_name in systems_ranked
            }
        }
        per_query_out.append(item)

    per_query_path = OUTPUT_DIR / "per_query_results.json"
    with open(per_query_path, "w", encoding="utf-8") as f:
        json.dump(per_query_out, f, indent=2)

    print("\nResults successfully saved to", OUTPUT_DIR)

    # 7. Generate HUMAN_EVAL_V2_REPORT.md
    report_lines = [
        "# Independent Human Evaluation Benchmark (v2) Report",
        "",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "**Benchmark:** `data/human_eval/manifest_v2.json` (24 queries, 100% human-authored without AI assistance)",
        "**Corpus:** `data/corpus.jsonl` (1,068 canonical chunks across 12 Soup documentation files)",
        "",
        "---",
        "",
        "## 1. Summary Benchmark Results",
        "",
        "| System | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Cold Start (ms) | Steady State (ms) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for sys_key, label in [
        ("bm25_improved", "Improved BM25"),
        ("e5_small", "Frozen E5-small"),
        ("e5_small_ft_lr2e5", "Fine-Tuned E5-small (lr=2e-5)"),
        ("hybrid_rrf", "Hybrid RRF (BM25 + Frozen E5)"),
        ("mini_lm_frozen", "Frozen MiniLM-L6-v2"),
        ("adapter_exp_c_matched_balanced", "C-matched-balanced (MiniLM)"),
    ]:
        m = summary_metrics[sys_key]
        lat = latency_stats[sys_key]
        cold_total = lat["model_loading_ms"] + lat["corpus_indexing_ms"]
        warm_mean = lat["steady_state_query_mean_ms"]
        report_lines.append(
            f"| **{label}** | {m['hit@1']:.4f} | {m['recall@3']:.4f} | {m['recall@5']:.4f} | {m['mrr@10']:.4f} | {m['sec_hit@1']:.4f} | {m['sec_mrr@10']:.4f} | {cold_total:,.1f} | {warm_mean:.2f} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Paired Document-Stratified Bootstrap Intervals (10,000 resamples, seed 42)",
        "",
        "Values reported as `observed delta [95% CI lower, 95% CI upper]`:",
        "",
        "| Comparison | Metric | Observed Delta | 95% CI Lower | 95% CI Upper | Zero in CI? |",
        "|---|---|---|---|---|---|",
    ])

    for comp_key, comp_label in [
        ("hybrid_vs_frozen_e5", "Hybrid RRF vs Frozen E5"),
        ("ft_e5_lr2e5_vs_frozen_e5", "Fine-Tuned E5 (2e-5) vs Frozen E5"),
        ("c_matched_balanced_vs_frozen_minilm", "C-matched-balanced vs Frozen MiniLM"),
        ("improved_bm25_vs_frozen_e5", "Improved BM25 vs Frozen E5"),
    ]:
        for metric in target_metrics:
            ci = bootstrap_results[comp_key][metric]
            delta = ci["delta"]
            low = ci["ci_lower"]
            high = ci["ci_upper"]
            zero_in = (low <= 0 <= high)
            report_lines.append(
                f"| {comp_label} | `{metric}` | {delta:+.4f} | {low:+.4f} | {high:+.4f} | {'Yes' if zero_in else '**No**'} |"
            )

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Evaluation Questions and Answers",
        "",
    ])

    report_path = RESULTS_DIR / "HUMAN_EVAL_V2_REPORT.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Wrote report draft to {report_path}")


if __name__ == "__main__":
    main()
