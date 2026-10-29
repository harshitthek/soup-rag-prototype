"""Evaluate dense retrieval quality on the held-out test queries.

Usage:
    # Baseline (frozen MiniLM):
    python evaluate_retrieval.py --output ../results/baseline.json

    # Candidate (fine-tuned adapter):
    python evaluate_retrieval.py --adapter-dir ../output_embedding --output ../results/candidate.json
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path
import numpy as np

# Filter benign NumPy 2.x BLAS warning on Apple Silicon Accelerate
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*encountered in matmul.*")

from encoder import SharedEncoder

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def load_corpus(path: Path) -> list[dict]:
    """Load corpus JSONL."""
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def load_queries(path: Path) -> list[dict]:
    """Load evaluation queries JSONL."""
    queries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            queries.append(json.loads(line))
    return queries


def build_embed_texts(chunks: list[dict]) -> list[str]:
    """Build the text to embed for each chunk (heading prefix + body)."""
    texts = []
    for c in chunks:
        prefix = c.get("heading_prefix", c.get("doc_name", ""))
        body = c["text"]
        texts.append(f"{prefix}\n\n{body}")
    return texts


def dense_retrieve(
    query_vec: np.ndarray,
    corpus_vecs: np.ndarray,
    chunk_ids: list[str],
    top_k: int = 10,
) -> list[dict]:
    """Rank corpus chunks by cosine similarity for a single query vector.

    Calculates the exact dot product between the L2-normalized query vector and
    corpus matrix. Applies deterministic tie-breaking on chunk_id (lexicographic).

    Args:
        query_vec: L2-normalized query embedding vector of shape (D,).
        corpus_vecs: Matrix of L2-normalized passage embeddings of shape (N, D).
        chunk_ids: List of unique chunk IDs corresponding to corpus_vecs rows.
        top_k: Maximum number of ranked chunks to return (default: 10).

    Returns:
        List of dictionaries with 'rank', 'chunk_id', and 'score' keys.
    """
    scores = corpus_vecs @ query_vec  # (N,)

    # Stable sort: negate scores for descending, then break ties on chunk_id
    indices = list(range(len(chunk_ids)))
    indices.sort(key=lambda i: (-scores[i], chunk_ids[i]))

    results = []
    for rank, idx in enumerate(indices[:top_k], start=1):
        results.append(
            {
                "rank": rank,
                "chunk_id": chunk_ids[idx],
                "score": float(scores[idx]),
            }
        )
    return results


def compute_metrics(
    query_results: list[dict],
    top_k_values: tuple[int, ...] = (1, 3, 5),
    mrr_cutoff: int = 10,
) -> dict:
    """Compute Recall@k and MRR@cutoff from per-query ranked results.

    Args:
        query_results: List of query result dicts containing 'ranked' and 'relevant_chunk_ids'.
        top_k_values: Tuple of k cutoffs for Recall calculation (default: 1, 3, 5).
        mrr_cutoff: Maximum rank cutoff for reciprocal rank computation (default: 10).

    Returns:
        Dictionary containing aggregate recall and MRR metrics along with raw per-query scores.
    """
    recalls = {k: [] for k in top_k_values}
    mrr_scores = []

    for qr in query_results:
        relevant = set(qr["relevant_chunk_ids"])
        retrieved_ids = [r["chunk_id"] for r in qr["ranked"]]

        # Recall@k: is any relevant chunk in top-k?
        for k in top_k_values:
            top_k_ids = set(retrieved_ids[:k])
            hit = 1.0 if top_k_ids & relevant else 0.0
            recalls[k].append(hit)

        # MRR@cutoff
        rr = 0.0
        for rank_idx, rid in enumerate(retrieved_ids[:mrr_cutoff], start=1):
            if rid in relevant:
                rr = 1.0 / rank_idx
                break
        mrr_scores.append(rr)

    metrics = {}
    for k in top_k_values:
        metrics[f"recall@{k}"] = float(np.mean(recalls[k]))
    metrics[f"mrr@{mrr_cutoff}"] = float(np.mean(mrr_scores))

    # Per-query scores for bootstrap
    metrics["_per_query"] = {
        "recall": {k: recalls[k] for k in top_k_values},
        "mrr": mrr_scores,
    }

    return metrics


def evaluate(
    adapter_dir: str | None = None,
    output_path: str | None = None,
) -> dict:
    """Run the dense retrieval evaluation pipeline against the held-out test suite.

    Loads the corpus chunks and evaluation queries, encodes passages using either the
    baseline base model or fine-tuned LoRA adapter, performs dense retrieval, computes
    ranking metrics (Recall@1/3/5, MRR@10), and optionally saves JSON output.

    Args:
        adapter_dir: Optional path to directory containing fine-tuned PEFT LoRA adapter.
        output_path: Optional path to write evaluated results JSON.

    Returns:
        Dictionary with mode, metrics, encode timings, and per-query predictions.

    Raises:
        FileNotFoundError: If corpus.jsonl or eval_queries.jsonl are missing.
    """
    corpus_path = DATA_DIR / "corpus.jsonl"
    queries_path = DATA_DIR / "eval_queries.jsonl"

    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Corpus not found at {corpus_path}. Run prepare_corpus.py first."
        )
    if not queries_path.exists():
        raise FileNotFoundError(
            f"Eval queries not found at {queries_path}. Create them first."
        )

    print(f"Loading corpus from {corpus_path}...")
    chunks = load_corpus(corpus_path)
    chunk_ids = [c["chunk_id"] for c in chunks]
    embed_texts = build_embed_texts(chunks)

    print(f"Loading queries from {queries_path}...")
    queries = load_queries(queries_path)

    mode = "candidate" if adapter_dir else "baseline"
    print(f"Encoding {len(chunks)} chunks in {mode} mode...")

    t0 = time.perf_counter()
    enc = SharedEncoder(adapter_dir=adapter_dir)
    corpus_vecs = enc.encode(embed_texts)
    encode_time = time.perf_counter() - t0
    print(f"  Encoded {len(chunks)} chunks in {encode_time:.2f}s")
    print(f"  Vector shape: {corpus_vecs.shape}")

    # Encode and rank queries
    query_texts = [q["query"] for q in queries]
    query_vecs = enc.encode(query_texts)

    query_results = []
    for i, q in enumerate(queries):
        ranked = dense_retrieve(query_vecs[i], corpus_vecs, chunk_ids, top_k=10)
        query_results.append(
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "relevant_chunk_ids": q["relevant_chunk_ids"],
                "ranked": ranked,
            }
        )

    metrics = compute_metrics(query_results)

    result = {
        "mode": mode,
        "adapter_dir": str(adapter_dir) if adapter_dir else None,
        "model_id": enc.tokenizer.name_or_path,
        "has_adapter": enc.has_adapter,
        "corpus_size": len(chunks),
        "query_count": len(queries),
        "encode_time_s": round(encode_time, 3),
        "metrics": {k: v for k, v in metrics.items() if not k.startswith("_")},
        "per_query_results": query_results,
        "_per_query_scores": metrics["_per_query"],
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {out}")

    print(f"\n{'='*50}")
    print(f"  Mode: {mode}")
    for k, v in result["metrics"].items():
        print(f"  {k}: {v:.4f}")
    print(f"{'='*50}")

    return result


def main() -> None:
    """Parse CLI options and execute retrieval evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate dense retrieval")
    parser.add_argument(
        "--adapter-dir",
        default=None,
        help="Path to SOUP-trained LoRA adapter (omit for baseline)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path",
    )
    args = parser.parse_args()
    evaluate(adapter_dir=args.adapter_dir, output_path=args.output)


if __name__ == "__main__":
    main()
