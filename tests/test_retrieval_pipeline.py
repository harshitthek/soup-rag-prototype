"""Unit and integration tests for the Soup dense retrieval pipeline.

Tests:
1. Pipeline Configuration: Verify val_split is 0.0, output path, margin is 0.5, LoRA target_modules is auto.
2. Chunk Formatting & Section Extraction: Heading prefix prepending and base section deduplication helpers.
3. Mining Logic (Synthetic): Hard negative mining with section deduplication and heading prefix retention.
4. Dataset Invariants (Corpus Integration): Exactly 3,234 triplets, 3 negatives per query, section deduplication, 0 self-negatives.
5. Model & Adapter Integrity: Verify output_embedding loads with SharedEncoder, produces 384-dim unit-normalized vectors.
6. Comparison & Reporting: Verify paired bootstrap CI schema and report formatting without unsupported p-values.
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

from encoder import SharedEncoder
from mine_hard_negatives import format_chunk_text, get_base_section, mine_hard_negatives
from compare_results import paired_bootstrap_ci, generate_report


class TestPipelineConfig:
    """Tests for configuration in config/embedding.yaml."""

    def test_val_split_is_zero(self):
        config_path = REPO_ROOT / "config" / "embedding.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert cfg["data"]["val_split"] == 0.0, (
            f"Expected val_split to be 0.0, got {cfg['data']['val_split']}"
        )

    def test_paths_and_model_settings(self):
        config_path = REPO_ROOT / "config" / "embedding.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert cfg["data"]["train"] == "data/train_triplets.jsonl"
        assert cfg["output"] == "output_embedding"
        assert cfg["training"]["embedding_loss"] == "triplet"
        assert cfg["training"]["embedding_margin"] == 0.5
        assert cfg["training"]["lora"]["target_modules"] == "auto"
        assert cfg["training"]["lora"]["r"] == 16
        assert cfg["training"]["lora"]["alpha"] == 32


class TestChunkFormattingAndSections:
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

        class MockEncoder:
            def encode(self, texts: list[str]) -> np.ndarray:
                dim = 8
                if len(texts) == 1 and texts[0] == "How does synthetic test work?":
                    v = np.zeros((1, dim), dtype=np.float32)
                    v[0, 0] = 1.0
                    return v
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

        assert len(triplets) == 3

        for t in triplets:
            assert t["anchor"] == "How does synthetic test work?"
            assert t["positive"] == "doc1: Positive Section\n\nRelevant chunk text."
            assert "\n\n" in t["positive"]
            assert "\n\n" in t["negative"]

        assert triplets[0]["negative"] == "doc1: Negative 1 Part 0\n\nHigh score negative 1 part 0."
        assert triplets[1]["negative"] == "doc1: Negative 2\n\nNegative 2 text."
        assert triplets[2]["negative"] == "doc1: Negative 3\n\nNegative 3 text."

        with open(hn_file, "r", encoding="utf-8") as f:
            hn_records = [json.loads(line) for line in f]

        assert len(hn_records) == 3
        assert hn_records[0]["negative_chunk_id"] == "doc1::sec_neg1::sub_000"
        assert hn_records[0]["negative_rank"] == 1
        assert hn_records[1]["negative_chunk_id"] == "doc1::sec_neg2::sub_000"
        assert hn_records[1]["negative_rank"] == 2
        assert hn_records[2]["negative_chunk_id"] == "doc1::sec_neg3::sub_000"
        assert hn_records[2]["negative_rank"] == 3

        picked_sections = [get_base_section(r["negative_chunk_id"]) for r in hn_records]
        assert len(picked_sections) == len(set(picked_sections)), "Negatives must belong to unique sections"
        assert "doc1::sec_pos" not in picked_sections, "Negative cannot share section with relevant chunk"

    def test_synthetic_mining_creates_nested_output_directories(self, synthetic_data, tmp_path):
        corpus_file, queries_file, _, _ = synthetic_data
        nested_triplets = tmp_path / "nested" / "dir" / "triplets.jsonl"
        nested_hn = tmp_path / "another" / "deeply" / "nested" / "hn.jsonl"

        assert not nested_triplets.parent.exists()
        assert not nested_hn.parent.exists()

        mine_hard_negatives(
            num_negatives=1,
            corpus_path=corpus_file,
            queries_path=queries_file,
            output_triplets=nested_triplets,
            output_hard_negatives=nested_hn,
        )

        assert nested_triplets.exists()
        assert nested_hn.exists()


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

            assert t["positive"].startswith(pos_chunk["heading_prefix"]), (
                f"Positive text missing heading prefix {pos_chunk['heading_prefix']}"
            )
            assert t["negative"].startswith(neg_chunk["heading_prefix"]), (
                f"Negative text missing heading prefix {neg_chunk['heading_prefix']}"
            )

    def test_section_deduplication_per_query(self, mined_results):
        hn_records = mined_results["hn_records"]
        from collections import defaultdict
        query_negatives = defaultdict(list)
        for r in hn_records:
            query_negatives[r["query_id"]].append(r)

        assert len(query_negatives) == 1078

        for qid, negs in query_negatives.items():
            assert len(negs) == 3, f"Query {qid} does not have exactly 3 negatives"

            ranks = [n["negative_rank"] for n in negs]
            assert ranks == [1, 2, 3]

            scores = [n["negative_score"] for n in negs]
            assert scores[0] >= scores[1] >= scores[2], (
                f"Scores not descending for query {qid}: {scores}"
            )

            neg_sections = [get_base_section(n["negative_chunk_id"]) for n in negs]
            assert len(neg_sections) == len(set(neg_sections)), (
                f"Duplicate negative section found for query {qid}: {neg_sections}"
            )

            pos_section = get_base_section(negs[0]["positive_chunk_id"])
            assert pos_section not in neg_sections, (
                f"Negative section shares base section with positive for query {qid}: {pos_section}"
            )


class TestModelAdapter:
    """Tests for the fine-tuned LoRA adapter in output_embedding."""

    def test_adapter_load_and_encode(self):
        adapter_path = REPO_ROOT / "output_embedding"
        assert adapter_path.exists(), "output_embedding must exist"
        assert (adapter_path / "adapter_model.safetensors").exists(), "adapter weights must exist"

        encoder = SharedEncoder(adapter_dir=str(adapter_path))
        test_texts = [
            "commands: soup train\n\nTrain an embedding model.",
            "evaluation: probes\n\nEvaluate retrieval quality.",
        ]
        vecs = encoder.encode(test_texts)

        assert vecs.shape == (2, 384), f"Expected shape (2, 384), got {vecs.shape}"
        norms = np.linalg.norm(vecs, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5), "Vectors must be L2 normalized"


class TestCompareResults:
    """Tests for paired bootstrap uncertainty calculations and report formatting."""

    def test_paired_bootstrap_ci_schema(self):
        b = [0.5, 0.6, 0.7, 0.8]
        c = [0.7, 0.8, 0.9, 1.0]
        res = paired_bootstrap_ci(b, c, n_bootstrap=100)
        assert "delta" in res
        assert "ci_lower" in res
        assert "ci_upper" in res
        assert "p_value" not in res
        assert "significant" not in res
        assert res["delta"] == 0.2

    def test_generate_report_no_p_value_columns(self, tmp_path):
        with open(REPO_ROOT / "results" / "baseline.json", "r", encoding="utf-8") as f:
            baseline = json.load(f)
        with open(REPO_ROOT / "results" / "candidate.json", "r", encoding="utf-8") as f:
            candidate = json.load(f)

        output_file = tmp_path / "comparison.md"
        report = generate_report(baseline, candidate, output_file)

        assert output_file.exists()
        assert "p-value" not in report
        assert "Significant" not in report
        assert "95% Bootstrap CI" in report
        assert "synthetic test queries (template-generated from held-out docs)" in report

