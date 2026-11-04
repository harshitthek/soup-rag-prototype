# Phase 1.10 Final Experiment Lock & Evaluation Taxonomy Reconciliation Report

**Project:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Timestamp:** 2026-11-04  
**Audit Status:** Complete — Taxonomy Reconciled, Revision Pinning Audited, LoRA Config Locked, Invariants Passing (**150/150 Tests Passing**), Retraining Gate Pending Approval  

---

## 1. Executive Summary

Phase 1.10 resolves the two final experimental integrity issues identified in Phase 1.9:
1. **Query Overlap Taxonomy Reconciliation:** Reconciled the discrepancy between the Phase 0 audit and Phase 1.9 reports across the 9 union query IDs (`manual_003`, `manual_005`, `manual_020`, `manual_023`, `manual_024`, `manual_025`, `manual_030`, `manual_047`, `manual_048`). Conducted passage-level evidence inspection across the 23 vendored candidate documents (`benchmarks/` and `changelog.d/`), establishing that **exactly 2 queries** exhibit partial conceptual overlap (`manual_025` and `manual_048`) and **52 queries are clean**.
2. **Base Model Revision Lock Audit:** Evaluated Soup's native `BaseRevision` mechanism against the pinned commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Documented the existing runtime boundary (dynamic Hub HEAD query vs. local cache snapshot), established pre-flight assertion safeguards, and defined the minimal upstream Soup schema extension required for first-class declarative revision pinning.
3. **Explicit LoRA Configuration Parity:** Replaced `target_modules: auto` and implicit dropout across all six YAML configs with explicit declarations (`r: 16`, `alpha: 32`, `dropout: 0.05`, `target_modules: ["query", "value"]`). Verified via dry-run and PEFT inspection that the resolved architecture is byte-for-byte identical to the existing `output_embedding/adapter_config.json` (147,456 trainable parameters, 0.65% of base).
4. **Invariant Testing:** Added `tests/test_phase1_10_invariants.py`. The complete test suite now executes **150 tests, with 100% passing (0 failures, 0 regressions)**.

---

## 2. Query-by-Query Overlap Reconciliation

### 2.1 The 9-Query Union Reconciliation Table

The union of flagged queries between Phase 0 (`manual_020`, `manual_025`, `manual_030`, `manual_047`, `manual_048`) and Phase 1.9 (`manual_003`, `manual_005`, `manual_023`, `manual_024`, `manual_048`) was audited against the actual text of the 23 candidate documents:

| Query ID | Original Core Classification | Phase 0 Classification | Phase 1.9 Classification | Final Candidate Classification | Evidence Document | Justification |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `manual_003` | primary | clean (absent) | partial_overlap | **Clean** | None (Absent from all 23 docs) | **Phase 1.9 error corrected.** Phase 1.9 hallucinated an overlap with `architecture.md` / `SOUP_DATA_DIR`. In reality, `manual_003` asks *"how do I see which training rows influenced an adapter"*, which is answered by `soup adapters blame` and DataInf in `adapters-and-governance.md`. Neither DataInf nor adapter blame exists in the candidate docs. Occurrences of the word "blame" in candidate docs (`gate-974`, `gate-v0.72.4`) are colloquial debugging notes on disk I/O and CI benchmarks. |
| `manual_005` | overlap | clean (absent) | partial_overlap | **Clean** | None (Absent from all 23 docs) | **Phase 1.9 error corrected.** Phase 1.9 hallucinated an overlap with `eval_framework.md` / `SOUP_EVAL_SPLIT`. In reality, `manual_005` asks *"does soup roll back a canary automatically if the eval regresses"*, which covers `soup loop canary --autoroll-on-regress`. Canary promotion and auto-rollback are entirely absent from candidate docs. |
| `manual_020` | overlap | partial_overlap | clean | **Clean** | None (Absent from all 23 docs) | **Phase 0 error corrected.** Phase 0 misclassified `manual_020` (*"what ends up in the generated model card"*) by misinterpreting `gate-836-bench-train-contract.md`'s GPU hardware report line (`RTX 5070 Laptop GPU \| nvidia-smi; report provenance.card`) as a model card reference. Passage inspection confirms `gate-836` contains zero references to `MODELCARD.md`, `soup card`, or compliance model card autogen. |
| `manual_023` | primary | clean (absent) | partial_overlap | **Clean** | None (Absent from all 23 docs) | **Phase 1.9 error corrected.** Phase 1.9 cited nonexistent `lora_tuning_guide.md`. `manual_023` asks *"which expectation checks can go in expectations.yaml"*. Neither `expectations.yaml` nor `soup expect` suites appear in candidate docs (the single occurrence of "expectation" in `unsloth-4bit-weight-dtypes.md` refers to test assertion expectations). |
| `manual_024` | primary | clean (absent) | partial_overlap | **Clean** | None (Absent from all 23 docs) | **Phase 1.9 error corrected.** Phase 1.9 cited nonexistent `cli_reference.md`. `manual_024` asks *"what steps does soup's compliance workflow cover"*. The compliance CLI workflow (`soup init --template`, `soup train --repro-receipt`, `soup bom emit`, `soup attest emit`, `soup adapters sign/verify`, `soup airgap-bundle`) is completely absent from candidate docs. |
| `manual_025` | primary | partial_overlap | clean | **Partial Conceptual Overlap** | `benchmarks/gate-v0.72.4-preference-losses.md` | **Phase 1.9 omission corrected; Phase 0 verified.** `gate-v0.72.4-preference-losses.md` extensively analyzes and benchmarks DPO vs. SFT memory scaling, peak VRAM differences (0.914x ratio), implicit reference model handling, and forward pass stack traversals (SFT=2x, DPO=3x). While the normative decision rubric (paired chosen/rejected rows -> DPO) is exclusive to `evaluation.md`, the empirical and architectural comparison between DPO and SFT constitutes genuine partial conceptual overlap. |
| `manual_030` | primary | partial_overlap (pre-exclusion) / clean (post-exclusion) | clean | **Clean** | None (in 23 approved docs) | **Reconciled.** Phase 0 originally noted overlap with `benchmarks/README.md` (which summarized `soup ab` mSPRT bounds). However, `benchmarks/README.md` was explicitly excluded from candidate vendoring in Phase 0. In the 23 approved candidate documents, `soup ab` and Wald SPRT stopping bounds are completely absent (the word "sequential" in `gate-971`/`gate-974` refers only to sequential disk reads). |
| `manual_047` | primary | partial_overlap | clean | **Clean** | None (Absent from all 23 docs) | **Phase 0 error corrected.** Phase 0 misread `gate-836-bench-train-contract.md` line 115 (`LoRA is r: 16, alpha: 32, dropout: 0.0 on q_proj/v_proj throughout`), assuming it set differential projection learning rates. Passage audit confirms `gate-836` used a standard uniform learning rate across all target modules. Neither per-module learning rates (`lr_groups`) nor LoRA+ multipliers appear in candidate docs. |
| `manual_048` | primary | partial_overlap | partial_overlap | **Partial Conceptual Overlap** | `benchmarks/gate-v0.72.0-layer-streaming.md` | **Unanimously verified.** `gate-v0.72.0-layer-streaming.md` discusses PiSSA initialization: *"HIGH — DoRA / VeRA / PiSSA / OLoRA read the real base weight at get_peft_model() time and crash opaquely on meta. Now refused by name at config-parse."* This directly discusses PiSSA base-weight initialization mechanisms, constituting partial conceptual overlap with the PiSSA initialization feature in `peft-and-efficiency.md`. |

---

## 3. Final Four-Way Evaluation Partition Matrix

Based on the verified classification across all 54 frozen evaluation queries:
- **Core Benchmark Scheme (8 Core Docs):** 39 Primary vs. 15 Overlap.
- **Candidate Benchmark Scheme (23 Candidate Docs):** 52 Clean vs. 2 Partial Conceptual Overlap (`manual_025`, `manual_048`).

### 3.1 Four-Way Intersection Table

```
                                  Final Candidate Scheme (23 Docs)
                              Candidate Clean    Candidate Partial Overlap    Total
                            ─────────────────   ─────────────────────────   ───────
Core Primary (8 Docs)              37                       2                  39
Core Overlap (8 Docs)              15                       0                  15
                            ─────────────────   ─────────────────────────   ───────
Total                              52                       2                  54
```

### 3.2 Evaluation Metric Reporting Contract

Post-training evaluation reports will break down retrieval metrics across all six mutually exclusive or nested evaluation slices:

1. **Full Benchmark (54 queries):** Overall macro and micro retrieval performance ($n=54$).
2. **Core Primary Slice (39 queries):** Queries whose answers appear exclusively in the 4 held-out documents relative to the 8 core training documents ($n=39$).
3. **Core Overlap Slice (15 queries):** Queries whose answers also appear in the 8 core training documents ($n=15$).
4. **Candidate Clean Slice (52 queries):** Queries with zero answer or conceptual overlap in the 23 newly added candidate documents ($n=52$).
5. **Candidate Partial Overlap Slice (2 queries):** The two queries (`manual_025`, `manual_048`) that touch concepts benchmarked in the candidate documents ($n=2$).
6. **Pure Held-Out Slice (37 queries):** The purest generalization evaluation set — queries that are **both** `Core Primary` and `Candidate Clean` ($n=37$).

---

## 4. Immutable Base Model Revision Lock Analysis

### 4.1 Native Soup Revision Resolution Mechanics

In Soup (`src/soup_cli/utils/run_provenance.py`), `BaseRevision` implements base model tracking:
```python
revision = get_hf_api().model_info(self.base, timeout=5).sha
if isinstance(revision, str) and _REVISION.fullmatch(revision):
    self.revision, self.source = revision, "hub_commit"
```
When `base: sentence-transformers/all-MiniLM-L6-v2` is passed:
1. `BaseRevision` calls Hugging Face Hub `model_info()` dynamically at run initialization.
2. It currently resolves to commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
3. In `base_revision_kwargs()`, it returns `{"revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"}`, which is forwarded to `AutoModel.from_pretrained()` and `AutoTokenizer.from_pretrained()`.
4. When training finishes, `write_run_provenance()` records `"base_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"` into `soup_run.json`.

### 4.2 Identified Integrity Risks
1. **Upstream Drift:** If Hugging Face Hub repository HEAD advances, `model_info()` would resolve to the new commit SHA, causing newly trained models to diverge from the existing `A-full` checkpoint.
2. **Network/Offline Failure:** If Hugging Face Hub API is unreachable or times out, `BaseRevision` catches the exception and sets `self.source = "resolution_failed"`, returning `{}` and silently falling back to unversioned loading.

### 4.3 Prototype Pre-Flight Enforcement Safeguards

To strictly enforce immutability without modifying upstream Soup:
1. **Pre-Training Gate:** A programmatic pre-flight assertion verifies that `HfApi().model_info("sentence-transformers/all-MiniLM-L6-v2").sha == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"`. If the Hub HEAD drifts or cannot be verified, training aborts before launching.
2. **Local Cache Verification:** Test `test_base_revision_lock_integrity()` verifies that the local cache snapshot `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41` exists with valid `model.safetensors` and `config.json`.
3. **Post-Training Provenance Verification:** Every completed training run's `soup_run.json` will be asserted to contain `"base_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"` and `"base_revision_source": "hub_commit"`.

### 4.4 Proposed Upstream Soup Implementation Change

For upstream Soup to support first-class declarative revision pinning:
1. **Schema Extension (`soup_cli/config/schema.py`):**
   ```python
   base_revision: Optional[str] = Field(
       default=None,
       pattern=r"^[0-9a-f]{40}$",
       description="Explicit 40-hex Git commit SHA for base model revision pinning."
   )
   ```
2. **Provenance Scope Update (`soup_cli/utils/run_provenance.py`):**
   Accept `explicit_revision: str | None = None` in `BaseRevision`. If specified, skip the dynamic Hub HEAD query and directly bind `self.revision = explicit_revision; self.source = "hub_commit"`. If the requested revision cannot be loaded by `AutoModel`, raise a hard failure.

---

## 5. Explicit LoRA Configuration & Dependency Matrix

### 5.1 Updated YAML Configuration Syntax

All six experiment configuration files (`config/embedding_exp_*.yaml`) were updated to explicitly document LoRA hyperparameters:
```yaml
  lora:
    r: 16
    alpha: 32
    dropout: 0.05
    target_modules:
      - query
      - value
```

### 5.2 PEFT Architecture Verification

Direct instantiation with PEFT 0.21.2 confirms exact architectural parity with `output_embedding/adapter_config.json`:
- **LoRA Rank ($r$):** 16
- **LoRA Alpha ($\alpha$):** 32
- **LoRA Dropout:** 0.05
- **Target Modules:** `["query", "value"]`
- **Base Architecture:** `BertModel` (6 layers, 12 attention heads, hidden dim 384)
- **Trainable Parameters:** 147,456 (0.65% of base)
- **Total Parameters:** 22,860,672

### 5.3 Pinned Runtime Dependency Versions

The exact installed package versions across the training runtime (`/Users/pernavjain/Documents/Soup/.venv`) and evaluation runtime (`./.venv`) are recorded:

| Dependency | Training Runtime (`Soup .venv`) | Prototype Runtime (`rag .venv`) | Role |
| :--- | :---: | :---: | :--- |
| **Python** | `3.10.20` | `3.14.7` | Execution interpreter |
| **PyTorch** | `2.14.1` | `2.15.0` | Tensor backend & MPS acceleration |
| **Transformers** | `5.18.0` | `5.22.1` | Model loading & tokenization |
| **PEFT** | `0.21.2` | `0.21.2` | LoRA adapter layers |
| **Tokenizers** | `0.23.2` | `0.23.3` | Fast BPE / WordPiece tokenizer |
| **PyYAML** | `6.0.3` | `6.0.3` | Configuration parsing |
| **Sentence Transformers** | *N/A (Native)* | *N/A (Native)* | Soup uses native AutoModel + Cosine Loss |

---

## 6. Complete Test Results & Frozen Checksum Verification

### 6.1 Frozen File Checksums

All 5 canonical evaluation files remain 100% bit-exact and unaltered:
- `data/corpus.jsonl`: `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3`
- `data/manual_queries.jsonl`: `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3`
- `data/eval_queries.jsonl`: `7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3`
- `data/train_query_labels.jsonl`: `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae`
- `data/train_triplets.jsonl`: `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75`

### 6.2 Full Test Suite Execution

Executed `./.venv/bin/pytest`:
```
============================= 150 passed in 22.79s =============================
```
- `tests/test_compare_retrievers.py`: 14 passed
- `tests/test_manual_queries_validation.py`: 25 passed
- `tests/test_phase1_10_invariants.py`: 6 passed
- `tests/test_phase1_5_invariants.py`: 18 passed
- `tests/test_phase1_6_invariants.py`: 5 passed
- `tests/test_phase1_7_invariants.py`: 3 passed
- `tests/test_phase1_8_invariants.py`: 4 passed
- `tests/test_phase1_invariants.py`: 13 passed
- `tests/test_retrieval_metrics.py`: 21 passed
- `tests/test_retrieval_pipeline.py`: 15 passed
- `tests/test_retrievers.py`: 16 passed
- `tests/test_run_retrieval.py`: 5 passed
- `tests/test_v1_dataset_invariants.py`: 5 passed

---

## 7. Retraining Gate Decision Matrix

All prerequisites for adapter training are met:
- **Taxonomy:** 54 evaluation queries partitioned into 37 pure held-out, 2 candidate partial overlap, and 15 core overlap.
- **Data:** Training datasets validated, hard negatives mined with sibling masking, query types stratified and balanced.
- **Arithmetic:** Exact batch sizes and step counts verified (1,857 updates for matched runs; 5,079 updates for C-full).
- **Configurations:** 6 explicit, self-documenting YAML configurations dry-run validated.
- **Base Model:** Locked to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

### Path A Training Decisions

| Experiment | Configuration | Training Dataset | Optimizer Updates | Output Path | Decision |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **`A-matched`** | `config/embedding_exp_a_matched.yaml` | `triplets_exp_a_matched_v1_5.jsonl` | 1,857 | `output/adapter_exp_a_matched` | **GO** |
| **`B`** | `config/embedding_exp_b.yaml` | `triplets_exp_b_v1_5.jsonl` | 1,857 | `output/adapter_exp_b` | **GO** |
| **`C-matched`** | `config/embedding_exp_c_matched.yaml` | `triplets_exp_c_matched_v1_5.jsonl` | 1,857 | `output/adapter_exp_c_matched` | **GO** |
| **`C-matched-balanced`** | `config/embedding_exp_c_matched_balanced.yaml` | `triplets_exp_c_matched_balanced_v1_6.jsonl` | 1,857 | `output/adapter_exp_c_matched_balanced` | **GO** |
| **`C-full`** | `config/embedding_exp_c_full.yaml` | `triplets_exp_c_full_v1_5.jsonl` | 5,079 | `output/adapter_exp_c_full` | **GO** |

*(Note: Model training and retrieval evaluation remain strictly gated awaiting explicit user authorization).*
