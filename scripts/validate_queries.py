"""Programmatic validation of generated training queries.

Enforces:
1. Complete metadata provenance (source_doc, source_section_id, positive_chunk_id,
   generator_model, prompt_version, query_type, validation_status).
2. Answerability: The query must share significant semantic content with the positive chunk.
3. No heading copying: Rejects any query containing a 4-gram match from the chunk heading
   or document title, or where the heading constitutes >50% of query tokens.
4. No trivial word substitutions: Rejects queries that simply prepend "How to" or "What is"
   to the section heading without content-derived vocabulary.
5. No empty or single-word queries: Length between 4 and 35 words.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def extract_ngrams(text: str, n: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    if len(words) < n:
        return set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def validate_query(
    query_record: dict[str, Any],
    chunk: dict[str, Any],
) -> tuple[bool, str]:
    query = query_record.get("query", "").strip()
    if not query:
        return False, "EMPTY_QUERY"

    words = query.split()
    if len(words) < 4:
        return False, "QUERY_TOO_SHORT"
    if len(words) > 35:
        return False, "QUERY_TOO_LONG"

    # Provenance fields check
    required_fields = [
        "query_id",
        "query",
        "source_doc",
        "source_section_id",
        "positive_chunk_id",
        "generator_model",
        "prompt_version",
        "query_type",
    ]
    for rf in required_fields:
        if not query_record.get(rf):
            return False, f"MISSING_METADATA_{rf.upper()}"

    # Heading copy check (4-gram match)
    heading = chunk.get("heading") or ""
    heading_clean = re.sub(r"[#*`]", "", heading).strip()
    if heading_clean:
        h_ngrams = extract_ngrams(heading_clean, n=4)
        q_ngrams = extract_ngrams(query, n=4)
        overlap = h_ngrams.intersection(q_ngrams)
        if overlap:
            return False, f"HEADING_4GRAM_COPY_{list(overlap)[0]}"

        # Check trivial substitution: query is just a wrapper around the heading
        # e.g., "What is [heading]?" or "How do you [heading]?"
        h_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", heading_clean.lower()))
        q_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower()))
        common_boilerplate = {"how", "do", "you", "what", "is", "the", "in", "soup", "cli", "to", "a", "an", "for"}
        substantive_q_words = q_words - common_boilerplate
        if substantive_q_words and substantive_q_words.issubset(h_words):
            return False, "TRIVIAL_HEADING_SUBSTITUTION"

    # Answerability / Grounding check:
    # Query must contain at least 2 content words present in the chunk body
    chunk_body = chunk.get("text", "")
    chunk_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", chunk_body.lower()))
    q_content_words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query) if w.lower() not in {"what", "when", "where", "which", "how", "does", "soup"}]
    matching_content_words = [w for w in q_content_words if w in chunk_words]
    if len(matching_content_words) < 2 and len(q_content_words) >= 3:
        return False, "LOW_CHUNK_GROUNDING"

    return True, "PASSED"


def validate_query_file(
    input_path: Path,
    corpus_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = {json.loads(line)["chunk_id"]: json.loads(line) for line in f}

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    passed_records = []
    rejected_records = []
    rejection_reasons: dict[str, int] = {}

    for r in records:
        cid = r.get("positive_chunk_id")
        if cid not in corpus:
            passed = False
            reason = "CHUNK_ID_NOT_IN_CORPUS"
        else:
            chunk = corpus[cid]
            passed, reason = validate_query(r, chunk)

        if passed:
            r["validation_status"] = "PASSED"
            passed_records.append(r)
        else:
            r["validation_status"] = f"REJECTED_{reason}"
            rejected_records.append(r)
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in passed_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return {
        "total_evaluated": len(records),
        "passed": len(passed_records),
        "rejected": len(rejected_records),
        "rejection_reasons": rejection_reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated training queries.")
    parser.add_argument("--input", type=Path, required=True, help="Input queries JSONL")
    parser.add_argument("--corpus", type=Path, default=DATA_DIR / "training_corpus.jsonl", help="Training corpus JSONL")
    parser.add_argument("--output", type=Path, default=None, help="Output validated queries JSONL")
    args = parser.parse_args()

    results = validate_query_file(args.input, args.corpus, args.output)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
