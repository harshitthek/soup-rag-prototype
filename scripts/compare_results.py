"""Compare baseline vs candidate retrieval results.

Computes deltas, paired bootstrap 95% confidence intervals, per-document
breakdown, and identifies the worst failure cases.

Usage:
    python compare_results.py \
        --baseline ../results/baseline.json \
        --candidate ../results/candidate.json \
        --output ../results/comparison.md
"""

from __future__ import annotations

import argparse
import json
import numpy as np
from pathlib import Path

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42


def load_result(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def paired_bootstrap_ci(
    baseline_scores: list[float],
    candidate_scores: list[float],
    n_bootstrap: int = BOOTSTRAP_N,
    seed: int = BOOTSTRAP_SEED,
    alpha: float = 0.05,
) -> dict:
    """Paired percentile bootstrap confidence interval on the delta (candidate - baseline).

    Computes empirical uncertainty bounds for the paired metric difference across
    the evaluation query sample.
    """
    rng = np.random.RandomState(seed)
    b = np.array(baseline_scores)
    c = np.array(candidate_scores)
    n = len(b)
    observed_delta = float(np.mean(c) - np.mean(b))

    boot_deltas = []
    for _ in range(n_bootstrap):
        indices = rng.choice(n, size=n, replace=True)
        boot_delta = float(np.mean(c[indices]) - np.mean(b[indices]))
        boot_deltas.append(boot_delta)

    boot_deltas = sorted(boot_deltas)
    lo = boot_deltas[int(alpha / 2 * n_bootstrap)]
    hi = boot_deltas[int((1 - alpha / 2) * n_bootstrap)]

    return {
        "delta": round(observed_delta, 4),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
    }


def find_regressions(baseline: dict, candidate: dict) -> list[dict]:
    """Find queries where candidate ranks the relevant chunk worse than baseline."""
    regressions = []

    b_results = {q["query_id"]: q for q in baseline["per_query_results"]}
    c_results = {q["query_id"]: q for q in candidate["per_query_results"]}

    for qid in b_results:
        bq = b_results[qid]
        cq = c_results.get(qid)
        if not cq:
            continue

        relevant = set(bq["relevant_chunk_ids"])

        # Find first relevant rank in each
        b_rank = None
        b_top1 = bq["ranked"][0] if bq["ranked"] else None
        for r in bq["ranked"]:
            if r["chunk_id"] in relevant:
                b_rank = r["rank"]
                break

        c_rank = None
        c_top1 = cq["ranked"][0] if cq["ranked"] else None
        for r in cq["ranked"]:
            if r["chunk_id"] in relevant:
                c_rank = r["rank"]
                break

        # Regression = candidate ranks relevant chunk lower (or misses it)
        b_rank_val = b_rank if b_rank is not None else 999
        c_rank_val = c_rank if c_rank is not None else 999

        if c_rank_val > b_rank_val:
            regressions.append(
                {
                    "query_id": qid,
                    "query": bq["query"],
                    "relevant_ids": list(relevant),
                    "baseline_rank": b_rank,
                    "candidate_rank": c_rank,
                    "baseline_top1": b_top1["chunk_id"] if b_top1 else None,
                    "candidate_top1": c_top1["chunk_id"] if c_top1 else None,
                }
            )

    regressions.sort(
        key=lambda r: (r["candidate_rank"] or 999) - (r["baseline_rank"] or 999),
        reverse=True,
    )
    return regressions


def build_per_doc_metrics(result: dict) -> dict[str, dict]:
    """Break down metrics by source document."""
    per_doc: dict[str, list[dict]] = {}

    for qr in result["per_query_results"]:
        # Infer doc from relevant chunk IDs
        for cid in qr["relevant_chunk_ids"]:
            doc = cid.split("::")[0]
            per_doc.setdefault(doc, []).append(qr)
            break  # One doc per query

    doc_metrics = {}
    for doc, queries in sorted(per_doc.items()):
        recalls = {1: [], 3: [], 5: []}
        mrr_scores = []

        for qr in queries:
            relevant = set(qr["relevant_chunk_ids"])
            retrieved = [r["chunk_id"] for r in qr["ranked"]]

            for k in (1, 3, 5):
                hit = 1.0 if set(retrieved[:k]) & relevant else 0.0
                recalls[k].append(hit)

            rr = 0.0
            for ri, rid in enumerate(retrieved[:10], 1):
                if rid in relevant:
                    rr = 1.0 / ri
                    break
            mrr_scores.append(rr)

        doc_metrics[doc] = {
            "n_queries": len(queries),
            "recall@1": round(float(np.mean(recalls[1])), 4),
            "recall@3": round(float(np.mean(recalls[3])), 4),
            "recall@5": round(float(np.mean(recalls[5])), 4),
            "mrr@10": round(float(np.mean(mrr_scores)), 4),
        }

    return doc_metrics


def generate_report(
    baseline: dict,
    candidate: dict,
    output_path: Path,
) -> str:
    """Generate the comparison markdown report."""
    b_scores = baseline["_per_query_scores"]
    c_scores = candidate["_per_query_scores"]

    # Compute bootstrap CIs
    metrics_to_compare = ["recall@1", "recall@3", "recall@5", "mrr@10"]
    bootstrap_results = {}

    for metric in metrics_to_compare:
        if metric.startswith("recall@"):
            k = metric.split("@")[1]  # JSON keys are strings
            b_vals = b_scores["recall"][k]
            c_vals = c_scores["recall"][k]
        else:
            b_vals = b_scores["mrr"]
            c_vals = c_scores["mrr"]

        bootstrap_results[metric] = paired_bootstrap_ci(b_vals, c_vals)

    # Regressions
    regressions = find_regressions(baseline, candidate)

    # Per-doc breakdown
    b_per_doc = build_per_doc_metrics(baseline)
    c_per_doc = build_per_doc_metrics(candidate)
    all_docs = sorted(set(list(b_per_doc.keys()) + list(c_per_doc.keys())))
    doc_count_str = f"{len(all_docs)} held-out docs" if all_docs else "held-out docs"

    # Build report
    lines = [
        "# Retrieval Quality: Before vs After Embedding Fine-Tuning",
        "",
        f"**Baseline:** Frozen `{baseline['model_id']}`  ",
        f"**Candidate:** Fine-tuned (adapter: `{candidate['adapter_dir']}`)  ",
        f"**Corpus:** {baseline['corpus_size']} chunks from 12 docs  ",
        f"**Queries:** {baseline['query_count']} synthetic test queries (template-generated from held-out docs)  ",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Baseline | Candidate | Delta | 95% Bootstrap CI |",
        "|--------|----------|-----------|-------|------------------|",
    ]

    for metric in metrics_to_compare:
        b_val = baseline["metrics"].get(metric, 0)
        c_val = candidate["metrics"].get(metric, 0)
        bs = bootstrap_results[metric]
        lines.append(
            f"| {metric} | {b_val:.4f} | {c_val:.4f} | "
            f"{bs['delta']:+.4f} | [{bs['ci_lower']:+.4f}, {bs['ci_upper']:+.4f}] |"
        )

    lines.extend(
        [
            "",
            f"> Bootstrap: {BOOTSTRAP_N} resamples, seed={BOOTSTRAP_SEED}, "
            f"paired query-level percentile interval. With n={baseline['query_count']} queries from "
            f"{doc_count_str}, treat these intervals as exploratory uncertainty estimates on the paired difference.",
            "",
            "## Per-Document Breakdown",
            "",
            "| Document | Queries | B Recall@1 | C Recall@1 | B MRR@10 | C MRR@10 |",
            "|----------|---------|------------|------------|----------|----------|",
        ]
    )

    for doc in all_docs:
        b = b_per_doc.get(doc, {})
        c = c_per_doc.get(doc, {})
        lines.append(
            f"| {doc} | {b.get('n_queries', 0)} | "
            f"{b.get('recall@1', 0):.4f} | {c.get('recall@1', 0):.4f} | "
            f"{b.get('mrr@10', 0):.4f} | {c.get('mrr@10', 0):.4f} |"
        )

    lines.extend(
        [
            "",
            f"## Retrieval Regressions ({len(regressions)} queries)",
            "",
        ]
    )

    if regressions:
        lines.append(
            "| Query | Baseline Rank | Candidate Rank | B Top-1 | C Top-1 |"
        )
        lines.append("|-------|---------------|----------------|---------|---------|")
        for reg in regressions[:10]:
            b_rank = reg["baseline_rank"] or ">10"
            c_rank = reg["candidate_rank"] or ">10"
            lines.append(
                f"| {reg['query'][:60]}... | {b_rank} | {c_rank} | "
                f"`{reg['baseline_top1']}` | `{reg['candidate_top1']}` |"
            )
    else:
        lines.append("No regressions detected.")

    lines.append("")

    report = "\n".join(lines) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Compare baseline vs candidate")
    parser.add_argument("--baseline", required=True, help="Baseline JSON")
    parser.add_argument("--candidate", required=True, help="Candidate JSON")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "results" / "comparison.md"),
    )
    args = parser.parse_args()

    baseline = load_result(Path(args.baseline))
    candidate = load_result(Path(args.candidate))

    generate_report(baseline, candidate, Path(args.output))


if __name__ == "__main__":
    main()
