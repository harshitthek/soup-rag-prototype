"""Shared retrieval evaluation primitives for Evaluation v2.

Pure-Python (stdlib-only) ranking, section mapping, multi-label metrics, and
the mutually exclusive failure classifier. Used by all four retrievers so the
metric implementation exists exactly once.

The ranking semantics (descending score, lexicographic ``chunk_id``
tie-break) are intentionally identical to the v1 implementation in
``scripts/evaluate_retrieval.py:dense_retrieve``; v1 scripts are preserved
unchanged and this module is additive.
"""

from __future__ import annotations

from typing import Any, Sequence

FAILURE_CATEGORIES = (
    "empty_ranking",
    "exact_relevant_chunk_top1",
    "relevant_section_unlabeled_chunk_top1",
    "relevant_chunk_below_top1",
    "relevant_section_below_top1",
    "wrong_section_same_document",
    "wrong_document",
)

# wrong_section_same_document + wrong_document both imply nothing relevant in
# the top 10; the owner-requested aggregate row is computed from them.
NO_RELEVANT_RESULT_LEAVES = ("wrong_section_same_document", "wrong_document")


def get_base_section(chunk_id: str) -> str:
    """Strip the sequential sub-chunk suffix to get the canonical section id."""
    return chunk_id.rsplit("::sub_", 1)[0]


def chunk_doc_name(chunk_id: str) -> str:
    return chunk_id.split("::", 1)[0]


def rank_corpus(
    scores: Sequence[float],
    chunk_ids: Sequence[str],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Rank chunks by score descending with deterministic tie-breaking.

    Returns ``[{"rank": 1-based, "chunk_id": str, "score": float}, ...]``.
    Identical ordering rule to v1 ``dense_retrieve``.
    """
    indices = list(range(len(chunk_ids)))
    indices.sort(key=lambda i: (-float(scores[i]), chunk_ids[i]))
    return [
        {
            "rank": rank,
            "chunk_id": chunk_ids[idx],
            "score": float(scores[idx]),
        }
        for rank, idx in enumerate(indices[:top_k], start=1)
    ]


def section_ranking(ranked: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse ranked chunks into unique canonical sections.

    Preserves the first occurrence of each section; the rank of a section is
    its position in the deduplicated sequence (1-based).
    """
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in ranked:
        section_id = entry.get("section_id") or get_base_section(entry["chunk_id"])
        if section_id in seen:
            continue
        seen.add(section_id)
        unique.append(
            {
                "rank": len(unique) + 1,
                "section_id": section_id,
                "chunk_id": entry["chunk_id"],
                "score": entry.get("score"),
            }
        )
    return unique


def _hit(rel: set[str], retrieved: Sequence[str]) -> float:
    return 1.0 if set(retrieved) & rel else 0.0


def _recall(rel: set[str], retrieved: Sequence[str]) -> float:
    if not rel:
        raise ValueError("relevant set must be non-empty")
    return len(set(retrieved) & rel) / len(rel)


def _first_rank(rel: set[str], retrieved: Sequence[str]) -> int | None:
    for idx, item in enumerate(retrieved, start=1):
        if item in rel:
            return idx
    return None


def compute_query_metrics(
    query_result: dict[str, Any],
    top_k_values: tuple[int, ...] = (1, 3, 5),
    mrr_cutoff: int = 10,
) -> dict[str, dict[str, float]]:
    """Chunk- and section-level hit/recall/mrr for one query.

    ``query_result``: {"ranked": [...], "relevant_chunk_ids": [...],
    "relevant_section_ids": [...]}. ``ranked`` entries need only ``chunk_id``.
    Returns {"chunk": {...}, "section": {...}} with float scores.
    """
    ranked = query_result["ranked"]
    rel_chunks = set(query_result["relevant_chunk_ids"])
    rel_sections = set(query_result["relevant_section_ids"])
    if not rel_chunks or not rel_sections:
        raise ValueError("relevant_chunk_ids and relevant_section_ids must be non-empty")

    chunk_ids = [r["chunk_id"] for r in ranked]
    sec_ranked = section_ranking(ranked)
    sec_ids = [s["section_id"] for s in sec_ranked]

    chunk_scores: dict[str, float] = {}
    for k in top_k_values:
        top = chunk_ids[:k]
        chunk_scores[f"hit@{k}"] = _hit(rel_chunks, top)
        chunk_scores[f"recall@{k}"] = _recall(rel_chunks, top)

    chunk_rank = _first_rank(rel_chunks, chunk_ids[:mrr_cutoff])
    chunk_scores[f"mrr@{mrr_cutoff}"] = 1.0 / chunk_rank if chunk_rank else 0.0

    section_scores: dict[str, float] = {}
    for k in top_k_values:
        top = sec_ids[:k]
        section_scores[f"sec_hit@{k}"] = _hit(rel_sections, top)
        section_scores[f"sec_recall@{k}"] = _recall(rel_sections, top)

    section_rank = _first_rank(rel_sections, sec_ids[:mrr_cutoff])
    section_scores[f"sec_mrr@{mrr_cutoff}"] = 1.0 / section_rank if section_rank else 0.0

    return {"chunk": chunk_scores, "section": section_scores}


def compute_metrics(
    query_results: Sequence[dict[str, Any]],
    top_k_values: tuple[int, ...] = (1, 3, 5),
    mrr_cutoff: int = 10,
) -> dict[str, Any]:
    """Aggregate chunk/section metrics over queries (micro-average).

    Returns {"metrics": {name: mean}, "_per_query": {name: [per-query scores]}}.
    """
    per_query: dict[str, list[float]] = {}
    for qr in query_results:
        scores = compute_query_metrics(qr, top_k_values, mrr_cutoff)
        for level in ("chunk", "section"):
            for name, value in scores[level].items():
                per_query.setdefault(name, []).append(value)

    metrics = {name: sum(vals) / len(vals) for name, vals in per_query.items()}
    return {"metrics": metrics, "_per_query": per_query}


def classify_failure(
    ranked: Sequence[dict[str, Any]],
    relevant_chunk_ids: Sequence[str],
    relevant_section_ids: Sequence[str],
    source_document: str | None = None,
) -> str:
    """Mutually exclusive, deterministic failure classification.

    Decision order (first match wins):

    1. empty ranking                              -> empty_ranking
    2. top-1 is a labeled relevant chunk          -> exact_relevant_chunk_top1
    3. top-1 is an unlabeled chunk whose section
       is relevant                                -> relevant_section_unlabeled_chunk_top1
    4. a labeled chunk in ranks 2..10            -> relevant_chunk_below_top1
    5. no labeled chunk in top-10, but a chunk
       of a relevant section is in top-10        -> relevant_section_below_top1
    6. top-1 is in the query's source document   -> wrong_section_same_document
    7. otherwise                                 -> wrong_document

    Leaves 6 and 7 imply nothing relevant in the top 10; aggregate them as
    ``no_relevant_result_top10`` (NO_RELEVANT_RESULT_LEAVES).
    """
    top10 = list(ranked[:10])
    if not top10:
        return "empty_ranking"

    rel_chunks = set(relevant_chunk_ids)
    rel_sections = set(relevant_section_ids)

    first = top10[0]
    first_chunk_id = first["chunk_id"]
    if first_chunk_id in rel_chunks:
        return "exact_relevant_chunk_top1"

    first_section = first.get("section_id") or get_base_section(first_chunk_id)
    if first_section in rel_sections:
        return "relevant_section_unlabeled_chunk_top1"

    for entry in top10[1:]:
        if entry["chunk_id"] in rel_chunks:
            return "relevant_chunk_below_top1"

    for entry in top10:
        section = entry.get("section_id") or get_base_section(entry["chunk_id"])
        if section in rel_sections:
            return "relevant_section_below_top1"

    if source_document is not None and chunk_doc_name(first_chunk_id) == source_document:
        return "wrong_section_same_document"
    return "wrong_document"
