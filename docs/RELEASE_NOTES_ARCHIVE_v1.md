# GitHub Release Notes: Research Archive Bundle (v1)

**Release Asset:** `soup-rag-research-archive-v1.tar.gz`  
**Asset Size:** 6.88 MB (7,210,831 bytes)  
**SHA256 Checksum:** `9603f4f51bc144d8dd08935f54e455b640ce93faf1684e473251e327e119d805`  
**License:** MIT License  
**Publication Status:** Draft / Release-ready (awaiting maintainer authorization to publish)  

---

## 1. Purpose of This Archive

This research archive preserves full historical reproducibility for all intermediate experiments, training configurations, raw training logs, and Phase 1–3 audit records generated during the development of the Soup RAG prototype. It allows maintainers and external researchers to audit intermediate artifacts without forcing everyday prototype users to clone large historical logs and intermediate datasets.

---

## 2. Archive Contents & Inventory (73 Files)

The archive contains five self-contained directories:

### 1. `reports/` (Historical Audit & Phase Documentation)
- `PHASE_1_5_QUERY_QUALITY_REPORT.md` and `PHASE_1_5_QUERY_AUDIT.json`: Detailed heuristic query audit and synthetic generation quality analysis.
- `PHASE_1_6_RECONCILIATION_REPORT.md`: Training query reconciliation across partitions.
- `PHASE_1_7_TRAINING_READINESS_REPORT.md`: Pre-training integrity verification.
- `PHASE_1_8_FINAL_RUN_MANIFEST.md` and `PHASE_1_9_CONFIG_AND_PROVENANCE_LOCK.md`: Run configurations and provenance locks.
- `PHASE_1_10_FINAL_EXPERIMENT_LOCK.md`: Experiment matrices.
- `PHASE_2_TRAINING_EXECUTION_REPORT.md` and `PHASE_2_1_ARTIFACT_VERIFICATION_REPORT.md`: Adapter training logs and validation receipts.
- `PHASE_3_BENCHMARK_EVALUATION_REPORT.md` and `PHASE_3_1_INTEGRITY_AUDIT.md`: Phase 3 multi-retriever benchmark report and integrity audit.
- `PHASE_3_DOCUMENTATION_AUDIT.md`: Documentation structural audit.

### 2. `phase3/` (Phase 3 Benchmark Outputs)
- Frozen Phase 3 multi-retriever outputs (`aggregate_comparison.json`, `bootstrap_ci.json`, `failure_analysis.json`, `lodo_analysis.json`, per-retriever outputs) sealed by `manifest.sha256`.

### 3. `training_logs/` (Complete Console & Telemetry Logs)
- `a_matched.log`, `b.log`, `c_matched.log`, `c_matched_balanced.log`, `c_full.log`: Full stdout and stderr from Phase 2 adapter training.
- `e5_exp_b.log` and `e5_exp_b_summary.json`: Full training log and metadata from E5-small LoRA fine-tuning.

### 4. `data/` (Intermediate Datasets & Hard Negatives)
- `triplets_exp_a_matched*.jsonl`, `triplets_exp_b*.jsonl`, `triplets_exp_c_*.jsonl`: Pre-processed triplet files.
- `triplets_e5_exp_b.jsonl`: Prefixed E5 training dataset.
- `train_queries_exp_*.jsonl`: Raw generated query files.
- `hard_negatives_exp_*.jsonl`: Mined negative passages.

### 5. `config/` (Full YAML Configurations)
- `embedding_exp_a_matched.yaml`, `embedding_exp_b.yaml`, `embedding_exp_c_*.yaml`, `embedding_e5_exp_b.yaml`.

---

## 3. How to Verify and Extract

To verify archive integrity and extract artifacts:

```bash
# Verify checksum
echo "9603f4f51bc144d8dd08935f54e455b640ce93faf1684e473251e327e119d805  soup-rag-research-archive-v1.tar.gz" | sha256sum -c

# Extract bundle
tar -xzf soup-rag-research-archive-v1.tar.gz

# Verify internal file manifest
cd soup-rag-research-archive-v1
sha256sum -c ARCHIVE_MANIFEST.sha256
```
