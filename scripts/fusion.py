"""Reciprocal Rank Fusion (RRF) for hybrid retrieval.

Implements standard Reciprocal Rank Fusion:
    RRF(d) = sum_{r in R} (w_r / (k + rank_r(d)))
with predefined parameter k=60 and equal retriever weights by default.

Deterministic tie-breaking:
    1. Fused RRF score descending.
    2. chunk_id ascending (lexicographic).

Pure Python with stdlib-only dependencies, fully compatible with existing
retrieval evaluation pipelines.
"""

from __future__ import annotations

from typing import Any, Sequence

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_runs: Sequence[Sequence[dict[str, Any] | str]],
    k: int = DEFAULT_RRF_K,
    weights: Sequence[float] | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Fuse multiple ranked lists of documents using Reciprocal Rank Fusion.

    Parameters
    ----------
    ranked_runs : Sequence[Sequence[dict[str, Any] | str]]
        A sequence of ranked lists (one per retriever). Each item in a ranked
        list can be either a dictionary containing a ``"chunk_id"`` key (and
        optional ``"rank"``), or a string representing the ``chunk_id`` directly.
        Items are assumed to be in 1-based ranked order from best (rank 1)
        to worst.
    k : int, default=60
        Smoothing constant in reciprocal rank calculation. Fixed to 60 per
        project specification.
    weights : Sequence[float] | None, default=None
        Per-retriever weight multipliers. Defaults to equal weights (1.0 each).
    top_k : int, default=10
        Number of fused top results to return.

    Returns
    -------
    list[dict[str, Any]]
        List of fused ranked results, each formatted as:
        ``{"rank": int, "chunk_id": str, "score": float, "component_ranks": dict[int, int]}``
    """
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k}")
    if top_k <= 0:
        raise ValueError(f"top_k must be a positive integer, got {top_k}")

    num_runs = len(ranked_runs)
    if num_runs == 0:
        return []

    if weights is None:
        run_weights = [1.0] * num_runs
    else:
        if len(weights) != num_runs:
            raise ValueError(
                f"weights length ({len(weights)}) must match ranked_runs count ({num_runs})"
            )
        run_weights = [float(w) for w in weights]

    # Map chunk_id -> {score: float, component_ranks: dict[run_idx, rank]}
    doc_scores: dict[str, float] = {}
    doc_ranks: dict[str, dict[int, int]] = {}

    for run_idx, run in enumerate(ranked_runs):
        w = run_weights[run_idx]
        seen_chunks_in_run: set[str] = set()

        for rank_pos, item in enumerate(run, start=1):
            if isinstance(item, dict):
                chunk_id = str(item["chunk_id"])
                # If item explicitly provides 1-based rank, respect it; otherwise use position
                explicit_rank = item.get("rank")
                rank = int(explicit_rank) if explicit_rank is not None else rank_pos
            else:
                chunk_id = str(item)
                rank = rank_pos

            # Deduplication: only credit the best (first) rank in a single run
            if chunk_id in seen_chunks_in_run:
                continue
            seen_chunks_in_run.add(chunk_id)

            rrf_contrib = w / (k + rank)
            doc_scores[chunk_id] = doc_scores.get(chunk_id, 0.0) + rrf_contrib

            if chunk_id not in doc_ranks:
                doc_ranks[chunk_id] = {}
            doc_ranks[chunk_id][run_idx] = rank

    if not doc_scores:
        return []

    # Sort deterministically: score descending, then chunk_id ascending
    sorted_chunks = sorted(
        doc_scores.keys(),
        key=lambda cid: (-doc_scores[cid], cid),
    )

    fused: list[dict[str, Any]] = []
    for rank_idx, chunk_id in enumerate(sorted_chunks[:top_k], start=1):
        fused.append(
            {
                "rank": rank_idx,
                "chunk_id": chunk_id,
                "score": doc_scores[chunk_id],
                "component_ranks": doc_ranks.get(chunk_id, {}),
            }
        )

    return fused


def fuse_per_query(
    bm25_ranked_lists: Sequence[Sequence[dict[str, Any]]],
    dense_ranked_lists: Sequence[Sequence[dict[str, Any]]],
    k: int = DEFAULT_RRF_K,
    top_k: int = 10,
) -> list[list[dict[str, Any]]]:
    """Fuse parallel query rankings from BM25 and Dense retrievers.

    Parameters
    ----------
    bm25_ranked_lists : Sequence[Sequence[dict[str, Any]]]
        Ranked lists per query from BM25.
    dense_ranked_lists : Sequence[Sequence[dict[str, Any]]]
        Ranked lists per query from dense retriever.
    k : int, default=60
        RRF smoothing constant.
    top_k : int, default=10
        Max items per query ranking.

    Returns
    -------
    list[list[dict[str, Any]]]
        Fused ranked lists per query.
    """
    if len(bm25_ranked_lists) != len(dense_ranked_lists):
        raise ValueError(
            f"Query count mismatch: {len(bm25_ranked_lists)} BM25 rankings vs {len(dense_ranked_lists)} dense rankings"
        )

    fused_all: list[list[dict[str, Any]]] = []
    for bm25_ranked, dense_ranked in zip(bm25_ranked_lists, dense_ranked_lists):
        fused = reciprocal_rank_fusion(
            [bm25_ranked, dense_ranked],
            k=k,
            weights=[1.0, 1.0],
            top_k=top_k,
        )
        fused_all.append(fused)
    return fused_all
