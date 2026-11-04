#!/usr/bin/env python3
"""Sample C-matched-balanced dataset matching Exp B query type distribution.

Phase 1.6 Experimental Control:
- Target count: 825 queries (matching A-matched, B, C-matched update budget: 1,857 updates).
- Candidate pool: data/train_queries_exp_c_full_v1_5.jsonl (2,257 queries across 31 documents).
- Target distribution (matching Exp B v1.5):
    - how_to: 327
    - conceptual: 309
    - parameter: 184
    - troubleshooting: 5
- Sampling method: Deterministic stratified round-robin across source documents per query type.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

TARGET_DISTRIBUTION = {
    "how_to": 327,
    "conceptual": 309,
    "parameter": 184,
    "troubleshooting": 5,
}
TARGET_TOTAL = 825
SEED = 42


def sample_c_matched_balanced() -> list[dict[str, Any]]:
    c_full_path = DATA_DIR / "train_queries_exp_c_full_v1_5.jsonl"
    with open(c_full_path, "r", encoding="utf-8") as f:
        c_full = [json.loads(line) for line in f]

    print(f"Loaded {len(c_full)} queries from {c_full_path.name}")
    available_types = Counter(q["query_type"] for q in c_full)
    print(f"Available query types in candidate pool: {dict(available_types)}")

    for q_type, target_count in TARGET_DISTRIBUTION.items():
        avail = available_types.get(q_type, 0)
        if avail < target_count:
            raise ValueError(
                f"Cannot satisfy target quota for '{q_type}': target={target_count}, available={avail}"
            )

    sampled: list[dict[str, Any]] = []

    for q_type, target_count in TARGET_DISTRIBUTION.items():
        pool = [q for q in c_full if q["query_type"] == q_type]
        by_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for q in pool:
            by_doc[q["source_doc"]].append(q)

        sorted_docs = sorted(by_doc.keys())
        rng = random.Random(SEED)
        for doc in sorted_docs:
            by_doc[doc].sort(key=lambda x: x["query_id"])
            rng.shuffle(by_doc[doc])

        selected_for_type: list[dict[str, Any]] = []
        idx = 0
        while len(selected_for_type) < target_count:
            doc = sorted_docs[idx % len(sorted_docs)]
            if by_doc[doc]:
                selected_for_type.append(by_doc[doc].pop(0))
            idx += 1

        sampled.extend(selected_for_type)
        print(
            f"Sampled {len(selected_for_type)} queries for type '{q_type}' across {len(sorted_docs)} docs"
        )

    # Sort final sampled queries deterministically by query_id for canonical ordering
    sampled.sort(key=lambda x: x["query_id"])

    # Verification assertions
    assert len(sampled) == TARGET_TOTAL, f"Expected {TARGET_TOTAL}, got {len(sampled)}"
    unique_ids = set(q["query_id"] for q in sampled)
    assert len(unique_ids) == TARGET_TOTAL, "All query_ids must be unique!"

    c_full_ids = {q["query_id"] for q in c_full}
    assert unique_ids.issubset(c_full_ids), "Sampled queries must be a strict subset of C-full v1.5!"

    type_counts = Counter(q["query_type"] for q in sampled)
    assert dict(type_counts) == TARGET_DISTRIBUTION, (
        f"Distribution mismatch: expected {TARGET_DISTRIBUTION}, got {dict(type_counts)}"
    )

    doc_counts = Counter(q["source_doc"] for q in sampled)
    all_c_docs = set(q["source_doc"] for q in c_full)
    assert set(doc_counts.keys()) == all_c_docs, (
        f"Document coverage incomplete: missing {all_c_docs - set(doc_counts.keys())}"
    )

    print(f"Sampling verified: {len(sampled)} queries across {len(doc_counts)} documents.")
    print(f"Distribution: {dict(type_counts)}")

    return sampled


def main() -> None:
    sampled = sample_c_matched_balanced()
    out_path = DATA_DIR / "train_queries_exp_c_matched_balanced_v1_6.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for q in sampled:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {len(sampled)} queries to {out_path}")


if __name__ == "__main__":
    main()
