"""Mine hard negatives for training triplets using baseline embeddings.

For each training query, finds the highest-similarity non-relevant chunks
from the training documents as hard negative candidates (top-3 per query
with section deduplication). Prepends heading_prefix to both positive and
negative passages so training matches the evaluation text representation.

Usage:
    python mine_hard_negatives.py [--num-negatives 3]
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
from encoder import SharedEncoder

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def format_chunk_text(chunk: dict) -> str:
    """Format chunk text with prepended heading prefix to match evaluation format.

    Args:
        chunk: Dictionary containing 'text', optional 'heading_prefix', and 'doc_name'.

    Returns:
        Formatted string combining prefix and body text separated by double newline.
    """
    prefix = chunk.get("heading_prefix")
    if not prefix or not prefix.strip():
        prefix = chunk.get("doc_name", "")
    prefix = prefix.strip() if prefix else ""
    body = chunk["text"]
    if prefix:
        return f"{prefix}\n\n{body}"
    return body


def get_base_section(chunk_id: str) -> str:
    """Extract base section identifier by stripping sequential sub-chunk suffix.

    Args:
        chunk_id: Unique chunk identifier (e.g., 'doc::sec::sub_000').

    Returns:
        Base section identifier without the sub-split suffix (e.g., 'doc::sec').
    """
    return chunk_id.rsplit("::sub_", 1)[0]


def mine_hard_negatives(
    num_negatives: int = 3,
    corpus_path: Path | None = None,
    queries_path: Path | None = None,
    output_triplets: Path | None = None,
    output_hard_negatives: Path | None = None,
) -> list[dict]:
    """Mine hard negatives for training queries using frozen baseline model.

    Selects top-k scoring non-relevant chunks per query while enforcing section-level
    deduplication to ensure diversity. Streamed query-by-query to avoid large memory
    allocations for cross-similarity matrices.

    Args:
        num_negatives: Number of contrastive negatives to mine per query (default: 3).
        corpus_path: Optional path to corpus JSONL (defaults to data/corpus.jsonl).
        queries_path: Optional path to train queries JSONL (defaults to data/train_query_labels.jsonl).
        output_triplets: Optional path to output triplets JSONL (defaults to data/train_triplets.jsonl).
        output_hard_negatives: Optional path to hard negative annotations JSONL.

    Returns:
        List of generated triplet dictionaries with 'anchor', 'positive', and 'negative' keys.

    Raises:
        FileNotFoundError: If corpus_path or queries_path do not exist.
    """
    corpus_file = corpus_path or (DATA_DIR / "corpus.jsonl")
    queries_file = queries_path or (DATA_DIR / "train_query_labels.jsonl")
    triplets_file = output_triplets or (DATA_DIR / "train_triplets.jsonl")
    hn_file = output_hard_negatives or (DATA_DIR / "hard_negatives.jsonl")

    if not corpus_file.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_file}. Run prepare_corpus.py first")
    if not queries_file.exists():
        raise FileNotFoundError(
            f"Queries file not found: {queries_file}. Create train_query_labels.jsonl first "
            "(training queries with relevant chunk IDs from the 8 training docs)"
        )

    # Load corpus
    chunks = []
    with open(corpus_file, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    # Only use training doc chunks for negatives
    train_chunks = [c for c in chunks if c["split"] == "train"]
    train_ids = [c["chunk_id"] for c in train_chunks]
    train_chunk_map = {c["chunk_id"]: c for c in train_chunks}
    train_texts = [format_chunk_text(c) for c in train_chunks]

    # Load training queries
    queries = []
    with open(queries_file, "r", encoding="utf-8") as f:
        for line in f:
            queries.append(json.loads(line))

    print(f"Mining hard negatives (top-{num_negatives} per query with section deduplication) "
          f"for {len(queries)} queries against {len(train_chunks)} training chunks...")

    # Encode everything with frozen baseline
    enc = SharedEncoder()
    chunk_vecs = enc.encode(train_texts)
    query_texts = [q["query"] for q in queries]
    query_vecs = enc.encode(query_texts)

    # For each query, find top-k highest-scoring non-relevant chunks with section deduplication
    triplets = []
    hard_neg_records = []

    # Stream query similarity computations to avoid large (Q, C) matrix allocation
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*encountered in matmul.*")

        for i, q in enumerate(queries):
            relevant = set(q["relevant_chunk_ids"])
            relevant_bases = {get_base_section(r) for r in relevant}
            # Vector-matrix product (C,) avoids allocating full (Q, C) float32 matrix
            scores = chunk_vecs @ query_vecs[i]

            # Sort candidate indices by similarity descending
            ranked_indices = np.argsort(-scores)

            # Find positive chunk and text (with heading prefix)
            positive_chunk = None
            positive_chunk_id = None
            for cid in q["relevant_chunk_ids"]:
                if cid in train_chunk_map:
                    positive_chunk = train_chunk_map[cid]
                    positive_chunk_id = cid
                    break

            if not positive_chunk:
                print(f"  WARNING: No positive chunk found for {q['query_id']}")
                continue

            positive_text = format_chunk_text(positive_chunk)

            # Find top-N hard negatives with section deduplication
            mined_negatives = []
            seen_sections = set(relevant_bases)

            for idx in ranked_indices:
                cid = train_ids[idx]
                if cid in relevant:
                    continue

                base_section = get_base_section(cid)
                if base_section in seen_sections:
                    continue

                seen_sections.add(base_section)
                mined_negatives.append({
                    "chunk_id": cid,
                    "text": format_chunk_text(train_chunks[idx]),
                    "score": float(scores[idx]),
                })

                if len(mined_negatives) >= num_negatives:
                    break

            if not mined_negatives:
                print(f"  WARNING: No valid hard negatives for {q['query_id']}")
                continue

            for rank, neg in enumerate(mined_negatives, 1):
                triplets.append({
                    "anchor": q["query"],
                    "positive": positive_text,
                    "negative": neg["text"],
                })

                hard_neg_records.append({
                    "query_id": q["query_id"],
                    "query": q["query"],
                    "positive_chunk_id": positive_chunk_id,
                    "negative_chunk_id": neg["chunk_id"],
                    "negative_score": neg["score"],
                    "negative_rank": rank,
                })

    # Ensure parent output directories exist before writing
    triplets_file.parent.mkdir(parents=True, exist_ok=True)
    hn_file.parent.mkdir(parents=True, exist_ok=True)

    # Write triplets (SOUP format)
    with open(triplets_file, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(t, ensure_ascii=False) + "\n" for t in triplets)

    # Write hard negative annotations
    with open(hn_file, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in hard_neg_records)

    print(f"\nGenerated {len(triplets)} triplets -> {triplets_file}")
    print(f"Hard negative annotations -> {hn_file}")

    # Verify all triplets have non-empty fields
    empty_count = sum(
        1 for t in triplets
        if not t["anchor"].strip() or not t["positive"].strip() or not t["negative"].strip()
    )
    if empty_count:
        print(f"  WARNING: {empty_count} triplets have empty fields!")
    else:
        print("  All triplets have non-empty anchor, positive, and negative fields.")

    return triplets


def main() -> None:
    """Parse command line arguments and execute hard negative mining."""
    parser = argparse.ArgumentParser(
        description="Mine hard negatives for training triplets using baseline embeddings."
    )
    parser.add_argument(
        "--num-negatives",
        type=int,
        default=3,
        help="Number of hard negatives to mine per query (default: 3)",
    )
    parser.add_argument(
        "--output-triplets",
        type=Path,
        default=None,
        help="Output path for triplets JSONL (default: data/train_triplets.jsonl)",
    )
    parser.add_argument(
        "--output-hard-negatives",
        type=Path,
        default=None,
        help="Output path for hard negative annotations JSONL (default: data/hard_negatives.jsonl)",
    )
    args = parser.parse_args()
    mine_hard_negatives(
        num_negatives=args.num_negatives,
        output_triplets=args.output_triplets,
        output_hard_negatives=args.output_hard_negatives,
    )


if __name__ == "__main__":
    main()
