"""Mine hard negatives for training triplets using baseline embeddings.

For each training query, finds the highest-similarity non-relevant chunk
from the training documents as a hard negative candidate.

Usage:
    python mine_hard_negatives.py
"""

from __future__ import annotations

import json
import numpy as np
from pathlib import Path

from encoder import SharedEncoder

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def mine_hard_negatives() -> None:
    """Mine hard negatives for training queries using frozen baseline model."""
    corpus_path = DATA_DIR / "corpus.jsonl"
    queries_path = DATA_DIR / "train_query_labels.jsonl"

    if not corpus_path.exists():
        raise FileNotFoundError("Run prepare_corpus.py first")
    if not queries_path.exists():
        raise FileNotFoundError(
            "Create train_query_labels.jsonl first (training queries with "
            "relevant chunk IDs from the 8 training docs)"
        )

    # Load corpus
    chunks = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    # Only use training doc chunks for negatives
    train_chunks = [c for c in chunks if c["split"] == "train"]
    train_ids = [c["chunk_id"] for c in train_chunks]
    train_texts = [f"{c['heading_prefix']}\n\n{c['text']}" for c in train_chunks]

    # Load training queries
    queries = []
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            queries.append(json.loads(line))

    print(f"Mining hard negatives for {len(queries)} queries "
          f"against {len(train_chunks)} training chunks...")

    # Encode everything with frozen baseline
    enc = SharedEncoder()
    chunk_vecs = enc.encode(train_texts)
    query_texts = [q["query"] for q in queries]
    query_vecs = enc.encode(query_texts)

    # For each query, find highest-scoring non-relevant training chunk
    triplets = []
    hard_neg_records = []

    for i, q in enumerate(queries):
        relevant = set(q["relevant_chunk_ids"])
        scores = chunk_vecs @ query_vecs[i]

        # Sort by similarity descending
        ranked_indices = np.argsort(-scores)

        # Find positive text
        positive_text = None
        for cid in q["relevant_chunk_ids"]:
            for c in train_chunks:
                if c["chunk_id"] == cid:
                    positive_text = c["text"]
                    break
            if positive_text:
                break

        if not positive_text:
            print(f"  WARNING: No positive chunk found for {q['query_id']}")
            continue

        # Find hard negative: highest-scoring non-relevant chunk
        hard_neg_id = None
        hard_neg_text = None
        hard_neg_score = None

        for idx in ranked_indices:
            cid = train_ids[idx]
            if cid not in relevant:
                # Also skip chunks from the same section (potential overlap)
                base_section = cid.rsplit("::sub_", 1)[0]
                relevant_bases = {r.rsplit("::sub_", 1)[0] for r in relevant}
                if base_section not in relevant_bases:
                    hard_neg_id = cid
                    hard_neg_text = train_chunks[idx]["text"]
                    hard_neg_score = float(scores[idx])
                    break

        if not hard_neg_text:
            print(f"  WARNING: No valid hard negative for {q['query_id']}")
            continue

        triplets.append({
            "anchor": q["query"],
            "positive": positive_text,
            "negative": hard_neg_text,
        })

        hard_neg_records.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "positive_chunk_id": q["relevant_chunk_ids"][0],
            "negative_chunk_id": hard_neg_id,
            "negative_score": hard_neg_score,
        })

    # Write triplets (SOUP format)
    triplets_path = DATA_DIR / "train_triplets.jsonl"
    with open(triplets_path, "w", encoding="utf-8") as f:
        for t in triplets:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Write hard negative annotations
    hn_path = DATA_DIR / "hard_negatives.jsonl"
    with open(hn_path, "w", encoding="utf-8") as f:
        for r in hard_neg_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nGenerated {len(triplets)} triplets -> {triplets_path}")
    print(f"Hard negative annotations -> {hn_path}")

    # Verify all triplets have non-empty fields
    empty_count = sum(
        1 for t in triplets
        if not t["anchor"].strip() or not t["positive"].strip() or not t["negative"].strip()
    )
    if empty_count:
        print(f"  WARNING: {empty_count} triplets have empty fields!")
    else:
        print("  All triplets have non-empty anchor, positive, and negative fields.")


if __name__ == "__main__":
    mine_hard_negatives()
