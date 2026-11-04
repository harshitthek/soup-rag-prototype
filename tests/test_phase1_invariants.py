"""Phase 1 dataset invariant tests.

Verifies:
1. Frozen evaluation corpus (data/corpus.jsonl) remains untouched (1,068 chunks).
2. Frozen manual evaluation queries (data/manual_queries.jsonl) remain untouched (54 queries).
3. Expanded training corpus (data/training_corpus.jsonl) has exactly 1,522 chunks and zero held-out documents.
4. Experiment B and Experiment C-matched have identical query counts and triplet counts.
5. All mined triplets have non-empty anchor, positive, and negative fields.
6. Section-level sibling masking safeguard is strictly enforced: positive and negative chunks never share a base section.
"""

from __future__ import annotations

import json
from collections import defaultdict
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


def test_expanded_training_corpus():
    train_corpus = load_jsonl(DATA_DIR / "training_corpus.jsonl")
    assert len(train_corpus) == 1522
    for c in train_corpus:
        assert c["split"] == "train"
        assert c["source_file"] not in HELD_OUT_TEST_DOCS
        assert c["token_count"] <= 256


def test_budget_matching():
    q_a_matched = load_jsonl(DATA_DIR / "train_queries_exp_a_matched.jsonl")
    q_b = load_jsonl(DATA_DIR / "train_queries_exp_b.jsonl")
    q_c_matched = load_jsonl(DATA_DIR / "train_queries_exp_c_matched.jsonl")
    t_a_matched = load_jsonl(DATA_DIR / "triplets_exp_a_matched.jsonl")
    t_b = load_jsonl(DATA_DIR / "triplets_exp_b.jsonl")
    t_c_matched = load_jsonl(DATA_DIR / "triplets_exp_c_matched.jsonl")

    assert len(q_a_matched) == len(q_b) == len(q_c_matched) == 825
    assert len(t_a_matched) == len(t_b) == len(t_c_matched) == 2475


def test_experiment_c_full_counts():
    q_c_full = load_jsonl(DATA_DIR / "train_queries_exp_c_full.jsonl")
    t_c_full = load_jsonl(DATA_DIR / "triplets_exp_c_full.jsonl")

    assert len(q_c_full) == 1883
    assert len(t_c_full) == 5649


@pytest.mark.parametrize("triplet_file", [
    "triplets_exp_a_matched.jsonl",
    "triplets_exp_b.jsonl",
    "triplets_exp_c_matched.jsonl",
    "triplets_exp_c_full.jsonl",
])
def test_triplet_non_empty(triplet_file: str):
    triplets = load_jsonl(DATA_DIR / triplet_file)
    for t in triplets:
        assert t["anchor"].strip()
        assert t["positive"].strip()
        assert t["negative"].strip()


@pytest.mark.parametrize("hn_file", [
    "hard_negatives_exp_a_matched.jsonl",
    "hard_negatives_exp_b.jsonl",
    "hard_negatives_exp_c_matched.jsonl",
    "hard_negatives_exp_c_full.jsonl",
])
def test_section_sibling_masking_enforced(hn_file: str):
    hn_records = load_jsonl(DATA_DIR / hn_file)
    per_query = defaultdict(list)
    for r in hn_records:
        per_query[r["query_id"]].append(r)

    for qid, negs in per_query.items():
        assert len(negs) == 3, f"Expected 3 negatives for {qid}"
        pos_section = get_base_section(negs[0]["positive_chunk_id"])
        neg_sections = [get_base_section(n["negative_chunk_id"]) for n in negs]

        # Enforce no duplicates among negative sections
        assert len(neg_sections) == len(set(neg_sections)), f"Duplicate negative sections in {qid}"
        # Enforce that positive section is NEVER mined as negative
        assert pos_section not in neg_sections, f"False negative collision: positive section {pos_section} in negatives for {qid}"
