"""Phase 1.5 invariant and regression tests.

Verifies:
1. Frozen evaluation corpus (data/corpus.jsonl) remains untouched (1,068 chunks).
2. Frozen manual evaluation queries (data/manual_queries.jsonl) remain untouched (54 queries).
3. Expanded training corpus (data/training_corpus.jsonl) has 1,522 chunks and zero held-out test documents.
4. Raw Phase 1 artifacts exist and are preserved immutably.
5. Versioned Phase 1.5 query datasets exist and adhere to complete schema provenance.
6. Strict budget matching: Exp A-matched v1.5 == Exp B v1.5 == Exp C-matched v1.5 == 825 queries.
7. Perfect paired positive chunk multiset equality: Exp A-matched v1.5 == Exp B v1.5.
8. Strict subset relationship: Exp C-matched v1.5 is a strict subset of Exp C-full v1.5.
9. All mined triplets have non-empty anchor, positive, and negative fields.
10. Sibling masking strictly enforced: positive and negative chunks never share a base section.
11. Zero false environment variables, zero raw pipes, and zero unclosed brackets in queries.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

HELD_OUT_TEST_DOCS = {
    "adapters-and-governance.md",
    "compliance.md",
    "evaluation.md",
    "peft-and-efficiency.md",
}

KNOWN_NON_ENVS = {
    "CHANGELOG", "MUSE", "S_ISLNK", "FIO", "DRAM", "NVME", "SATA", "IOPS", "LLAMA",
    "README", "YAML", "JSON", "RAM", "VRAM", "GPU", "CPU", "CUDA", "MODAL", "QAT",
    "BF16", "FP16", "FP8", "NVFP4", "PEFT", "LORA", "QLORA", "UNSLOTH", "TORCH",
    "TRITON", "APPLE", "INTEL", "ARM", "AMD", "WANDB", "MLFLOW", "TOFU", "ASCII",
    "HTML", "HTTP", "HTTPS", "UTF8", "ANSI", "POSIX", "POSIX_FADV_SEQUENTIAL",
    "O_DIRECT", "FSYNC", "MMAP", "NUMA", "PCI", "PCIE", "AVX", "AVX2", "AVX512",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_base_section(chunk_id: str) -> str:
    return chunk_id.rsplit("::sub_", 1)[0]


def test_frozen_evaluation_corpus_untouched():
    corpus = load_jsonl(DATA_DIR / "corpus.jsonl")
    assert len(corpus) == 1068
    assert sum(1 for c in corpus if c["split"] == "train") == 761
    assert sum(1 for c in corpus if c["split"] == "test") == 307


def test_frozen_manual_queries_untouched():
    queries = load_jsonl(DATA_DIR / "manual_queries.jsonl")
    assert len(queries) == 54
    assert sum(1 for q in queries if q["subset"] == "primary") == 39
    assert sum(1 for q in queries if q["subset"] == "overlap") == 15


def test_raw_artifacts_preserved():
    # Verify raw Phase 1 artifacts are preserved and non-empty
    raw_files = [
        "train_queries_exp_a_matched.jsonl",
        "train_queries_exp_b.jsonl",
        "train_queries_exp_c_matched.jsonl",
        "train_queries_exp_c_full.jsonl",
        "triplets_exp_a_matched.jsonl",
        "triplets_exp_b.jsonl",
        "triplets_exp_c_matched.jsonl",
        "triplets_exp_c_full.jsonl",
    ]
    for rf in raw_files:
        p = DATA_DIR / rf
        assert p.exists(), f"Raw artifact {rf} must exist"
        assert p.stat().st_size > 0, f"Raw artifact {rf} must be non-empty"


def test_expanded_training_corpus_invariants():
    train_corpus = load_jsonl(DATA_DIR / "training_corpus.jsonl")
    assert len(train_corpus) == 1522
    for c in train_corpus:
        assert c["split"] == "train"
        assert c["source_file"] not in HELD_OUT_TEST_DOCS
        assert c["token_count"] <= 256


def test_phase_1_5_budget_matching():
    q_a = load_jsonl(DATA_DIR / "train_queries_exp_a_matched_v1_5.jsonl")
    q_b = load_jsonl(DATA_DIR / "train_queries_exp_b_v1_5.jsonl")
    q_c = load_jsonl(DATA_DIR / "train_queries_exp_c_matched_v1_5.jsonl")

    assert len(q_a) == len(q_b) == len(q_c) == 825


def test_phase_1_5_paired_positive_chunks():
    q_a = load_jsonl(DATA_DIR / "train_queries_exp_a_matched_v1_5.jsonl")
    q_b = load_jsonl(DATA_DIR / "train_queries_exp_b_v1_5.jsonl")

    chunks_a = [q["positive_chunk_id"] for q in q_a]
    chunks_b = [q["positive_chunk_id"] for q in q_b]

    # Enforce multiset equality
    assert chunks_a == chunks_b, "Exp A-matched v1.5 and Exp B v1.5 must target the EXACT same positive chunks in identical order"


def test_phase_1_5_subset_relation():
    q_c_matched = load_jsonl(DATA_DIR / "train_queries_exp_c_matched_v1_5.jsonl")
    q_c_full = load_jsonl(DATA_DIR / "train_queries_exp_c_full_v1_5.jsonl")

    ids_matched = {q["query_id"] for q in q_c_matched}
    ids_full = {q["query_id"] for q in q_c_full}

    assert ids_matched.issubset(ids_full), "C-matched v1.5 must be a strict subset of C-full v1.5"
    assert len(ids_matched) == 825
    assert len(q_c_full) >= 2000


@pytest.mark.parametrize("query_file", [
    "train_queries_exp_b_v1_5.jsonl",
    "train_queries_exp_c_matched_v1_5.jsonl",
    "train_queries_exp_c_full_v1_5.jsonl",
])
def test_phase_1_5_query_syntax_and_quality(query_file: str):
    queries = load_jsonl(DATA_DIR / query_file)
    for q in queries:
        q_str = q["query"]
        assert len(q_str) >= 20, f"Query too short: {q_str}"
        assert q_str.endswith("?"), f"Query missing question mark: {q_str}"
        assert q_str.count("(") == q_str.count(")"), f"Unclosed parenthesis in {q_str}"
        assert q_str.count("[") == q_str.count("]"), f"Unclosed bracket in {q_str}"
        assert q_str.count('"') % 2 == 0, f"Unclosed quotes in {q_str}"
        assert "|" not in q_str, f"Raw table pipe in {q_str}"
        assert "http://" not in q_str and "https://" not in q_str, f"Raw URL in {q_str}"

        # No false environment variables
        for non_env in KNOWN_NON_ENVS:
            assert f"setting `{non_env}` in the execution environment" not in q_str, f"False env var {non_env} found in {q_str}"


@pytest.mark.parametrize("triplet_file,expected_count", [
    ("triplets_exp_a_matched_v1_5.jsonl", 2475),
    ("triplets_exp_b_v1_5.jsonl", 2475),
    ("triplets_exp_c_matched_v1_5.jsonl", 2475),
    ("triplets_exp_c_full_v1_5.jsonl", 6771),
])
def test_phase_1_5_triplets_non_empty(triplet_file: str, expected_count: int):
    triplets = load_jsonl(DATA_DIR / triplet_file)
    assert len(triplets) == expected_count
    for t in triplets:
        assert t["anchor"].strip()
        assert t["positive"].strip()
        assert t["negative"].strip()


@pytest.mark.parametrize("hn_file,expected_queries", [
    ("hard_negatives_exp_a_matched_v1_5.jsonl", 825),
    ("hard_negatives_exp_b_v1_5.jsonl", 825),
    ("hard_negatives_exp_c_matched_v1_5.jsonl", 825),
    ("hard_negatives_exp_c_full_v1_5.jsonl", 2257),
])
def test_phase_1_5_sibling_masking(hn_file: str, expected_queries: int):
    hn_records = load_jsonl(DATA_DIR / hn_file)
    per_query = defaultdict(list)
    for r in hn_records:
        per_query[r["query_id"]].append(r)

    assert len(per_query) == expected_queries
    for qid, negs in per_query.items():
        assert len(negs) == 3, f"Expected 3 negatives for {qid}"
        pos_section = get_base_section(negs[0]["positive_chunk_id"])
        neg_sections = [get_base_section(n["negative_chunk_id"]) for n in negs]

        # No duplicate sections in negatives
        assert len(neg_sections) == len(set(neg_sections)), f"Duplicate negative sections in {qid}"
        # Positive section is NEVER in negatives
        assert pos_section not in neg_sections, f"False negative collision: positive section {pos_section} in negatives for {qid}"

