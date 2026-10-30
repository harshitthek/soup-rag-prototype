"""v1 dataset invariant checks (stdlib-only, no v1 code modified).

Locks the properties asserted by the v1 mining-integration tests directly on
the saved artifacts. The v1 test file's ``mined_results`` fixture uses a
``@classmethod``+``@pytest.fixture`` pattern that pytest >= 8.4 no longer
discovers; the original environment's ``.pytest_cache/v/cache/lastfailed``
records those three tests as failed there too, so this is a pre-existing
condition, not a v2 regression.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mine_hard_negatives import format_chunk_text, get_base_section  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def artifacts():
    return {
        "corpus": load_jsonl(REPO_ROOT / "data" / "corpus.jsonl"),
        "triplets": load_jsonl(REPO_ROOT / "data" / "train_triplets.jsonl"),
        "hard_neg": load_jsonl(REPO_ROOT / "data" / "hard_negatives.jsonl"),
        "train_q": load_jsonl(REPO_ROOT / "data" / "train_query_labels.jsonl"),
        "eval_q": load_jsonl(REPO_ROOT / "data" / "eval_queries.jsonl"),
    }


def test_corpus_counts(artifacts):
    corpus = artifacts["corpus"]
    assert len(corpus) == 1068
    assert sum(1 for c in corpus if c["split"] == "train") == 761
    assert sum(1 for c in corpus if c["split"] == "test") == 307


def test_query_dataset_counts(artifacts):
    assert len(artifacts["train_q"]) == 1078
    assert len(artifacts["eval_q"]) == 497


def test_triplet_count_and_content(artifacts):
    triplets = artifacts["triplets"]
    corpus = {c["chunk_id"]: c for c in artifacts["corpus"]}
    assert len(triplets) == 3234
    for t in triplets:
        assert t["anchor"].strip() and t["positive"].strip() and t["negative"].strip()


def test_hard_negative_invariants(artifacts):
    hn = artifacts["hard_neg"]
    assert len(hn) == 3234
    per_query = defaultdict(list)
    for r in hn:
        per_query[r["query_id"]].append(r)
    assert len(per_query) == 1078
    for qid, negs in per_query.items():
        assert len(negs) == 3, qid
        assert [n["negative_rank"] for n in negs] == [1, 2, 3], qid
        scores = [n["negative_score"] for n in negs]
        assert scores[0] >= scores[1] >= scores[2], qid
        neg_sections = [get_base_section(n["negative_chunk_id"]) for n in negs]
        assert len(neg_sections) == len(set(neg_sections)), qid
        pos_section = get_base_section(negs[0]["positive_chunk_id"])
        assert pos_section not in neg_sections, qid


def test_triplets_carry_heading_prefixes(artifacts):
    corpus = {c["chunk_id"]: c for c in artifacts["corpus"]}
    for t, hn in zip(artifacts["triplets"], artifacts["hard_neg"]):
        pos = corpus[hn["positive_chunk_id"]]
        neg = corpus[hn["negative_chunk_id"]]
        assert t["positive"] == format_chunk_text(pos)
        assert t["negative"] == format_chunk_text(neg)
        assert t["positive"].startswith(pos["heading_prefix"])
        assert t["negative"].startswith(neg["heading_prefix"])
