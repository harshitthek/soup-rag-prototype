from pathlib import Path
import pytest
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_retrieval import run, DATA_DIR, RESULTS_DIR


def test_run_guards(tmp_path):
    valid_queries = DATA_DIR / "manual_queries.jsonl"
    valid_corpus = DATA_DIR / "corpus.jsonl"
    valid_output = RESULTS_DIR / "v2" / "dummy.json"

    # top_k < 10
    with pytest.raises(ValueError, match="top_k must be at least 10"):
        run("bm25", valid_queries, valid_corpus, valid_output, top_k=9)

    # non-manual queries
    with pytest.raises(ValueError, match="refusing to run on query file other than"):
        run("bm25", tmp_path / "other_queries.jsonl", valid_corpus, valid_output)

    # non-default corpus
    with pytest.raises(ValueError, match="refusing to run on corpus file other than"):
        run("bm25", valid_queries, tmp_path / "other_corpus.jsonl", valid_output)

    # output not under results/v2
    with pytest.raises(ValueError, match="must resolve under"):
        run("bm25", valid_queries, valid_corpus, RESULTS_DIR / "baseline.json")


def test_query_fingerprint_guard(monkeypatch):
    valid_queries = DATA_DIR / "manual_queries.jsonl"
    valid_corpus = DATA_DIR / "corpus.jsonl"
    valid_output = RESULTS_DIR / "v2" / "dummy.json"

    monkeypatch.setattr("run_retrieval.query_set_fingerprint", lambda p: "tampered_hash")
    with pytest.raises(ValueError, match="query file fingerprint mismatch"):
        run("bm25", valid_queries, valid_corpus, valid_output)


def test_corpus_digest_stored(tmp_path):
    import hashlib
    valid_queries = DATA_DIR / "manual_queries.jsonl"
    valid_corpus = DATA_DIR / "corpus.jsonl"
    test_output = RESULTS_DIR / "v2" / "test_dummy_output.json"

    try:
        res = run("bm25", valid_queries, valid_corpus, test_output)
        assert "corpus_digest" in res
        expected_digest = hashlib.sha256(valid_corpus.read_bytes()).hexdigest()
        assert res["corpus_digest"] == expected_digest
    finally:
        if test_output.exists():
            test_output.unlink()

