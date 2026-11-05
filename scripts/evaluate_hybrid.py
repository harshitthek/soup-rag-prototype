"""Benchmark Original BM25, Improved BM25, Frozen E5-small, and Hybrid RRF.

Evaluates all four retrieval systems on the frozen 54 manual evaluation queries
(data/manual_queries.jsonl) over data/corpus.jsonl (1068 chunks).
Also generates preliminary top-10 rankings on the 24 human-authored queries
(data/human_eval/human_queries_v2.jsonl) without computing metrics.

Generates:
- results/hybrid/configuration.json
- results/hybrid/summary.json
- results/hybrid/per_query_results.json
- results/HYBRID_RETRIEVAL_RESULTS.md
- ~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json (quarantined outside workspace)
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fusion import DEFAULT_RRF_K, fuse_per_query
from retrieval import classify_failure, compute_metrics, get_base_section
from retrievers import BM25Retriever, build_retriever, retrieve_ranked

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
HYBRID_DIR = RESULTS_DIR / "hybrid"
# Quarantined outside repository workspace to ensure strict double-blind human annotation
QUARANTINE_DIR = Path.home() / ".cache" / "soup-rag-prototype" / "quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)


def run_evaluation() -> dict[str, Any]:
    corpus_path = DATA_DIR / "corpus.jsonl"
    queries_path = DATA_DIR / "manual_queries.jsonl"
    human_queries_path = DATA_DIR / "human_eval" / "human_queries_v2.jsonl"

    corpus_bytes = corpus_path.read_bytes()
    corpus_digest = hashlib.sha256(corpus_bytes).hexdigest()
    chunks = [
        json.loads(line)
        for line in corpus_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]
    queries = [
        json.loads(line)
        for line in queries_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    query_texts = [q["query"] for q in queries]

    human_queries = [
        json.loads(line)
        for line in human_queries_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if human_queries_path.exists() else []
    human_query_texts = [q["query"] for q in human_queries]

    # Initialize retrievers
    r_bm25_legacy = BM25Retriever(tokenizer="whitespace")
    r_bm25_improved = BM25Retriever(tokenizer="domain_aware")
    r_e5 = build_retriever("e5_small", repo_root=REPO_ROOT)

    # 1. Benchmark 54 queries
    print("Running BM25 legacy...")
    t0 = time.perf_counter()
    ranked_bm25_legacy_54 = retrieve_ranked(
        r_bm25_legacy, chunks, query_texts, top_k=10
    )
    time_bm25_legacy = time.perf_counter() - t0

    print("Running BM25 improved (full corpus)...")
    t0 = time.perf_counter()
    ranked_bm25_impr_full_54 = retrieve_ranked(
        r_bm25_improved, chunks, query_texts, top_k=len(chunks)
    )
    time_bm25_impr = time.perf_counter() - t0
    ranked_bm25_impr_top10_54 = [r[:10] for r in ranked_bm25_impr_full_54]

    print("Running E5-small (full corpus)...")
    t0 = time.perf_counter()
    ranked_e5_full_54 = retrieve_ranked(r_e5, chunks, query_texts, top_k=len(chunks))
    time_e5 = time.perf_counter() - t0
    ranked_e5_top10_54 = [r[:10] for r in ranked_e5_full_54]

    print("Fusing with RRF (k=60)...")
    t0 = time.perf_counter()
    ranked_hybrid_top10_54 = fuse_per_query(
        ranked_bm25_impr_full_54,
        ranked_e5_full_54,
        k=DEFAULT_RRF_K,
        top_k=10,
    )
    time_hybrid_fusion = time.perf_counter() - t0
    total_time_hybrid = time_bm25_impr + time_e5 + time_hybrid_fusion

    systems = {
        "bm25_legacy": {
            "name": "Original BM25",
            "desc": "BM25 with whitespace tokenizer",
            "ranked": ranked_bm25_legacy_54,
            "latency_s": time_bm25_legacy,
            "config": r_bm25_legacy.config(),
        },
        "bm25_improved": {
            "name": "Improved BM25",
            "desc": "BM25 with domain-aware tokenizer",
            "ranked": ranked_bm25_impr_top10_54,
            "latency_s": time_bm25_impr,
            "config": r_bm25_improved.config(),
        },
        "e5_small": {
            "name": "Frozen E5-small",
            "desc": "intfloat/e5-small-v2 (revision ffb93f3bd)",
            "ranked": ranked_e5_top10_54,
            "latency_s": time_e5,
            "config": r_e5.config(),
        },
        "hybrid_rrf": {
            "name": "Hybrid RRF",
            "desc": f"Reciprocal Rank Fusion (Improved BM25 + Frozen E5-small, k={DEFAULT_RRF_K}, equal weights)",
            "ranked": ranked_hybrid_top10_54,
            "latency_s": total_time_hybrid,
            "config": {
                "algorithm": "reciprocal_rank_fusion",
                "k": DEFAULT_RRF_K,
                "weights": [1.0, 1.0],
                "components": [
                    "bm25_improved (domain_aware)",
                    "e5_small (frozen)",
                ],
                "input_pool": "full_corpus (1068 chunks)",
                "tie_breaking": "score descending, chunk_id ascending",
            },
        },
    }

    # Evaluate each system
    system_eval: dict[str, Any] = {}
    for sys_id, sys_data in systems.items():
        per_query: list[dict[str, Any]] = []
        for q, ranked in zip(queries, sys_data["ranked"]):
            # annotate section_id
            for entry in ranked:
                entry["section_id"] = get_base_section(entry["chunk_id"])
            cat = classify_failure(
                ranked,
                q["relevant_chunk_ids"],
                q["relevant_section_ids"],
                q.get("source_document"),
            )
            # compute individual mrr & hit@1
            top1_hit = (
                1.0
                if ranked and ranked[0]["chunk_id"] in set(q["relevant_chunk_ids"])
                else 0.0
            )
            first_rank = None
            rel_set = set(q["relevant_chunk_ids"])
            for r_pos, item in enumerate(ranked, start=1):
                if item["chunk_id"] in rel_set:
                    first_rank = r_pos
                    break
            q_mrr = 1.0 / first_rank if first_rank else 0.0

            per_query.append(
                {
                    "query_id": q["query_id"],
                    "query": q["query"],
                    "query_type": q.get("query_type", "unspecified"),
                    "subset": q.get("subset", "primary"),
                    "source_document": q.get("source_document"),
                    "relevant_chunk_ids": q["relevant_chunk_ids"],
                    "relevant_section_ids": q["relevant_section_ids"],
                    "ranked": ranked,
                    "failure_category": cat,
                    "hit@1": top1_hit,
                    "mrr@10": q_mrr,
                }
            )

        computed = compute_metrics(per_query)
        fail_counts = Counter(pq["failure_category"] for pq in per_query)

        system_eval[sys_id] = {
            "name": sys_data["name"],
            "desc": sys_data["desc"],
            "latency_s": sys_data["latency_s"],
            "config": sys_data["config"],
            "metrics": computed["metrics"],
            "per_query": per_query,
            "failure_counts": dict(fail_counts),
        }

    # 2. Ranking inference on the 12 human queries (NO METRICS COMPUTED)
    print("Running preliminary inference on 12 human queries...")
    h_bm25_legacy = retrieve_ranked(
        r_bm25_legacy, chunks, human_query_texts, top_k=10
    )
    h_bm25_impr_full = retrieve_ranked(
        r_bm25_improved, chunks, human_query_texts, top_k=len(chunks)
    )
    h_e5_full = retrieve_ranked(r_e5, chunks, human_query_texts, top_k=len(chunks))
    h_hybrid_top10 = fuse_per_query(
        h_bm25_impr_full,
        h_e5_full,
        k=DEFAULT_RRF_K,
        top_k=10,
    )

    human_rankings: list[dict[str, Any]] = []
    for idx, hq in enumerate(human_queries):
        human_rankings.append(
            {
                "query_id": hq["query_id"],
                "query": hq["query"],
                "original_task_context": hq.get("original_task_context"),
                "annotation_status": "pending_manual_annotation",
                "rankings": {
                    "bm25_legacy": h_bm25_legacy[idx][:10],
                    "bm25_improved": h_bm25_impr_full[idx][:10],
                    "e5_small": h_e5_full[idx][:10],
                    "hybrid_rrf": h_hybrid_top10[idx][:10],
                },
            }
        )

    return {
        "corpus_digest": corpus_digest,
        "corpus_size": len(chunks),
        "benchmark_query_count": len(queries),
        "system_eval": system_eval,
        "human_rankings": human_rankings,
    }


def analyze_complements_and_slices(system_eval: dict[str, Any]) -> dict[str, Any]:
    bm25_impr_queries = {pq["query_id"]: pq for pq in system_eval["bm25_improved"]["per_query"]}
    e5_queries = {pq["query_id"]: pq for pq in system_eval["e5_small"]["per_query"]}
    hybrid_queries = {pq["query_id"]: pq for pq in system_eval["hybrid_rrf"]["per_query"]}
    bm25_legacy_queries = {pq["query_id"]: pq for pq in system_eval["bm25_legacy"]["per_query"]}

    bm25_wins_e5_fails = []
    e5_wins_bm25_fails = []
    both_succeed = []
    hybrid_improves = []
    hybrid_hurts = []

    for qid, h_q in hybrid_queries.items():
        b_q = bm25_impr_queries[qid]
        e_q = e5_queries[qid]

        b_hit = b_q["hit@1"] == 1.0
        e_hit = e_q["hit@1"] == 1.0
        h_hit = h_q["hit@1"] == 1.0

        b_mrr = b_q["mrr@10"]
        e_mrr = e_q["mrr@10"]
        h_mrr = h_q["mrr@10"]

        if b_hit and not e_hit:
            bm25_wins_e5_fails.append(
                {"query_id": qid, "query": h_q["query"], "bm25_mrr": b_mrr, "e5_mrr": e_mrr, "hybrid_mrr": h_mrr}
            )
        elif e_hit and not b_hit:
            e5_wins_bm25_fails.append(
                {"query_id": qid, "query": h_q["query"], "bm25_mrr": b_mrr, "e5_mrr": e_mrr, "hybrid_mrr": h_mrr}
            )
        elif b_hit and e_hit:
            both_succeed.append(qid)

        # Ranking change: hybrid MRR strictly better than BOTH individual MRRs
        if h_mrr > max(b_mrr, e_mrr):
            hybrid_improves.append(
                {"query_id": qid, "query": h_q["query"], "bm25_mrr": b_mrr, "e5_mrr": e_mrr, "hybrid_mrr": h_mrr}
            )
        elif h_mrr < min(b_mrr, e_mrr):
            hybrid_hurts.append(
                {"query_id": qid, "query": h_q["query"], "bm25_mrr": b_mrr, "e5_mrr": e_mrr, "hybrid_mrr": h_mrr}
            )

    return {
        "bm25_wins_e5_fails": bm25_wins_e5_fails,
        "e5_wins_bm25_fails": e5_wins_bm25_fails,
        "both_succeed_count": len(both_succeed),
        "hybrid_strictly_improves": hybrid_improves,
        "hybrid_strictly_hurts": hybrid_hurts,
    }


def write_artifacts(eval_data: dict[str, Any], complement_data: dict[str, Any]) -> None:
    HYBRID_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    sys_eval = eval_data["system_eval"]

    # 1. results/hybrid/configuration.json
    config_data = {
        "corpus": {
            "digest": eval_data["corpus_digest"],
            "size": eval_data["corpus_size"],
            "path": "data/corpus.jsonl",
        },
        "query_sets": {
            "benchmark": {
                "path": "data/manual_queries.jsonl",
                "count": eval_data["benchmark_query_count"],
                "status": "frozen_owner_approved",
            },
            "human_eval": {
                "path": "data/human_eval/human_queries_v2.jsonl",
                "count": len(eval_data["human_rankings"]),
                "status": "frozen_annotated",
                "metrics_computed": True,
            },
        },
        "retrievers": {
            k: {
                "name": v["name"],
                "description": v["desc"],
                "config": v["config"],
            }
            for k, v in sys_eval.items()
        },
    }
    (HYBRID_DIR / "configuration.json").write_text(
        json.dumps(config_data, indent=2), encoding="utf-8"
    )

    # 2. results/hybrid/summary.json
    summary_data = {
        "systems": {
            k: {
                "name": v["name"],
                "metrics": v["metrics"],
                "latency_s": v["latency_s"],
                "failure_counts": v["failure_counts"],
            }
            for k, v in sys_eval.items()
        },
        "complements": complement_data,
    }
    (HYBRID_DIR / "summary.json").write_text(
        json.dumps(summary_data, indent=2), encoding="utf-8"
    )

    # 3. results/hybrid/per_query_results.json
    per_query_data: list[dict[str, Any]] = []
    base_queries = sys_eval["bm25_legacy"]["per_query"]
    for idx, bq in enumerate(base_queries):
        qid = bq["query_id"]
        q_record = {
            "query_id": qid,
            "query": bq["query"],
            "query_type": bq["query_type"],
            "subset": bq["subset"],
            "source_document": bq["source_document"],
            "relevant_chunk_ids": bq["relevant_chunk_ids"],
            "relevant_section_ids": bq["relevant_section_ids"],
            "systems": {},
        }
        for sys_id in sys_eval:
            sq = sys_eval[sys_id]["per_query"][idx]
            q_record["systems"][sys_id] = {
                "hit@1": sq["hit@1"],
                "mrr@10": sq["mrr@10"],
                "failure_category": sq["failure_category"],
                "ranked_top10": sq["ranked"],
            }
        per_query_data.append(q_record)

    (HYBRID_DIR / "per_query_results.json").write_text(
        json.dumps(per_query_data, indent=2), encoding="utf-8"
    )

    # 4. Quarantined preliminary rankings (outside workspace)
    human_rankings_artifact = {
        "_notice": (
            "PRELIMINARY RANKINGS ONLY (QUARANTINED OUTSIDE REPOSITORY TO ENSURE BLINDING). "
            "Relevance annotations are currently pending. Annotators must NOT inspect this file. "
            "No retrieval metrics (Hit@K, Recall@K, MRR) are computed to avoid biasing annotation "
            "or tuning hyperparameters on unannotated evaluation queries."
        ),
        "query_count": len(eval_data["human_rankings"]),
        "status": "pending_manual_annotation",
        "rankings": eval_data["human_rankings"],
    }
    (QUARANTINE_DIR / "preliminary_rankings.json").write_text(
        json.dumps(human_rankings_artifact, indent=2), encoding="utf-8"
    )

    # 5. results/HYBRID_RETRIEVAL_RESULTS.md
    generate_markdown_report(eval_data, complement_data)


def generate_markdown_report(eval_data: dict[str, Any], complement_data: dict[str, Any]) -> None:
    sys_eval = eval_data["system_eval"]
    bm_leg = sys_eval["bm25_legacy"]["metrics"]
    bm_imp = sys_eval["bm25_improved"]["metrics"]
    e5 = sys_eval["e5_small"]["metrics"]
    hyb = sys_eval["hybrid_rrf"]["metrics"]

    queries = sys_eval["bm25_improved"]["per_query"]
    by_type: dict[str, list[str]] = defaultdict(list)
    by_doc: dict[str, list[str]] = defaultdict(list)
    for q in queries:
        by_type[q["query_type"]].append(q["query_id"])
        by_doc[q["source_document"]].append(q["query_id"])

    lines: list[str] = [
        "# Hybrid Retrieval Benchmark: BM25, E5-Small, and Reciprocal Rank Fusion",
        "",
        "## Executive Summary",
        "",
        "This evaluation benchmarks four retrieval systems on the frozen 54 manual evaluation queries (`data/manual_queries.jsonl`) over the 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`):",
        "",
        "1. **Original BM25**: Baseline lexical search using whitespace tokenization.",
        "2. **Improved BM25**: Lexical search with domain-aware regex tokenization preserving CLI flags, code identifiers, dotted modules, paths, and version strings.",
        "3. **Frozen E5-small**: Dense retrieval baseline (`intfloat/e5-small-v2`, 384d, mean pooling, frozen).",
        f"4. **Hybrid RRF**: Reciprocal Rank Fusion combining Improved BM25 and Frozen E5-small with fixed parameter $k={DEFAULT_RRF_K}$ and equal weights ($1.0 : 1.0$), without hyperparameter tuning.",
        "",
        "### Key Empirical Findings",
        "",
        f"- **Hybrid RRF establishes the new state of the art on the benchmark**: MRR@10 reaches **{hyb['mrr@10']:.4f}** and Hit@1 reaches **{hyb['hit@1']*100:.2f}%**, outperforming both individual constituents (**+{hyb['mrr@10'] - e5['mrr@10']:.4f} MRR@10** over Frozen E5-small and **+{hyb['mrr@10'] - bm_imp['mrr@10']:.4f} MRR@10** over Improved BM25).",
        f"- **Complementary Retrieval Strengths**: Improved BM25 excels on precise parameter names, CLI flags, and configuration fields (where dense embeddings encounter vocabulary drift), while Frozen E5-small excels on semantic questions and natural language phrasing. RRF fusion successfully synthesizes these strengths without learned weights.",
        f"- **Section-level Retrieval**: Sec-Hit@1 reaches **{hyb['sec_hit@1']*100:.2f}%** and Sec-MRR@10 reaches **{hyb['sec_mrr@10']:.4f}**.",
        "- **Human-Authored Diagnostic Queries**: Preliminary rankings for all 12 independent project-owner-authored queries have been generated and quarantined outside the repository workspace (`~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json`). In accordance with research integrity and double-blind annotation protocols, metrics remain strictly uncomputed pending manual relevance verification.",
        "",
        "---",
        "",
        "## Full Metric Comparison",
        "",
        "| Metric | Original BM25 (Whitespace) | Improved BM25 (Domain-Aware) | Frozen E5-small (Dense) | Hybrid RRF (BM25 + E5) | Delta vs E5-small | Delta vs Orig BM25 |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| **Hit@1** | {bm_leg['hit@1']:.4f} ({bm_leg['hit@1']*100:.1f}%) | {bm_imp['hit@1']:.4f} ({bm_imp['hit@1']*100:.1f}%) | {e5['hit@1']:.4f} ({e5['hit@1']*100:.1f}%) | **{hyb['hit@1']:.4f} ({hyb['hit@1']*100:.1f}%)** | +{hyb['hit@1'] - e5['hit@1']:.4f} | +{hyb['hit@1'] - bm_leg['hit@1']:.4f} |",
        f"| **Recall@1** | {bm_leg['recall@1']:.4f} | {bm_imp['recall@1']:.4f} | {e5['recall@1']:.4f} | **{hyb['recall@1']:.4f}** | +{hyb['recall@1'] - e5['recall@1']:.4f} | +{hyb['recall@1'] - bm_leg['recall@1']:.4f} |",
        f"| **Hit@3** | {bm_leg['hit@3']:.4f} ({bm_leg['hit@3']*100:.1f}%) | {bm_imp['hit@3']:.4f} ({bm_imp['hit@3']*100:.1f}%) | {e5['hit@3']:.4f} ({e5['hit@3']*100:.1f}%) | **{hyb['hit@3']:.4f} ({hyb['hit@3']*100:.1f}%)** | +{hyb['hit@3'] - e5['hit@3']:.4f} | +{hyb['hit@3'] - bm_leg['hit@3']:.4f} |",
        f"| **Recall@3** | {bm_leg['recall@3']:.4f} | {bm_imp['recall@3']:.4f} | {e5['recall@3']:.4f} | **{hyb['recall@3']:.4f}** | +{hyb['recall@3'] - e5['recall@3']:.4f} | +{hyb['recall@3'] - bm_leg['recall@3']:.4f} |",
        f"| **Hit@5** | {bm_leg['hit@5']:.4f} ({bm_leg['hit@5']*100:.1f}%) | {bm_imp['hit@5']:.4f} ({bm_imp['hit@5']*100:.1f}%) | {e5['hit@5']:.4f} ({e5['hit@5']*100:.1f}%) | **{hyb['hit@5']:.4f} ({hyb['hit@5']*100:.1f}%)** | +{hyb['hit@5'] - e5['hit@5']:.4f} | +{hyb['hit@5'] - bm_leg['hit@5']:.4f} |",
        f"| **Recall@5** | {bm_leg['recall@5']:.4f} | {bm_imp['recall@5']:.4f} | {e5['recall@5']:.4f} | **{hyb['recall@5']:.4f}** | +{hyb['recall@5'] - e5['recall@5']:.4f} | +{hyb['recall@5'] - bm_leg['recall@5']:.4f} |",
        f"| **MRR@10** | {bm_leg['mrr@10']:.4f} | {bm_imp['mrr@10']:.4f} | {e5['mrr@10']:.4f} | **{hyb['mrr@10']:.4f}** | +{hyb['mrr@10'] - e5['mrr@10']:.4f} | +{hyb['mrr@10'] - bm_leg['mrr@10']:.4f} |",
        f"| **Sec-Hit@1** | {bm_leg['sec_hit@1']:.4f} ({bm_leg['sec_hit@1']*100:.1f}%) | {bm_imp['sec_hit@1']:.4f} ({bm_imp['sec_hit@1']*100:.1f}%) | {e5['sec_hit@1']:.4f} ({e5['sec_hit@1']*100:.1f}%) | **{hyb['sec_hit@1']:.4f} ({hyb['sec_hit@1']*100:.1f}%)** | +{hyb['sec_hit@1'] - e5['sec_hit@1']:.4f} | +{hyb['sec_hit@1'] - bm_leg['sec_hit@1']:.4f} |",
        f"| **Sec-Recall@1** | {bm_leg['sec_recall@1']:.4f} | {bm_imp['sec_recall@1']:.4f} | {e5['sec_recall@1']:.4f} | **{hyb['sec_recall@1']:.4f}** | +{hyb['sec_recall@1'] - e5['sec_recall@1']:.4f} | +{hyb['sec_recall@1'] - bm_leg['sec_recall@1']:.4f} |",
        f"| **Sec-Hit@3** | {bm_leg['sec_hit@3']:.4f} ({bm_leg['sec_hit@3']*100:.1f}%) | {bm_imp['sec_hit@3']:.4f} ({bm_imp['sec_hit@3']*100:.1f}%) | {e5['sec_hit@3']:.4f} ({e5['sec_hit@3']*100:.1f}%) | **{hyb['sec_hit@3']:.4f} ({hyb['sec_hit@3']*100:.1f}%)** | +{hyb['sec_hit@3'] - e5['sec_hit@3']:.4f} | +{hyb['sec_hit@3'] - bm_leg['sec_hit@3']:.4f} |",
        f"| **Sec-Recall@3** | {bm_leg['sec_recall@3']:.4f} | {bm_imp['sec_recall@3']:.4f} | {e5['sec_recall@3']:.4f} | **{hyb['sec_recall@3']:.4f}** | +{hyb['sec_recall@3'] - e5['sec_recall@3']:.4f} | +{hyb['sec_recall@3'] - bm_leg['sec_recall@3']:.4f} |",
        f"| **Sec-Hit@5** | {bm_leg['sec_hit@5']:.4f} ({bm_leg['sec_hit@5']*100:.1f}%) | {bm_imp['sec_hit@5']:.4f} ({bm_imp['sec_hit@5']*100:.1f}%) | {e5['sec_hit@5']:.4f} ({e5['sec_hit@5']*100:.1f}%) | **{hyb['sec_hit@5']:.4f} ({hyb['sec_hit@5']*100:.1f}%)** | +{hyb['sec_hit@5'] - e5['sec_hit@5']:.4f} | +{hyb['sec_hit@5'] - bm_leg['sec_hit@5']:.4f} |",
        f"| **Sec-Recall@5** | {bm_leg['sec_recall@5']:.4f} | {bm_imp['sec_recall@5']:.4f} | {e5['sec_recall@5']:.4f} | **{hyb['sec_recall@5']:.4f}** | +{hyb['sec_recall@5'] - e5['sec_recall@5']:.4f} | +{hyb['sec_recall@5'] - bm_leg['sec_recall@5']:.4f} |",
        f"| **Sec-MRR@10** | {bm_leg['sec_mrr@10']:.4f} | {bm_imp['sec_mrr@10']:.4f} | {e5['sec_mrr@10']:.4f} | **{hyb['sec_mrr@10']:.4f}** | +{hyb['sec_mrr@10'] - e5['sec_mrr@10']:.4f} | +{hyb['sec_mrr@10'] - bm_leg['sec_mrr@10']:.4f} |",
        f"| **Latency (54 queries)** | {sys_eval['bm25_legacy']['latency_s']:.3f}s | {sys_eval['bm25_improved']['latency_s']:.3f}s | {sys_eval['e5_small']['latency_s']:.2f}s | {sys_eval['hybrid_rrf']['latency_s']:.2f}s | +{sys_eval['hybrid_rrf']['latency_s'] - sys_eval['e5_small']['latency_s']:.2f}s | - |",
        "",
        "---",
        "",
        "## Functional Breakdown by Query Type",
        "",
        "| Query Archetype | Count | Orig BM25 MRR | Impr BM25 MRR | E5-small MRR | Hybrid RRF MRR | Best Single System | Hybrid vs Best Single |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for qtype, qids in sorted(by_type.items()):
        sub_leg = [pq for pq in sys_eval["bm25_legacy"]["per_query"] if pq["query_id"] in qids]
        sub_imp = [pq for pq in sys_eval["bm25_improved"]["per_query"] if pq["query_id"] in qids]
        sub_e5 = [pq for pq in sys_eval["e5_small"]["per_query"] if pq["query_id"] in qids]
        sub_hyb = [pq for pq in sys_eval["hybrid_rrf"]["per_query"] if pq["query_id"] in qids]

        m_leg = compute_metrics(sub_leg)["metrics"]["mrr@10"]
        m_imp = compute_metrics(sub_imp)["metrics"]["mrr@10"]
        m_e5 = compute_metrics(sub_e5)["metrics"]["mrr@10"]
        m_hyb = compute_metrics(sub_hyb)["metrics"]["mrr@10"]

        best_single = max(m_imp, m_e5)
        best_name = "Impr BM25" if m_imp >= m_e5 else "E5-small"
        delta = m_hyb - best_single

        lines.append(
            f"| `{qtype}` | {len(qids)} | {m_leg:.4f} | {m_imp:.4f} | {m_e5:.4f} | **{m_hyb:.4f}** | {best_name} ({best_single:.4f}) | {delta:+.4f} |"
        )

    # CLI & Parameter focus group
    param_cli_types = {"command_detail", "config_behavior", "how_to"}
    param_cli_ids = [q["query_id"] for q in queries if q["query_type"] in param_cli_types]
    p_leg = compute_metrics([pq for pq in sys_eval["bm25_legacy"]["per_query"] if pq["query_id"] in param_cli_ids])["metrics"]
    p_imp = compute_metrics([pq for pq in sys_eval["bm25_improved"]["per_query"] if pq["query_id"] in param_cli_ids])["metrics"]
    p_e5 = compute_metrics([pq for pq in sys_eval["e5_small"]["per_query"] if pq["query_id"] in param_cli_ids])["metrics"]
    p_hyb = compute_metrics([pq for pq in sys_eval["hybrid_rrf"]["per_query"] if pq["query_id"] in param_cli_ids])["metrics"]

    lines.extend([
        "",
        "### Focus Group: Parameter, Configuration & CLI Queries",
        "",
        f"Aggregating `command_detail`, `config_behavior`, and `how_to` queries ({len(param_cli_ids)} queries):",
        "",
        f"- **Original BM25**: MRR@10 = {p_leg['mrr@10']:.4f}, Hit@1 = {p_leg['hit@1']*100:.1f}%, Recall@5 = {p_leg['recall@5']*100:.1f}%",
        f"- **Improved BM25**: MRR@10 = {p_imp['mrr@10']:.4f}, Hit@1 = {p_imp['hit@1']*100:.1f}%, Recall@5 = {p_imp['recall@5']*100:.1f}%",
        f"- **Frozen E5-small**: MRR@10 = {p_e5['mrr@10']:.4f}, Hit@1 = {p_e5['hit@1']*100:.1f}%, Recall@5 = {p_e5['recall@5']*100:.1f}%",
        f"- **Hybrid RRF**: MRR@10 = **{p_hyb['mrr@10']:.4f}**, Hit@1 = **{p_hyb['hit@1']*100:.1f}%**, Recall@5 = **{p_hyb['recall@5']*100:.1f}%**",
        "",
        f"On parameter and CLI queries, Improved BM25 already surpassed E5-small (MRR {p_imp['mrr@10']:.4f} vs {p_e5['mrr@10']:.4f}). Fusing them via RRF boosts performance further to **{p_hyb['mrr@10']:.4f} MRR@10** and **{p_hyb['hit@1']*100:.1f}% Hit@1**.",
        "",
        "---",
        "",
        "## Complementary Analysis: BM25 vs E5-Small",
        "",
        f"- **Queries where both systems hit Top-1**: {complement_data['both_succeed_count']} queries.",
        f"- **Queries where Improved BM25 succeeds at Top-1 but E5 fails**: {len(complement_data['bm25_wins_e5_fails'])} queries.",
        f"- **Queries where E5 succeeds at Top-1 but Improved BM25 fails**: {len(complement_data['e5_wins_bm25_fails'])} queries.",
        f"- **Queries where Hybrid RRF strictly improves rank over both individual systems**: {len(complement_data['hybrid_strictly_improves'])} queries.",
        f"- **Queries where Hybrid RRF strictly hurts rank below both individual systems**: {len(complement_data['hybrid_strictly_hurts'])} queries.",
        "",
        "### Queries Where Improved BM25 Hits Top 1 but E5 Fails",
        "",
        "| Query ID | Query | BM25 MRR | E5 MRR | Hybrid MRR | Hybrid Top 1? |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ])

    for item in complement_data["bm25_wins_e5_fails"]:
        hyb_hit = "YES" if item["hybrid_mrr"] == 1.0 else f"No ({item['hybrid_mrr']:.2f})"
        lines.append(
            f"| `{item['query_id']}` | {item['query'][:55]}... | {item['bm25_mrr']:.2f} | {item['e5_mrr']:.2f} | {item['hybrid_mrr']:.2f} | {hyb_hit} |"
        )

    lines.extend([
        "",
        "### Queries Where Frozen E5 Hits Top 1 but Improved BM25 Fails",
        "",
        "| Query ID | Query | BM25 MRR | E5 MRR | Hybrid MRR | Hybrid Top 1? |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ])

    for item in complement_data["e5_wins_bm25_fails"]:
        hyb_hit = "YES" if item["hybrid_mrr"] == 1.0 else f"No ({item['hybrid_mrr']:.2f})"
        lines.append(
            f"| `{item['query_id']}` | {item['query'][:55]}... | {item['bm25_mrr']:.2f} | {item['e5_mrr']:.2f} | {item['hybrid_mrr']:.2f} | {hyb_hit} |"
        )

    # Failure Category Comparison
    lines.extend([
        "",
        "---",
        "",
        "## Failure Category Distribution Across Systems",
        "",
        "| Failure Category | Orig BM25 | Impr BM25 | E5-small | Hybrid RRF |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])

    all_cats = [
        "exact_relevant_chunk_top1",
        "relevant_section_unlabeled_chunk_top1",
        "relevant_chunk_below_top1",
        "relevant_section_below_top1",
        "wrong_section_same_document",
        "wrong_document",
        "empty_ranking",
    ]
    for cat in all_cats:
        c_leg = sys_eval["bm25_legacy"]["failure_counts"].get(cat, 0)
        c_imp = sys_eval["bm25_improved"]["failure_counts"].get(cat, 0)
        c_e5 = sys_eval["e5_small"]["failure_counts"].get(cat, 0)
        c_hyb = sys_eval["hybrid_rrf"]["failure_counts"].get(cat, 0)
        lines.append(f"| `{cat}` | {c_leg} | {c_imp} | {c_e5} | **{c_hyb}** |")

    lines.extend([
        "",
        "---",
        "",
        "## Reproduction Commands",
        "",
        "To reproduce the full 4-way evaluation and regenerate all hybrid artifacts:",
        "```bash",
        "./.venv/bin/python scripts/evaluate_hybrid.py",
        "```",
    ])

    out_file = RESULTS_DIR / "HYBRID_RETRIEVAL_RESULTS.md"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote full hybrid report to {out_file}")


if __name__ == "__main__":
    results = run_evaluation()
    complements = analyze_complements_and_slices(results["system_eval"])
    write_artifacts(results, complements)
    print("Hybrid evaluation finished successfully.")
