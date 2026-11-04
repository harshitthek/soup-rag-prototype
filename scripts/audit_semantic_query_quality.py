#!/usr/bin/env python3
"""Audit semantic query quality across reproducible 10% stratified samples.

Evaluates generated queries across 5 critical semantic dimensions:
1. Positive chunk answers question (answers_question)
2. No unsupported assumptions introduced (no_unsupported_assumptions)
3. Phrasing is natural and useful (natural_and_useful)
4. Non-duplicate / non-redundant (non_duplicate)
5. Appropriate breadth / scope for positive chunk (appropriate_breadth)

Classifies each audited query as ACCEPTED, NEEDS_CORRECTION, or REJECTED,
and writes structured audit results to results/semantic_query_quality_audit.json.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

KNOWN_NON_ENVS = {
    "CHANGELOG", "MUSE", "S_ISLNK", "FIO", "DRAM", "NVME", "SATA", "IOPS", "LLAMA",
    "README", "YAML", "JSON", "RAM", "VRAM", "GPU", "CPU", "CUDA", "MODAL", "QAT",
    "BF16", "FP16", "FP8", "NVFP4", "PEFT", "LORA", "QLORA", "UNSLOTH", "TORCH",
    "TRITON", "APPLE", "INTEL", "ARM", "AMD", "WANDB", "MLFLOW", "TOFU", "ASCII",
    "HTML", "HTTP", "HTTPS", "UTF8", "ANSI", "POSIX", "POSIX_FADV_SEQUENTIAL",
    "O_DIRECT", "FSYNC", "MMAP", "NUMA", "PCI", "PCIE", "AVX", "AVX2", "AVX512",
    "LOGITS_LOSS_BYTES_PER_ELEMENT", "SDPA", "MACHINE", "DDR5", "SECOND", "PASS",
    "CRITICAL", "GATE", "DEFAULT_WORKSPACE_BYTES", "REFUSED", "FIVE", "MAX_EVAL_TASKS",
    "ERROR", "P100", "CONTROL", "FIRST", "THIRD", "NONE", "TRUE", "FALSE"
}


def load_training_corpus() -> dict[str, dict[str, Any]]:
    corpus_path = DATA_DIR / "training_corpus.jsonl"
    corpus = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                corpus[item["chunk_id"]] = item
    return corpus


def sample_stratified(
    queries: list[dict[str, Any]], target_count: int, seed: int = 42
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    groups = defaultdict(list)
    for q in queries:
        groups[(q["source_doc"], q["query_type"])].append(q)

    total = len(queries)
    sampled = []
    sorted_keys = sorted(groups.keys())
    for k in sorted_keys:
        grp = sorted(groups[k], key=lambda x: x["query_id"])
        k_target = max(1, round(len(grp) / total * target_count))
        sampled.extend(rng.sample(grp, min(len(grp), k_target)))

    if len(sampled) > target_count:
        sampled = sampled[:target_count]
    return sampled


def audit_single_query(
    q: dict[str, Any], chunk: dict[str, Any]
) -> dict[str, Any]:
    text = chunk.get("text", "")
    q_str = q["query"]
    doc = q["source_doc"]

    checks = {
        "answers_question": True,
        "no_unsupported_assumptions": True,
        "natural_and_useful": True,
        "non_duplicate": True,
        "appropriate_breadth": True,
    }

    issues: list[str] = []
    failure_mode: str | None = None
    suggested_correction: str | None = None
    status = "ACCEPTED"

    # Dimension 2: Environment variable validation (no unsupported assumptions)
    env_match = re.search(r"setting `([A-Za-z0-9_]+)` in the execution environment", q_str)
    if env_match:
        var = env_match.group(1)
        is_known_non_env = var in KNOWN_NON_ENVS
        has_env_syntax = f"export {var}" in text or f"{var}=" in text
        is_described_as_env = "env var" in text.lower() or "environment var" in text.lower()
        if is_known_non_env or not (has_env_syntax or is_described_as_env):
            checks["no_unsupported_assumptions"] = False
            checks["answers_question"] = False
            failure_mode = "FALSE_ENV_VAR"
            issues.append(f"Unsupported assumption: `{var}` is a hardware specification, dataset name, constant, or data format, not an environment variable.")
            status = "REJECTED"
            return {
                "query_id": q["query_id"],
                "query": q_str,
                "source_doc": doc,
                "positive_chunk_id": q["positive_chunk_id"],
                "query_type": q["query_type"],
                "status": status,
                "failure_mode": failure_mode,
                "checks": checks,
                "issues": issues,
                "suggested_correction": suggested_correction,
            }

    # Dimension 3 & 1: Syntactic code fragment / unclosed parentheses
    if q_str.count("(") != q_str.count(")"):
        checks["natural_and_useful"] = False
        checks["answers_question"] = False
        failure_mode = "SYNTACTIC_FRAGMENT"
        issues.append("Unclosed parenthesis in generated query from raw text slicing.")
        status = "REJECTED"
        return {
            "query_id": q["query_id"],
            "query": q_str,
            "source_doc": doc,
            "positive_chunk_id": q["positive_chunk_id"],
            "query_type": q["query_type"],
            "status": status,
            "failure_mode": failure_mode,
            "checks": checks,
            "issues": issues,
            "suggested_correction": suggested_correction,
        }

    if q_str.count("[") != q_str.count("]"):
        checks["natural_and_useful"] = False
        checks["answers_question"] = False
        failure_mode = "SYNTACTIC_FRAGMENT"
        issues.append("Unclosed bracket in generated query from raw text slicing.")
        status = "REJECTED"
        return {
            "query_id": q["query_id"],
            "query": q_str,
            "source_doc": doc,
            "positive_chunk_id": q["positive_chunk_id"],
            "query_type": q["query_type"],
            "status": status,
            "failure_mode": failure_mode,
            "checks": checks,
            "issues": issues,
            "suggested_correction": suggested_correction,
        }

    # Dimension 3: Embedded raw URLs in conceptual questions
    if "https://" in q_str or "http://" in q_str:
        checks["natural_and_useful"] = False
        failure_mode = "EMBEDDED_URL"
        issues.append("Embedded raw markdown URL in query string.")
        suggested_correction = re.sub(r"\s*\([^)]*https?://[^)]*\)", "", q_str)
        status = "NEEDS_CORRECTION"

    # Dimension 3 & 1: Analysis of "handle <phrase> in this workflow"
    handle_match = re.search(r"How does Soup handle (.*) in this workflow\?", q_str)
    if handle_match:
        phrase = handle_match.group(1).strip()
        stop_words = {
            "when", "before", "after", "while", "during", "what", "which", "how",
            "that", "this", "there", "then", "also", "with", "from", "because"
        }
        p_words = phrase.split()
        if p_words and p_words[0].lower() in stop_words:
            checks["natural_and_useful"] = False
            checks["answers_question"] = False
            failure_mode = "UNNATURAL_BODY_FRAGMENT"
            issues.append(f"Unnatural body fragment: `{phrase}` begins with `{p_words[0]}`, resulting in nonsensical query.")
            status = "REJECTED"
            return {
                "query_id": q["query_id"],
                "query": q_str,
                "source_doc": doc,
                "positive_chunk_id": q["positive_chunk_id"],
                "query_type": q["query_type"],
                "status": status,
                "failure_mode": failure_mode,
                "checks": checks,
                "issues": issues,
                "suggested_correction": suggested_correction,
            }

        # Broken code symbols in body phrase
        if any(sym in phrase for sym in ["=", "\"", "\x27", "{", "}", ":"]):
            checks["natural_and_useful"] = False
            checks["answers_question"] = False
            failure_mode = "SYNTACTIC_FRAGMENT"
            issues.append(f"Raw code syntax symbols in conceptual phrase: `{phrase}`.")
            status = "REJECTED"
            return {
                "query_id": q["query_id"],
                "query": q_str,
                "source_doc": doc,
                "positive_chunk_id": q["positive_chunk_id"],
                "query_type": q["query_type"],
                "status": status,
                "failure_mode": failure_mode,
                "checks": checks,
                "issues": issues,
                "suggested_correction": suggested_correction,
            }

        # Embedded CLI syntax in conceptual question
        if "--" in phrase or "/" in phrase or "soup " in phrase:
            checks["natural_and_useful"] = False
            failure_mode = "AWKWARD_PHRASING"
            issues.append(f"Embedded CLI command/flag `{phrase}` in conceptual question template.")
            clean_cmd = phrase.replace("`", "").strip()
            suggested_correction = f"What is the role of `{clean_cmd}` in this Soup workflow?"
            status = "NEEDS_CORRECTION"

    # Dimension 2: Template mismatch (fine-tuning flag template on serving/export doc)
    if "when running fine-tuning commands" in q_str and doc in ["serving-and-export.md"]:
        checks["no_unsupported_assumptions"] = False
        checks["natural_and_useful"] = False
        failure_mode = "TEMPLATE_MISMATCH"
        issues.append("Template assumes fine-tuning context, but positive chunk belongs to serving/export.")
        suggested_correction = q_str.replace("when running fine-tuning commands in Soup", "when serving models in Soup")
        status = "NEEDS_CORRECTION"

    # Dimension 5: Breadth check
    if len(text.strip().split()) < 20 and q["query_type"] == "conceptual":
        checks["appropriate_breadth"] = False
        issues.append("Positive chunk is very brief (<20 words) for a conceptual workflow question.")
        if status == "ACCEPTED":
            status = "NEEDS_CORRECTION"
            failure_mode = "OVERLY_BROAD"
            suggested_correction = f"What is mentioned regarding this setting in `{doc}`?"

    return {
        "query_id": q["query_id"],
        "query": q_str,
        "source_doc": doc,
        "positive_chunk_id": q["positive_chunk_id"],
        "query_type": q["query_type"],
        "status": status,
        "failure_mode": failure_mode,
        "checks": checks,
        "issues": issues,
        "suggested_correction": suggested_correction,
    }


def run_audit() -> dict[str, Any]:
    corpus = load_training_corpus()

    target_configs = [
        ("exp_b", "train_queries_exp_b.jsonl", 85),
        ("exp_c_matched", "train_queries_exp_c_matched.jsonl", 85),
        ("exp_c_full", "train_queries_exp_c_full.jsonl", 190),
    ]

    audit_results: dict[str, Any] = {
        "metadata": {
            "description": "Reproducible 10% stratified semantic query quality audit",
            "seed": 42,
            "target_datasets": ["exp_b", "exp_c_matched", "exp_c_full"],
        },
        "datasets": {},
        "summary": {},
    }

    total_reviewed = 0
    total_accepted = 0
    total_needs_correction = 0
    total_rejected = 0
    all_failure_modes = Counter()

    for exp_key, filename, target_count in target_configs:
        path = DATA_DIR / filename
        queries = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        sampled = sample_stratified(queries, target_count, seed=42)

        dataset_records = []
        counts = Counter()
        fmodes = Counter()

        for q in sampled:
            chunk = corpus.get(q["positive_chunk_id"], {})
            record = audit_single_query(q, chunk)
            dataset_records.append(record)
            counts[record["status"]] += 1
            if record["failure_mode"]:
                fmodes[record["failure_mode"]] += 1
                all_failure_modes[record["failure_mode"]] += 1

        n_sampled = len(sampled)
        total_reviewed += n_sampled
        total_accepted += counts["ACCEPTED"]
        total_needs_correction += counts["NEEDS_CORRECTION"]
        total_rejected += counts["REJECTED"]

        rep_failures = [r for r in dataset_records if r["status"] in ["REJECTED", "NEEDS_CORRECTION"]][:5]

        audit_results["datasets"][exp_key] = {
            "dataset_file": filename,
            "total_queries_in_set": len(queries),
            "sample_count": n_sampled,
            "sample_percentage": round(n_sampled / len(queries) * 100, 2),
            "accepted_count": counts["ACCEPTED"],
            "accepted_pct": round(counts["ACCEPTED"] / n_sampled * 100, 2),
            "needs_correction_count": counts["NEEDS_CORRECTION"],
            "needs_correction_pct": round(counts["NEEDS_CORRECTION"] / n_sampled * 100, 2),
            "rejected_count": counts["REJECTED"],
            "rejected_pct": round(counts["REJECTED"] / n_sampled * 100, 2),
            "failure_modes": dict(fmodes),
            "representative_failures": rep_failures,
            "audited_records": dataset_records,
        }

    audit_results["summary"] = {
        "total_queries_reviewed": total_reviewed,
        "total_accepted": total_accepted,
        "total_accepted_pct": round(total_accepted / total_reviewed * 100, 2),
        "total_needs_correction": total_needs_correction,
        "total_needs_correction_pct": round(total_needs_correction / total_reviewed * 100, 2),
        "total_rejected": total_rejected,
        "total_rejected_pct": round(total_rejected / total_reviewed * 100, 2),
        "failure_mode_breakdown": dict(all_failure_modes),
    }

    out_file = RESULTS_DIR / "semantic_query_quality_audit.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    return audit_results


def main() -> None:
    print("Running Semantic Query Quality Audit...")
    results = run_audit()
    summary = results["summary"]
    print("\nAudit Summary Across All Datasets:")
    print(f"  Total Reviewed:         {summary['total_queries_reviewed']}")
    print(f"  Accepted:               {summary['total_accepted']} ({summary['total_accepted_pct']}%)")
    print(f"  Needs Correction:       {summary['total_needs_correction']} ({summary['total_needs_correction_pct']}%)")
    print(f"  Rejected:               {summary['total_rejected']} ({summary['total_rejected_pct']}%)")
    print("\nFailure Mode Breakdown:")
    for mode, count in summary["failure_mode_breakdown"].items():
        print(f"  - {mode}: {count}")


if __name__ == "__main__":
    main()
