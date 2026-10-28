"""Prepare the retrieval corpus from Soup CLI documentation.

Reads the 12 Markdown files, splits on ATX headings using Soup's existing
``split_markdown_by_headings``, sub-splits oversized sections to fit within
the MiniLM tokenizer budget, and writes a canonical JSONL corpus plus
metadata.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_DOCS = REPO_ROOT.parent / "scratch" / "upstream_soup" / "docs"
DATA_DIR = REPO_ROOT / "data"

# ---------------------------------------------------------------------------
# Add upstream src to path so we can reuse split_markdown_by_headings
# ---------------------------------------------------------------------------

_upstream_src = str(REPO_ROOT.parent / "scratch" / "upstream_soup" / "src")
if _upstream_src not in sys.path:
    sys.path.insert(0, _upstream_src)

from soup_cli.utils.data_pipeline import split_markdown_by_headings  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# MiniLM-L6-v2 was trained with max_seq_length=256.
# Target ~220 tokens for chunk body to leave room for heading prefix + specials.
MAX_CHUNK_TOKENS = 220
OVERLAP_TOKENS = 28
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Document split: 8 train / 4 held-out test
TRAIN_DOCS = [
    "backends-and-ops.md",
    "commands.md",
    "data.md",
    "models.md",
    "performance-and-quantization.md",
    "README.md",
    "serving-and-export.md",
    "training.md",
]

TEST_DOCS = [
    "adapters-and-governance.md",
    "compliance.md",
    "evaluation.md",
    "peft-and-efficiency.md",
]


def _slugify(text: str | None) -> str:
    """Convert heading text to a stable slug."""
    if text is None:
        return "preamble"
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-") or "untitled"


def _content_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_tokenizer():
    """Load the MiniLM tokenizer (lazy)."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_ID)


def _count_tokens(tokenizer, text: str) -> int:
    """Count wordpiece tokens (without special tokens)."""
    return len(tokenizer.encode(text, add_special_tokens=False))


def _split_on_paragraphs(text: str) -> list[str]:
    """Split text on double newlines (paragraph boundaries)."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_on_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries (period/question/exclamation
    followed by space or newline)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _recursive_subsplit(
    text: str,
    tokenizer,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split text into sub-chunks that fit within the token budget.

    Strategy: paragraph boundaries first, then sentence boundaries,
    then hard token-based splitting as last resort.
    """
    token_count = _count_tokens(tokenizer, text)
    if token_count <= max_tokens:
        return [text]

    # Try paragraph splitting first
    paragraphs = _split_on_paragraphs(text)
    if len(paragraphs) > 1:
        return _merge_segments(paragraphs, tokenizer, max_tokens, overlap_tokens)

    # Try sentence splitting
    sentences = _split_on_sentences(text)
    if len(sentences) > 1:
        return _merge_segments(sentences, tokenizer, max_tokens, overlap_tokens)

    # Last resort: hard token split
    return _hard_token_split(text, tokenizer, max_tokens, overlap_tokens)


def _merge_segments(
    segments: list[str],
    tokenizer,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Merge small segments into chunks that fit the token budget,
    with overlap between consecutive chunks."""
    chunks: list[str] = []
    current_segments: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = _count_tokens(tokenizer, seg)

        # If this single segment exceeds the limit, recursively split it
        if seg_tokens > max_tokens:
            # Flush current
            if current_segments:
                chunks.append("\n\n".join(current_segments))
                current_segments = []
                current_tokens = 0
            # Recurse on the oversized segment
            sub_chunks = _recursive_subsplit(
                seg, tokenizer, max_tokens, overlap_tokens
            )
            chunks.extend(sub_chunks)
            continue

        if current_tokens + seg_tokens > max_tokens and current_segments:
            # Flush and start new chunk with overlap
            chunks.append("\n\n".join(current_segments))

            # Overlap: keep last segment(s) up to overlap_tokens
            overlap_segs: list[str] = []
            overlap_count = 0
            for prev_seg in reversed(current_segments):
                prev_tokens = _count_tokens(tokenizer, prev_seg)
                if overlap_count + prev_tokens > overlap_tokens:
                    break
                overlap_segs.insert(0, prev_seg)
                overlap_count += prev_tokens

            current_segments = overlap_segs + [seg]
            current_tokens = overlap_count + seg_tokens
        else:
            current_segments.append(seg)
            current_tokens += seg_tokens

    if current_segments:
        chunks.append("\n\n".join(current_segments))

    return chunks


def _hard_token_split(
    text: str,
    tokenizer,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split text by token boundaries when no natural boundaries exist."""
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks: list[str] = []
    start = 0
    while start < len(token_ids):
        end = min(start + max_tokens, len(token_ids))
        chunk_ids = token_ids[start:end]
        chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True)
        chunks.append(chunk_text.strip())
        start = end - overlap_tokens if end < len(token_ids) else end
    return chunks


def prepare_corpus() -> dict[str, Any]:
    """Main entry point: prepare the canonical corpus JSONL and metadata."""
    tokenizer = _load_tokenizer()

    md_files = sorted(UPSTREAM_DOCS.glob("*.md"))
    if len(md_files) != 12:
        raise RuntimeError(
            f"Expected 12 markdown files, found {len(md_files)}: "
            f"{[f.name for f in md_files]}"
        )

    all_chunks: list[dict[str, Any]] = []
    source_manifest: list[dict[str, str]] = []
    section_lengths_before: list[int] = []
    chunk_lengths_after: list[int] = []

    for md_file in md_files:
        raw_bytes = md_file.read_bytes()
        text = raw_bytes.decode("utf-8")
        content_hash = _content_sha256(raw_bytes)
        doc_name = md_file.stem
        split = "train" if md_file.name in TRAIN_DOCS else "test"

        source_manifest.append(
            {
                "file": md_file.name,
                "doc_name": doc_name,
                "split": split,
                "content_sha256": content_hash,
                "size_bytes": len(raw_bytes),
            }
        )

        sections = split_markdown_by_headings(text)
        section_counter: dict[str, int] = {}

        for section_idx, section in enumerate(sections):
            heading = section["section"]
            level = section["level"]
            body = section["text"]

            if not body.strip():
                continue

            slug = _slugify(heading)
            # Handle duplicate slugs within a document
            if slug in section_counter:
                section_counter[slug] += 1
                slug = f"{slug}-{section_counter[slug]}"
            else:
                section_counter[slug] = 0

            # Build heading prefix for embedding context
            heading_prefix = f"{doc_name}: {heading}" if heading else doc_name

            # Measure section length before splitting
            full_text = f"{heading_prefix}\n\n{body}"
            section_token_count = _count_tokens(tokenizer, full_text)
            section_lengths_before.append(section_token_count)

            # Sub-split if needed (budget is for body; prefix is prepended later)
            prefix_tokens = _count_tokens(tokenizer, heading_prefix + "\n\n")
            body_budget = MAX_CHUNK_TOKENS - prefix_tokens
            if body_budget < 50:
                # Heading prefix too long; use the full budget
                body_budget = MAX_CHUNK_TOKENS

            sub_chunks = _recursive_subsplit(
                body, tokenizer, body_budget, OVERLAP_TOKENS
            )

            for sub_idx, sub_text in enumerate(sub_chunks):
                if len(sub_chunks) == 1:
                    chunk_id = f"{doc_name}::{slug}"
                else:
                    chunk_id = f"{doc_name}::{slug}::sub_{sub_idx:03d}"

                chunk_record = {
                    "chunk_id": chunk_id,
                    "doc_name": doc_name,
                    "source_file": md_file.name,
                    "split": split,
                    "heading": heading,
                    "heading_level": level,
                    "heading_prefix": heading_prefix,
                    "text": sub_text,
                    "section_index": section_idx,
                }

                # Measure final chunk length
                embed_text = f"{heading_prefix}\n\n{sub_text}"
                final_tokens = _count_tokens(tokenizer, embed_text)
                chunk_record["token_count"] = final_tokens
                chunk_lengths_after.append(final_tokens)

                all_chunks.append(chunk_record)

    # Write corpus
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    corpus_path = DATA_DIR / "corpus.jsonl"
    with open(corpus_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Write source manifest
    manifest_path = DATA_DIR / "source_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "upstream_commit": "8ab26641ed34e724018e696a93a06460f26c153e",
                "model_id": MODEL_ID,
                "max_chunk_tokens": MAX_CHUNK_TOKENS,
                "overlap_tokens": OVERLAP_TOKENS,
                "files": source_manifest,
            },
            f,
            indent=2,
        )

    # Write document split
    split_path = DATA_DIR / "document_split.json"
    with open(split_path, "w", encoding="utf-8") as f:
        json.dump({"train": TRAIN_DOCS, "test": TEST_DOCS}, f, indent=2)

    # Compute corpus fingerprint
    sorted_pairs = sorted(
        [(m["file"], m["content_sha256"]) for m in source_manifest]
    )
    fingerprint_input = json.dumps(sorted_pairs, sort_keys=True).encode()
    corpus_fingerprint = _content_sha256(fingerprint_input)

    # Statistics
    import statistics

    stats = {
        "total_files": len(source_manifest),
        "train_files": len(TRAIN_DOCS),
        "test_files": len(TEST_DOCS),
        "total_chunks": len(all_chunks),
        "train_chunks": sum(1 for c in all_chunks if c["split"] == "train"),
        "test_chunks": sum(1 for c in all_chunks if c["split"] == "test"),
        "corpus_fingerprint": corpus_fingerprint,
        "section_lengths_before_split": {
            "count": len(section_lengths_before),
            "min": min(section_lengths_before),
            "median": statistics.median(section_lengths_before),
            "p75": sorted(section_lengths_before)[
                int(0.75 * len(section_lengths_before))
            ],
            "p90": sorted(section_lengths_before)[
                int(0.90 * len(section_lengths_before))
            ],
            "max": max(section_lengths_before),
            "exceeding_256": sum(1 for x in section_lengths_before if x > 256),
            "exceeding_512": sum(1 for x in section_lengths_before if x > 512),
        },
        "chunk_lengths_after_split": {
            "count": len(chunk_lengths_after),
            "min": min(chunk_lengths_after),
            "median": statistics.median(chunk_lengths_after),
            "p75": sorted(chunk_lengths_after)[
                int(0.75 * len(chunk_lengths_after))
            ],
            "p90": sorted(chunk_lengths_after)[
                int(0.90 * len(chunk_lengths_after))
            ],
            "max": max(chunk_lengths_after),
            "exceeding_256": sum(1 for x in chunk_lengths_after if x > 256),
        },
    }

    stats_path = REPO_ROOT / "results" / "corpus_stats.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats


def main() -> None:
    print("Preparing corpus...")
    stats = prepare_corpus()
    print(f"\nCorpus prepared:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Train files: {stats['train_files']}, Test files: {stats['test_files']}")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Train chunks: {stats['train_chunks']}, Test chunks: {stats['test_chunks']}")
    print(f"  Corpus fingerprint: {stats['corpus_fingerprint']}")
    print(f"\nSection lengths BEFORE sub-splitting:")
    before = stats["section_lengths_before_split"]
    print(f"  Count: {before['count']}")
    print(f"  Min: {before['min']}, Median: {before['median']}, Max: {before['max']}")
    print(f"  P75: {before['p75']}, P90: {before['p90']}")
    print(f"  Exceeding 256 tokens: {before['exceeding_256']}/{before['count']}")
    print(f"  Exceeding 512 tokens: {before['exceeding_512']}/{before['count']}")
    print(f"\nChunk lengths AFTER sub-splitting:")
    after = stats["chunk_lengths_after_split"]
    print(f"  Count: {after['count']}")
    print(f"  Min: {after['min']}, Median: {after['median']}, Max: {after['max']}")
    print(f"  P75: {after['p75']}, P90: {after['p90']}")
    print(f"  Exceeding 256 tokens: {after['exceeding_256']}/{after['count']}")


if __name__ == "__main__":
    main()
