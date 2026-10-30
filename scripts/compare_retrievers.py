"""Comparative analysis for Evaluation v2.

Consumes the four retriever result JSONs produced by
``scripts/run_retrieval.py`` and produces ``results/v2/comparison.md``:

- micro-average (all queries equally) and macro-average (mean of the four
  per-document scores) for every chunk- and section-level metric;
- paired document-stratified bootstrap intervals (10,000 resamples, seed 42)
  with a single shared resampler so identical query indices are applied to
  all retrievers, for the three pairwise comparisons Soup−frozen,
  Soup−BM25, Soup−E5;
- leave-one-document-out sensitivity for the same comparisons;
- a section-cluster bootstrap only if the frozen dataset's cluster structure
  makes it informative (>= 30% of query-occupied sections contain >= 2
  queries); otherwise documented as skipped;
- mutually exclusive failure-category tables;
- primary and overlap subsets reported separately.

All intervals are exploratory uncertainty estimates on the fixed query
sample. Four held-out documents are insufficient for population-level
inference. No p-values, no significance claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_V2 = REPO_ROOT / "results" / "v2"

RETRIEVER_IDS = ("mini_lm_frozen", "mini_lm_soup", "bm25", "e5_small")
COMPARISONS = (("mini_lm_soup", "mini_lm_frozen"), ("mini_lm_soup", "bm25"), ("mini_lm_soup", "e5_small"))
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42
CLUSTER_MIN_FRACTION = 0.30

CAVEAT = (
    "Four held-out documents are insufficient for population-level inference; "
    "all intervals describe uncertainty within this fixed query sample. "
    "No p-values and no significance claims are made."
)


def load_result(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def metric_names(result: dict[str, Any]) -> list[str]:
    return sorted(result["_per_query_scores"].keys())


def per_doc_scores(result: dict[str, Any], metric: str) -> dict[str, list[float]]:
    doc_scores: dict[str, list[float]] = defaultdict(list)
    for qr, score in zip(
        result["per_query_results"], result["_per_query_scores"][metric]
    ):
        doc_scores[qr["source_document"]].append(score)
    return dict(doc_scores)


def micro_metric(result: dict[str, Any], metric: str) -> float:
    scores = result["_per_query_scores"][metric]
    return float(np.mean(scores)) if scores else float("nan")


def macro_metric(result: dict[str, Any], metric: str) -> float:
    doc_scores = per_doc_scores(result, metric)
    return float(np.mean([np.mean(v) for v in doc_scores.values()])) if doc_scores else float("nan")


class StratifiedResampler:
    """Doc-stratified bootstrap: resamples query indices within each document.

    One resampler instance generates identical indices for every retriever,
    preserving pairedness across all comparisons.
    """

    def __init__(
        self,
        query_docs: Sequence[str],
        n_bootstrap: int = BOOTSTRAP_N,
        seed: int = BOOTSTRAP_SEED,
    ):
        self.query_docs = list(query_docs)
        self.n_bootstrap = n_bootstrap
        self.seed = seed
        self._rng = np.random.RandomState(seed)
        self._doc_indices: dict[str, np.ndarray] = {}
        for i, doc in enumerate(self.query_docs):
            self._doc_indices.setdefault(doc, []).append(i)
        for doc in self._doc_indices:
            self._doc_indices[doc] = np.array(self._doc_indices[doc])

    def iterations(self):
        for _ in range(self.n_bootstrap):
            flat: list[int] = []
            for doc, indices in self._doc_indices.items():
                flat.extend(int(i) for i in self._rng.choice(indices, size=len(indices), replace=True))
            yield flat


def paired_bootstrap_ci(
    a_scores: Sequence[float],
    b_scores: Sequence[float],
    resampler: StratifiedResampler,
    alpha: float = 0.05,
) -> dict[str, float]:
    a = np.asarray(a_scores, dtype=float)
    b = np.asarray(b_scores, dtype=float)
    observed_delta = float(np.mean(a) - np.mean(b))
    deltas = []
    for idx in resampler.iterations():
        deltas.append(float(np.mean(a[idx]) - np.mean(b[idx])))
    deltas = sorted(deltas)
    lo = deltas[int(alpha / 2 * len(deltas))]
    hi = deltas[int((1 - alpha / 2) * len(deltas))]
    return {
        "delta": round(observed_delta, 4),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
    }


def leave_one_doc_out(
    results: dict[str, dict[str, Any]],
    metric: str,
    query_ids: Sequence[str],
    docs_per_query: Sequence[str],
) -> dict[str, Any]:
    """Micro and macro values per retriever with each document dropped."""
    out: dict[str, Any] = {"docs": []}
    docs = sorted(set(docs_per_query))
    for dropped in docs:
        keep = [i for i, d in enumerate(docs_per_query) if d != dropped]
        row: dict[str, Any] = {"dropped_document": dropped, "n_kept_queries": len(keep)}
        for rid, result in results.items():
            doc_scores = per_doc_scores(result, metric)
            kept_docs = {d: v for d, v in doc_scores.items() if d != dropped}
            micro = float(np.mean(
                [result["_per_query_scores"][metric][i] for i in keep]
            ))
            macro = float(np.mean([np.mean(v) for v in kept_docs.values()])) if kept_docs else float("nan")
            row[f"{rid}_micro"] = round(micro, 4)
            row[f"{rid}_macro"] = round(macro, 4)
        for a, b in COMPARISONS:
            delta = row[f"{a}_micro"] - row[f"{b}_micro"]
            row[f"delta_{a}_vs_{b}"] = round(delta, 4)
        out["docs"].append(row)
    return out


def cluster_structure(
    per_query_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Count queries per (document, section) cluster and decide whether a
    cluster bootstrap would differ meaningfully from query-level resampling."""
    from retrieval import get_base_section

    clusters = Counter()
    for qr in per_query_results:
        for cid in qr["relevant_chunk_ids"]:
            clusters[(qr["source_document"], get_base_section(cid))] += 1
            break
    occupied = list(clusters.values())
    multi = sum(1 for c in occupied if c >= 2)
    fraction = multi / len(occupied) if occupied else 0.0
    informative = fraction >= CLUSTER_MIN_FRACTION
    return {
        "occupied_sections": len(occupied),
        "sections_with_single_query": sum(1 for c in occupied if c == 1),
        "sections_with_multiple_queries": multi,
        "multi_query_fraction": round(fraction, 4),
        "threshold": CLUSTER_MIN_FRACTION,
        "cluster_bootstrap_informative": informative,
        "decision": (
            "implemented (cluster structure adds information beyond query-level resampling)"
            if informative
            else "skipped: most query-occupied sections contain a single query, so "
                 "cluster resampling degenerates to query-level resampling"
        ),
    }


def first_relevant_rank(ranked: Sequence[dict], relevant_ids: set[str]) -> int | None:
    for entry in ranked:
        if entry["chunk_id"] in relevant_ids:
            return entry["rank"]
    return None


def first_relevant_section_rank(
    ranked: Sequence[dict], relevant_sections: set[str]
) -> int | None:
    from retrieval import section_ranking

    for entry in section_ranking(ranked):
        if entry["section_id"] in relevant_sections:
            return entry["rank"]
    return None


def regression_counts(
    a_result: dict[str, Any],
    b_result: dict[str, Any],
    query_ids: Sequence[str],
) -> dict[str, int]:
    """Queries where b ranks the first relevant chunk/section worse than a.

    Sibling-first (relevant_section_unlabeled_chunk_top1) cases do not
    inflate section regressions: the first relevant *section* rank is what is
    compared at section level.
    """
    a_by_id = {q["query_id"]: q for q in a_result["per_query_results"]}
    b_by_id = {q["query_id"]: q for q in b_result["per_query_results"]}
    chunk_reg = 0
    section_reg = 0
    for qid in query_ids:
        a, b = a_by_id[qid], b_by_id[qid]
        rel_chunks = set(a["relevant_chunk_ids"])
        rel_sections = set(a["relevant_section_ids"])
        a_cr = first_relevant_rank(a["ranked"], rel_chunks)
        b_cr = first_relevant_rank(b["ranked"], rel_chunks)
        if (b_cr is None and a_cr is not None) or (
            a_cr is not None and b_cr is not None and b_cr > a_cr
        ):
            chunk_reg += 1
        a_sr = first_relevant_section_rank(a["ranked"], rel_sections)
        b_sr = first_relevant_section_rank(b["ranked"], rel_sections)
        if (b_sr is None and a_sr is not None) or (
            a_sr is not None and b_sr is not None and b_sr > a_sr
        ):
            section_reg += 1
    return {"chunk_regressions": chunk_reg, "section_regressions": section_reg}


def failure_category_counts(result: dict[str, Any]) -> dict[str, int]:
    counts = Counter(q["failure_category"] for q in result["per_query_results"])
    no_relevant = sum(
        counts.get(leaf, 0) for leaf in ("wrong_section_same_document", "wrong_document")
    )
    table = {leaf: counts.get(leaf, 0) for leaf in (
        "empty_ranking",
        "exact_relevant_chunk_top1",
        "relevant_section_unlabeled_chunk_top1",
        "relevant_chunk_below_top1",
        "relevant_section_below_top1",
        "wrong_section_same_document",
        "wrong_document",
    )}
    table["no_relevant_result_top10"] = no_relevant
    return table


def generate_report(
    results: dict[str, dict[str, Any]],
    output_path: Path,
    n_bootstrap: int = BOOTSTRAP_N,
    seed: int = BOOTSTRAP_SEED,
) -> str:
    lines: list[str] = []
    query_ids = [q["query_id"] for q in results["mini_lm_frozen"]["per_query_results"]]
    docs_per_query = [
        q["source_document"] for q in results["mini_lm_frozen"]["per_query_results"]
    ]
    subsets_present = sorted({
        q.get("subset", "primary") for q in results["mini_lm_frozen"]["per_query_results"]
    })

    lines += [
        "# Evaluation v2 — Four-Way Retrieval Comparison (Manual Queries)",
        "",
        f"**Retrievers:** {', '.join(RETRIEVER_IDS)}  ",
        f"**Queries:** {len(query_ids)} manual queries (owner-authored)  ",
        f"**Corpus fingerprint:** {results['mini_lm_frozen'].get('corpus_fingerprint', '?')}  ",
        f"**Query-set fingerprint:** {results['mini_lm_frozen'].get('query_set_fingerprint', '?')[:16]}…  ",
        f"**Bootstrap:** {n_bootstrap} resamples, seed={seed}, paired document-stratified percentile intervals, shared indices across retrievers.",
        "",
        f"> {CAVEAT}",
        "",
    ]

    resampler = StratifiedResampler(docs_per_query, n_bootstrap=n_bootstrap, seed=seed)

    for metric in metric_names(results["mini_lm_frozen"]):
        lines += [f"## {metric}", ""]
        header = "| Retriever | Micro | Macro |" + "".join(
            f" Δ vs {b} [95% CI] |" for _, b in COMPARISONS
        )
        lines += [header, "|---|:---:|:---:|" + ":---:|" * len(COMPARISONS)]
        for rid in RETRIEVER_IDS:
            micro = micro_metric(results[rid], metric)
            macro = macro_metric(results[rid], metric)
            cells = [f"{micro:.4f}", f"{macro:.4f}"]
            for a, b in COMPARISONS:
                if rid == a:
                    scores_a = results[a]["_per_query_scores"][metric]
                    scores_b = results[b]["_per_query_scores"][metric]
                    ci = paired_bootstrap_ci(scores_a, scores_b, resampler)
                    cells.append(f"{ci['delta']:+.4f} [{ci['ci_lower']:+.4f}, {ci['ci_upper']:+.4f}]")
                else:
                    cells.append("—")
            lines.append(f"| {rid} | " + " | ".join(cells) + " |")
        lines += [""]

    lines += ["## Leave-One-Document-Out Sensitivity (micro deltas)", ""]
    for metric in metric_names(results["mini_lm_frozen"]):
        lines += [f"### {metric}", ""]
        lines += ["| Dropped doc | n kept | " + " | ".join(
            f"Δ Soup−{b}" for _, b in COMPARISONS
        ) + " |", "|---|:---:|" + ":---:|" * len(COMPARISONS)]
        for row in leave_one_doc_out(results, metric, query_ids, docs_per_query)["docs"]:
            cells = []
            for _, b in COMPARISONS:
                key = f"delta_mini_lm_soup_vs_{b}"
                cells.append(f"{row[key]:+.4f}")
            lines.append(
                f"| {row['dropped_document']} | {row['n_kept_queries']} | " + " | ".join(cells) + " |"
            )
        lines += [""]

    lines += ["## Failure Categories (mutually exclusive, one leaf per query)", ""]
    lines += ["| Category | " + " | ".join(RETRIEVER_IDS) + " |",
              "|---|" + ":---:|" * len(RETRIEVER_IDS)]
    categories = list(failure_category_counts(results["mini_lm_frozen"]).keys())
    for cat in categories:
        row = [cat] + [str(failure_category_counts(results[rid])[cat]) for rid in RETRIEVER_IDS]
        lines.append("| " + " | ".join(row) + " |")
    lines += [
        "",
        "> `no_relevant_result_top10` is the aggregate of `wrong_section_same_document` + `wrong_document`.",
        "",
    ]

    lines += ["## Regression Counts (candidate ranks first relevant item worse)", ""]
    lines += ["| Comparison | Chunk regressions | Section regressions |",
              "|---|:---:|:---:|"]
    for a, b in COMPARISONS:
        counts = regression_counts(results[a], results[b], query_ids)
        lines.append(
            f"| {a} vs {b} | {counts['chunk_regressions']} | {counts['section_regressions']} |"
        )
    lines += [
        "",
        "> A sibling-first result (`relevant_section_unlabeled_chunk_top1`) is a chunk-level miss "
        "but a section-level hit and never counts as a section regression.",
        "",
    ]

    for subset in subsets_present:
        subset_ids = [
            q["query_id"] for q in results["mini_lm_frozen"]["per_query_results"]
            if q.get("subset", "primary") == subset
        ]
        title = "Overlap Subset" if subset == "overlap" else "Primary Subset"
        lines += [f"## {title} (n={len(subset_ids)})", ""]
        if not subset_ids:
            lines += ["(no queries in this subset)", ""]
            continue
        lines += ["| Metric | " + " | ".join(RETRIEVER_IDS) + " |",
                  "|---|" + ":---:|" * len(RETRIEVER_IDS)]
        for metric in metric_names(results["mini_lm_frozen"]):
            cells = []
            for rid in RETRIEVER_IDS:
                by_id = {q["query_id"]: s for q, s in zip(
                    results[rid]["per_query_results"],
                    results[rid]["_per_query_scores"][metric],
                )}
                values = [by_id[qid] for qid in subset_ids]
                cells.append(f"{np.mean(values):.4f}")
            lines.append(f"| {metric} | " + " | ".join(cells) + " |")
        lines += [""]

    cluster = cluster_structure(results["mini_lm_frozen"]["per_query_results"])
    lines += ["## Section-Cluster Bootstrap Decision", ""]
    lines += [
        f"- Query-occupied sections: {cluster['occupied_sections']} "
        f"(single-query: {cluster['sections_with_single_query']}, "
        f"multi-query: {cluster['sections_with_multiple_queries']}; "
        f"multi-query fraction {cluster['multi_query_fraction']}, threshold {cluster['threshold']})",
        f"- Decision: **{cluster['decision']}**.",
        "",
    ]

    report = "\n".join(lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare the four v2 retrievers")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_V2)
    parser.add_argument("--output", type=Path, default=RESULTS_V2 / "comparison.md")
    parser.add_argument("--bootstrap-n", type=int, default=BOOTSTRAP_N)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    args = parser.parse_args()

    results = {rid: load_result(args.results_dir / f"{rid}.json") for rid in RETRIEVER_IDS}
    report = generate_report(results, args.output, n_bootstrap=args.bootstrap_n, seed=args.seed)
    print(f"report -> {args.output} ({len(report.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
