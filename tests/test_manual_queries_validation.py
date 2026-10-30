"""Tests for scripts/validate_manual_queries.py (stdlib-only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_manual_queries import validate  # noqa: E402


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    chunks = [
        {
            "chunk_id": "mydoc::registry::sub_000",
            "doc_name": "mydoc",
            "source_file": "mydoc.md",
            "split": "test",
            "heading": "Adapter Registry",
            "heading_level": 1,
            "heading_prefix": "mydoc: Adapter Registry",
            "text": "Registry entries store adapters and lineage metadata.",
        },
        {
            "chunk_id": "mydoc::registry::sub_001",
            "doc_name": "mydoc",
            "source_file": "mydoc.md",
            "split": "test",
            "heading": "Adapter Registry",
            "heading_level": 1,
            "heading_prefix": "mydoc: Adapter Registry",
            "text": "Entries can be packed into cans and published.",
        },
        {
            "chunk_id": "mydoc::bom",
            "doc_name": "mydoc",
            "source_file": "mydoc.md",
            "split": "test",
            "heading": "Bill of Materials (soup bom emit)",
            "heading_level": 2,
            "heading_prefix": "mydoc: Bill of Materials (soup bom emit)",
            "text": "Emits CycloneDX and SPDX documents.",
        },
        {
            "chunk_id": "evaluation::1-0",
            "doc_name": "evaluation",
            "source_file": "evaluation.md",
            "split": "test",
            "heading": "1.0",
            "heading_level": 1,
            "heading_prefix": "evaluation: 1.0",
            "text": "rouge_l_score([\"the quick brown fox\"], [\"a quick brown dog\"])",
        },
        {
            "chunk_id": "train_doc::x",
            "doc_name": "train_doc",
            "source_file": "train_doc.md",
            "split": "train",
            "heading": "X",
            "heading_level": 1,
            "heading_prefix": "train_doc: X",
            "text": "soup adapters merge weights with ties strategy density",
        },
    ]
    path = tmp_path / "corpus.jsonl"
    path.write_text("\n".join(json.dumps(c) for c in chunks) + "\n", encoding="utf-8")
    return path


def base_record(**overrides) -> dict:
    record = {
        "query_id": "manual_001",
        "query": "How do I list what is inside the adapter registry?",
        "source_document": "mydoc",
        "query_type": "how_to",
        "subset": "primary",
        "relevant_section_ids": ["mydoc::registry"],
        "relevant_chunk_ids": ["mydoc::registry::sub_000"],
        "evidence_chunk_ids": ["mydoc::registry::sub_000"],
        "rationale": "The first registry chunk describes entry contents.",
        "cross_corpus_overlap": None,
    }
    record.update(overrides)
    return record


def write_queries(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "manual_queries.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def run_validate(tmp_path, mini_corpus, records, check_globals=False, semantic=False):
    queries = write_queries(tmp_path, records)
    return validate(
        corpus_path=mini_corpus,
        queries_path=queries,
        scripts_dir=tmp_path,
        config_dir=tmp_path,
        check_globals=check_globals,
        semantic=semantic,
    )


def test_valid_primary_query_passes(tmp_path, mini_corpus):
    report = run_validate(tmp_path, mini_corpus, [base_record()])
    assert report["valid"], report["errors"]


def test_missing_file_reported(tmp_path, mini_corpus):
    report = validate(
        corpus_path=mini_corpus,
        queries_path=tmp_path / "nope.jsonl",
        scripts_dir=tmp_path,
        config_dir=tmp_path,
    )
    assert not report["valid"]
    assert "not found" in report["errors"][0]


def test_query_id_format(tmp_path, mini_corpus):
    report = run_validate(tmp_path, mini_corpus, [base_record(query_id="q1")])
    assert any("query_id must match" in e for e in report["errors"])


def test_duplicate_query_id_and_text(tmp_path, mini_corpus):
    a = base_record()
    b = base_record(query_id="manual_002", query=a["query"])
    report = run_validate(tmp_path, mini_corpus, [a, b, a])
    errors = report["errors"]
    assert any("duplicate query_id" in e for e in errors)
    assert any("duplicate query text" in e for e in errors)


def test_heading_copy_detected(tmp_path, mini_corpus):
    record = base_record(
        query="What is the bill of materials soup bom emit output format?",
        relevant_section_ids=["mydoc::bom"],
        relevant_chunk_ids=["mydoc::bom"],
        evidence_chunk_ids=["mydoc::bom"],
    )
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("copies a heading phrase" in e for e in report["errors"])


def test_mechanical_template_is_error(tmp_path, mini_corpus):
    record = base_record(query="How do you configure adapter registry in Soup?")
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("mechanical v1 template" in e for e in report["errors"])


def test_template_like_warning_only(tmp_path, mini_corpus):
    record = base_record(query="What is the role of the adapter registry?")
    report = run_validate(tmp_path, mini_corpus, [record])
    assert report["valid"]
    assert any("resembles a v1 template" in w for w in report["warnings"])


def test_train_chunk_in_primary_rejected(tmp_path, mini_corpus):
    record = base_record(
        relevant_section_ids=["train_doc::x"],
        relevant_chunk_ids=["train_doc::x"],
        evidence_chunk_ids=["train_doc::x"],
    )
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("not held-out" in e for e in report["errors"])


def test_overlap_subset_requires_overlap_field(tmp_path, mini_corpus):
    record = base_record(subset="overlap")
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("requires cross_corpus_overlap" in e for e in report["errors"])


def test_overlap_subset_valid(tmp_path, mini_corpus):
    record = base_record(
        subset="overlap",
        relevant_section_ids=["mydoc::registry", "train_doc::x"],
        relevant_chunk_ids=["mydoc::registry::sub_000", "train_doc::x"],
        evidence_chunk_ids=["mydoc::registry::sub_000"],
        cross_corpus_overlap={
            "train_chunk_ids": ["train_doc::x"],
            "note": "Equivalent answer in training doc.",
        },
    )
    report = run_validate(tmp_path, mini_corpus, [record])
    assert report["valid"], report["errors"]


def test_section_chunk_consistency(tmp_path, mini_corpus):
    wrong_section = base_record(
        relevant_section_ids=["mydoc::other"],
        relevant_chunk_ids=["mydoc::registry::sub_000"],
    )
    report = run_validate(tmp_path, mini_corpus, [wrong_section])
    assert any("not in relevant_section_ids" in e for e in report["errors"])
    assert any("has no corresponding relevant chunk" in e for e in report["errors"])

    missing_chunk = base_record(
        relevant_section_ids=["mydoc::registry"],
        relevant_chunk_ids=["mydoc::registry::sub_000", "mydoc::nope"],
    )
    report = run_validate(tmp_path, mini_corpus, [missing_chunk])
    assert any("not in corpus" in e for e in report["errors"])


def test_evidence_must_be_subset(tmp_path, mini_corpus):
    record = base_record(evidence_chunk_ids=["mydoc::bom"])
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("subset of relevant_chunk_ids" in e for e in report["errors"])


def test_excluded_degenerate_section(tmp_path, mini_corpus):
    record = base_record(
        source_document="evaluation",
        relevant_section_ids=["evaluation::1-0"],
        relevant_chunk_ids=["evaluation::1-0"],
        evidence_chunk_ids=["evaluation::1-0"],
    )
    report = run_validate(tmp_path, mini_corpus, [record])
    assert any("degenerate table-artifact" in e for e in report["errors"])


def test_allocation_out_of_range(tmp_path, mini_corpus):
    record = base_record(
        source_document="evaluation",
        relevant_section_ids=["evaluation::1-0"],
        relevant_chunk_ids=["evaluation::1-0"],
        evidence_chunk_ids=["evaluation::1-0"],
    )
    report = run_validate(tmp_path, mini_corpus, [record], check_globals=True)
    assert any("allocation for 'evaluation'" in e for e in report["errors"])


def test_query_type_vocab(tmp_path, mini_corpus):
    report = run_validate(tmp_path, mini_corpus, [base_record(query_type="banana")])
    assert any("query_type" in e for e in report["errors"])


def test_count_bounds(tmp_path, mini_corpus):
    empty = run_validate(tmp_path, mini_corpus, [], check_globals=True)
    assert any("outside" in e for e in empty["errors"])
    many = [base_record(query_id=f"manual_{i:03d}", query=f"question number {i}?") for i in range(40)]
    report = run_validate(tmp_path, mini_corpus, many)
    assert report["valid"], report["errors"]


def test_overlap_flag_is_review_material(tmp_path, mini_corpus):
    record = base_record(query="How do I merge adapters with ties?")
    report = run_validate(tmp_path, mini_corpus, [record])
    assert report["valid"], report["errors"]
    assert any("lexical overlap" in f for f in report["flags"])
    assert "provisional" in report["note"]
    top = report["per_record"][0]["lex_top_matches"]
    assert top and top[0]["chunk_id"] == "train_doc::x"


def test_lex_top_matches_reported_below_threshold(tmp_path, mini_corpus):
    record = base_record(query="merge strategy")
    report = run_validate(tmp_path, mini_corpus, [record], )
    assert report["valid"], report["errors"]
    top = report["per_record"][0]["lex_top_matches"]
    assert any(m["chunk_id"] == "train_doc::x" for m in top)
    assert all("lexical overlap" not in f for f in report["flags"])


def test_non_coupling_scan(tmp_path, mini_corpus):
    bad_scripts = tmp_path / "scripts"
    bad_scripts.mkdir()
    (bad_scripts / "mine_hard_negatives.py").write_text("data/manual_queries.jsonl", encoding="utf-8")
    report = validate(
        corpus_path=mini_corpus,
        queries_path=write_queries(tmp_path, [base_record()]),
        scripts_dir=bad_scripts,
        config_dir=tmp_path,
    )
    assert any("coupling" in e for e in report["errors"])


def test_semantic_stage_wiring(monkeypatch, tmp_path, mini_corpus):
    import validate_manual_queries as vq

    monkeypatch.setattr(
        vq,
        "semantic_overlap_flags",
        lambda records, maps, threshold, max_flags: {
            "flags": ["manual_001: semantic similarity 0.99 with train chunk 'train_doc::x'"],
            "top_matches": [
                {"query_id": "manual_001", "top_train_chunks": [{"chunk_id": "train_doc::x", "cosine": 0.99}]}
            ],
            "note": None,
        },
    )
    report = run_validate(tmp_path, mini_corpus, [base_record()], semantic=True)
    assert report["semantic_stage"] is None
    assert any("semantic similarity" in f for f in report["flags"])
    assert report["semantic_top_matches"][0]["query_id"] == "manual_001"
    assert "semantic cosine >= 0.65" in report["note"]
    assert "top-5 train-chunk matches" in report["note"]


def test_semantic_stage_unavailable_is_a_note(tmp_path, mini_corpus):
    import validate_manual_queries as vq

    original = vq.semantic_overlap_flags

    def unavailable(records, maps, threshold, max_flags):
        return {"flags": [], "top_matches": [], "note": "semantic stage unavailable: no torch"}

    vq.semantic_overlap_flags = unavailable
    try:
        report = run_validate(tmp_path, mini_corpus, [base_record()], semantic=True)
    finally:
        vq.semantic_overlap_flags = original
    assert "unavailable" in report["semantic_stage"]
    assert report["valid"]


def test_non_coupling_scan_ignores_v2_scripts(tmp_path, mini_corpus):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    # v2 script legitimately references the manual dataset -> not a coupling error
    (scripts / "run_retrieval.py").write_text("queries_path = DATA_DIR / 'manual_queries.jsonl'", encoding="utf-8")
    (scripts / "mine_hard_negatives.py").write_text("data/manual_queries.jsonl", encoding="utf-8")
    report = validate(
        corpus_path=mini_corpus,
        queries_path=write_queries(tmp_path, [base_record()]),
        scripts_dir=scripts,
        config_dir=tmp_path,
    )
    errors = report["errors"]
    assert any("coupling" in e and "mine_hard_negatives" in e for e in errors)
    assert not any("run_retrieval" in e for e in errors)
