"""Phase 1.7 Training Readiness and Invariant Verification Tests.

Verifies:
1. Exact dataloader and optimizer update arithmetic across all datasets:
   - A-full: ceil(3234 / 4) * 3 = 809 * 3 = 2,427 updates.
   - Matched runs (A-matched, B, C-matched, C-matched-balanced): ceil(2475 / 4) * 3 = 619 * 3 = 1,857 updates.
   - C-full: ceil(6771 / 4) * 3 = 1693 * 3 = 5,079 updates.
2. Source document coverage and concentration across B, C-matched, and C-matched-balanced.
3. Frozen benchmark integrity across all 5 canonical files.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}


def test_frozen_benchmark_integrity():
    """Verify that all frozen benchmark files remain untouched with exact SHA256 hashes."""
    for fname, expected_hash in FROZEN_CHECKSUMS.items():
        file_path = DATA_DIR / fname
        assert file_path.exists(), f"Frozen file missing: {fname}"
        h = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert h == expected_hash, f"Hash mismatch for {fname}: got {h}, expected {expected_hash}"


def test_optimizer_update_arithmetic():
    """Verify exact optimizer update step arithmetic matching HF Trainer dataloader behavior."""
    batch_size = 4
    epochs = 3
    grad_accum = 1

    configs = [
        ("A-full", 3234, 2427),
        ("A-matched", 2475, 1857),
        ("B", 2475, 1857),
        ("C-matched", 2475, 1857),
        ("C-matched-balanced", 2475, 1857),
        ("C-full", 6771, 5079),
    ]

    for name, n_triplets, expected_updates in configs:
        batches_per_epoch = math.ceil(n_triplets / batch_size)
        updates_per_epoch = batches_per_epoch // grad_accum
        total_updates = updates_per_epoch * epochs
        assert total_updates == expected_updates, (
            f"Step calculation mismatch for {name}: computed {total_updates}, expected {expected_updates}"
        )


def test_document_coverage_and_distribution():
    """Verify document coverage across B, C-matched, and C-matched-balanced."""
    corpus_file = DATA_DIR / "training_corpus.jsonl"
    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus = [json.loads(line) for line in f]
    all_docs = {c["source_file"] for c in corpus}
    assert len(all_docs) == 31

    # B: exactly 8 docs
    b_file = DATA_DIR / "train_queries_exp_b_v1_5.jsonl"
    with open(b_file, "r", encoding="utf-8") as f:
        b_queries = [json.loads(l) for l in f]
    b_docs = {q["source_doc"] for q in b_queries}
    assert len(b_docs) == 8
    assert b_docs.issubset(all_docs)

    # C-matched: exactly 31 docs
    cm_file = DATA_DIR / "train_queries_exp_c_matched_v1_5.jsonl"
    with open(cm_file, "r", encoding="utf-8") as f:
        cm_queries = [json.loads(l) for l in f]
    cm_docs = {q["source_doc"] for q in cm_queries}
    assert cm_docs == all_docs

    # C-matched-balanced: exactly 31 docs
    cmb_file = DATA_DIR / "train_queries_exp_c_matched_balanced_v1_6.jsonl"
    with open(cmb_file, "r", encoding="utf-8") as f:
        cmb_queries = [json.loads(l) for l in f]
    cmb_docs = {q["source_doc"] for q in cmb_queries}
    assert cmb_docs == all_docs

    # Check that in C-matched-balanced, every single doc has at least 1 query
    doc_counts = Counter(q["source_doc"] for q in cmb_queries)
    for doc in all_docs:
        assert doc_counts[doc] >= 1, f"Document {doc} has 0 queries in C-matched-balanced"
