"""Generate training and evaluation queries from the corpus.

Creates two datasets:
  - train_query_labels.jsonl: queries from the 8 training docs
  - eval_queries.jsonl: queries from the 4 held-out test docs

Uses template-based question generation from chunk headings and content.
No LLM required — fully deterministic and reproducible.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

# Question templates keyed by pattern matches in headings/content
QUESTION_TEMPLATES = [
    # "What" questions
    ("what_is", "What is {topic}?"),
    ("what_does", "What does {topic} do?"),
    ("how_to", "How do you {topic}?"),
    ("how_does", "How does {topic} work?"),
    ("when_to", "When should you use {topic}?"),
    ("explain", "Explain {topic} in Soup CLI."),
    ("describe", "Describe the {topic} feature."),
    ("configure", "How do you configure {topic}?"),
    ("difference", "What is the role of {topic}?"),
    ("purpose", "What is the purpose of {topic}?"),
]


def _clean_heading(heading: str | None) -> str | None:
    """Clean heading text for use in questions."""
    if not heading:
        return None
    # Remove markdown formatting
    h = re.sub(r"`([^`]+)`", r"\1", heading)
    h = re.sub(r"\*\*([^*]+)\*\*", r"\1", h)
    h = re.sub(r"\*([^*]+)\*", r"\1", h)
    return h.strip()


def _extract_key_terms(text: str) -> list[str]:
    """Extract key technical terms from chunk text."""
    terms = set()
    # Find backtick-enclosed terms
    for m in re.finditer(r"`([^`]{2,40})`", text):
        terms.add(m.group(1))
    # Find --flag patterns
    for m in re.finditer(r"(--[\w-]+)", text):
        terms.add(m.group(1))
    # Find soup commands
    for m in re.finditer(r"(soup\s+\w+(?:\s+\w+)?)", text):
        terms.add(m.group(1))
    return sorted(terms)[:5]  # Cap at 5 terms


def _generate_questions_for_chunk(chunk: dict[str, Any]) -> list[dict[str, str]]:
    """Generate 1-3 questions for a given chunk."""
    heading = _clean_heading(chunk.get("heading"))
    text = chunk["text"]
    chunk_id = chunk["chunk_id"]
    doc_name = chunk["doc_name"]

    if not text.strip() or len(text.strip()) < 30:
        return []

    questions = []

    # Strategy 1: Heading-based question
    if heading and len(heading) > 3:
        topic = heading.lower()

        # Pick template based on content patterns
        if any(w in text.lower() for w in ["configure", "config", "yaml", "set"]):
            q = f"How do you configure {topic} in Soup?"
        elif any(w in text.lower() for w in ["command", "cli", "run", "execute"]):
            q = f"How do you use {topic} in Soup CLI?"
        elif any(w in text.lower() for w in ["error", "fail", "issue", "problem"]):
            q = f"What happens when {topic} fails?"
        elif any(w in text.lower() for w in ["support", "compatible", "backend"]):
            q = f"What backends or options does {topic} support?"
        else:
            q = f"What is {topic} and how does it work in Soup?"

        questions.append({
            "query_id": f"{doc_name}_h_{hashlib.md5(q.encode()).hexdigest()[:8]}",
            "query": q,
            "relevant_chunk_ids": [chunk_id],
            "source": "heading",
        })

    # Strategy 2: Key-term based question
    key_terms = _extract_key_terms(text)
    if key_terms and heading:
        term = key_terms[0]
        q = f"What does {term} do in the context of {heading.lower() if heading else doc_name}?"
        qid = f"{doc_name}_t_{hashlib.md5(q.encode()).hexdigest()[:8]}"

        # Avoid duplicate question IDs
        if not any(existing["query_id"] == qid for existing in questions):
            questions.append({
                "query_id": qid,
                "query": q,
                "relevant_chunk_ids": [chunk_id],
                "source": "key_term",
            })

    # Strategy 3: Content-pattern based question
    # Look for definitions, lists, or explanations
    if re.search(r"(?:is|are|refers to|means|defines)\s", text[:200]):
        first_sentence = re.split(r"[.!?]\s", text[:300])[0]
        if 10 < len(first_sentence) < 150 and heading:
            q = f"How does Soup define or handle {heading.lower()}?"
            qid = f"{doc_name}_d_{hashlib.md5(q.encode()).hexdigest()[:8]}"
            if not any(existing["query_id"] == qid for existing in questions):
                questions.append({
                    "query_id": qid,
                    "query": q,
                    "relevant_chunk_ids": [chunk_id],
                    "source": "definition",
                })

    return questions[:2]  # Cap at 2 questions per chunk


def generate_queries() -> None:
    """Generate training and evaluation query datasets."""
    corpus_path = DATA_DIR / "corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError("Run prepare_corpus.py first")

    chunks = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    train_queries: list[dict] = []
    eval_queries: list[dict] = []

    for chunk in chunks:
        questions = _generate_questions_for_chunk(chunk)
        for q in questions:
            if chunk["split"] == "train":
                train_queries.append(q)
            else:
                eval_queries.append(q)

    # Deduplicate by query text (keep first occurrence)
    seen_train: set[str] = set()
    deduped_train: list[dict] = []
    for q in train_queries:
        if q["query"] not in seen_train:
            seen_train.add(q["query"])
            deduped_train.append(q)
    train_queries = deduped_train

    seen_eval: set[str] = set()
    deduped_eval: list[dict] = []
    for q in eval_queries:
        if q["query"] not in seen_eval:
            seen_eval.add(q["query"])
            deduped_eval.append(q)
    eval_queries = deduped_eval

    # Write training queries
    train_path = DATA_DIR / "train_query_labels.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for q in train_queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Write evaluation queries
    eval_path = DATA_DIR / "eval_queries.jsonl"
    with open(eval_path, "w", encoding="utf-8") as f:
        for q in eval_queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Stats
    train_docs = set()
    for q in train_queries:
        for cid in q["relevant_chunk_ids"]:
            train_docs.add(cid.split("::")[0])

    eval_docs = set()
    for q in eval_queries:
        for cid in q["relevant_chunk_ids"]:
            eval_docs.add(cid.split("::")[0])

    print(f"Training queries: {len(train_queries)} -> {train_path}")
    print(f"  From docs: {sorted(train_docs)}")
    print(f"Evaluation queries: {len(eval_queries)} -> {eval_path}")
    print(f"  From docs: {sorted(eval_docs)}")

    # Show sample queries
    print("\nSample training queries:")
    for q in train_queries[:5]:
        print(f"  [{q['query_id']}] {q['query']}")
        print(f"    -> {q['relevant_chunk_ids']}")

    print("\nSample evaluation queries:")
    for q in eval_queries[:5]:
        print(f"  [{q['query_id']}] {q['query']}")
        print(f"    -> {q['relevant_chunk_ids']}")


if __name__ == "__main__":
    generate_queries()
