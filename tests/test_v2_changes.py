"""Unit and integration tests for RAG prototype v2 changes (P0, P1, P2).

Tests:
1. P0: Prepend heading_prefix to positive and negative in triplets
2. P1: Mine top-3 negatives per query with section deduplication
3. P2: Verify val_split is 0.0 in config/embedding.yaml
4. Defer: Verify margin is 0.5, target_modules is auto (no premature changes)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mine_hard_negatives import format_chunk_text, get_base_section, mine_hard_negatives


class TestP2Config:
    """Tests for P2 and deferred items in config/embedding.yaml."""

    def test_val_split_is_zero(self):
        config_path = REPO_ROOT / "config" / "embedding.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert cfg["data"]["val_split"] == 0.0, (
            f"Expected val_split to be 0.0, got {cfg['data']['val_split']}"
        )

    def test_deferred_items_unchanged(self):
        config_path = REPO_ROOT / "config" / "embedding.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        # Margin should remain 0.5 (deferred)
        assert cfg["training"]["embedding_margin"] == 0.5, (
            f"Expected embedding_margin to remain 0.5, got {cfg['training']['embedding_margin']}"
        )
        # LoRA target modules should remain auto (deferred)
        assert cfg["training"]["lora"]["target_modules"] == "auto", (
            f"Expected target_modules to remain 'auto', got {cfg['training']['lora']['target_modules']}"
        )


class TestP0P1Helpers:
    """Tests for format_chunk_text and get_base_section."""

    def test_format_chunk_text_with_heading_prefix(self):
        chunk = {
            "heading_prefix": "doc: Header Section",
            "doc_name": "doc",
            "text": "Body paragraph content.",
        }
        formatted = format_chunk_text(chunk)
        assert formatted == "doc: Header Section\n\nBody paragraph content."

    def test_format_chunk_text_fallback_to_doc_name(self):
        chunk = {
            "heading_prefix": "",
            "doc_name": "doc-name",
            "text": "Body content without header.",
        }
        formatted = format_chunk_text(chunk)
        assert formatted == "doc-name\n\nBody content without header."

    def test_format_chunk_text_whitespace_prefix(self):
        chunk = {
            "heading_prefix": "   ",
            "doc_name": "doc",
            "text": "Body content.",
        }
        formatted = format_chunk_text(chunk)
        assert formatted == "doc\n\nBody content."

    def test_get_base_section_sub_chunk(self):
        assert get_base_section("doc::sec-name::sub_000") == "doc::sec-name"
        assert get_base_section("doc::sec-name::sub_042") == "doc::sec-name"

    def test_get_base_section_plain_chunk(self):
        assert get_base_section("doc::sec-name") == "doc::sec-name"
        assert get_base_section("doc") == "doc"


class TestMiningLogicSynthetic:
    """Tests for hard negative mining logic on synthetic corpus with mock encoder."""

    @pytest.fixture
    def synthetic_data(self, monkeypatch, tmp_path):
        # 5 sections across doc1:
        # sec_pos: sub_000 (relevant), sub_001 (same section as relevant)
        # sec_neg1: sub_000, sub_001 (should only pick one of these due to section dedup)
        # sec_neg2: sub_000
        # sec_neg3: sub_000
        # sec_neg4: sub_000
        corpus = [
            {
                "chunk_id": "doc1::sec_pos::sub_000",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Positive Section",
                "text": "Relevant chunk text.",
            },
            {
                "chunk_id": "doc1::sec_pos::sub_001",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Positive Section",
                "text": "Same section sibling chunk.",
            },
            {
                "chunk_id": "doc1::sec_neg1::sub_000",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Negative 1 Part 0",
                "text": "High score negative 1 part 0.",
            },
            {
                "chunk_id": "doc1::sec_neg1::sub_001",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Negative 1 Part 1",
                "text": "High score negative 1 part 1 (same section!).",
            },
            {
                "chunk_id": "doc1::sec_neg2::sub_000",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Negative 2",
                "text": "Negative 2 text.",
            },
            {
                "chunk_id": "doc1::sec_neg3::sub_000",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Negative 3",
                "text": "Negative 3 text.",
            },
            {
                "chunk_id": "doc1::sec_neg4::sub_000",
                "doc_name": "doc1",
                "split": "train",
                "heading_prefix": "doc1: Negative 4",
                "text": "Negative 4 text.",
            },
        ]

        queries = [
            {
                "query_id": "q1",
                "query": "How does synthetic test work?",
                "relevant_chunk_ids": ["doc1::sec_pos::sub_000"],
            }
        ]

        corpus_file = tmp_path / "corpus.jsonl"
        with open(corpus_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(c) + "\n" for c in corpus)

        queries_file = tmp_path / "queries.jsonl"
        with open(queries_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(q) + "\n" for q in queries)

        triplets_file = tmp_path / "train_triplets.jsonl"
        hn_file = tmp_path / "hard_negatives.jsonl"

        # Mock SharedEncoder:
        # Predefined vectors so that:
        # chunk 0 (sec_pos sub_0): dot = 0.95
        # chunk 1 (sec_pos sub_1): dot = 0.90 (same section, must be excluded)
        # chunk 2 (sec_neg1 sub_0): dot = 0.85 (rank 1 negative)
        # chunk 3 (sec_neg1 sub_1): dot = 0.80 (must be deduplicated because sec_neg1 is already taken)
        # chunk 4 (sec_neg2 sub_0): dot = 0.75 (rank 2 negative)
        # chunk 5 (sec_neg3 sub_0): dot = 0.70 (rank 3 negative)
        # chunk 6 (sec_neg4 sub_0): dot = 0.65 (not picked because top-3 reached)
        class MockEncoder:
            def encode(self, texts: list[str]) -> np.ndarray:
                dim = 8
                # If encoding query
                if len(texts) == 1 and texts[0] == "How does synthetic test work?":
                    v = np.zeros((1, dim), dtype=np.float32)
                    v[0, 0] = 1.0
                    return v
                # If encoding corpus chunks (7 chunks)
                vecs = np.zeros((len(texts), dim), dtype=np.float32)
                weights = [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65]
                for idx, w in enumerate(weights):
                    vecs[idx, 0] = w
                    vecs[idx, 1] = np.sqrt(1.0 - w**2)
                return vecs

        monkeypatch.setattr("mine_hard_negatives.SharedEncoder", MockEncoder)

        return corpus_file, queries_file, triplets_file, hn_file

    def test_synthetic_mining_dedup_and_prefix(self, synthetic_data):
        corpus_file, queries_file, triplets_file, hn_file = synthetic_data

        triplets = mine_hard_negatives(
            num_negatives=3,
            corpus_path=corpus_file,
            queries_path=queries_file,
            output_triplets=triplets_file,
            output_hard_negatives=hn_file,
        )

        # 1 query * 3 negatives = 3 triplets
        assert len(triplets) == 3

        # P0 Check: heading_prefix prepended to positive in all triplets
        for t in triplets:
            assert t["anchor"] == "How does synthetic test work?"
            assert t["positive"] == "doc1: Positive Section\n\nRelevant chunk text."
            assert "\n\n" in t["positive"]
            assert "\n\n" in t["negative"]

        # Check negative texts
        assert triplets[0]["negative"] == "doc1: Negative 1 Part 0\n\nHigh score negative 1 part 0."
        assert triplets[1]["negative"] == "doc1: Negative 2\n\nNegative 2 text."
        assert triplets[2]["negative"] == "doc1: Negative 3\n\nNegative 3 text."

        # Verify hard negative annotations
        with open(hn_file, "r", encoding="utf-8") as f:
            hn_records = [json.loads(line) for line in f]

        assert len(hn_records) == 3
        assert hn_records[0]["negative_chunk_id"] == "doc1::sec_neg1::sub_000"
        assert hn_records[0]["negative_rank"] == 1
        assert hn_records[1]["negative_chunk_id"] == "doc1::sec_neg2::sub_000"
        assert hn_records[1]["negative_rank"] == 2
        assert hn_records[2]["negative_chunk_id"] == "doc1::sec_neg3::sub_000"
        assert hn_records[2]["negative_rank"] == 3

        # Verify section deduplication:
        # sec_neg1::sub_001 was skipped because sec_neg1::sub_000 was already selected
        # sec_pos::sub_001 was skipped because it shares section with relevant chunk
        picked_sections = [get_base_section(r["negative_chunk_id"]) for r in hn_records]
        assert len(picked_sections) == len(set(picked_sections)), "Negatives must belong to unique sections"
        assert "doc1::sec_pos" not in picked_sections, "Negative cannot share section with relevant chunk"


class TestMiningRealCorpusIntegration:
    """Integration test running mine_hard_negatives on real corpus to temp files."""

    @classmethod
    @pytest.fixture(scope="class")
    def mined_results(cls, tmp_path_factory):
        tmp_dir = tmp_path_factory.mktemp("mining_test")
        triplets_file = tmp_dir / "test_triplets.jsonl"
        hn_file = tmp_dir / "test_hard_negatives.jsonl"

        triplets = mine_hard_negatives(
            num_negatives=3,
            output_triplets=triplets_file,
            output_hard_negatives=hn_file,
        )

        with open(hn_file, "r", encoding="utf-8") as f:
            hn_records = [json.loads(line) for line in f]

        with open(REPO_ROOT / "data" / "corpus.jsonl", "r", encoding="utf-8") as f:
            corpus_chunks = {c["chunk_id"]: c for c in (json.loads(line) for line in f)}

        with open(REPO_ROOT / "data" / "train_query_labels.jsonl", "r", encoding="utf-8") as f:
            queries = [json.loads(line) for line in f]

        return {
            "triplets": triplets,
            "hn_records": hn_records,
            "corpus_chunks": corpus_chunks,
            "queries": queries,
        }

    def test_total_triplets_count(self, mined_results):
        triplets = mined_results["triplets"]
        queries = mined_results["queries"]
        # Exactly 3 negatives per query: 1078 * 3 = 3234
        assert len(triplets) == len(queries) * 3
        assert len(triplets) == 3234

    def test_heading_prefix_prepended_to_pos_and_neg(self, mined_results):
        triplets = mined_results["triplets"]
        hn_records = mined_results["hn_records"]
        corpus_chunks = mined_results["corpus_chunks"]

        for t, hn in zip(triplets, hn_records):
            pos_chunk = corpus_chunks[hn["positive_chunk_id"]]
            neg_chunk = corpus_chunks[hn["negative_chunk_id"]]

            expected_pos = format_chunk_text(pos_chunk)
            expected_neg = format_chunk_text(neg_chunk)

            assert t["positive"] == expected_pos, (
                f"Positive text mismatch for query {hn['query_id']}"
            )
            assert t["negative"] == expected_neg, (
                f"Negative text mismatch for query {hn['query_id']}"
            )

            # Explicitly verify heading_prefix is present at start
            assert t["positive"].startswith(pos_chunk["heading_prefix"]), (
                f"Positive text missing heading prefix {pos_chunk['heading_prefix']}"
            )
            assert t["negative"].startswith(neg_chunk["heading_prefix"]), (
                f"Negative text missing heading prefix {neg_chunk['heading_prefix']}"
            )

    def test_section_deduplication_per_query(self, mined_results):
        hn_records = mined_results["hn_records"]
        # Group hn_records by query_id
        from collections import defaultdict
        query_negatives = defaultdict(list)
        for r in hn_records:
            query_negatives[r["query_id"]].append(r)

        assert len(query_negatives) == 1078

        for qid, negs in query_negatives.items():
            assert len(negs) == 3, f"Query {qid} does not have exactly 3 negatives"

            # Check ranks
            ranks = [n["negative_rank"] for n in negs]
            assert ranks == [1, 2, 3]

            # Check scores are descending
            scores = [n["negative_score"] for n in negs]
            assert scores[0] >= scores[1] >= scores[2], (
                f"Scores not descending for query {qid}: {scores}"
            )

            # Check section deduplication among negatives
            neg_sections = [get_base_section(n["negative_chunk_id"]) for n in negs]
            assert len(neg_sections) == len(set(neg_sections)), (
                f"Duplicate negative section found for query {qid}: {neg_sections}"
            )

            # Check negative does not share section with positive
            pos_section = get_base_section(negs[0]["positive_chunk_id"])
            assert pos_section not in neg_sections, (
                f"Negative section shares base section with positive for query {qid}: {pos_section}"
            )

