r"""Prepare the expanded training corpus for embedding adapter retraining.

Combines the 8 original training documents from data/corpus.jsonl with the 23
curated candidate documentation files from data/candidate_docs/ (pinned to
upstream commit 595173f73eb45399aeb4997bab44642827b31799).

Writes data/training_corpus.jsonl and data/training_source_manifest.json.
Guarantees zero modification to data/corpus.jsonl and zero inclusion of the
4 held-out evaluation documents.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from markdown_splitter import split_markdown_by_headings

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
CANDIDATE_DIR = DATA_DIR / "candidate_docs"

MAX_CHUNK_TOKENS = 220
OVERLAP_TOKENS = 28
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
UPSTREAM_COMMIT = "595173f73eb45399aeb4997bab44642827b31799"

HELD_OUT_TEST_DOCS = {
    "adapters-and-governance.md",
    "compliance.md",
    "evaluation.md",
    "peft-and-efficiency.md",
}


def _slugify(text: str | None) -> str:
    """Convert heading text to a stable slug."""
    if text is None:
        return "preamble"
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-") or "untitled"


def _content_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_ID)


def _count_tokens(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def _split_on_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_on_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _hard_token_split(text: str, tokenizer, max_tokens: int, overlap_tokens: int) -> list[str]:
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks: list[str] = []
    start = 0
    step = max(max_tokens - overlap_tokens, 1)
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_text = tokenizer.decode(tokens[start:end], skip_special_tokens=True).strip()
        if chunk_text:
            chunks.append(chunk_text)
        start += step
    return chunks or [text]


def _recursive_subsplit(
    text: str,
    tokenizer,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    token_count = _count_tokens(tokenizer, text)
    if token_count <= max_tokens:
        return [text]

    paragraphs = _split_on_paragraphs(text)
    if len(paragraphs) > 1:
        return _merge_segments(paragraphs, tokenizer, max_tokens, overlap_tokens)

    sentences = _split_on_sentences(text)
    if len(sentences) > 1:
        return _merge_segments(sentences, tokenizer, max_tokens, overlap_tokens)

    return _hard_token_split(text, tokenizer, max_tokens, overlap_tokens)


def _merge_segments(
    segments: list[str],
    tokenizer,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    chunks: list[str] = []
    current_segments: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = _count_tokens(tokenizer, seg)

        if seg_tokens > max_tokens:
            if current_segments:
                chunks.append("\n\n".join(current_segments))
                current_segments = []
                current_tokens = 0
            sub_chunks = _recursive_subsplit(
                seg, tokenizer, max_tokens, overlap_tokens
            )
            chunks.extend(sub_chunks)
            continue

        if current_tokens + seg_tokens > max_tokens and current_segments:
            chunks.append("\n\n".join(current_segments))
            overlap_segs: list[str] = []
            overlap_count = 0
            for prev_seg in reversed(current_segments):
                prev_tokens = _count_tokens(tokenizer, prev_seg)
                if overlap_count + prev_tokens > overlap_tokens:
                    break
                overlap_segs.insert(0, prev_seg)
                overlap_count += prev_tokens
            current_segments = list(overlap_segs)
            current_tokens = overlap_count

        current_segments.append(seg)
        current_tokens += seg_tokens

    if current_segments:
        chunks.append("\n\n".join(current_segments))
    return chunks


def prepare_training_corpus() -> dict[str, Any]:
    tokenizer = _load_tokenizer()

    # 1. Load canonical training chunks from existing corpus.jsonl (8 docs, split == 'train')
    existing_corpus_path = DATA_DIR / "corpus.jsonl"
    if not existing_corpus_path.exists():
        raise FileNotFoundError(f"Missing {existing_corpus_path}")

    all_chunks: list[dict[str, Any]] = []
    existing_train_docs = set()

    with open(existing_corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["split"] == "train":
                # Safety check against held-out docs
                if c["source_file"] in HELD_OUT_TEST_DOCS:
                    raise ValueError(f"Held-out test doc found in train split: {c['source_file']}")
                all_chunks.append(c)
                existing_train_docs.add(c["source_file"])

    print(f"Loaded {len(all_chunks)} existing training chunks from {len(existing_train_docs)} documents.")

    # 2. Chunk candidate documents from data/candidate_docs
    if not CANDIDATE_DIR.exists():
        raise FileNotFoundError(f"Missing {CANDIDATE_DIR}")

    cand_files = sorted(list(CANDIDATE_DIR.glob("**/*.md")))
    if len(cand_files) != 23:
        raise ValueError(f"Expected 23 candidate files in {CANDIDATE_DIR}, found {len(cand_files)}")

    candidate_records: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []

    for fpath in cand_files:
        rel_path = fpath.relative_to(CANDIDATE_DIR).as_posix()
        raw_bytes = fpath.read_bytes()
        content_sha = _content_sha256(raw_bytes)
        text = raw_bytes.decode("utf-8")
        doc_stem = fpath.stem

        # Verify not in held-out
        if rel_path in HELD_OUT_TEST_DOCS or doc_stem in HELD_OUT_TEST_DOCS:
            raise ValueError(f"Candidate matches held-out doc: {rel_path}")

        sections = split_markdown_by_headings(text)
        section_counter: dict[str, int] = {}
        doc_chunk_count = 0
        doc_token_count = 0

        for section_idx, section in enumerate(sections):
            heading = section["section"]
            level = section["level"]
            body = section["text"]
            if not body.strip():
                continue

            slug = _slugify(heading)
            if slug in section_counter:
                section_counter[slug] += 1
                slug = f"{slug}-{section_counter[slug]}"
            else:
                section_counter[slug] = 0

            heading_prefix = f"{doc_stem}: {heading}" if heading else doc_stem
            prefix_tokens = _count_tokens(tokenizer, heading_prefix + "\n\n")
            body_budget = MAX_CHUNK_TOKENS - prefix_tokens
            if body_budget < 50:
                body_budget = MAX_CHUNK_TOKENS

            sub_chunks = _recursive_subsplit(body, tokenizer, body_budget, OVERLAP_TOKENS)

            for sub_idx, sub_text in enumerate(sub_chunks):
                if len(sub_chunks) == 1:
                    chunk_id = f"{doc_stem}::{slug}"
                else:
                    chunk_id = f"{doc_stem}::{slug}::sub_{sub_idx:03d}"

                embed_text = f"{heading_prefix}\n\n{sub_text}"
                final_tokens = _count_tokens(tokenizer, embed_text)

                chunk_rec = {
                    "chunk_id": chunk_id,
                    "doc_name": doc_stem,
                    "source_file": rel_path,
                    "split": "train",
                    "heading": heading,
                    "heading_level": level,
                    "heading_prefix": heading_prefix,
                    "text": sub_text,
                    "section_index": section_idx,
                    "token_count": final_tokens,
                }
                candidate_records.append(chunk_rec)
                doc_chunk_count += 1
                doc_token_count += final_tokens

        manifest_entries.append({
            "file": rel_path,
            "doc_name": doc_stem,
            "content_sha256": content_sha,
            "size_bytes": len(raw_bytes),
            "chunks": doc_chunk_count,
            "tokens": doc_token_count,
            "split": "train",
            "source_type": "upstream_candidate",
        })

    print(f"Generated {len(candidate_records)} chunks from {len(cand_files)} candidate documents.")

    # 3. Combine and verify zero ID collision
    all_chunks.extend(candidate_records)
    chunk_ids = [c["chunk_id"] for c in all_chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        duplicates = [cid for cid in chunk_ids if chunk_ids.count(cid) > 1]
        raise ValueError(f"Duplicate chunk IDs found: {set(duplicates)}")

    # 4. Write data/training_corpus.jsonl
    training_corpus_path = DATA_DIR / "training_corpus.jsonl"
    with open(training_corpus_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # 5. Write data/training_source_manifest.json
    manifest_path = DATA_DIR / "training_source_manifest.json"
    manifest_data = {
        "upstream_commit": UPSTREAM_COMMIT,
        "model_id": MODEL_ID,
        "max_chunk_tokens": MAX_CHUNK_TOKENS,
        "overlap_tokens": OVERLAP_TOKENS,
        "total_documents": len(existing_train_docs) + len(cand_files),
        "existing_training_docs": sorted(list(existing_train_docs)),
        "candidate_docs": manifest_entries,
        "total_chunks": len(all_chunks),
        "total_tokens": sum(c["token_count"] for c in all_chunks),
        "held_out_docs_excluded": sorted(list(HELD_OUT_TEST_DOCS)),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    stats = {
        "total_documents": len(existing_train_docs) + len(cand_files),
        "existing_docs": len(existing_train_docs),
        "new_candidate_docs": len(cand_files),
        "total_chunks": len(all_chunks),
        "existing_train_chunks": len(all_chunks) - len(candidate_records),
        "candidate_chunks": len(candidate_records),
        "total_tokens": sum(c["token_count"] for c in all_chunks),
        "max_chunk_token_count": max(c["token_count"] for c in all_chunks),
        "min_chunk_token_count": min(c["token_count"] for c in all_chunks),
    }

    stats_path = REPO_ROOT / "results" / "training_corpus_stats.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return stats


def main() -> None:
    print("Preparing expanded training corpus...")
    stats = prepare_training_corpus()
    print("\nExpanded Training Corpus Ready:")
    print(f"  Total Documents: {stats['total_documents']} (8 existing + 23 candidate)")
    print(f"  Total Chunks: {stats['total_chunks']} (761 existing + {stats['candidate_chunks']} candidate)")
    print(f"  Total Tokens: {stats['total_tokens']:,}")
    print(f"  Chunk Tokens: min={stats['min_chunk_token_count']}, max={stats['max_chunk_token_count']}")


if __name__ == "__main__":
    main()
