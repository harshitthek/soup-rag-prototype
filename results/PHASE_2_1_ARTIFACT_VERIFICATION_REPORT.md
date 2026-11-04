# Phase 2.1 Post-Training Artifact Verification Report

**Project:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Timestamp:** 2026-11-04  
**Audit Status:** Complete — All Checkpoints Verified, Adapter Configurations Reconciled, Architecture Invariants Passing (**174/174 Tests Passing**), Ready for Benchmark Evaluation Gate  

---

## 1. Executive Summary

Phase 2.1 performs a rigorous post-training integrity audit across all six adapter checkpoints (`A-full`, `A-matched`, `B`, `C-matched`, `C-matched-balanced`, `C-full`):
1. **Adapter Configuration Checksum Discrepancy Resolved:** The SHA256 hash difference between `C-full` (`181ca478...`) and the other five checkpoints (`9f1ae088...`) was thoroughly investigated. Line-by-line diff and semantic parsing confirm that 40 of 41 configuration fields are byte-identical. The sole difference is list element ordering in `target_modules`: `["value", "query"]` vs. `["query", "value"]`. In PEFT (`LoraConfig`), `target_modules` is internally cast to a Python `set` (`{'query', 'value'}`). Its serialization order is determined by Python's process-level hash seed randomization (`PYTHONHASHSEED`). When normalized, all six adapter configurations are **100% semantically and architecturally identical**.
2. **Checkpoint Integrity Verified:** All six adapter checkpoints (`adapter_model.safetensors`, `adapter_config.json`, `soup_run.json`) exist, are uncorrupted, and exactly match the cryptographic checksums recorded in the Phase 2 execution summary. The immutable baseline `A-full` remains byte-exact and untouched.
3. **Inference Pipeline Smoke Testing:** All six adapters were instantiated through the project's native retrieval inference engine ([`DenseRetriever`](file:///Users/pernavjain/Documents/soup-rag-prototype/scripts/retrievers.py#L81) in `scripts/retrievers.py`). Inference on a fixed smoke-test query set confirmed:
   - Output dimension: exactly **384** (MiniLM hidden dimension).
   - Numerical validity: **0 NaNs**, **0 Infs**.
   - L2 normalization: $\|\mathbf{v}\|_2 = 1.00000$ (tolerance $< 10^{-5}$).
   - Runtime determinism: identical inputs generate bit-identical embeddings across inference passes (maximum absolute difference = $0.00\times 10^0$).
4. **Final Recommendation:** **GO** for Phase 3 Multi-Retriever Benchmark Evaluation.

---

## 2. Adapter Configuration Checksum Investigation

### 2.1 Observed Checksums
- `A-full` (baseline in `output_embedding/`): `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670`
- `A-matched`: `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670`
- `B`: `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670`
- `C-matched`: `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670`
- `C-matched-balanced`: `9f1ae0887d14404fcef2e160db94e50bc0ff0537f212cc7052900e8b4b048670`
- `C-full`: `181ca4782837c30fd0bbc336d849f1daea9d57c2c0d32053ff66858a2d49ce8b`

### 2.2 Raw Unified Diff
Executing `diff -u` between `output/adapter_exp_a_matched/adapter_config.json` and `output/adapter_exp_c_full/adapter_config.json`:
```diff
--- output/adapter_exp_a_matched/adapter_config.json	2026-11-04 10:27:08
+++ output/adapter_exp_c_full/adapter_config.json	2026-11-04 10:55:23
@@ -32,8 +32,8 @@
   "rank_pattern": {},
   "revision": null,
   "target_modules": [
-    "value",
-    "query"
+    "query",
+    "value"
   ],
   "target_parameters": null,
   "task_type": "FEATURE_EXTRACTION",
```

### 2.3 Root Cause Analysis: PEFT Set Serialization
1. **Internal PEFT Representation:** In Hugging Face PEFT (`peft/tuners/lora/config.py`), `LoraConfig.__post_init__` converts `target_modules` to a Python `set`:
   ```python
   self.target_modules = set(target_modules) if isinstance(target_modules, (list, set, tuple)) else target_modules
   ```
2. **Hash Seed Randomization (`PYTHONHASHSEED`):** In Python 3.10+, set iteration order is randomized per process launch based on string hash salts.
3. **Empirical Reproduction:** Spawning 10 independent Python processes in the Soup environment:
   ```bash
   for i in {1..10}; do
     python -c 'from peft import LoraConfig; print(list(LoraConfig(target_modules=["query", "value"]).target_modules))'
   done
   ```
   Yielded:
   ```
   ['value', 'query']
   ['query', 'value']
   ['value', 'query']
   ['value', 'query']
   ['value', 'query']
   ['value', 'query']
   ['query', 'value']
   ['query', 'value']
   ['value', 'query']
   ['value', 'query']
   ```
   Runs 1–4 generated the iteration order `['value', 'query']`, producing SHA256 `9f1ae088...`. Run 5 (`C-full`) was launched in a separate process that happened to iterate `['query', 'value']`, producing SHA256 `181ca478...`.
4. **Architectural & Semantic Impact:** Zero. PEFT matches modules by testing membership in `self.target_modules` (a set) or via regular expressions. The serialization ordering is purely cosmetic.

### 2.4 Critical Configuration Fields Verification

| Field | `A-full` | `A-matched` | `B` | `C-matched` | `C-matched-balanced` | `C-full` | Semantic Equivalence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`base_model_name_or_path`** | `...all-MiniLM-L6-v2` | `...all-MiniLM-L6-v2` | `...all-MiniLM-L6-v2` | `...all-MiniLM-L6-v2` | `...all-MiniLM-L6-v2` | `...all-MiniLM-L6-v2` | **IDENTICAL** |
| **`peft_type`** | `LORA` | `LORA` | `LORA` | `LORA` | `LORA` | `LORA` | **IDENTICAL** |
| **`task_type`** | `FEATURE_EXTRACTION` | `FEATURE_EXTRACTION` | `FEATURE_EXTRACTION` | `FEATURE_EXTRACTION` | `FEATURE_EXTRACTION` | `FEATURE_EXTRACTION` | **IDENTICAL** |
| **`r`** | `16` | `16` | `16` | `16` | `16` | `16` | **IDENTICAL** |
| **`lora_alpha`** | `32` | `32` | `32` | `32` | `32` | `32` | **IDENTICAL** |
| **`lora_dropout`** | `0.05` | `0.05` | `0.05` | `0.05` | `0.05` | `0.05` | **IDENTICAL** |
| **`target_modules`** | `{"query", "value"}` | `{"query", "value"}` | `{"query", "value"}` | `{"query", "value"}` | `{"query", "value"}` | `{"query", "value"}` | **IDENTICAL SET** |
| **`bias`** | `none` | `none` | `none` | `none` | `none` | `none` | **IDENTICAL** |
| **`modules_to_save`** | `null` | `null` | `null` | `null` | `null` | `null` | **IDENTICAL** |
| **`init_lora_weights`** | `true` | `true` | `true` | `true` | `true` | `true` | **IDENTICAL** |
| **`inference_mode`** | `true` | `true` | `true` | `true` | `true` | `true` | **IDENTICAL** |
| **`revision`** | `null` | `null` | `null` | `null` | `null` | `null` | **IDENTICAL** |

Normalized dictionary comparison (`target_modules=sorted(...)`) asserts 100% dictionary equality across all six checkpoints.

---

## 3. Checkpoint Integrity & Provenance Audit

Every adapter checkpoint directory was inspected and validated against the Phase 2 training execution summary:

| Checkpoint Name | Checkpoint Path | Weights File Size | `adapter_model.safetensors` SHA256 | `soup_run.json` Base Revision | Base Source | Trainable Parameters | Status |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **`A-full`** | [`output_embedding/`](file:///Users/pernavjain/Documents/soup-rag-prototype/output_embedding) | 593,072 B | `4dceadcb293ef4805d3bf1e0200e5d7fc8f0c05a6ed190528f9eb8fc56a88534` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |
| **`A-matched`** | [`output/adapter_exp_a_matched`](file:///Users/pernavjain/Documents/soup-rag-prototype/output/adapter_exp_a_matched) | 593,072 B | `81c35eeda72341bd5460eb3af547e2e52e0c5829c39c59a3103a2e90c7adebb1` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |
| **`B`** | [`output/adapter_exp_b`](file:///Users/pernavjain/Documents/soup-rag-prototype/output/adapter_exp_b) | 593,072 B | `7ce33a5063deaa91c8f38d2bdab96d81a196ca129a01e86515bbc69429009c8a` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |
| **`C-matched`** | [`output/adapter_exp_c_matched`](file:///Users/pernavjain/Documents/soup-rag-prototype/output/adapter_exp_c_matched) | 593,072 B | `6fe28922a98f6c13afbb3709cd9486f2b2173166802d61831852d992ba3f21b5` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |
| **`C-matched-balanced`** | [`output/adapter_exp_c_matched_balanced`](file:///Users/pernavjain/Documents/soup-rag-prototype/output/adapter_exp_c_matched_balanced) | 593,072 B | `25e0064078516ff068b6db2bface1065059f0d44a7a33592e8c0eb2094367137` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |
| **`C-full`** | [`output/adapter_exp_c_full`](file:///Users/pernavjain/Documents/soup-rag-prototype/output/adapter_exp_c_full) | 593,072 B | `145df326e64e6043d4fa313a1ef59d7ee958a705114978d1a3eaf7cb24fc0355` | `1110a243fdf4...` | `hub_commit` | 147,456 (0.65%) | **VERIFIED** |

- **Directory Completeness:** Each checkpoint directory contains `adapter_model.safetensors`, `adapter_config.json`, `soup_run.json`, and `README.md`.
- **Baseline Preservation:** The historical `A-full` baseline was not overwritten, modified, or touched during or after Phase 2 execution.

---

## 4. Inference Pipeline Smoke Testing

All six models were loaded through the retrieval evaluation pipeline ([`DenseRetriever`](file:///Users/pernavjain/Documents/soup-rag-prototype/scripts/retrievers.py#L81) in `scripts/retrievers.py`) using base model `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

### 4.1 Fixed Smoke Test Inputs
1. *"How do I configure LoRA fine-tuning for embedding models?"*
2. *"What is the Wald sequential probability ratio test?"*
3. *"Soup documentation for gradient accumulation and multi-GPU training."*
4. *"Differences between DPO and SFT training tasks."*

### 4.2 Smoke Test Validation Results

| Checkpoint | Loading Success | Output Shape | Numerical Health | L2 Norm Range | Determinism ($\Delta$) | Sample Embedding Vector (Input 0, First 3 Dimensions) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`A-full`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.04877, -0.12113, +0.01815]` |
| **`A-matched`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.04795, -0.11973, +0.01535]` |
| **`B`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.04480, -0.11883, +0.01513]` |
| **`C-matched`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.04272, -0.11061, -0.00559]` |
| **`C-matched-balanced`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.05214, -0.11241, +0.00598]` |
| **`C-full`** | **PASS** | `(4, 384)` | 0 NaN, 0 Inf | `[1.000000, 1.000000]` | $0.00\times 10^0$ | `[+0.02379, -0.10751, -0.00287]` |

**Observations:**
- Every checkpoint initialized without warnings or layer-name mismatches.
- All embedding tensors strictly conform to 384-dimensional unit spheres.
- Embeddings are distinct across training regimes, demonstrating that each adapter acquired unique parameter weights reflecting its training dataset.
- Repeating inference on identical inputs within the runtime yielded bit-identical results ($\Delta = 0.00\times 10^0$).

*(Note: In strict accordance with execution restrictions, zero benchmark queries were evaluated, and zero retrieval metrics were computed).*

---

## 5. Invariant Test Suite Execution

A dedicated invariant test file ([`tests/test_phase2_1_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_phase2_1_invariants.py)) was created to programmatically enforce:
1. Exact cryptographic checksum matching across all six weights, configs, and run metadata files.
2. Semantic parity and normalized dictionary equality across all six `adapter_config.json` files.
3. Successful `DenseRetriever` instantiation and embedding generation across all six models.

Full pytest suite execution:
```
============================= 174 passed in 21.90s =============================
```
All **174 tests** pass cleanly with 0 failures, 0 regressions, and 0 warnings.

---

## 6. Final GO/NO-GO Recommendation

- **Architecture Compatibility:** **GO** (All six adapters share byte-compatible PEFT rank-16 LoRA architectures targeting BERT `query` and `value` matrices).
- **Artifact Integrity:** **GO** (All weight tensors, configurations, and provenance records match recorded cryptographic digests).
- **Inference Pipeline:** **GO** (Tested through native `DenseRetriever` with perfect numerical health and deterministic outputs).
- **Evaluation Benchmark:** **GO** (All 54 frozen manual evaluation queries and 1,068 retrieval chunks are intact and ready).

**Final Recommendation:** **GO** to proceed with Phase 3 Multi-Retriever Benchmark Evaluation across all 8 retrievers (BM25, Frozen MiniLM, Frozen E5-small, A-full, A-matched, B, C-matched, C-matched-balanced, C-full).
