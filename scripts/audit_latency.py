"""Detailed latency benchmark separating cold-start and steady-state stages:
- Model Loading (disk -> RAM/CPU)
- Corpus Indexing / Encoding (corpus preparation)
- Query Encoding
- Retrieval / Scoring
- Fusion (RRF)
- Steady-state per-query latency
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from fusion import fuse_per_query
from retrievers import BM25Retriever, build_retriever, retrieve_ranked

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def measure_latency_stages() -> dict[str, Any]:
    corpus = [
        json.loads(line)
        for line in (DATA_DIR / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    queries = [
        json.loads(line)
        for line in (DATA_DIR / "manual_queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    query_texts = [q["query"] for q in queries]
    chunk_ids = [c["chunk_id"] for c in corpus]

    # ==========================================
    # 1. Improved BM25 (Domain-Aware)
    # ==========================================
    # Cold start: init
    t0 = time.perf_counter()
    bm25 = BM25Retriever(tokenizer="domain_aware")
    bm25_init_s = time.perf_counter() - t0

    # Cold start: fit corpus index
    t0 = time.perf_counter()
    bm25.fit(corpus)
    bm25_fit_s = time.perf_counter() - t0

    # Steady state: scoring + ranking
    bm25_steady_runs = []
    for _ in range(5):
        t0 = time.perf_counter()
        for q in query_texts:
            scores = bm25.score(q)
            # top-10 sort
            sorted_pairs = sorted(zip(scores, chunk_ids), key=lambda x: -x[0])[:10]
        bm25_steady_runs.append(time.perf_counter() - t0)

    bm25_steady_total_s = float(np.mean(bm25_steady_runs))
    bm25_steady_per_query_ms = (bm25_steady_total_s / len(query_texts)) * 1000.0

    # ==========================================
    # 2. Frozen E5-small (Dense)
    # ==========================================
    # Cold start: model load (PyTorch weights from disk)
    t0 = time.perf_counter()
    e5 = build_retriever("e5_small", repo_root=REPO_ROOT)
    e5._load()
    e5_load_s = time.perf_counter() - t0

    # Cold start: corpus encoding (1,068 chunks)
    t0 = time.perf_counter()
    corpus_vecs = e5.encode_corpus(corpus)
    e5_corpus_encode_s = time.perf_counter() - t0

    # Warmup pass (1 query)
    t0 = time.perf_counter()
    w_vec = e5.encode_queries([query_texts[0]])
    _ = corpus_vecs @ w_vec[0]
    e5_warmup_s = time.perf_counter() - t0

    # Steady state: query encoding and search over 3 runs
    e5_query_encode_runs = []
    e5_search_runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        q_vecs = e5.encode_queries(query_texts)
        e5_query_encode_runs.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        # Matrix multiply (54, 384) x (384, 1068) -> (54, 1068)
        sim_matrix = q_vecs @ corpus_vecs.T
        for i in range(len(query_texts)):
            top_idx = np.argsort(-sim_matrix[i])[:10]
        e5_search_runs.append(time.perf_counter() - t0)

    e5_query_encode_total_s = float(np.mean(e5_query_encode_runs))
    e5_search_total_s = float(np.mean(e5_search_runs))
    e5_steady_total_s = e5_query_encode_total_s + e5_search_total_s
    e5_steady_per_query_ms = (e5_steady_total_s / len(query_texts)) * 1000.0

    # ==========================================
    # 3. Reciprocal Rank Fusion (RRF)
    # ==========================================
    # Pre-rank full corpus lists for fusion
    bm25_full = retrieve_ranked(bm25, corpus, query_texts, top_k=len(corpus))
    e5_full = retrieve_ranked(e5, corpus, query_texts, top_k=len(corpus))

    fusion_runs = []
    for _ in range(5):
        t0 = time.perf_counter()
        _ = fuse_per_query(bm25_full, e5_full, k=60, top_k=10)
        fusion_runs.append(time.perf_counter() - t0)

    fusion_total_s = float(np.mean(fusion_runs))
    fusion_per_query_ms = (fusion_total_s / len(query_texts)) * 1000.0

    # ==========================================
    # 4. Total Pipeline Summary
    # ==========================================
    # Cold start total: model load + corpus indexing/encoding
    cold_start_bm25_s = bm25_init_s + bm25_fit_s
    cold_start_e5_s = e5_load_s + e5_corpus_encode_s
    cold_start_hybrid_s = cold_start_bm25_s + cold_start_e5_s

    # Steady state per query:
    # Hybrid = BM25 scoring + E5 query encode + E5 dot product + RRF fusion
    hybrid_steady_per_query_ms = (
        bm25_steady_per_query_ms + e5_steady_per_query_ms + fusion_per_query_ms
    )

    return {
        "bm25_improved": {
            "cold_start": {
                "model_init_s": round(bm25_init_s, 4),
                "corpus_indexing_s": round(bm25_fit_s, 4),
                "total_cold_start_s": round(cold_start_bm25_s, 4),
            },
            "steady_state": {
                "batch_54_queries_s": round(bm25_steady_total_s, 4),
                "per_query_ms": round(bm25_steady_per_query_ms, 2),
            },
        },
        "e5_small": {
            "cold_start": {
                "model_load_s": round(e5_load_s, 3),
                "corpus_encode_1068_chunks_s": round(e5_corpus_encode_s, 3),
                "warmup_query_s": round(e5_warmup_s, 4),
                "total_cold_start_s": round(cold_start_e5_s, 3),
            },
            "steady_state": {
                "query_encoding_54_s": round(e5_query_encode_total_s, 3),
                "query_encoding_per_query_ms": round(
                    e5_query_encode_total_s / len(query_texts) * 1000.0, 2
                ),
                "matrix_search_54_s": round(e5_search_total_s, 4),
                "matrix_search_per_query_ms": round(
                    e5_search_total_s / len(query_texts) * 1000.0, 2
                ),
                "total_batch_54_queries_s": round(e5_steady_total_s, 3),
                "per_query_ms": round(e5_steady_per_query_ms, 2),
            },
        },
        "rrf_fusion": {
            "fusion_batch_54_queries_s": round(fusion_total_s, 4),
            "per_query_ms": round(fusion_per_query_ms, 2),
            "input_pool_depth": len(corpus),
            "k": 60,
        },
        "hybrid_pipeline": {
            "total_cold_start_s": round(cold_start_hybrid_s, 3),
            "steady_state_batch_54_queries_s": round(
                bm25_steady_total_s + e5_steady_total_s + fusion_total_s, 3
            ),
            "steady_state_per_query_ms": round(hybrid_steady_per_query_ms, 2),
            "latency_breakdown_pct": {
                "e5_query_encoding": round(
                    (e5_query_encode_total_s / (bm25_steady_total_s + e5_steady_total_s + fusion_total_s)) * 100, 1
                ),
                "bm25_scoring": round(
                    (bm25_steady_total_s / (bm25_steady_total_s + e5_steady_total_s + fusion_total_s)) * 100, 1
                ),
                "e5_dot_product": round(
                    (e5_search_total_s / (bm25_steady_total_s + e5_steady_total_s + fusion_total_s)) * 100, 1
                ),
                "rrf_fusion": round(
                    (fusion_total_s / (bm25_steady_total_s + e5_steady_total_s + fusion_total_s)) * 100, 1
                ),
            },
        },
    }


if __name__ == "__main__":
    results = measure_latency_stages()
    print(json.dumps(results, indent=2))
