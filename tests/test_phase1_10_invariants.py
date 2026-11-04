"""Phase 1.10 Final Evaluation Taxonomy Reconciliation and Model Revision Lock Invariant Tests.

Verifies:
1. Frozen benchmark SHA256 integrity across all canonical evaluation files.
2. Query benchmark completeness (exactly 54 queries, 39 core primary, 15 core overlap).
3. Mutual exclusivity and completeness of evaluation taxonomy partitions.
4. Exact four-way intersection counts summing to 54 (37 + 2 + 15 + 0 = 54).
5. Authoritative candidate overlap query IDs (manual_025, manual_048).
6. Explicit LoRA configuration parity across all 6 YAML experiment files against A-full adapter_config.json.
7. Base model revision pinning alignment with A-full soup_run.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"
OUTPUT_DIR = REPO_ROOT / "output_embedding"

FROZEN_CHECKSUMS = {
    "corpus.jsonl": "d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3",
    "manual_queries.jsonl": "971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3",
    "eval_queries.jsonl": "7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3",
    "train_query_labels.jsonl": "4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae",
    "train_triplets.jsonl": "60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75",
}

EXPECTED_CANDIDATE_OVERLAP_QIDS = {"manual_025", "manual_048"}
EXPECTED_BASE_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def test_frozen_benchmark_sha256_integrity():
    """Verify all frozen benchmark files match canonical SHA256 hashes bit-for-bit."""
    for fname, expected_hash in FROZEN_CHECKSUMS.items():
        file_path = DATA_DIR / fname
        assert file_path.exists(), f"Frozen benchmark file missing: {fname}"
        h = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert h == expected_hash, f"Hash mismatch on {fname}: got {h}, expected {expected_hash}"


def test_query_benchmark_counts_and_core_classifications():
    """Verify exactly 54 query IDs and preserve 39 primary / 15 overlap core classification."""
    queries_path = DATA_DIR / "manual_queries.jsonl"
    with open(queries_path, "r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f]

    assert len(queries) == 54, f"Expected 54 queries, found {len(queries)}"
    qids = {q["query_id"] for q in queries}
    assert len(qids) == 54, "Query IDs must be unique"

    primary_qids = {q["query_id"] for q in queries if q["subset"] == "primary"}
    overlap_qids = {q["query_id"] for q in queries if q["subset"] == "overlap"}

    assert len(primary_qids) == 39, f"Expected 39 primary queries, got {len(primary_qids)}"
    assert len(overlap_qids) == 15, f"Expected 15 overlap queries, got {len(overlap_qids)}"
    assert primary_qids.isdisjoint(overlap_qids), "Primary and overlap subsets must be disjoint"
    assert primary_qids | overlap_qids == qids, "Every query must be either primary or overlap"


def test_candidate_taxonomy_mutual_exclusivity_and_four_way_matrix():
    """Verify candidate clean and partial overlap assignments are mutually exclusive and sum to 54."""
    queries_path = DATA_DIR / "manual_queries.jsonl"
    with open(queries_path, "r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f]

    candidate_overlap_found = set()
    candidate_clean_found = set()

    for q in queries:
        qid = q["query_id"]
        if qid in EXPECTED_CANDIDATE_OVERLAP_QIDS:
            candidate_overlap_found.add(qid)
        else:
            candidate_clean_found.add(qid)

    # Mutual exclusivity & exhaustiveness
    assert candidate_overlap_found == EXPECTED_CANDIDATE_OVERLAP_QIDS
    assert candidate_overlap_found.isdisjoint(candidate_clean_found)
    assert len(candidate_clean_found) == 52
    assert len(candidate_overlap_found) + len(candidate_clean_found) == 54

    # Calculate 4-way intersection counts
    primary_clean = sum(1 for q in queries if q["subset"] == "primary" and q["query_id"] not in EXPECTED_CANDIDATE_OVERLAP_QIDS)
    primary_overlap = sum(1 for q in queries if q["subset"] == "primary" and q["query_id"] in EXPECTED_CANDIDATE_OVERLAP_QIDS)
    overlap_clean = sum(1 for q in queries if q["subset"] == "overlap" and q["query_id"] not in EXPECTED_CANDIDATE_OVERLAP_QIDS)
    overlap_overlap = sum(1 for q in queries if q["subset"] == "overlap" and q["query_id"] in EXPECTED_CANDIDATE_OVERLAP_QIDS)

    assert primary_clean == 37, f"Expected 37 pure held-out queries, got {primary_clean}"
    assert primary_overlap == 2, f"Expected 2 primary candidate-overlap queries, got {primary_overlap}"
    assert overlap_clean == 15, f"Expected 15 core-overlap candidate-clean queries, got {overlap_clean}"
    assert overlap_overlap == 0, f"Expected 0 core-overlap candidate-overlap queries, got {overlap_overlap}"
    assert primary_clean + primary_overlap + overlap_clean + overlap_overlap == 54


def test_reconciliation_table_artifact_alignment():
    """Verify that results/query_partitions_reconciliation_table.md matches final classifications."""
    table_path = REPO_ROOT / "results" / "query_partitions_reconciliation_table.md"
    assert table_path.exists(), "query_partitions_reconciliation_table.md missing"

    content = table_path.read_text(encoding="utf-8")
    for qid in EXPECTED_CANDIDATE_OVERLAP_QIDS:
        assert f"`{qid}`" in content
        # Check that it is listed as partial_overlap
        for line in content.splitlines():
            if f"`{qid}`" in line:
                assert "partial_overlap" in line, f"{qid} must be classified as partial_overlap in table"

    # Discredited Phase 1.9 false overlaps must be classified as clean
    for qid in ["manual_003", "manual_005", "manual_023", "manual_024"]:
        for line in content.splitlines():
            if f"`{qid}`" in line:
                assert "clean" in line, f"{qid} must be classified as clean in table"


def test_explicit_lora_configuration_parity():
    """Verify all 6 YAML configurations specify explicit LoRA settings identical to A-full checkpoint."""
    configs = [
        "embedding_exp_a_full.yaml",
        "embedding_exp_a_matched.yaml",
        "embedding_exp_b.yaml",
        "embedding_exp_c_matched.yaml",
        "embedding_exp_c_matched_balanced.yaml",
        "embedding_exp_c_full.yaml",
    ]

    # Reference adapter_config.json
    orig_config_path = OUTPUT_DIR / "adapter_config.json"
    with open(orig_config_path, "r", encoding="utf-8") as f:
        orig = json.load(f)

    for cfg_name in configs:
        p = CONFIG_DIR / cfg_name
        assert p.exists(), f"Missing config: {cfg_name}"
        with open(p, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)

        lora = y["training"]["lora"]
        assert lora["r"] == orig["r"] == 16
        assert lora["alpha"] == orig["lora_alpha"] == 32
        assert float(lora["dropout"]) == orig["lora_dropout"] == 0.05
        assert lora["target_modules"] == ["query", "value"]
        assert set(lora["target_modules"]) == set(orig["target_modules"])


def test_base_revision_lock_integrity():
    """Verify that A-full checkpoint records the immutable revision and matching cache snapshot exists."""
    run_path = OUTPUT_DIR / "soup_run.json"
    assert run_path.exists(), "soup_run.json missing"
    with open(run_path, "r", encoding="utf-8") as f:
        run = json.load(f)

    assert run["base_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert run["base_revision"] == EXPECTED_BASE_REVISION
    assert run["base_revision_source"] == "hub_commit"

    # Check local Hugging Face cache snapshot
    cache_snapshot = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots" / EXPECTED_BASE_REVISION
    assert cache_snapshot.exists(), f"Local snapshot missing for revision {EXPECTED_BASE_REVISION}"
    assert (cache_snapshot / "config.json").exists()
    assert (cache_snapshot / "model.safetensors").exists()
