"""Validate the manually authored evaluation query dataset.

Checks structural integrity of ``data/manual_queries.jsonl`` against the
corpus, audits query wording for leakage (copied headings, mechanical
template phrasing), and flags candidate cross-corpus answer overlap for
human review.

All overlap thresholds are provisional review flags, not calibrated
thresholds: flagged pairs go to the query author for the primary/overlap
decision. The validator never relabels queries.

Exit code: 0 if no errors (warnings and flags do not block), 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

ALLOCATION = {
    "adapters-and-governance": 16,
    "compliance": 8,
    "evaluation": 17,
    "peft-and-efficiency": 13,
}
ALLOCATION_TOLERANCE = 2
MIN_QUERIES = 40
MAX_QUERIES = 60
QUERY_TYPES = {
    "conceptual",
    "how_to",
    "troubleshooting",
    "config_behavior",
    "relationship",
    "command_detail",
}
EXCLUDED_SECTIONS = {"evaluation::1-0", "evaluation::0-5"}
REQUIRED_FIELDS = (
    "query_id",
    "query",
    "source_document",
    "query_type",
    "subset",
    "relevant_section_ids",
    "relevant_chunk_ids",
    "evidence_chunk_ids",
    "rationale",
    "cross_corpus_overlap",
)

# Distinctively mechanical v1 template shapes (error). Question-like phrasings
# that a human might plausibly write are warnings, not errors.
TEMPLATE_ERRORS = [
    re.compile(r"^how do you (configure|use) .+ in soup( cli)?\??$", re.IGNORECASE),
    re.compile(r"^what is .+ and how does it work in soup\??$", re.IGNORECASE),
    re.compile(r"^what does .+ do in the context of", re.IGNORECASE),
    re.compile(r"^how does soup define or handle", re.IGNORECASE),
    re.compile(r"^explain .+ in soup cli", re.IGNORECASE),
    re.compile(r"^describe the .+ feature", re.IGNORECASE),
    re.compile(r"^what backends or options does .+ support", re.IGNORECASE),
    re.compile(r"^what happens when .+ fails\??$", re.IGNORECASE),
]
TEMPLATE_WARNINGS = [
    re.compile(r"^what is the (role|purpose) of", re.IGNORECASE),
    re.compile(r"^what does .+ do\??$", re.IGNORECASE),
    re.compile(r"^when should you use", re.IGNORECASE),
]

V1_SCRIPTS_DIR = REPO_ROOT / "scripts"
V1_CONFIG_DIR = REPO_ROOT / "config"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'_-]*", text.lower())


def ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def get_base_section(chunk_id: str) -> str:
    return chunk_id.rsplit("::sub_", 1)[0]


def build_corpus_maps(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {c["chunk_id"]: c for c in chunks}
    test_docs = {c["doc_name"] for c in chunks if c["split"] == "test"}
    train_chunks = [c for c in chunks if c["split"] == "train"]
    heading_ngrams_by_doc: dict[str, set[tuple[str, ...]]] = {}
    for doc in test_docs:
        grams: set[tuple[str, ...]] = set()
        for c in chunks:
            if c["doc_name"] == doc:
                grams |= ngrams(normalize_tokens(c["heading"]), 4)
        heading_ngrams_by_doc[doc] = grams
    return {
        "by_id": by_id,
        "test_docs": test_docs,
        "train_chunks": train_chunks,
        "heading_ngrams_by_doc": heading_ngrams_by_doc,
    }


def check_query_record(
    record: dict[str, Any],
    index: int,
    maps: dict[str, Any],
    lex_threshold: float,
    max_flags_per_query: int,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    flags: list[str] = []
    qid = record.get("query_id", f"<record {index}>")

    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        errors.append(f"{qid}: missing fields {missing}")

    query = record.get("query", "")
    if not isinstance(query, str) or not query.strip():
        errors.append(f"{qid}: query is empty")

    if not re.fullmatch(r"manual_\d{3,}", str(qid)):
        errors.append(f"{qid}: query_id must match manual_NNN")

    doc = record.get("source_document")
    if doc not in maps["test_docs"]:
        errors.append(f"{qid}: source_document '{doc}' is not a held-out document")

    qtype = record.get("query_type")
    if qtype not in QUERY_TYPES:
        errors.append(f"{qid}: query_type '{qtype}' not in {sorted(QUERY_TYPES)}")

    subset = record.get("subset")
    if subset not in {"primary", "overlap"}:
        errors.append(f"{qid}: subset must be 'primary' or 'overlap'")

    sections = record.get("relevant_section_ids", [])
    chunks = record.get("relevant_chunk_ids", [])
    evidence = record.get("evidence_chunk_ids", [])
    if not isinstance(sections, list) or not sections:
        errors.append(f"{qid}: relevant_section_ids must be a non-empty list")
    if not isinstance(chunks, list) or not chunks:
        errors.append(f"{qid}: relevant_chunk_ids must be a non-empty list")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{qid}: evidence_chunk_ids must be a non-empty list")
    if errors:
        return {"query_id": qid, "errors": errors, "warnings": warnings, "flags": flags}

    for sid in sections:
        if sid in EXCLUDED_SECTIONS:
            errors.append(f"{qid}: relevant section '{sid}' is a degenerate table-artifact section (excluded)")
        base_ok = any(get_base_section(c["chunk_id"]) == sid for c in maps["by_id"].values())
        if not base_ok:
            errors.append(f"{qid}: section '{sid}' does not match any corpus chunk's base section")

    chunk_ids_seen = set()
    for cid in chunks:
        if cid in chunk_ids_seen:
            errors.append(f"{qid}: duplicate chunk id '{cid}'")
        chunk_ids_seen.add(cid)
        c = maps["by_id"].get(cid)
        if c is None:
            errors.append(f"{qid}: chunk id '{cid}' not in corpus")
            continue
        if subset == "primary" and c["split"] != "test":
            errors.append(f"{qid}: primary-subset chunk '{cid}' is not held-out (split={c['split']})")
        if get_base_section(cid) not in sections:
            errors.append(f"{qid}: chunk '{cid}' section '{get_base_section(cid)}' not in relevant_section_ids")
        if subset == "primary" and c["doc_name"] != doc:
            errors.append(f"{qid}: chunk '{cid}' belongs to '{c['doc_name']}' but source_document is '{doc}'")

    for sid in sections:
        if not any(get_base_section(cid) == sid for cid in chunks):
            errors.append(f"{qid}: section '{sid}' has no corresponding relevant chunk")

    if not set(evidence) <= set(chunks):
        errors.append(f"{qid}: evidence_chunk_ids must be a subset of relevant_chunk_ids")

    overlap = record.get("cross_corpus_overlap")
    if subset == "overlap":
        if not isinstance(overlap, dict) or not overlap.get("train_chunk_ids"):
            errors.append(f"{qid}: overlap subset requires cross_corpus_overlap.train_chunk_ids")
        else:
            for cid in overlap["train_chunk_ids"]:
                c = maps["by_id"].get(cid)
                if c is None:
                    errors.append(f"{qid}: overlap train chunk '{cid}' not in corpus")
                elif c["split"] != "train":
                    errors.append(f"{qid}: overlap chunk '{cid}' is not a training-document chunk")
            if not any(maps["by_id"].get(cid, {}).get("split") == "test" for cid in chunks):
                errors.append(f"{qid}: overlap query must also label at least one held-out chunk")
    elif subset == "primary" and overlap not in (None, {}):
        warnings.append(f"{qid}: primary subset has a non-null cross_corpus_overlap field")

    if not record.get("rationale", "").strip():
        warnings.append(f"{qid}: rationale is empty")

    # --- wording audit ---
    if isinstance(query, str) and query.strip():
        q_tokens = normalize_tokens(query)
        if doc in maps["heading_ngrams_by_doc"]:
            q_grams = ngrams(q_tokens, 4)
            hits = q_grams & maps["heading_ngrams_by_doc"][doc]
            if hits:
                errors.append(
                    f"{qid}: query copies a heading phrase of '{doc}': "
                    + "; ".join(" ".join(g) for g in sorted(hits))
                )
        for pat in TEMPLATE_ERRORS:
            if pat.search(query):
                errors.append(f"{qid}: query matches mechanical v1 template pattern: {pat.pattern}")
        for pat in TEMPLATE_WARNINGS:
            if pat.search(query):
                warnings.append(f"{qid}: query resembles a v1 template shape: {pat.pattern} (review)")

        # --- provisional cross-corpus overlap flags (review only, never errors) ---
        q_set = set(q_tokens)
        for c in maps["train_chunks"]:
            c_tokens = normalize_tokens(c["heading_prefix"] + " " + c["text"])
            c_set = set(c_tokens)
            inter = q_set & c_set
            if not inter:
                continue
            jacc = len(inter) / len(q_set | c_set)
            if jacc >= lex_threshold:
                flags.append(f"{qid}: lexical overlap {jacc:.2f} with train chunk '{c['chunk_id']}'")
        if len(flags) > max_flags_per_query:
            flags = flags[:max_flags_per_query] + [f"{qid}: … {len(flags) - max_flags_per_query} more overlap flags suppressed"]

    return {"query_id": qid, "errors": errors, "warnings": warnings, "flags": flags}


def scan_v1_non_coupling(scripts_dir: Path, config_dir: Path) -> list[str]:
    """v1 training/eval scripts must never reference the manual query dataset."""
    errors = []
    needle = "manual_queries"
    for path in list(scripts_dir.glob("*.py")) + list(config_dir.glob("*.yaml")):
        if path.name == "validate_manual_queries.py":
            continue
        text = path.read_text(encoding="utf-8")
        if needle in text:
            errors.append(f"{path}: references 'manual_queries' (v1 coupling risk)")
    return errors


def semantic_overlap_flags(
    records: list[dict[str, Any]],
    maps: dict[str, Any],
    threshold: float,
    max_flags_per_query: int,
) -> tuple[list[str], str | None]:
    """Embedding-based cross-corpus overlap flags (provisional, review only).

    Uses the frozen MiniLM retriever. Returns (flags, note); note is None on
    success or an explanation when the encoder is unavailable.
    """
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parent))
    try:
        from retrievers import MINILM_MODEL_ID, MINILM_REVISION, DenseRetriever
    except Exception as exc:  # heavy deps unavailable
        return [], f"semantic stage unavailable: {exc}"

    try:
        encoder = DenseRetriever(
            "mini_lm_frozen",
            MINILM_MODEL_ID,
            revision=MINILM_REVISION,
            max_length=256,
        )
    except Exception as exc:
        return [], f"semantic stage unavailable: {exc}"

    train_chunks = maps["train_chunks"]
    queries = [r.get("query", "") for r in records]
    try:
        query_vecs = encoder.encode(queries)
        chunk_vecs = encoder.encode_corpus(train_chunks)
    except Exception as exc:
        return [], f"semantic stage failed: {exc}"

    flags: list[str] = []
    for i, record in enumerate(records):
        qid = record.get("query_id")
        sims = chunk_vecs @ query_vecs[i]
        order = sorted(range(len(sims)), key=lambda j: -sims[j])
        hits = [
            f"{qid}: semantic similarity {sims[j]:.2f} with train chunk '{train_chunks[j]['chunk_id']}'"
            for j in order
            if float(sims[j]) >= threshold
        ][:max_flags_per_query]
        if hits:
            flags.extend(hits)
    return flags, None


def validate(
    corpus_path: Path,
    queries_path: Path,
    scripts_dir: Path,
    config_dir: Path,
    lex_threshold: float = 0.25,
    max_flags_per_query: int = 5,
    check_globals: bool = True,
    semantic: bool = False,
    sem_threshold: float = 0.65,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    flags: list[str] = []
    per_record: list[dict[str, Any]] = []

    if not queries_path.exists():
        return {
            "valid": False,
            "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "n_queries": 0,
            "per_doc_counts": {},
            "note": f"queries file not found: {queries_path}",
            "errors": [f"queries file not found: {queries_path}"],
            "warnings": [],
            "flags": [],
            "per_record": [],
        }

    chunks = load_jsonl(corpus_path)
    maps = build_corpus_maps(chunks)
    records = load_jsonl(queries_path)

    errors += scan_v1_non_coupling(scripts_dir, config_dir)

    if check_globals and not (MIN_QUERIES <= len(records) <= MAX_QUERIES):
        errors.append(f"query count {len(records)} outside [{MIN_QUERIES}, {MAX_QUERIES}]")

    per_doc: dict[str, int] = {}
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    for i, record in enumerate(records):
        qid = record.get("query_id")
        if qid in seen_ids:
            errors.append(f"duplicate query_id '{qid}'")
        seen_ids.add(qid)
        norm = " ".join(normalize_tokens(record.get("query", "")))
        if norm and norm in seen_texts:
            errors.append(f"{qid}: duplicate query text")
        seen_texts.add(norm)
        doc = record.get("source_document")
        if doc:
            per_doc[doc] = per_doc.get(doc, 0) + 1
        result = check_query_record(record, i, maps, lex_threshold, max_flags_per_query)
        per_record.append(result)
        errors += result["errors"]
        warnings += result["warnings"]
        flags += result["flags"]

    if check_globals:
        for doc, target in ALLOCATION.items():
            count = per_doc.get(doc, 0)
            if abs(count - target) > ALLOCATION_TOLERANCE:
                errors.append(
                    f"allocation for '{doc}': {count} queries, target {target} (tolerance ±{ALLOCATION_TOLERANCE})"
                )

    semantic_note = "semantic stage not requested"
    if semantic:
        sem_flags, semantic_note = semantic_overlap_flags(
            records, maps, sem_threshold, max_flags_per_query
        )
        flags += sem_flags

    return {
        "valid": not errors,
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "n_queries": len(records),
        "per_doc_counts": per_doc,
        "errors": errors,
        "warnings": warnings,
        "flags": flags,
        "per_record": per_record,
        "semantic_stage": semantic_note,
        "note": (
            "Overlap flags use provisional review thresholds "
            f"(lexical Jaccard >= {lex_threshold}"
            + (f", semantic cosine >= {sem_threshold}" if semantic else "")
            + "); they are review material, "
            "not calibrated thresholds, and never relabel queries."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the manual evaluation query dataset")
    parser.add_argument("--corpus", type=Path, default=DATA_DIR / "corpus.jsonl")
    parser.add_argument("--queries", type=Path, default=DATA_DIR / "manual_queries.jsonl")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "manual_queries_validation_report.json")
    parser.add_argument("--scripts-dir", type=Path, default=V1_SCRIPTS_DIR)
    parser.add_argument("--config-dir", type=Path, default=V1_CONFIG_DIR)
    parser.add_argument("--lex-overlap-threshold", type=float, default=0.25,
                        help="provisional lexical flag threshold (uncalibrated)")
    parser.add_argument("--max-flags-per-query", type=int, default=5)
    parser.add_argument("--semantic", action="store_true",
                        help="run the optional embedding-based overlap stage (frozen MiniLM)")
    parser.add_argument("--sem-overlap-threshold", type=float, default=0.65,
                        help="provisional semantic flag threshold (uncalibrated)")
    args = parser.parse_args()

    report = validate(
        corpus_path=args.corpus,
        queries_path=args.queries,
        scripts_dir=args.scripts_dir,
        config_dir=args.config_dir,
        lex_threshold=args.lex_overlap_threshold,
        max_flags_per_query=args.max_flags_per_query,
        semantic=args.semantic,
        sem_threshold=args.sem_overlap_threshold,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"checked {report['n_queries']} queries")
    print(f"errors: {len(report['errors'])} | warnings: {len(report['warnings'])} | overlap flags: {len(report['flags'])}")
    for e in report["errors"]:
        print(f"  ERROR: {e}")
    for w in report["warnings"]:
        print(f"  WARN:  {w}")
    for fl in report["flags"]:
        print(f"  FLAG:  {fl}")
    print(f"report -> {args.output}")
    print("VALID" if report["valid"] else "INVALID")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
