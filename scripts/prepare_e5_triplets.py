"""Prepare derived E5-specific triplet dataset from Experiment B triplets.

Applies 'query: ' prefix to anchors and 'passage: ' prefix to positive and negative passages.
Preserves original dataset, validates record counts, and verifies no double-prefixing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = REPO_ROOT / "data" / "triplets_exp_b_v1_5.jsonl"
DST_PATH = REPO_ROOT / "data" / "triplets_e5_exp_b.jsonl"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def transform_triplets() -> dict[str, str | int]:
    src_bytes = SRC_PATH.read_bytes()
    src_sha256 = hashlib.sha256(src_bytes).hexdigest()
    lines = [
        json.loads(line)
        for line in src_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]

    print(f"Read {len(lines)} records from {SRC_PATH.name} (SHA256: {src_sha256})")
    assert len(lines) == 2475, f"Expected 2475 records, got {len(lines)}"

    transformed = []
    for idx, r in enumerate(lines):
        anchor_text = r["anchor"]
        pos_text = r["positive"]
        neg_text = r["negative"]

        # Ensure no existing prefixes
        if anchor_text.startswith("query: "):
            raise ValueError(f"Record {idx} anchor already has 'query: ' prefix!")
        if pos_text.startswith("passage: "):
            raise ValueError(f"Record {idx} positive already has 'passage: ' prefix!")
        if neg_text.startswith("passage: "):
            raise ValueError(f"Record {idx} negative already has 'passage: ' prefix!")

        transformed.append({
            "anchor": f"query: {anchor_text}",
            "positive": f"passage: {pos_text}",
            "negative": f"passage: {neg_text}",
        })

    # Write output
    with open(DST_PATH, "w", encoding="utf-8") as f:
        for rec in transformed:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    dst_sha256 = compute_sha256(DST_PATH)
    print(f"Wrote {len(transformed)} records to {DST_PATH.name} (SHA256: {dst_sha256})")

    # Verification checks
    check_lines = [
        json.loads(line)
        for line in DST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(check_lines) == 2475
    for idx, rec in enumerate(check_lines):
        assert rec["anchor"].startswith("query: "), f"Missing query: prefix at {idx}"
        assert not rec["anchor"].startswith("query: query: "), f"Duplicate query prefix at {idx}"
        assert rec["positive"].startswith("passage: "), f"Missing passage: prefix at {idx}"
        assert not rec["positive"].startswith("passage: passage: "), f"Duplicate passage prefix at {idx}"
        assert rec["negative"].startswith("passage: "), f"Missing passage: prefix at {idx}"
        assert not rec["negative"].startswith("passage: passage: "), f"Duplicate passage prefix at {idx}"

    print("  ✓ All 2,475 transformed records verified with exactly one prefix.")
    return {
        "source_path": str(SRC_PATH.relative_to(REPO_ROOT)),
        "source_sha256": src_sha256,
        "dest_path": str(DST_PATH.relative_to(REPO_ROOT)),
        "dest_sha256": dst_sha256,
        "triplet_count": len(transformed),
    }


if __name__ == "__main__":
    meta = transform_triplets()
    print("Metadata:", json.dumps(meta, indent=2))
