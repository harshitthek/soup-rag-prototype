# Phase 1.8 Final Experiment Run Manifest

**Project:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Timestamp:** 2026-11-04  
**Audit Status:** Complete — Manifest Locked, Awaiting User Approval to Retrain  

---

## 1. Executive Summary

Phase 1.8 delivers an unambiguous, verified, and reproducible training run manifest for the experimental matrix on branch `feat/evaluation-v2`.

**Core Reconciliations Accomplished:**
1. **A-full Checkpoint Ambiguity Resolved:** Confirmed that `A-full` has an existing, verified, byte-identical trained LoRA adapter in `output_embedding/` (MD5 `05e30132…`, SHA256 `4dceadcb…`, Run ID `run_20261029_004201_f3588165`). Two explicit execution paths are documented:
   - **Path A (Recommended):** Use existing validated `output_embedding/` checkpoint for `A-full`, executing **5 new training runs** (`A-matched`, `B`, `C-matched`, `C-matched-balanced`, `C-full`).
   - **Path B (Full Parity Retraining):** Retrain `A-full` from scratch to `output/adapter_exp_a_full`, executing **6 new training runs**.
2. **Runtime & Dataloader Verification:** Inspected the exact entry point and confirmed execution via the official Soup embedding trainer (`soup_cli.trainer.embedding.EmbeddingTrainerWrapper`) on Apple Silicon (MPS) under single-process topology (`world_size = 1`).
3. **Exact Partial Batch Accounting:** Documented that `A-full` has a final partial batch of **2** ($3,234 = 808 \times 4 + 2$), while matched runs and `C-full` have a final partial batch of **3** ($2,475 = 618 \times 4 + 3$ and $6,771 = 1,692 \times 4 + 3$). Under `dataloader_drop_last = False`, these partial batches yield active optimizer steps in each epoch.
4. **Configuration Artifacts Prepared:** Created 6 dedicated, dry-run-validated YAML configs under `config/embedding_exp_*.yaml` with isolated output paths.
5. **Frozen Benchmark & Test Suite Verification:** All 5 canonical benchmark files remain bit-exact identical to their pinned SHA256 hashes, and all **144 tests in the test suite pass**.

---

## 2. Final List of Datasets

The experimental matrix comprises six distinct training datasets:

| Dataset Identifier | Query Strategy | Corpus Scope | Unique Queries | Total Triplets | Positive Chunks | Query Type Distribution |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`A-full`** | Synthetic templates | 8 docs (core) | 1,078 | 3,234 | 586 | Template-derived |
| **`A-matched`** | Synthetic templates | 8 docs (core) | 825 | 2,475 | 586 | Template-derived |
| **`B`** | Diverse LLM (Gemini) | 8 docs (core) | 825 | 2,475 | 586 | 327 how_to / 309 conc / 184 param / 5 trbl |
| **`C-matched`** | Diverse LLM (Gemini) | 31 docs (expanded) | 825 | 2,475 | 565 | 171 how_to / 583 conc / 70 param / 1 trbl |
| **`C-matched-balanced`** | Diverse LLM (Gemini) | 31 docs (expanded) | 825 | 2,475 | 720* | 327 how_to / 309 conc / 184 param / 5 trbl |
| **`C-full`** | Diverse LLM (Gemini) | 31 docs (expanded) | 2,257 | 6,771 | 1,522 | 594 how_to / 1,353 conc / 303 param / 7 trbl |

*\*Note on positive chunk count: Earlier draft manifests listed 586 (inherited from the Experiment B matching target). In the actual stratified sampling from C-full across all 31 documents, C-matched-balanced covers 720 unique positive chunks (compared to 565 in C-matched and 586 in B), as documented in `results/PHASE_3_1_INTEGRITY_AUDIT.md` and `results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`.*

---

## 3. Identification and Provenance of the A-full Checkpoint

The investigation confirmed that an authentic, fully evaluated checkpoint for `A-full` exists in the repository.

### 3.1 Existing Checkpoint Provenance
- **Filesystem Location:** [`output_embedding/`](file:///Users/pernavjain/Documents/soup-rag-prototype/output_embedding)
- **Adapter Weights File:** `output_embedding/adapter_model.safetensors`
- **Adapter Weights SHA256:** `4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534`
- **Adapter Weights MD5:** `05e30132a26bf0d6f469aa72ec86fa53`
- **Git Commit Provenance:** Verified in commit `e58da081362fa15579ddb8675a014be937f3baaf`. The weights in `output_embedding/adapter_model.safetensors` were verified to be byte-identical to `checkpoint-2427` (the final step of the 2,427-step training run) before intermediate checkpoint directories were pruned from Git.
- **Base Model & Revision:** `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- **Adapter Architecture:**
  - PEFT type: `LORA` ($r=16, \alpha=32$, dropout 0.05, `target_modules`: `["query", "value"]`).
  - Task type: `FEATURE_EXTRACTION`.
  - Trainable parameters: 147,456 (0.65% of base).
- **Training Dataset Fingerprint:**
  - Triplets file: `data/train_triplets.jsonl` (3,234 triplets).
  - Triplets SHA256: `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75`.
  - Queries file: `data/train_query_labels.jsonl` (1,078 queries).
  - Queries SHA256: `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae`.
- **Hyperparameters:**
  - Loss: triplet margin loss (margin 0.5, mean pooling).
  - Optimizer: AdamW, learning rate 2e-5, batch size 4, gradient accumulation 1.
  - Seeds: `seed = 42`, `data_seed = 42`.
  - Updates executed: 2,427 optimizer updates ($809\text{ steps/epoch} \times 3\text{ epochs}$).
- **Soup Provenance Record:** Recorded in `output_embedding/soup_run.json`:
  ```json
  {
    "base_model": "sentence-transformers/all-MiniLM-L6-v2",
    "base_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    "base_revision_source": "hub_commit",
    "run_id": "run_20261029_004201_f3588165",
    "schema_version": 1,
    "training_data_sha256": null
  }
  ```
- **Existing Benchmark Evaluations:**
  - v1 Synthetic Evaluation: `results/candidate.json` (Recall@1 = 0.7565, MRR@10 = 0.8477).
  - v2 Manual Evaluation: `results/v2/mini_lm_soup.json` (Hit@1 = 0.5370, Recall@1 = 0.3256).

### 3.2 Decision Regarding A-full Execution
Because `output_embedding/` is verified, byte-identical to `checkpoint-2427`, and directly loadable:
- **Path A (Recommended - 5 Training Runs):** Retain `output_embedding/` as the immutable evaluation target for `A-full`. Execute training for the 5 remaining datasets (`A-matched`, `B`, `C-matched`, `C-matched-balanced`, `C-full`). This preserves exact historical evaluation continuity and avoids redundant training.
- **Path B (Parity Retraining - 6 Training Runs):** Execute training for all 6 datasets, writing `A-full` to `output/adapter_exp_a_full` using `config/embedding_exp_a_full.yaml`.

Both paths are fully configured and ready.

---

## 4. Training Command and Resolved Trainer Implementation

### 4.1 Invocation Command
Training will be executed via the official Soup CLI:
```bash
/Users/pernavjain/Documents/Soup/.venv/bin/soup train -y --config <CONFIG_PATH>
```

### 4.2 Resolved Trainer Architecture
- **CLI Entry Point:** `/Users/pernavjain/Documents/Soup/src/soup_cli/commands/train.py`
- **Dispatcher:** `/Users/pernavjain/Documents/Soup/src/soup_cli/trainer/dispatch.py` (lines 99–102)
- **Resolved Module:** `soup_cli.trainer.embedding.EmbeddingTrainerWrapper`
- **Underlying Trainer:** `_EmbeddingTrainer` (a subclass of Hugging Face `transformers.Trainer`).
- **Official Trainer Confirmation:** Confirmed. The training run directly executes the native embedding trainer from the official Soup repository (`https://github.com/MakazhanAlpamys/Soup`).

---

## 5. Runtime Topology and Optimizer Update Calculations

### 5.1 Single-Process Execution Topology
- **Execution Target:** Local Apple Silicon (MPS backend).
- **Topology:** Single node, single process (`nodes = 1`, `world_size = 1`).
- **Distributed Training:** Disabled. No multi-GPU or multi-node re-exec is triggered.
- **Batching Parameters:**
  - `per_device_train_batch_size = 4`
  - `gradient_accumulation_steps = 1`
  - `effective_batch_size = 4 \times 1 \times 1 = 4`
  - `dataloader_drop_last = False` (in `soup_cli/trainer/embedding.py`, line 200, `(loss_type == "contrastive")` evaluates to `False` for `triplet` loss).

### 5.2 Exact Dataloader Length & Partial Batch Accounting
Because `dataloader_drop_last = False` in single-process mode, any partial batch at the end of an epoch is retained, processed, and triggers an optimizer step:

$$\text{batches\_per\_epoch} = \left\lceil \frac{N}{B} \right\rceil = \left\lceil \frac{N}{4} \right\rceil$$
$$\text{total\_optimizer\_updates} = 3 \times \left\lceil \frac{N}{4} \right\rceil$$

1. **`A-full` ($N = 3,234$ triplets):**
   - Partition: **808 full batches of 4** plus **one partial batch of 2** ($3,234 = 808 \times 4 + 2$).
   - `len(train_dataloader)` = 809 batches per epoch.
   - Updates per epoch = 809.
   - Total updates (3 epochs) = $809 \times 3 = \mathbf{2,427}\text{ updates}$.
2. **`A-matched`, `B`, `C-matched`, `C-matched-balanced` ($N = 2,475$ triplets each):**
   - Partition: **618 full batches of 4** plus **one partial batch of 3** ($2,475 = 618 \times 4 + 3$).
   - `len(train_dataloader)` = 619 batches per epoch.
   - Updates per epoch = 619.
   - Total updates (3 epochs) = $619 \times 3 = \mathbf{1,857}\text{ updates}$.
3. **`C-full` ($N = 6,771$ triplets):**
   - Partition: **1,692 full batches of 4** plus **one partial batch of 3** ($6,771 = 1,692 \times 4 + 3$).
   - `len(train_dataloader)` = 1,693 batches per epoch.
   - Updates per epoch = 1,693.
   - Total updates (3 epochs) = $1,693 \times 3 = \mathbf{5,079}\text{ updates}$.

*Note on Partial Batch Sizing:* `A-full` has a partial batch size of **2**, whereas the matched runs and `C-full` have a partial batch size of **3**. Both produce valid optimizer updates under the verified single-process dataloader.

---

## 6. Expected Model Checkpoints and Output Locations

To prevent directory collisions or accidental overwriting, each run has a dedicated YAML configuration and isolated output directory:

| Run Identifier | YAML Config File | Training Data Input | Output Directory | Checkpoint Safetensors Path |
| :--- | :--- | :--- | :--- | :--- |
| **`A-full` (Existing)** | `config/embedding.yaml` | `data/train_triplets.jsonl` | `output_embedding/` | `output_embedding/adapter_model.safetensors` |
| **`A-full` (If Retrained)** | `config/embedding_exp_a_full.yaml` | `data/train_triplets.jsonl` | `output/adapter_exp_a_full` | `output/adapter_exp_a_full/adapter_model.safetensors` |
| **`A-matched`** | `config/embedding_exp_a_matched.yaml` | `data/triplets_exp_a_matched_v1_5.jsonl` | `output/adapter_exp_a_matched` | `output/adapter_exp_a_matched/adapter_model.safetensors` |
| **`B`** | `config/embedding_exp_b.yaml` | `data/triplets_exp_b_v1_5.jsonl` | `output/adapter_exp_b` | `output/adapter_exp_b/adapter_model.safetensors` |
| **`C-matched`** | `config/embedding_exp_c_matched.yaml` | `data/triplets_exp_c_matched_v1_5.jsonl` | `output/adapter_exp_c_matched` | `output/adapter_exp_c_matched/adapter_model.safetensors` |
| **`C-matched-balanced`** | `config/embedding_exp_c_matched_balanced.yaml` | `data/triplets_exp_c_matched_balanced_v1_6.jsonl` | `output/adapter_exp_c_matched_balanced` | `output/adapter_exp_c_matched_balanced/adapter_model.safetensors` |
| **`C-full`** | `config/embedding_exp_c_full.yaml` | `data/triplets_exp_c_full_v1_5.jsonl` | `output/adapter_exp_c_full` | `output/adapter_exp_c_full/adapter_model.safetensors` |

All 6 YAML configs have been validated via `soup train --dry-run` and verified against dataset line counts and unique output paths in [`tests/test_phase1_8_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_phase1_8_invariants.py).

---

## 7. Fixed Configuration and Reproducibility Settings

The following hyperparameter contract is strictly fixed across all training runs:

```yaml
base: sentence-transformers/all-MiniLM-L6-v2
task: embedding
backend: transformers

data:
  format: embedding
  val_split: 0.0
  max_length: 256

training:
  epochs: 3
  lr: 2e-5
  batch_size: 4
  gradient_accumulation_steps: 1
  seed: 42
  data_seed: 42
  quantization: none

  embedding_loss: triplet
  embedding_margin: 0.5
  embedding_pooling: mean

  lora:
    r: 16
    alpha: 32
    target_modules: auto
```

---

## 8. Remaining Limitations

1. **Evaluation Benchmark Conceptual Overlap:** Five of the 54 manual evaluation queries exhibit partial conceptual overlap with the candidate corpus (identified during Phase 0). Evaluation reports will present micro-averaged metrics on the 49 primary queries alongside the 5 conceptual overlap queries.
2. **Partial Batch Remnants:** All runs feature one partial batch per epoch (size 2 for `A-full`, size 3 for all other runs). The single-process dataloader trains on these remnants without truncation.
3. **Automated Review Attribution:** Programmatic AST validation and semantic heuristics were executed algorithmically; the 6-point rubric evaluation was executed via Antigravity agentic evaluation. No human reviewer performed line-by-line manual grading of the 396 sampled queries.
4. **Corpus Document Length Variation:** Document token lengths range from ~50 tokens (changelog fragments) to multi-thousand-token reference guides, producing natural variation in queries per document.

---

## 9. Verification & Invariant Audit Results

- **Full Pytest Suite:** **144 / 144 tests passing** across 12 test modules in 14.30s (including `tests/test_phase1_8_invariants.py`).
- **Frozen Benchmark SHA256 Checksums (Bit-Exact Integrity):**
  - `data/corpus.jsonl`: `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3` (MATCH)
  - `data/manual_queries.jsonl`: `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3` (MATCH)
  - `data/eval_queries.jsonl`: `7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3` (MATCH)
  - `data/train_query_labels.jsonl`: `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae` (MATCH)
  - `data/train_triplets.jsonl`: `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75` (MATCH)
- **A-full Weights Checksum:**
  - `output_embedding/adapter_model.safetensors`: `4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534` (MATCH)

---

## 10. Final Retraining Gate Decisions

| Run Identifier | Dataset | Target Output Path | Pre-Flight Status | Recommendation |
| :--- | :--- | :--- | :---: | :---: |
| **`A-full`** | `data/train_triplets.jsonl` | `output_embedding/` (existing) | Validated Checkpoint Present | **GO** (Use Existing Checkpoint) |
| **`A-full` (Retrain Option)** | `data/train_triplets.jsonl` | `output/adapter_exp_a_full` | Config & Data Validated | **GO** (If Parity Retraining Preferred) |
| **`A-matched`** | `data/triplets_exp_a_matched_v1_5.jsonl` | `output/adapter_exp_a_matched` | Config & Data Validated | **GO** |
| **`B`** | `data/triplets_exp_b_v1_5.jsonl` | `output/adapter_exp_b` | Config & Data Validated | **GO** |
| **`C-matched`** | `data/triplets_exp_c_matched_v1_5.jsonl` | `output/adapter_exp_c_matched` | Config & Data Validated | **GO** |
| **`C-matched-balanced`** | `data/triplets_exp_c_matched_balanced_v1_6.jsonl` | `output/adapter_exp_c_matched_balanced` | Config & Data Validated | **GO** |
| **`C-full`** | `data/triplets_exp_c_full_v1_5.jsonl` | `output/adapter_exp_c_full` | Config & Data Validated | **GO** |

**Execution Gate:** Strictly halted. No model training or evaluation will begin without explicit approval.
