"""Benchmark manifest schema validation and integrity enforcement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_benchmark_manifest(
    manifest_path: Path, repo_root: Path
) -> dict[str, Any]:
    """Validate a benchmark manifest file according to strict integrity rules.

    Rejects:
    - Non-existent manifest files.
    - Path traversal outside repo_root / 'data'.
    - Unfrozen benchmarks (frozen != True or status != 'frozen').
    - Corrupt, missing, or altered corpus/query/annotation files.
    - Missing or invalid fingerprints.
    """
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Benchmark manifest not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in benchmark manifest {manifest_path}: {e}")

    # Required top-level fields
    for field in ("benchmark_id", "schema_version", "status", "frozen", "corpus", "queries"):
        if field not in manifest:
            raise ValueError(f"Manifest missing required top-level field '{field}'")

    data_dir = (repo_root / "data").resolve()

    def resolve_secure_path(rel_or_abs: str | Path, field_name: str) -> Path:
        p = Path(rel_or_abs)
        target = (repo_root / p if not p.is_absolute() else p).resolve()
        try:
            target.relative_to(data_dir)
        except ValueError:
            raise ValueError(
                f"Path traversal detected in manifest field '{field_name}': "
                f"'{rel_or_abs}' resolves to '{target}' outside '{data_dir}'"
            )
        return target

    # Resolve paths
    corpus_cfg = manifest["corpus"]
    query_cfg = manifest["queries"]
    annot_cfg = manifest.get("relevance_annotations", {})

    corpus_path = resolve_secure_path(corpus_cfg.get("path", ""), "corpus.path")
    query_path = resolve_secure_path(query_cfg.get("path", ""), "queries.path")
    annot_path = (
        resolve_secure_path(annot_cfg.get("path", ""), "relevance_annotations.path")
        if annot_cfg.get("path")
        else None
    )

    # Check freeze status
    if not manifest.get("frozen", False) or manifest.get("status") != "frozen":
        raise ValueError(
            f"Benchmark '{manifest['benchmark_id']}' is not frozen "
            f"(status: '{manifest.get('status')}', frozen: {manifest.get('frozen')}). "
            "Evaluation execution is blocked until human authorship and relevance annotations are frozen."
        )

    # Check corpus integrity
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
    expected_corpus_sha = corpus_cfg.get("sha256")
    if not expected_corpus_sha:
        raise ValueError("Corpus SHA256 checksum missing in manifest.")
    actual_corpus_sha = compute_file_sha256(corpus_path)
    if actual_corpus_sha != expected_corpus_sha:
        raise ValueError(
            f"Corpus SHA256 mismatch for {corpus_path.name}: "
            f"got {actual_corpus_sha}, expected {expected_corpus_sha}"
        )

    # Check query integrity
    if not query_path.exists():
        raise FileNotFoundError(f"Query file not found: {query_path}")
    expected_query_sha = query_cfg.get("sha256")
    if not expected_query_sha:
        raise ValueError("Query SHA256 checksum missing in manifest.")
    actual_query_sha = compute_file_sha256(query_path)
    if actual_query_sha != expected_query_sha:
        raise ValueError(
            f"Query SHA256 mismatch for {query_path.name}: "
            f"got {actual_query_sha}, expected {expected_query_sha}"
        )

    query_records = [
        json.loads(line)
        for line in query_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if "query_count" in query_cfg and len(query_records) != query_cfg["query_count"]:
        raise ValueError(
            f"Query count mismatch in {query_path.name}: "
            f"found {len(query_records)} records, expected {query_cfg['query_count']}"
        )

    # Check annotations integrity if provided
    if annot_path:
        if not annot_path.exists():
            raise FileNotFoundError(f"Annotations file not found: {annot_path}")
        expected_annot_sha = annot_cfg.get("sha256")
        if expected_annot_sha:
            actual_annot_sha = compute_file_sha256(annot_path)
            if actual_annot_sha != expected_annot_sha:
                raise ValueError(
                    f"Annotation SHA256 mismatch for {annot_path.name}: "
                    f"got {actual_annot_sha}, expected {expected_annot_sha}"
                )
        if annot_cfg.get("annotation_status") != "complete":
            raise ValueError(
                f"Relevance annotation status is '{annot_cfg.get('annotation_status')}', "
                "expected 'complete' for frozen benchmark."
            )

    return {
        "manifest": manifest,
        "corpus_path": corpus_path,
        "query_path": query_path,
        "annotation_path": annot_path,
        "corpus_sha256": actual_corpus_sha,
        "query_sha256": actual_query_sha,
        "query_count": len(query_records),
    }
