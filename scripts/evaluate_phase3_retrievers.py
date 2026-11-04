#!/usr/bin/env python3
"""Phase 3: Multi-Retriever Benchmark Evaluation Script.

Evaluates 9 retrievers over the frozen 54-query manual evaluation benchmark:
1. R1: BM25 (BM25Okapi, k1=1.5, b=0.75)
2. R2: Frozen MiniLM (all-MiniLM-L6-v2, rev: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41)
3. R3: Frozen E5-small (e5-small-v2, rev: ffb93f3bd4047442299a41ebb6fa998a38507c52)
4. R4: A-full (output_embedding/)
5. R5: A-matched (output/adapter_exp_a_matched/)
6. R6: B (output/adapter_exp_b/)
7. R7: C-matched (output/adapter_exp_c_matched/)
8. R8: C-matched-balanced (output/adapter_exp_c_matched_balanced/)
9. R9: C-full (output/adapter_exp_c_full/)

Produces all Phase 3 required deliverables under results/phase3/:
- Individual retriever results JSON files.
- Aggregate comparison report (micro and macro).
- Sliced metrics (Full 54, Core Primary 39, Core Overlap 15, Candidate Clean 52, Candidate Overlap 2, Pure Held-Out 37).
- Document-stratified paired percentile bootstrap (10,000 resamples, seed 42).
- Leave-one-document-out sensitivity analysis.
- Detailed failure analysis.
- SHA256 output manifest.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
PHASE3_DIR = RESULTS_DIR / "phase3"
PHASE3_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from retrieval import (
    FAILURE_CATEGORIES,
    NO_RELEVANT_RESULT_LEAVES,
    classify_failure,
    compute_metrics,
    compute_query_metrics,
    get_base_section,
    rank_corpus,
)
from retrievers import (
    BM25Retriever,
    DenseRetriever,
    E5_MODEL_ID,
    E5_REVISION,
    MINILM_MODEL_ID,
    MINILM_REVISION,
    build_passage_text,
    retrieve_ranked,
)

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}

CANDIDATE_OVERLAP_QIDS = {"manual_025", "manual_048"}
TOP_K = 10
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42

RETRIEVERS_CONFIG = [
    {
        "id": "bm25",
        "name": "BM25",
        "type": "bm25",
        "k1": 1.5,
        "b": 0.75,
    },
    {
        "id": "mini_lm_frozen",
        "name": "Frozen MiniLM",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": None,
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "e5_small",
        "name": "Frozen E5-small",
        "type": "dense",
        "model_id": E5_MODEL_ID,
        "revision": E5_REVISION,
        "adapter_dir": None,
        "max_length": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    {
        "id": "a_full",
        "name": "A-full",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output_embedding"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "a_matched",
        "name": "A-matched",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output/adapter_exp_a_matched"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "b",
        "name": "B",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output/adapter_exp_b"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "c_matched",
        "name": "C-matched",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output/adapter_exp_c_matched"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "c_matched_balanced",
        "name": "C-matched-balanced",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output/adapter_exp_c_matched_balanced"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "id": "c_full",
        "name": "C-full",
        "type": "dense",
        "model_id": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": str(REPO_ROOT / "output/adapter_exp_c_full"),
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_frozen_inputs():
    print("Verifying frozen benchmark inputs...")
    for fname, expected in FROZEN_CHECKSUMS.items():
        p = DATA_DIR / fname
        if not p.exists():
            raise FileNotFoundError(f"Missing frozen file: {p}")
        h = compute_sha256(p)
        if h != expected:
            raise ValueError(f"Checksum mismatch for {fname}: got {h}, expected {expected}")
    print("  ✓ All 5 frozen benchmark checksums verified bit-exact.")


class StratifiedResampler:
    def __init__(self, query_docs: Sequence[str], n_bootstrap: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED):
        self.query_docs = list(query_docs)
        self.n_bootstrap = n_bootstrap
        self.seed = seed
        rng = np.random.RandomState(seed)
        doc_indices: dict[str, list[int]] = {}
        for i, doc in enumerate(self.query_docs):
            doc_indices.setdefault(doc, []).append(i)
        indices: list[list[int]] = []
        for _ in range(n_bootstrap):
            flat: list[int] = []
            for doc, positions in doc_indices.items():
                chosen = rng.choice(positions, size=len(positions), replace=True)
                flat.extend(int(i) for i in chosen)
            indices.append(flat)
        self.indices = indices


def paired_bootstrap_ci(a_scores: Sequence[float], b_scores: Sequence[float], resampler: StratifiedResampler, alpha: float = 0.05) -> dict[str, float]:
    a = np.asarray(a_scores, dtype=float)
    b = np.asarray(b_scores, dtype=float)
    observed_delta = float(np.mean(a) - np.mean(b))
    deltas = []
    for idx in resampler.indices:
        deltas.append(float(np.mean(a[idx]) - np.mean(b[idx])))
    deltas = sorted(deltas)
    lo = deltas[int(alpha / 2 * len(deltas))]
    hi = deltas[int((1 - alpha / 2) * len(deltas))]
    return {
        "delta": round(observed_delta, 4),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
    }


def main():
    print("=" * 70)
    print("PHASE 3: MULTI-RETRIEVER BENCHMARK EVALUATION")
    print("=" * 70)

    # 1. Preflight check
    verify_frozen_inputs()

    # Load corpus and queries
    corpus_path = DATA_DIR / "corpus.jsonl"
    corpus_bytes = corpus_path.read_bytes()
    corpus_digest = hashlib.sha256(corpus_bytes).hexdigest()
    chunks = [json.loads(line) for line in corpus_bytes.decode("utf-8").splitlines() if line.strip()]
    chunk_ids = [c["chunk_id"] for c in chunks]

    queries_path = DATA_DIR / "manual_queries.jsonl"
    queries_bytes = queries_path.read_bytes()
    query_fp = hashlib.sha256(queries_bytes).hexdigest()
    queries = [json.loads(line) for line in queries_bytes.decode("utf-8").splitlines() if line.strip()]
    query_texts = [q["query"] for q in queries]
    query_docs = [q["source_document"] for q in queries]

    print(f"\nCorpus loaded: {len(chunks)} chunks (digest: {corpus_digest[:16]}...)")
    print(f"Queries loaded: {len(queries)} queries (digest: {query_fp[:16]}...)")

    # Build evaluation partition masks
    slice_indices = {
        "full": list(range(len(queries))),
        "core_primary": [i for i, q in enumerate(queries) if q["subset"] == "primary"],
        "core_overlap": [i for i, q in enumerate(queries) if q["subset"] == "overlap"],
        "candidate_clean": [i for i, q in enumerate(queries) if q["query_id"] not in CANDIDATE_OVERLAP_QIDS],
        "candidate_overlap": [i for i, q in enumerate(queries) if q["query_id"] in CANDIDATE_OVERLAP_QIDS],
        "pure_held_out": [i for i, q in enumerate(queries) if q["subset"] == "primary" and q["query_id"] not in CANDIDATE_OVERLAP_QIDS],
    }

    print("\nEvaluation Slice Sizes:")
    for s_name, indices in slice_indices.items():
        print(f"  {s_name:20s}: {len(indices)} queries")

    assert len(slice_indices["full"]) == 54
    assert len(slice_indices["core_primary"]) == 39
    assert len(slice_indices["core_overlap"]) == 15
    assert len(slice_indices["candidate_clean"]) == 52
    assert len(slice_indices["candidate_overlap"]) == 2
    assert len(slice_indices["pure_held_out"]) == 37

    # Run retrieval for all 9 retrievers
    all_results: dict[str, dict[str, Any]] = {}

    for rc in RETRIEVERS_CONFIG:
        rid = rc["id"]
        rname = rc["name"]
        print("\n" + "-" * 60)
        print(f"Evaluating Retriever: {rname} ({rid})")
        print("-" * 60)

        # Build retriever instance
        if rc["type"] == "bm25":
            retriever = BM25Retriever(rid, k1=rc["k1"], b=rc["b"])
        else:
            retriever = DenseRetriever(
                retriever_id=rid,
                model_id=rc["model_id"],
                revision=rc["revision"],
                adapter_dir=rc["adapter_dir"],
                max_length=rc["max_length"],
                query_prefix=rc["query_prefix"],
                passage_prefix=rc["passage_prefix"],
                device="cpu",
            )

        t0 = time.perf_counter()
        ranked_lists = retrieve_ranked(retriever, chunks, query_texts, top_k=TOP_K)
        encode_time = time.perf_counter() - t0
        print(f"  Retrieval finished in {encode_time:.2f}s")

        per_query_results = []
        for q, ranked in zip(queries, ranked_lists):
            for entry in ranked:
                entry["section_id"] = get_base_section(entry["chunk_id"])
            category = classify_failure(
                ranked,
                q["relevant_chunk_ids"],
                q["relevant_section_ids"],
                q.get("source_document"),
            )
            per_query_results.append({
                "query_id": q["query_id"],
                "query": q["query"],
                "subset": q.get("subset", "primary"),
                "source_document": q.get("source_document"),
                "candidate_subset": "partial_overlap" if q["query_id"] in CANDIDATE_OVERLAP_QIDS else "clean",
                "relevant_chunk_ids": q["relevant_chunk_ids"],
                "relevant_section_ids": q["relevant_section_ids"],
                "ranked": ranked,
                "failure_category": category,
            })

        computed = compute_metrics(per_query_results)

        # Compute metrics per slice (micro and macro)
        slice_metrics = {}
        for s_name, indices in slice_indices.items():
            sub_results = [per_query_results[i] for i in indices]
            sub_computed = compute_metrics(sub_results)
            # Micro
            sub_micro = sub_computed["metrics"]
            # Macro (mean of per-doc means)
            sub_doc_scores = defaultdict(lambda: defaultdict(list))
            for i in indices:
                doc = query_docs[i]
                for m_name, vals in computed["_per_query"].items():
                    sub_doc_scores[m_name][doc].append(vals[i])
            sub_macro = {}
            for m_name, d_map in sub_doc_scores.items():
                sub_macro[m_name] = float(np.mean([np.mean(vals) for vals in d_map.values()]))

            slice_metrics[s_name] = {
                "count": len(indices),
                "micro": sub_micro,
                "macro": sub_macro,
            }

        # Failure category counts
        fail_counts = collections.Counter(qr["failure_category"] for qr in per_query_results)
        fail_counts["no_relevant_result_top10"] = sum(fail_counts[k] for k in NO_RELEVANT_RESULT_LEAVES)

        result_obj = {
            "retriever_id": rid,
            "retriever_name": rname,
            "retriever_config": retriever.config(),
            "corpus_fingerprint": "1068_chunks_frozen",
            "corpus_digest": corpus_digest,
            "query_set": "manual",
            "query_set_fingerprint": query_fp,
            "corpus_size": len(chunk_ids),
            "query_count": len(queries),
            "top_k": TOP_K,
            "encode_time_s": round(encode_time, 3),
            "metrics": computed["metrics"],
            "slice_metrics": slice_metrics,
            "failure_counts": dict(fail_counts),
            "per_query_results": per_query_results,
            "_per_query_scores": computed["_per_query"],
        }

        all_results[rid] = result_obj

        # Save individual result JSON
        out_file = PHASE3_DIR / f"retriever_{rid}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        print(f"  Saved -> {out_file}")
        print(f"  Hit@1: {computed['metrics']['hit@1']:.4f} | Recall@3: {computed['metrics']['recall@3']:.4f} | MRR@10: {computed['metrics']['mrr@10']:.4f}")
        print(f"  Sec-Hit@1: {computed['metrics']['sec_hit@1']:.4f} | Sec-Recall@3: {computed['metrics']['sec_recall@3']:.4f} | Sec-MRR@10: {computed['metrics']['sec_mrr@10']:.4f}")

    # Build Aggregate Comparison Table
    print("\n" + "=" * 70)
    print("BUILDING AGGREGATE COMPARISONS & STATISTICAL ANALYSIS")
    print("=" * 70)

    resampler = StratifiedResampler(query_docs, n_bootstrap=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)

    # 1. Pairwise Bootstrap CIs against Baselines
    # Adapters vs MiniLM-frozen, vs BM25, vs E5-small
    baseline_ids = ["mini_lm_frozen", "bm25", "e5_small"]
    adapter_ids = ["a_full", "a_matched", "b", "c_matched", "c_matched_balanced", "c_full"]
    experimental_contrasts = [
        ("a_full", "a_matched"),
        ("a_matched", "b"),
        ("b", "c_matched_balanced"),
        ("c_matched", "c_matched_balanced"),
        ("c_matched_balanced", "c_full"),
    ]

    bootstrap_results = {}
    all_metrics_to_test = ["hit@1", "hit@3", "recall@3", "mrr@10", "sec_hit@1", "sec_hit@3", "sec_recall@3", "sec_mrr@10"]

    for m in all_metrics_to_test:
        bootstrap_results[m] = {}
        # Adapters vs Baselines
        for ad in adapter_ids:
            for base in baseline_ids:
                pair_key = f"{ad}_vs_{base}"
                a_sc = all_results[ad]["_per_query_scores"][m]
                b_sc = all_results[base]["_per_query_scores"][m]
                ci = paired_bootstrap_ci(a_sc, b_sc, resampler)
                bootstrap_results[m][pair_key] = ci

        # Experimental Contrasts
        for a, b in experimental_contrasts:
            pair_key = f"{a}_vs_{b}"
            a_sc = all_results[a]["_per_query_scores"][m]
            b_sc = all_results[b]["_per_query_scores"][m]
            ci = paired_bootstrap_ci(a_sc, b_sc, resampler)
            bootstrap_results[m][pair_key] = ci

    # Save bootstrap results
    boot_file = PHASE3_DIR / "bootstrap_ci.json"
    with open(boot_file, "w", encoding="utf-8") as f:
        json.dump(bootstrap_results, f, indent=2)
    print(f"Saved bootstrap CIs -> {boot_file}")

    # 2. Leave-One-Document-Out Analysis
    docs = sorted(set(query_docs))
    lodo_results = {}
    for m in ["hit@1", "mrr@10", "sec_hit@1", "sec_mrr@10"]:
        lodo_results[m] = []
        for dropped in docs:
            keep_idx = [i for i, d in enumerate(query_docs) if d != dropped]
            row = {"dropped_document": dropped, "kept_queries": len(keep_idx), "scores": {}}
            for rid in all_results:
                sc = [all_results[rid]["_per_query_scores"][m][i] for i in keep_idx]
                row["scores"][rid] = round(float(np.mean(sc)), 4)
            # Add deltas vs baselines
            row["deltas"] = {}
            for ad in adapter_ids:
                for base in baseline_ids:
                    delta = row["scores"][ad] - row["scores"][base]
                    row["deltas"][f"{ad}_vs_{base}"] = round(delta, 4)
            for a, b in experimental_contrasts:
                delta = row["scores"][a] - row["scores"][b]
                row["deltas"][f"{a}_vs_{b}"] = round(delta, 4)
            lodo_results[m].append(row)

    lodo_file = PHASE3_DIR / "lodo_analysis.json"
    with open(lodo_file, "w", encoding="utf-8") as f:
        json.dump(lodo_results, f, indent=2)
    print(f"Saved LODO analysis -> {lodo_file}")

    # 3. Per-Document Metrics
    per_doc_summary = {}
    for doc in docs:
        doc_idx = [i for i, d in enumerate(query_docs) if d == doc]
        per_doc_summary[doc] = {"count": len(doc_idx), "retrievers": {}}
        for rid in all_results:
            doc_m = {}
            for m in all_metrics_to_test:
                sc = [all_results[rid]["_per_query_scores"][m][i] for i in doc_idx]
                doc_m[m] = round(float(np.mean(sc)), 4)
            per_doc_summary[doc]["retrievers"][rid] = doc_m

    per_doc_file = PHASE3_DIR / "per_document_metrics.json"
    with open(per_doc_file, "w", encoding="utf-8") as f:
        json.dump(per_doc_summary, f, indent=2)
    print(f"Saved per-document metrics -> {per_doc_file}")

    # 4. Failure Analysis Compilation
    failure_summary = {
        "categories": list(FAILURE_CATEGORIES) + ["no_relevant_result_top10"],
        "counts": {rid: all_results[rid]["failure_counts"] for rid in all_results},
        "query_regressions_vs_frozen": {},
        "query_improvements_vs_frozen": {},
    }

    frozen_mrr = all_results["mini_lm_frozen"]["_per_query_scores"]["mrr@10"]
    frozen_hits = all_results["mini_lm_frozen"]["_per_query_scores"]["hit@1"]

    for ad in adapter_ids:
        ad_mrr = all_results[ad]["_per_query_scores"]["mrr@10"]
        ad_hits = all_results[ad]["_per_query_scores"]["hit@1"]
        regressions = []
        improvements = []
        for i, q in enumerate(queries):
            qid = q["query_id"]
            if ad_mrr[i] < frozen_mrr[i]:
                regressions.append({
                    "query_id": qid,
                    "doc": q["source_document"],
                    "query": q["query"],
                    "frozen_mrr": frozen_mrr[i],
                    "adapter_mrr": ad_mrr[i],
                    "frozen_hit1": frozen_hits[i],
                    "adapter_hit1": ad_hits[i],
                    "frozen_failure": all_results["mini_lm_frozen"]["per_query_results"][i]["failure_category"],
                    "adapter_failure": all_results[ad]["per_query_results"][i]["failure_category"],
                })
            elif ad_mrr[i] > frozen_mrr[i]:
                improvements.append({
                    "query_id": qid,
                    "doc": q["source_document"],
                    "query": q["query"],
                    "frozen_mrr": frozen_mrr[i],
                    "adapter_mrr": ad_mrr[i],
                    "frozen_hit1": frozen_hits[i],
                    "adapter_hit1": ad_hits[i],
                    "frozen_failure": all_results["mini_lm_frozen"]["per_query_results"][i]["failure_category"],
                    "adapter_failure": all_results[ad]["per_query_results"][i]["failure_category"],
                })
        failure_summary["query_regressions_vs_frozen"][ad] = regressions
        failure_summary["query_improvements_vs_frozen"][ad] = improvements

    failure_file = PHASE3_DIR / "failure_analysis.json"
    with open(failure_file, "w", encoding="utf-8") as f:
        json.dump(failure_summary, f, indent=2)
    print(f"Saved failure analysis -> {failure_file}")

    # 5. Full Per-Query Ranked Lists
    all_query_rankings = {}
    for rid in all_results:
        all_query_rankings[rid] = [
            {
                "query_id": qr["query_id"],
                "ranked": qr["ranked"],
                "failure_category": qr["failure_category"]
            }
            for qr in all_results[rid]["per_query_results"]
        ]
    rankings_file = PHASE3_DIR / "per_query_ranked_results.json"
    with open(rankings_file, "w", encoding="utf-8") as f:
        json.dump(all_query_rankings, f, indent=2)
    print(f"Saved per-query ranked results -> {rankings_file}")

    # 6. Aggregate Comparison JSON
    aggregate_comparison = {
        "retrievers": [rc["name"] for rc in RETRIEVERS_CONFIG],
        "slices": {},
    }
    for s_name in slice_indices:
        aggregate_comparison["slices"][s_name] = {}
        for rc in RETRIEVERS_CONFIG:
            rid = rc["id"]
            aggregate_comparison["slices"][s_name][rid] = all_results[rid]["slice_metrics"][s_name]

    agg_file = PHASE3_DIR / "aggregate_comparison.json"
    with open(agg_file, "w", encoding="utf-8") as f:
        json.dump(aggregate_comparison, f, indent=2)
    print(f"Saved aggregate comparison -> {agg_file}")

    # 7. Experiment Summary JSON
    exp_summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "corpus_fingerprint": corpus_digest,
        "query_fingerprint": query_fp,
        "total_queries": len(queries),
        "total_chunks": len(chunks),
        "retrievers": {
            rc["id"]: {
                "name": rc["name"],
                "encode_time_s": all_results[rc["id"]]["encode_time_s"],
                "metrics_full_micro": all_results[rc["id"]]["slice_metrics"]["full"]["micro"],
                "metrics_full_macro": all_results[rc["id"]]["slice_metrics"]["full"]["macro"],
                "metrics_pure_held_out_micro": all_results[rc["id"]]["slice_metrics"]["pure_held_out"]["micro"],
                "metrics_pure_held_out_macro": all_results[rc["id"]]["slice_metrics"]["pure_held_out"]["macro"],
            }
            for rc in RETRIEVERS_CONFIG
        }
    }
    exp_file = PHASE3_DIR / "experiment_summary.json"
    with open(exp_file, "w", encoding="utf-8") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"Saved experiment summary -> {exp_file}")

    # 8. SHA256 Manifest
    manifest_lines = []
    for p in sorted(PHASE3_DIR.glob("*")):
        if p.name == "manifest.sha256":
            continue
        h = compute_sha256(p)
        manifest_lines.append(f"{h}  {p.name}")
    manifest_file = PHASE3_DIR / "manifest.sha256"
    manifest_file.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(f"Saved manifest -> {manifest_file}")

    # Post-evaluation integrity check
    verify_frozen_inputs()
    print("\n✓ ALL PHASE 3 RETRIEVAL EVALUATIONS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
