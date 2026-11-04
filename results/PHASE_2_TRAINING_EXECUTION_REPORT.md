# Phase 2.0: Authorized Adapter Retraining Execution Report

**Project:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Timestamp:** 2026-11-04  
**Status:** Completed — All 5 Authorized Training Runs Successfully Executed and Verified  
**Total Training Wall-Clock Time:** 1,922.98 seconds (~32.0 minutes)  
**Hardware Platform:** Apple Silicon (MPS Unified Memory)  

---

## 1. Executive Summary

Under explicit user authorization (Path A), all five scheduled embedding adapter training runs were executed sequentially using the official Soup CLI trainer (`/Users/pernavjain/Documents/Soup/.venv/bin/soup train`) on Apple Silicon MPS:

1. **`A-matched`:** Replicated baseline under a matched update budget of 1,857 optimizer steps.
2. **`B`:** Diverse synthetic queries on the 8 core training documents (1,857 updates).
3. **`C-matched`:** Expanded corpus (31 documents) with diverse queries sampled under matched budget (1,857 updates).
4. **`C-matched-balanced`:** Expanded corpus with query types stratigraphically balanced to match Experiment B's type distribution (1,857 updates).
5. **`C-full`:** Full expanded corpus utilizing all 6,771 training triplets (5,079 updates).

The historical **`A-full`** baseline checkpoint in `output_embedding/` was preserved intact without modification. All five newly trained adapter checkpoints exist, are readable, match the locked LoRA architecture, and pass all system invariants (**161/161 tests passing**).

---

## 2. Complete Execution Status Matrix

| Order | Experiment | Output Path | Status | Start Time (UTC) | End Time (UTC) | Duration | Updates Completed | Final Loss |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| — | **`A-full`** (Historical) | `output_embedding/` | PRESERVED | *Historical* | *Historical* | *Historical* | 2,427 / 2,427 | 0.0482 |
| 1 | **`A-matched`** | `output/adapter_exp_a_matched` | **COMPLETED** | 04:53:21 | 04:57:09 | 228.04s (3m 48s) | 1,857 / 1,857 | 0.0676 |
| 2 | **`B`** | `output/adapter_exp_b` | **COMPLETED** | 04:57:09 | 05:00:49 | 219.35s (3m 39s) | 1,857 / 1,857 | 0.1626 |
| 3 | **`C-matched`** | `output/adapter_exp_c_matched` | **COMPLETED** | 05:00:49 | 05:04:55 | 246.12s (4m 06s) | 1,857 / 1,857 | 0.2006 |
| 4 | **`C-matched-balanced`** | `output/adapter_exp_c_matched_balanced` | **COMPLETED** | 05:04:55 | 05:09:20 | 264.33s (4m 24s) | 1,857 / 1,857 | 0.1566 |
| 5 | **`C-full`** | `output/adapter_exp_c_full` | **COMPLETED** | 05:09:20 | 05:25:23 | 963.42s (16m 03s) | 5,079 / 5,079 | 0.0677 |

---

## 3. Dataset & Configuration Provenance Checksums

Before initiating training, strict preflight assertions verified the record counts and cryptographic SHA256 checksums of every training dataset and configuration file:

| Experiment | Configuration Path | Configuration SHA256 | Training Dataset Path | Records | Dataset SHA256 |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`A-full`** (Base) | `config/embedding_exp_a_full.yaml` | `dbfa16e910543cb8...` | `data/train_triplets.jsonl` | 3,234 | `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75` |
| **`A-matched`** | `config/embedding_exp_a_matched.yaml` | `1ecba08afd22bff1f2277700ec980e2dcee0ccea58329e09e74186a525569f2e` | `data/triplets_exp_a_matched_v1_5.jsonl` | 2,475 | `605451c16af5e1d4c5d6c76aedbeb7df1b6be72242949eae4fb4d5b31b026acf` |
| **`B`** | `config/embedding_exp_b.yaml` | `5165a6d516c5756753d013f91372c5b2839d70e244e2b112e85eb46e145ccd8c` | `data/triplets_exp_b_v1_5.jsonl` | 2,475 | `55fbfeb9320d3c2ff2d2167e34b96ba7caa245ce0ebbf485f7194d6f2f193fcc` |
| **`C-matched`** | `config/embedding_exp_c_matched.yaml` | `7a5dfefa93c2a5697b4e1310e47927b8bde49d37f524e58212f2aeb53db6ac32` | `data/triplets_exp_c_matched_v1_5.jsonl` | 2,475 | `7d90222928e57b9025361328709032f733cf670aaa2ecb531b2efefdf18b763c` |
| **`C-matched-balanced`** | `config/embedding_exp_c_matched_balanced.yaml` | `b1c64fc741dda6eb6f72dd4187da86a898e1ac67b1b4e0c12f9562e602560c87` | `data/triplets_exp_c_matched_balanced_v1_6.jsonl` | 2,475 | `970192bf7a6c471ef5ab294382b75215eed9139e9d7aa32d5c9e26f4a2824016` |
| **`C-full`** | `config/embedding_exp_c_full.yaml` | `4021d4e6b0d62b01a9f1abb4317c931f9763020c91df6ac7387ca6157919ddce` | `data/triplets_exp_c_full_v1_5.jsonl` | 6,771 | `13731a2814f310147add6b831c940f0cc5a867c22ee3dc0f07b6eb8b06ac6523` |

---

## 4. Base Model Revision Pinning & Verification

Before launching each run, Soup verified the remote Hugging Face commit SHA and bound it at model instantiation. Post-run inspection of each run's `soup_run.json` verified:

- **Base Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Base Revision:** `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- **Revision Source:** `hub_commit`
- **Local Snapshot Match:** Confirmed byte alignment with `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

---

## 5. Checkpoint Inventory & Artifact Checksums

All adapter checkpoints were verified post-training. Weights (`adapter_model.safetensors`), configuration (`adapter_config.json`), and run metadata (`soup_run.json`) were cryptographically checksummed:

| Checkpoint Name | Run ID | Weights Bytes | `adapter_model.safetensors` SHA256 | `adapter_config.json` SHA256 | `soup_run.json` SHA256 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **`A-full`** (Baseline) | `run_20261029_004201_f3588165` | 593,072 | `4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534` | `e051390494df9da1ce7f0521e17d6682aeef1eb8a6a6838a0f9689f074d0d0c3` | `d5ba668d2bcf...` |
| **`A-matched`** | `run_20261104_102322_c1e304ad` | 593,072 | `81c35eeda72341bd5460eb3af547e2e52e0c5829c39c59a3103a2e90c7adebb1` | `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670` | `88b75f78d321447832874fb2fc03478ea9129af58ab9a6be92e0f2ebfcc1ef93` |
| **`B`** | `run_20261104_102710_b32802c0` | 593,072 | `7ce33a5063deaa91c8f38d2bdab96d81a196ca129a01e86515bbc69429009c8a` | `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670` | `8dbac369cb4dc306917ed84b269142be4dd254f6903bf6475d729c3b4c8c9069` |
| **`C-matched`** | `run_20261104_103050_06b4e812` | 593,072 | `6fe28922a98f6c13afbb3709cd9486f2b2173166802d61831852d992ba3f21b5` | `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670` | `9f44dd563aabf313d2bf270dd04fb16605b28d2ec7afb5696d904debeb3dd48b` |
| **`C-matched-balanced`** | `run_20261104_103456_3ae0bf18` | 593,072 | `25e0064078516ff068b6db2bface1065059f0d44a7a33592e8c0eb2094367137` | `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670` | `72eec8cb00a627b8a5117a28f3e36137b943ce6cdc0e238cf225f67460690501` |
| **`C-full`** | `run_20261104_103921_123d4886` | 593,072 | `145df326e64e6043d4fa313a1ef59d7ee958a705114978d1a3eaf7cb24fc0355` | `181ca4782837c30fd0bbc336d849f1daea9d57c2c0d32053ff66858a2d49ce8b` | `0a30c56e61b604f1801703c6c93f24a9e5fe8ffb7a96219a297c08f404fdf628` |

### Architecture Invariant Verification
All five checkpoints:
- **LoRA Rank ($r$):** 16
- **LoRA Alpha ($\alpha$):** 32
- **LoRA Dropout:** 0.05
- **Target Modules:** `["query", "value"]`
- **Trainable Parameters:** 147,456 (0.65% of base)
- **Base Architecture:** `sentence-transformers/all-MiniLM-L6-v2` (22.7M parameters)
- **Embedding Invariant:** Unit-normalized forward pass tested via Pytest across all 5 models (0 NaNs, 0 Infs, norm = 1.00000).

---

## 6. Training Loss Dynamics & Diagnostics

### 6.1 Loss Trajectories
Every model converged smoothly without loss explosions, gradient spikes, or NaN steps:
- **`A-matched`:** Initial loss: `0.4299` $\to$ Final loss: `0.0676` (avg speed: 8.47 it/s).
- **`B`:** Initial loss: `0.6535` $\to$ Final loss: `0.1626` (avg speed: 8.73 it/s).
- **`C-matched`:** Initial loss: `0.8404` $\to$ Final loss: `0.2006` (avg speed: 7.75 it/s).
- **`C-matched-balanced`:** Initial loss: `0.7281` $\to$ Final loss: `0.1566` (avg speed: 7.20 it/s).
- **`C-full`:** Initial loss: `0.7273` $\to$ Final loss: `0.0677` (avg speed: 6.24 it/s).

### 6.2 Observed Warnings & Non-Issues
- **`pin_memory` Warning:** PyTorch emitted standard DataLoader warning: `'pin_memory' argument is set as true but not supported on MPS now, device pinned memory won't be used.` This is the expected, benign behavior of PyTorch on Apple Silicon MPS unified memory architectures.
- **Failures / Retries:** 0 failures, 0 retries, 0 interrupted runs. All 5 runs completed on their initial attempt.

---

## 7. Frozen Benchmark Verification

Both before and immediately after the training sequence, SHA256 checksums of the frozen evaluation benchmark files were verified bit-for-bit:

| Frozen Benchmark File | Canonical SHA256 Checksum | Pre-Training Verification | Post-Training Verification |
| :--- | :--- | :---: | :---: |
| `data/corpus.jsonl` | `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3` | **MATCH** | **MATCH** |
| `data/manual_queries.jsonl` | `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3` | **MATCH** | **MATCH** |
| `data/eval_queries.jsonl` | `7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3` | **MATCH** | **MATCH** |
| `data/train_query_labels.jsonl` | `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae` | **MATCH** | **MATCH** |
| `data/train_triplets.jsonl` | `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75` | **MATCH** | **MATCH** |

---

## 8. Test Suite Verification

A dedicated invariant test suite ([`tests/test_phase2_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_phase2_invariants.py)) was added to assert checkpoint existence, file integrity, LoRA configuration, provenance matching, and forward embedding inference.

The full repository test suite was executed:
```
============================= 161 passed in 17.71s =============================
```
- `tests/test_compare_retrievers.py`: 14 passed
- `tests/test_manual_queries_validation.py`: 25 passed
- `tests/test_phase1_10_invariants.py`: 6 passed
- `tests/test_phase1_5_invariants.py`: 18 passed
- `tests/test_phase1_6_invariants.py`: 5 passed
- `tests/test_phase1_7_invariants.py`: 3 passed
- `tests/test_phase1_8_invariants.py`: 4 passed
- `tests/test_phase1_invariants.py`: 13 passed
- `tests/test_phase2_invariants.py`: 11 passed
- `tests/test_retrieval_metrics.py`: 21 passed
- `tests/test_retrieval_pipeline.py`: 15 passed
- `tests/test_retrievers.py`: 16 passed
- `tests/test_run_retrieval.py`: 5 passed
- `tests/test_v1_dataset_invariants.py`: 5 passed

---

## 9. Evaluation Gate Status

As mandated:
- **Retrieval evaluation has NOT been initiated.**
- All 6 adapter checkpoints (`A-full`, `A-matched`, `B`, `C-matched`, `C-matched-balanced`, and `C-full`) are fully trained, verified, and ready for benchmarking.
- The next phase is ready to execute retrieval evaluation against the frozen 54-query benchmark, reporting metrics across all defined partitions (Full, Core Primary, Core Overlap, Candidate Clean, Candidate Partial Overlap, and Pure Held-Out) against frozen MiniLM and frozen E5-small baselines.
