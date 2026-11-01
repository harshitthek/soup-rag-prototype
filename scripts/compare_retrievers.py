"""Comparative analysis for Evaluation v2.

Consumes the four retriever result JSONs produced by
``scripts/run_retrieval.py`` and produces ``results/v2/comparison.md``:

- micro-average (all queries equally) and macro-average (mean of the four
  per-document scores) for every chunk- and section-level metric;
- paired document-stratified bootstrap intervals (10,000 resamples, seed 42)
  from one precomputed index plan, so the identical query indices are applied
  to every metric, every retriever, and all three pairwise comparisons
  Soup−frozen, Soup−BM25, Soup−E5;
- leave-one-document-out sensitivity for the same comparisons;
- section-cluster structure evaluation to decide whether cluster resampling
  would be informative (>= 30% of query-occupied sections contain >= 2
  queries), recording the decision in the report (reported confidence
  intervals use paired document-stratified resampling; no cluster bootstrap
  resampling or cluster bootstrap confidence intervals are computed);
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

OVERLAP_AUDIT_NOTE = (
    "The 18 original overlap labels were audited against training-chunk text "
    "on 2026-10-31 (`docs/EVALUATION_V2_OVERLAP_AUDIT.md`): 15 confirmed and "
    "3 reclassified as primary with owner approval. The subset tables below "
    "use the final 39 primary / 15 overlap split."
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
    """Precomputed document-stratified bootstrap plan.

    All index draws are generated once at construction. Each resample keeps
    every document's original query count. Because the draws are stored,
    every metric and every pairwise comparison in a report reuses the exact
    same query positions, and both retrievers in a comparison are always
    scored on those same positions.
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
        self.indices: list[list[int]] = indices


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
    """Count queries per (document, section) cluster and evaluate whether a
    cluster bootstrap would differ meaningfully from query-level resampling.

    The decision heuristic is recorded in the report; no cluster bootstrap
    confidence intervals are computed.
    """
    from retrieval import chunk_doc_name, get_base_section

    clusters = Counter()
    for qr in per_query_results:
        sec_ids = {get_base_section(cid) for cid in qr["relevant_chunk_ids"]}
        for sid in sec_ids:
            clusters[(chunk_doc_name(sid), sid)] += 1
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
            "not implemented: cluster structure exceeds threshold but cluster resampling is "
            "unsupported; report uses query-level resampling"
            if informative
            else "skipped: most query-occupied sections contain a single query, so "
                 "cluster resampling degenerates to query-level resampling"
        ),
    }


def first_relevant_rank(ranked: Sequence[dict], relevant_ids: set[str]) -> int | None:
    for entry in ranked:
        rank = entry.get("rank")
        if rank is not None and 1 <= rank <= 10 and entry.get("chunk_id") in relevant_ids:
            return rank
    return None


def first_relevant_section_rank(
    ranked: Sequence[dict], relevant_sections: set[str]
) -> int | None:
    from retrieval import section_ranking

    for entry in section_ranking(ranked):
        rank = entry.get("rank")
        if rank is not None and 1 <= rank <= 10 and entry.get("section_id") in relevant_sections:
            return rank
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
        f"**Queries:** {len(query_ids)} manual queries (owner-approved; manually crafted by the owner with AI assistance)  ",
        f"**Corpus fingerprint:** {results['mini_lm_frozen'].get('corpus_fingerprint', '?')}  ",
        f"**Query-set fingerprint:** {results['mini_lm_frozen'].get('query_set_fingerprint', '?')[:16]}…  ",
        f"**Bootstrap:** {n_bootstrap} resamples, seed={seed}, paired document-stratified percentile intervals, one precomputed index plan shared across every metric and retriever.",
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
        counts = regression_counts(results[b], results[a], query_ids)
        lines.append(
            f"| {a} vs {b} | {counts['chunk_regressions']} | {counts['section_regressions']} |"
        )
    lines += [
        "",
        "> A sibling-first result (`relevant_section_unlabeled_chunk_top1`) is a chunk-level miss "
        "but a section-level hit and never counts as a section regression.",
        "",
    ]

    lines += [f"> {OVERLAP_AUDIT_NOTE}", ""]

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


REQUIRED_RESULT_FIELDS = (
    "corpus_fingerprint",
    "corpus_digest",
    "query_set_fingerprint",
    "query_count",
)


def validate_results(results: dict[str, dict[str, Any]]) -> None:
    for rid in RETRIEVER_IDS:
        if rid not in results:
            raise ValueError(f"missing result for retriever '{rid}'")
        res = results[rid]
        if res.get("retriever_id") != rid:
            raise ValueError(
                f"result file for '{rid}' has mismatched retriever_id: '{res.get('retriever_id')}'"
            )
        for field in REQUIRED_RESULT_FIELDS:
            if field not in res or res[field] is None:
                raise ValueError(
                    f"result file for '{rid}' is missing required field '{field}'"
                )
        pqr = res.get("per_query_results", [])
        n_pqr = len(pqr)
        per_query_scores = res.get("_per_query_scores", {})
        for metric, scores in per_query_scores.items():
            if len(scores) != n_pqr:
                raise ValueError(
                    f"result file for '{rid}' metric '{metric}' has {len(scores)} scores, "
                    f"expected {n_pqr} (matching per_query_results)"
                )

    first_res = results[RETRIEVER_IDS[0]]
    ref_corpus_fp = first_res["corpus_fingerprint"]
    ref_corpus_dg = first_res["corpus_digest"]
    ref_query_fp = first_res["query_set_fingerprint"]
    ref_query_count = first_res["query_count"]
    ref_query_order = [q["query_id"] for q in first_res.get("per_query_results", [])]

    for rid in RETRIEVER_IDS[1:]:
        res = results[rid]
        if res["corpus_fingerprint"] != ref_corpus_fp:
            raise ValueError(
                f"corpus_fingerprint mismatch: '{rid}' ({res['corpus_fingerprint']}) "
                f"!= '{RETRIEVER_IDS[0]}' ({ref_corpus_fp})"
            )
        if res["corpus_digest"] != ref_corpus_dg:
            raise ValueError(
                f"corpus_digest mismatch: '{rid}' ({res['corpus_digest']}) "
                f"!= '{RETRIEVER_IDS[0]}' ({ref_corpus_dg})"
            )
        if res["query_set_fingerprint"] != ref_query_fp:
            raise ValueError(
                f"query_set_fingerprint mismatch: '{rid}' ({res['query_set_fingerprint']}) "
                f"!= '{RETRIEVER_IDS[0]}' ({ref_query_fp})"
            )
        if res["query_count"] != ref_query_count:
            raise ValueError(
                f"query_count mismatch: '{rid}' ({res['query_count']}) "
                f"!= '{RETRIEVER_IDS[0]}' ({ref_query_count})"
            )
        query_order = [q["query_id"] for q in res.get("per_query_results", [])]
        if query_order != ref_query_order:
            raise ValueError(
                f"query order mismatch between '{rid}' and '{RETRIEVER_IDS[0]}'"
            )


def positive_int(val: str) -> int:
    try:
        ival = int(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: '{val}'")
    if ival < 1:
        raise argparse.ArgumentTypeError(
            f"--bootstrap-n must be at least 1, got {ival}"
        )
    return ival


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare the four v2 retrievers")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_V2)
    parser.add_argument("--output", type=Path, default=RESULTS_V2 / "comparison.md")
    parser.add_argument("--bootstrap-n", type=positive_int, default=BOOTSTRAP_N)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    args = parser.parse_args()

    results = {rid: load_result(args.results_dir / f"{rid}.json") for rid in RETRIEVER_IDS}
    validate_results(results)
    report = generate_report(results, args.output, n_bootstrap=args.bootstrap_n, seed=args.seed)
    print(f"report -> {args.output} ({len(report.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
