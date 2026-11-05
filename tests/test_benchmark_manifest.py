"""Tests for benchmark manifest schema validation and security enforcement."""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark_manifest import compute_file_sha256, validate_benchmark_manifest


@pytest.fixture
def test_repo(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)

    # Valid corpus and query
    corpus_file = data_dir / "corpus.jsonl"
    corpus_file.write_text('{"chunk_id": "c1", "text": "passage one"}\n', encoding="utf-8")

    query_file = data_dir / "queries.jsonl"
    query_file.write_text('{"query_id": "q1", "query": "hello"}\n', encoding="utf-8")

    corpus_sha = compute_file_sha256(corpus_file)
    query_sha = compute_file_sha256(query_file)

    manifest_file = data_dir / "manifest.json"
    manifest_data = {
        "benchmark_id": "test_bench",
        "schema_version": "1.0",
        "status": "frozen",
        "frozen": True,
        "corpus": {
            "path": "data/corpus.jsonl",
            "sha256": corpus_sha,
            "chunk_count": 1,
        },
        "queries": {
            "path": "data/queries.jsonl",
            "sha256": query_sha,
            "query_count": 1,
        },
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    return tmp_path, manifest_file, manifest_data


def test_valid_manifest_passes(test_repo):
    root, manifest_file, _ = test_repo
    res = validate_benchmark_manifest(manifest_file, root)
    assert res["manifest"]["benchmark_id"] == "test_bench"
    assert res["query_count"] == 1


def test_missing_manifest_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        validate_benchmark_manifest(tmp_path / "missing.json", tmp_path)


def test_unfrozen_manifest_rejected(test_repo):
    root, manifest_file, data = test_repo
    data["frozen"] = False
    data["status"] = "awaiting_human_authorship"
    manifest_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="is not frozen"):
        validate_benchmark_manifest(manifest_file, root)


def test_path_traversal_rejected(test_repo):
    root, manifest_file, data = test_repo
    data["corpus"]["path"] = "../../etc/passwd"
    manifest_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_benchmark_manifest(manifest_file, root)


def test_corpus_sha256_mismatch_rejected(test_repo):
    root, manifest_file, data = test_repo
    data["corpus"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    manifest_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Corpus SHA256 mismatch"):
        validate_benchmark_manifest(manifest_file, root)


def test_query_count_mismatch_rejected(test_repo):
    root, manifest_file, data = test_repo
    data["queries"]["query_count"] = 99
    manifest_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Query count mismatch"):
        validate_benchmark_manifest(manifest_file, root)
