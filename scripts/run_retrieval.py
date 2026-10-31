"""Run one retriever over the manual evaluation dataset and write a v2 result.

Usage:
    python scripts/run_retrieval.py --retriever bm25 \
        --output results/v2/bm25.json

Gate: requires a frozen ``data/manual_queries.jsonl`` (owner-approved). This
script refuses to run on any other query file and never touches v1 artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retrieval import classify_failure, compute_metrics, get_base_section  # noqa: E402
from retrievers import build_retriever, retrieve_ranked  # noqa: E402

TOP_K = 10


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def corpus_fingerprint() -> str:
    stats = json.loads((RESULTS_DIR / "corpus_stats.json").read_text(encoding="utf-8"))
    return stats["corpus_fingerprint"]


def query_set_fingerprint(queries_path: Path) -> str:
    return hashlib.sha256(queries_path.read_bytes()).hexdigest()


def run(
    retriever_id: str,
    queries_path: Path,
    corpus_path: Path,
    output_path: Path,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    if not queries_path.exists():
        raise FileNotFoundError(
            f"manual query dataset not found: {queries_path}. "
            "Phase 4 gate: the owner must author and freeze all 54 queries first "
            "(see docs/EVALUATION_V2_COVERAGE.md)."
        )

    chunks = load_jsonl(corpus_path)
    queries = load_jsonl(queries_path)
    chunk_ids = [c["chunk_id"] for c in chunks]

    retriever = build_retriever(retriever_id, repo_root=REPO_ROOT)
    query_texts = [q["query"] for q in queries]

    t0 = time.perf_counter()
    ranked_lists = retrieve_ranked(retriever, chunks, query_texts, top_k=top_k)
    encode_time = time.perf_counter() - t0

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
        per_query_results.append(
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "subset": q.get("subset", "primary"),
                "source_document": q.get("source_document"),
                "relevant_chunk_ids": q["relevant_chunk_ids"],
                "relevant_section_ids": q["relevant_section_ids"],
                "ranked": ranked,
                "failure_category": category,
            }
        )

    computed = compute_metrics(per_query_results)

    result = {
        "retriever_id": retriever_id,
        "retriever_config": retriever.config(),
        "corpus_fingerprint": corpus_fingerprint(),
        "query_set": "manual",
        "query_set_fingerprint": query_set_fingerprint(queries_path),
        "corpus_size": len(chunk_ids),
        "query_count": len(queries),
        "top_k": top_k,
        "encode_time_s": round(encode_time, 3),
        "metrics": computed["metrics"],
        "per_query_results": per_query_results,
        "_per_query_scores": computed["_per_query"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"retriever: {retriever_id}")
    for name, value in sorted(computed["metrics"].items()):
        print(f"  {name}: {value:.4f}")
    print(f"encode_time_s: {result['encode_time_s']}")
    print(f"saved -> {output_path}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one retriever on the manual dataset")
    parser.add_argument(
        "--retriever",
        required=True,
        choices=["mini_lm_frozen", "mini_lm_soup", "bm25", "e5_small"],
    )
    parser.add_argument("--queries", type=Path, default=DATA_DIR / "manual_queries.jsonl")
    parser.add_argument("--corpus", type=Path, default=DATA_DIR / "corpus.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    run(
        retriever_id=args.retriever,
        queries_path=args.queries,
        corpus_path=args.corpus,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
