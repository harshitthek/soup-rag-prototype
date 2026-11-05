"""Build research archive bundle outside active workspace with manifest and verification."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_OUT_DIR = Path.home() / ".cache" / "soup-rag-prototype" / "archive"
ARCHIVE_OUT_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR = Path(
    os.environ.get(
        "ANTIGRAVITY_SCRATCH_DIR",
        Path.home() / ".cache" / "soup-rag-prototype" / "scratch",
    )
)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_archive() -> dict[str, Any]:
    print("=== Building Soup RAG Research Archive Bundle ===")
    staging_dir = Path(tempfile.mkdtemp(prefix="soup_archive_staging_"))

    try:
        # 1. Historical Reports
        reports_dir = staging_dir / "reports"
        reports_dir.mkdir(parents=True)
        for p in (REPO_ROOT / "results").glob("PHASE_*.md"):
            shutil.copy2(p, reports_dir / p.name)
        for p in (REPO_ROOT / "results").glob("PHASE_*.json"):
            shutil.copy2(p, reports_dir / p.name)

        # 2. Phase 3 Benchmark artifacts
        phase3_dir = staging_dir / "phase3"
        phase3_dir.mkdir(parents=True)
        for p in (REPO_ROOT / "results" / "phase3").iterdir():
            if p.is_file():
                shutil.copy2(p, phase3_dir / p.name)

        # 3. Training Logs
        logs_dir = staging_dir / "training_logs"
        logs_dir.mkdir(parents=True)
        for p in (REPO_ROOT / "results" / "training_logs").glob("*.log"):
            shutil.copy2(p, logs_dir / p.name)
        for p in (REPO_ROOT / "results" / "training_logs").glob("*.json"):
            shutil.copy2(p, logs_dir / p.name)

        # 4. Training Datasets & Triplets
        data_dir = staging_dir / "data"
        data_dir.mkdir(parents=True)
        for p in (REPO_ROOT / "data").glob("triplets_*.jsonl"):
            shutil.copy2(p, data_dir / p.name)
        for p in (REPO_ROOT / "data").glob("train_queries_*.jsonl"):
            shutil.copy2(p, data_dir / p.name)
        for p in (REPO_ROOT / "data").glob("hard_negatives_*.jsonl"):
            shutil.copy2(p, data_dir / p.name)

        # 5. Configurations
        configs_dir = staging_dir / "config"
        configs_dir.mkdir(parents=True)
        for p in (REPO_ROOT / "config").glob("*.yaml"):
            shutil.copy2(p, configs_dir / p.name)

        # 6. Archive Readme & License
        readme_txt = """# Soup RAG Prototype: Research Archive Bundle (v1)

This archive preserves historical intermediate artifacts, training logs, triplet datasets, and phase reports generated during the development of the Soup RAG prototype.

## Contents:
- `reports/`: Phase 1.5 - Phase 3.1 technical and integrity audit reports.
- `phase3/`: Frozen Phase 3 multi-retriever benchmark outputs and SHA256 manifest.
- `training_logs/`: Full console and telemetry training logs for all LoRA runs.
- `data/`: Intermediate triplet datasets, hard negative mining files, and query generation outputs.
- `config/`: Full YAML training configurations matching all adapter training runs.

## Provenance:
- Base Encoders:
  - `sentence-transformers/all-MiniLM-L6-v2` (revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41)
  - `intfloat/e5-small-v2` (revision ffb93f3bd4047442299a41ebb6fa998a38507c52)
- License: MIT License (matching repository license).
"""
        (staging_dir / "ARCHIVE_README.md").write_text(readme_txt, encoding="utf-8")

        # 7. Compute SHA256 Manifest for all files in staging
        manifest_lines = []
        file_index = []
        for root, _, files in os.walk(staging_dir):
            for file in sorted(files):
                if file in ("ARCHIVE_MANIFEST.sha256", "INDEX.json"):
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(staging_dir)
                f_hash = compute_sha256(full_path)
                f_size = full_path.stat().st_size
                manifest_lines.append(f"{f_hash}  {rel_path}")
                file_index.append({"path": str(rel_path), "sha256": f_hash, "bytes": f_size})

        (staging_dir / "ARCHIVE_MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        (staging_dir / "INDEX.json").write_text(json.dumps(file_index, indent=2), encoding="utf-8")

        # 8. Create compressed tarball
        archive_name = "soup-rag-research-archive-v1.tar.gz"
        out_tar_path = ARCHIVE_OUT_DIR / archive_name
        scratch_tar_path = SCRATCH_DIR / archive_name

        print(f"Creating tarball {out_tar_path}...")
        with tarfile.open(out_tar_path, "w:gz") as tar:
            tar.add(staging_dir, arcname="soup-rag-research-archive-v1")

        shutil.copy2(out_tar_path, scratch_tar_path)
        tar_sha256 = compute_sha256(out_tar_path)
        tar_size = out_tar_path.stat().st_size
        print(f"✓ Archive created: {out_tar_path} ({tar_size / 1024 / 1024:.2f} MB, SHA256: {tar_sha256})")

        # 9. Verify archive extraction & checksums in separate test dir
        test_dir = Path(tempfile.mkdtemp(prefix="soup_archive_verify_"))
        try:
            with tarfile.open(out_tar_path, "r:gz") as tar:
                tar.extractall(test_dir)
            extracted_root = test_dir / "soup-rag-research-archive-v1"
            assert extracted_root.exists()
            assert (extracted_root / "ARCHIVE_MANIFEST.sha256").exists()

            manifest_content = (extracted_root / "ARCHIVE_MANIFEST.sha256").read_text(encoding="utf-8")
            verified_count = 0
            for line in manifest_content.splitlines():
                if not line.strip():
                    continue
                expected_h, rel_p = line.split("  ", 1)
                actual_h = compute_sha256(extracted_root / rel_p)
                assert actual_h == expected_h, f"Checksum mismatch for {rel_p} in archive!"
                verified_count += 1
            print(f"  ✓ Verified all {verified_count} files inside archive extract bit-perfect.")
        finally:
            shutil.rmtree(test_dir)

        return {
            "archive_path": str(out_tar_path),
            "archive_sha256": tar_sha256,
            "archive_size_bytes": tar_size,
            "file_count": len(file_index),
        }
    finally:
        shutil.rmtree(staging_dir)


if __name__ == "__main__":
    meta = build_archive()
    print("Archive Metadata:", json.dumps(meta, indent=2))
