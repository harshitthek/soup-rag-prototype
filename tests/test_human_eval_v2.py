"""Verification tests for the Independent Human Evaluation Benchmark (v2)."""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HUMAN_EVAL_DIR = REPO_ROOT / "data" / "human_eval"
MANIFEST_PATH = HUMAN_EVAL_DIR / "manifest_v2.json"
QUERIES_PATH = HUMAN_EVAL_DIR / "human_queries_v2.jsonl"
ANNOTATIONS_PATH = HUMAN_EVAL_DIR / "relevance_annotations_v2.jsonl"
CORPUS_PATH = REPO_ROOT / "data" / "corpus.jsonl"


def test_manifest_v2_frozen_and_valid():
    assert MANIFEST_PATH.exists(), "manifest_v2.json must exist"
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["status"] == "frozen"
    assert data["frozen"] is True
    assert data["query_count"] == 24
    assert len(data["queries"]) == 24


def test_human_queries_v2_count_and_schema():
    assert QUERIES_PATH.exists(), "human_queries_v2.jsonl must exist"
    lines = [json.loads(line) for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 24
    for i, item in enumerate(lines, start=1):
        expected_id = f"soup_human_{i:03d}"
        assert item["query_id"] == expected_id
        assert len(item["query"].strip()) > 0
        assert item["ai_assistance_declaration"] == "Human-authored without AI assistance"


def test_relevance_annotations_v2_resolve_to_corpus():
    assert ANNOTATIONS_PATH.exists(), "relevance_annotations_v2.jsonl must exist"
    corpus_chunks = {json.loads(line)["chunk_id"] for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()}
    
    annots = [json.loads(line) for line in ANNOTATIONS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(annots) == 24
    for a in annots:
        assert a["status"] == "resolved"
        assert len(a["relevant_chunk_ids"]) > 0, f"Query {a['query_id']} has empty relevant chunks"
        for cid in a["relevant_chunk_ids"]:
            assert cid in corpus_chunks, f"Chunk ID '{cid}' for {a['query_id']} not in corpus.jsonl"
