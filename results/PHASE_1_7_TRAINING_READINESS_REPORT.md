# Phase 1.7 Final Training Readiness Audit Report

**Project:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Timestamp:** 2026-11-04  
**Status:** Audit Complete — All Invariants Verified, Retraining Gate Pending Approval  

---

## 1. Executive Summary

Phase 1.7 performs the final pre-training audit of the experimental configuration, dataloader arithmetic, variable isolation semantics, source document distributions, test suite modifications, and frozen benchmark integrity.

**Key Findings:**
1. **Optimizer Update Arithmetic:** Verified against the official Soup training implementation (`soup_cli/trainer/embedding.py`). Hugging Face `Trainer` processes datasets epoch by epoch with `dataloader_drop_last=False` for triplet loss. The actual optimizer update count for `C-full` is **5,079 updates** ($1,693\text{ steps/epoch} \times 3\text{ epochs}$), not 5,078. The previous figure of 5,078 was an artifact of global integer division across epoch boundaries.
2. **Comparison Terminology Revised:** Updated comparison definitions to eliminate the claim that all five comparisons isolate a single independent variable. Clearly distinguished strictly controlled variables from co-varying variables.
3. **Source Document Distribution:** Verified document coverage across Experiment B (8 docs), C-matched (31 docs), and C-matched-balanced (31 docs). Confirmed **all 31 documents are represented** in C-matched-balanced. In Experiment B, 5 core docs each contribute ~17.5% of total queries; in C-matched-balanced, maximum single-document concentration drops to **8.12%**.
4. **Test Modification Audited:** Inspected the Git diff of `tests/test_retrieval_pipeline.py`. The modification removed an invalid `@classmethod` decorator on a class-scoped fixture that caused Pytest 8.4 discovery failure under Python 3.14. **Zero assertions were removed or weakened**, restoring 3 broken integration tests to active passing status.
5. **Frozen Checksum Integrity:** All 5 canonical benchmark files remain bit-exact identical to their approved SHA256 hashes.
6. **Recommendation:** **GO** for all five experimental adapter training runs upon user approval.

---

## 2. Optimizer Update Count Verification

### 2.1 Implementation Inspection (`soup_cli/trainer/embedding.py`)
In the official Soup codebase (`/Users/pernavjain/Documents/Soup/src/soup_cli/trainer/embedding.py`, lines 177–220):
- **Loss Type:** Configured as `triplet` margin loss (`config/embedding.yaml`, line 20).
- **Drop Last Behavior:**
  ```python
  "dataloader_drop_last": (loss_type == "contrastive"),
  ```
  Because `loss_type == "triplet"`, `dataloader_drop_last` evaluates to `False`. Partial batches at the end of each epoch are **retained and trained**.
- **Batch Size & Gradient Accumulation:** `per_device_train_batch_size = 4`, `gradient_accumulation_steps = 1`.
- **Dataloader Length:** Hugging Face `Trainer` constructs the dataloader per epoch using PyTorch `DataLoader`. With $N$ samples and batch size $B$, `len(dataloader)` is:
  $$\text{batches\_per\_epoch} = \left\lceil \frac{N}{B} \right\rceil$$
- **Optimizer Updates per Epoch:** With `gradient_accumulation_steps = 1`, every dataloader iteration triggers an optimizer step:
  $$\text{updates\_per\_epoch} = \left\lfloor \frac{\text{batches\_per\_epoch}}{\text{gradient\_accumulation\_steps}} \right\rfloor = \left\lceil \frac{N}{B} \right\rceil$$
- **Total Training Steps:** Across $E = 3$ epochs:
  $$\text{total\_updates} = E \times \left\lceil \frac{N}{B} \right\rceil$$

### 2.2 Dataset Step Calculations

| Dataset | Total Triplets ($N$) | Batch Size ($B$) | Batches / Epoch ($\lceil N/B \rceil$) | Epochs ($E$) | Actual Optimizer Updates ($E \times \lceil N/B \rceil$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`A-full`** | 3,234 | 4 | 809 | 3 | **2,427** |
| **`A-matched`** | 2,475 | 4 | 619 | 3 | **1,857** |
| **`B`** | 2,475 | 4 | 619 | 3 | **1,857** |
| **`C-matched`** | 2,475 | 4 | 619 | 3 | **1,857** |
| **`C-matched-balanced`** | 2,475 | 4 | 619 | 3 | **1,857** |
| **`C-full`** | 6,771 | 4 | 1,693 | 3 | **5,079** |

### 2.3 Explanation of Discrepancy (5,079 vs. 5,078)
- The earlier figure of **5,078** was calculated using global floor division across the total sample exposure of the entire 3-epoch run:
  $$\lfloor (6,771 \times 3) / 4 \rfloor = \lfloor 20,313 / 4 \rfloor = 5,078$$
- That calculation implicitly assumed that fractional sample remnants across epochs accumulate into full batches across epoch boundaries.
- In reality, PyTorch `DataLoader` iterates strictly per epoch:
  - In each epoch, 6,771 samples are partitioned into **1,692 full batches of 4** and **1 partial batch of 3** ($6,771 = 1,692 \times 4 + 3$).
  - Because `dataloader_drop_last=False`, that partial batch is executed as step 1,693 in each epoch.
  - Across 3 epochs, the optimizer updates exactly:
    $$1,693 \times 3 = 5,079\text{ updates}$$
- The identical phenomenon occurs in the matched budget runs: $2,475 = 618 \times 4 + 3$, yielding $\lceil 2475/4 \rceil = 619$ batches per epoch and $619 \times 3 = 1,857$ updates (whereas $(2475 \times 3) // 4 = 7425 // 4 = 1856$).
- The actual executed step count for `C-full` in `Trainer.train()` is **5,079 updates**.

---

## 3. Revised Experimental Comparison Definitions

Empirical ML comparisons rarely isolate a single theoretical parameter in a vacuum. To preserve experimental integrity, the 5 comparisons are formally defined with explicit acknowledgment of controlled variables and co-varying factors:

### 3.1 Comparison Definitions and Controlled Variables

#### 1. `A-matched` vs. `B` — Query Generation Strategy Comparison
- **Formal Description:** Query generation strategy comparison, with matched positive chunk multiset and update budget.
- **Controlled Variables:** 
  - Training corpus: 8 core documents.
  - Positive chunk multiset: 100% identical chunk IDs and frequencies across all 825 queries.
  - Negative mining method: dense MiniLM similarity with section-level sibling masking.
  - Training budget: 825 queries, 2,475 triplets, 1,857 optimizer updates.
- **Compared Factor:** Synthetic template queries (derived mechanically from document headings) vs. diverse LLM-generated questions (synthesized with semantic variety and paraphrasing).

#### 2. `B` vs. `C-matched-balanced` — Expanded Corpus and Associated Training Examples Comparison
- **Formal Description:** Expanded corpus and associated training examples under matched query type proportions and update budget.
- **Controlled Variables:**
  - Query generation model: Gemini 2.5 Flash with grounded prompts.
  - Query count & budget: 825 queries, 2,475 triplets, 1,857 optimizer updates.
  - Query type distribution: identical proportions (327 `how_to`, 309 `conceptual`, 184 `parameter`, 5 `troubleshooting`).
  - Negative mining method: dense MiniLM similarity with section-level sibling masking.
- **Co-Varying Factors:**
  - Underlying document set: 8 core docs (586 chunks) vs. 31 expanded docs (1,522 chunks).
  - Training passages: positive chunks are distributed across 31 documents rather than concentrated in 8 documents.

#### 3. `C-matched` vs. `C-matched-balanced` — Sampling and Query Type Distribution Strategy Comparison
- **Formal Description:** Sampling and query type distribution strategy comparison.
- **Controlled Variables:**
  - Training corpus: 31 expanded documents (1,522 chunks).
  - Candidate pool: `C-full v1.5` dataset.
  - Training budget: 825 queries, 2,475 triplets, 1,857 optimizer updates.
  - Negative mining method: dense MiniLM similarity with section-level sibling masking.
- **Compared Factor:** Natural unconstrained distribution (70.67% conceptual, 20.73% how-to, 8.48% parameter, 0.12% troubleshooting) vs. stratified balanced distribution matching core documentation proportions (37.45% conceptual, 39.64% how-to, 22.30% parameter, 0.61% troubleshooting).

#### 4. `C-matched-balanced` vs. `C-full` — Full Data Regime Comparison
- **Formal Description:** Full data regime comparison, combining dataset size, query coverage, distribution and optimizer budget.
- **Controlled Variables:**
  - Training corpus: 31 expanded documents.
  - Query generation model: Gemini 2.5 Flash grounded.
  - Negative mining method: dense MiniLM similarity with section-level sibling masking.
- **Co-Varying Factors:**
  - Dataset size: 825 queries / 2,475 triplets vs. 2,257 queries / 6,771 triplets.
  - Corpus chunk coverage: 565 chunks (partial) vs. 1,522 chunks (100% full coverage).
  - Query distribution: balanced 4-way quota vs. full natural distribution.
  - Training budget: 1,857 updates vs. 5,079 updates.

#### 5. `A-full` vs. `A-matched` — Synthetic Baseline Training Budget Sensitivity
- **Formal Description:** Synthetic baseline training budget sensitivity.
- **Controlled Variables:**
  - Training corpus: 8 core documents.
  - Query generation strategy: synthetic heading templates.
  - Negative mining method: dense MiniLM similarity with section-level sibling masking.
- **Compared Factor:** Optimizer update budget and example volume (1,078 queries / 2,427 updates vs. 825 queries / 1,857 updates).

---

## 4. Source Document Distribution Analysis

The table below reports queries per source document, unique positive chunks, query-to-chunk ratios, query type breakdowns, and percentage contributions across Experiment B (8 docs), Experiment C-matched (31 docs), and Experiment C-matched-balanced (31 docs):

### 4.1 Complete Document Distribution Table

| Source Document | Exp B Queries (%) [Chunks, Q/C] | Exp B Query Types | Exp C-matched Queries (%) [Chunks, Q/C] | Exp C-matched Query Types | Exp C-matched-balanced Queries (%) [Chunks, Q/C] | Exp C-matched-balanced Query Types |
| :--- | :---: | :--- | :---: | :--- | :---: | :--- |
| **`backends-and-ops.md`** | 145 (17.58%) [99, 1.46] | 74 how, 39 con, 31 par, 1 trb | 39 (4.73%) [21, 1.86] | 21 how, 11 con, 7 par | **67 (8.12%)** [58, 1.16] | 27 how, 14 con, 24 par, 2 trb |
| **`data.md`** | 145 (17.58%) [99, 1.46] | 69 how, 29 con, 46 par, 1 trb | 38 (4.61%) [23, 1.65] | 18 how, 11 con, 9 par | **64 (7.76%)** [58, 1.10] | 27 how, 13 con, 24 par |
| **`performance-and-quantization.md`** | 145 (17.58%) [102, 1.42] | 49 how, 65 con, 31 par | 38 (4.61%) [23, 1.65] | 14 how, 17 con, 7 par | **63 (7.64%)** [55, 1.15] | 26 how, 13 con, 24 par |
| **`serving-and-export.md`** | 144 (17.45%) [95, 1.52] | 71 how, 37 con, 36 par | 38 (4.61%) [23, 1.65] | 17 how, 14 con, 7 par | **62 (7.52%)** [54, 1.15] | 26 how, 13 con, 23 par |
| **`training.md`** | 144 (17.45%) [111, 1.30] | 35 how, 78 con, 31 par | 38 (4.61%) [23, 1.65] | 15 how, 16 con, 7 par | **62 (7.52%)** [53, 1.17] | 26 how, 13 con, 23 par |
| **`commands.md`** | 67 (8.12%) [59, 1.14] | 21 how, 36 con, 8 par, 2 trb | 38 (4.61%) [23, 1.65] | 14 how, 17 con, 7 par | **60 (7.27%)** [43, 1.40] | 27 how, 13 con, 19 par, 1 trb |
| **`models.md`** | 26 (3.15%) [16, 1.62] | 6 how, 18 con, 1 par, 1 trb | 20 (2.42%) [13, 1.54] | 4 how, 15 con, 1 par | **17 (2.06%)** [15, 1.13] | 3 how, 13 con, 1 par |
| **`README.md`** | 9 (1.09%) [5, 1.80] | 2 how, 7 con | 9 (1.09%) [5, 1.80] | 2 how, 7 con | **10 (1.21%)** [6, 1.67] | 3 how, 7 con |
| `benchmarks/gate-974-disk-tier-direct-io.md` | — | — | 38 (4.61%) [27, 1.41] | 6 how, 31 con, 1 par | **42 (5.09%)** [42, 1.00] | 27 how, 14 con, 1 par |
| `benchmarks/gate-971-async-nvme-source.md` | — | — | 39 (4.73%) [25, 1.56] | 5 how, 25 con, 9 par | **40 (4.85%)** [36, 1.11] | 15 how, 14 con, 11 par |
| `benchmarks/gate-836-bench-train-contract.md` | — | — | 39 (4.73%) [25, 1.56] | 6 how, 31 con, 2 par | **38 (4.61%)** [35, 1.09] | 16 how, 14 con, 7 par, 1 trb |
| `benchmarks/gate-v0.72.2-nf4.md` | — | — | 38 (4.61%) [26, 1.46] | 9 how, 26 con, 3 par | **34 (4.12%)** [32, 1.06] | 17 how, 13 con, 4 par |
| `benchmarks/gate-v0.72.3-breadth.md` | — | — | 37 (4.48%) [25, 1.48] | 8 how, 26 con, 3 par | **33 (4.00%)** [30, 1.10] | 15 how, 13 con, 5 par |
| `benchmarks/probe-v0.73.0-what-bounds-streaming.md` | — | — | 34 (4.12%) [22, 1.55] | 6 how, 26 con, 2 par | **26 (3.15%)** [24, 1.08] | 10 how, 13 con, 2 par, 1 trb |
| `benchmarks/gate-2049-resident-vram.md` | — | — | 39 (4.73%) [28, 1.39] | 7 how, 31 con, 1 par | **25 (3.03%)** [22, 1.14] | 8 how, 14 con, 3 par |
| `benchmarks/gate-2050-selective-checkpoint.md` | — | — | 39 (4.73%) [30, 1.30] | 9 how, 28 con, 2 par | **25 (3.03%)** [23, 1.09] | 9 how, 14 con, 2 par |
| `benchmarks/run-m1-8gb-mlx-sft.md` | — | — | 35 (4.24%) [23, 1.52] | 6 how, 27 con, 2 par | **25 (3.03%)** [22, 1.14] | 9 how, 13 con, 3 par |
| `benchmarks/gate-v0.72.0-layer-streaming.md` | — | — | 37 (4.48%) [25, 1.48] | 7 how, 29 con, 1 par | **24 (2.91%)** [22, 1.09] | 9 how, 14 con, 1 par |
| `benchmarks/run-t4-colab-free-tier.md` | — | — | 31 (3.76%) [22, 1.41] | 5 how, 26 con | **21 (2.55%)** [20, 1.05] | 8 how, 13 con |
| `benchmarks/gate-v0.72.4-preference-losses.md` | — | — | 31 (3.76%) [21, 1.48] | 5 how, 25 con, 1 par | **20 (2.42%)** [18, 1.11] | 6 how, 13 con, 1 par |
| `benchmarks/gate-655-pinned-store-accounting.md` | — | — | 27 (3.27%) [16, 1.69] | 27 con | **16 (1.94%)** [13, 1.23] | 14 con, 2 par |
| `benchmarks/unsloth-4bit-weight-dtypes.md` | — | — | 21 (2.55%) [13, 1.62] | 4 how, 17 con | **16 (1.94%)** [12, 1.33] | 4 how, 12 con |
| `benchmarks/gate-expert-streaming.md` | — | — | 24 (2.91%) [15, 1.60] | 23 con, 1 par | **15 (1.82%)** [12, 1.25] | 1 how, 13 con, 1 par |
| `changelog.d/README.md` | — | — | 4 (0.48%) [2, 2.00] | 4 con | **4 (0.48%)** [2, 2.00] | 4 con |
| `changelog.d/0.77.1/2185.fixed.md` | — | — | 4 (0.48%) [2, 2.00] | 2 how, 2 par | **3 (0.36%)** [2, 1.50] | 2 how, 1 par |
| `changelog.d/0.77.1/2329.changed.md` | — | — | 4 (0.48%) [2, 2.00] | 2 how, 2 par | **3 (0.36%)** [2, 1.50] | 1 how, 2 par |
| `changelog.d/0.77.1/2372.fixed.md` | — | — | 3 (0.36%) [3, 1.00] | 1 how, 2 con | **3 (0.36%)** [3, 1.00] | 1 how, 2 con |
| `changelog.d/0.77.1/2285.added.md` | — | — | 2 (0.24%) [2, 1.00] | 2 how | **2 (0.24%)** [2, 1.00] | 2 how |
| `changelog.d/0.77.1/2315.added.md` | — | — | 2 (0.24%) [1, 2.00] | 1 how, 1 con | **2 (0.24%)** [1, 2.00] | 1 how, 1 con |
| `changelog.d/0.77.1/2386.added.md` | — | — | 2 (0.24%) [2, 1.00] | 2 con | **2 (0.24%)** [2, 1.00] | 2 con |
| `changelog.d/0.77.1/2333.added.md` | — | — | 2 (0.24%) [1, 2.00] | 2 how | **1 (0.12%)** [1, 1.00] | 1 how |
| **Total** | **825 (100.0%)** | 8 docs | **825 (100.0%)** | 31 docs | **825 (100.0%)** | **31 docs** |

### 4.2 Distribution Analysis & Concentration Audit
1. **100% Document Coverage:** All 31 documents are confirmed to have active representation in `C-matched-balanced` (minimum queries = 1, maximum queries = 67).
2. **Reduced Document Concentration:**
   - In Experiment B, five documents (`backends-and-ops`, `data`, `performance-and-quantization`, `serving-and-export`, `training`) each contribute ~17.5% of total queries (collectively 87.6% of the dataset).
   - In `C-matched-balanced`, the maximum single-document contribution drops to **8.12%** (`backends-and-ops.md`), followed closely by `data.md` (7.76%), `performance-and-quantization.md` (7.64%), and `serving-and-export.md` (7.52%).
   - The top 6 documents represent 45.8% of the dataset, while benchmark engineering records represent 51.5% and unreleased changelog fragments represent 2.7%.
3. **Chunk-to-Query Ratio Stability:** Across all 31 documents in `C-matched-balanced`, the query-to-chunk ratio ranges between 1.00 and 2.00 (average 1.15), avoiding over-concentration on individual passages.

---

## 5. Audit of Test Modification (`tests/test_retrieval_pipeline.py`)

### 5.1 Git Diff Inspection
A working tree modification was recorded on `tests/test_retrieval_pipeline.py`:

```diff
diff --git a/tests/test_retrieval_pipeline.py b/tests/test_retrieval_pipeline.py
index b74e9f2..03158aa 100644
--- a/tests/test_retrieval_pipeline.py
+++ b/tests/test_retrieval_pipeline.py
@@ -247,9 +247,8 @@ class TestMiningLogicSynthetic:
 class TestMiningRealCorpusIntegration:
     """Integration test running mine_hard_negatives on real corpus to temp files."""
 
-    @classmethod
     @pytest.fixture(scope="class")
-    def mined_results(cls, tmp_path_factory):
+    def mined_results(self, tmp_path_factory):
         tmp_dir = tmp_path_factory.mktemp("mining_test")
         triplets_file = tmp_dir / "test_triplets.jsonl"
         hn_file = tmp_dir / "test_hard_negatives.jsonl"
```

### 5.2 Technical Justification
- **Why it was modified:** In Python 3.14 with Pytest 8.4, decorating a fixture with `@classmethod` causes Pytest's fixture collection mechanism to treat the method as an unbound classmethod descriptor, resulting in `fixture 'mined_results' not found` errors and breaking 3 integration tests.
- **What changed:** Removed `@classmethod` and adjusted parameter naming (`cls` $\to$ `self`) to comply with standard Pytest fixture signatures.
- **Assertion and Coverage Impact:** **Zero assertions were modified, removed, or weakened.**
  - `test_total_triplets_count` (asserts exactly 3,234 triplets) is actively passing.
  - `test_heading_prefix_prepended_to_pos_and_neg` (asserts canonical heading prefix formatting) is actively passing.
  - `test_section_deduplication_per_query` (asserts 1,078 queries, exactly 3 negatives per query, ranks 1-3, descending scores, base section uniqueness, zero positive section overlap) is actively passing.
- This change repaired fixture discovery and restored 3 integration tests without reducing test rigor.

---

## 6. Full Test Suite Results

The entire automated test suite was executed in the project virtualenv:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-8.4.2, pluggy-1.7.0
rootdir: /Users/pernavjain/Documents/soup-rag-prototype
plugins: anyio-4.15.1
collected 140 items

tests/test_compare_retrievers.py ..............                          [ 10%]
tests/test_manual_queries_validation.py .........................        [ 27%]
tests/test_phase1_5_invariants.py ..................                     [ 40%]
tests/test_phase1_6_invariants.py .....                                  [ 44%]
tests/test_phase1_7_invariants.py ...                                    [ 46%]
tests/test_phase1_invariants.py .............                            [ 55%]
tests/test_retrieval_metrics.py .....................                    [ 70%]
tests/test_retrieval_pipeline.py ...............                         [ 81%]
tests/test_retrievers.py ................                                [ 92%]
tests/test_run_retrieval.py .....                                        [ 96%]
tests/test_v1_dataset_invariants.py .....                                [100%]

============================= 140 passed in 14.12s =============================
```

- **Passed:** 140 / 140 tests (100%).
- **Failed:** 0.
- **Errors:** 0.
- **Skipped:** 0.

---

## 7. Frozen Benchmark Checksum Verification

All 5 canonical benchmark files remain bit-exact identical to their pinned SHA256 hashes:

| File Path | Canonical SHA256 Hash | Status |
| :--- | :--- | :---: |
| `data/corpus.jsonl` | `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3` | Verified Match |
| `data/manual_queries.jsonl` | `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3` | Verified Match |
| `data/eval_queries.jsonl` | `7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3` | Verified Match |
| `data/train_query_labels.jsonl` | `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae` | Verified Match |
| `data/train_triplets.jsonl` | `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75` | Verified Match |

All Phase 1 (`train_queries_exp_a_matched.jsonl`, etc.) and Phase 1.5 raw artifacts are preserved without modification.

---

## 8. Explicit Remaining Limitations

To ensure full scientific transparency before retraining commences, the following known structural properties and limitations are disclosed:

1. **Evaluation Benchmark Conceptual Overlap:** Five of the 54 manual evaluation queries exhibit partial conceptual overlap with candidate documents (identified in Phase 0). These 5 queries will be reported separately from the 49 held-out primary queries in all evaluation outputs.
2. **Partial Batch Remnants:** Because 2,475 and 6,771 are not multiples of 4, both matched-budget runs ($2475 = 618 \times 4 + 3$) and full runs ($6771 = 1692 \times 4 + 3$) include one partial batch of 3 samples per epoch. Both regimes share identical partial batch dynamics.
3. **Source Document Length Asymmetry:** Document token lengths range from ~50 tokens (changelog fragments) to thousands of tokens (core docs). While all 31 documents are represented, smaller documents naturally contribute fewer total queries than larger reference guides.
4. **Automated Review Attribution:** Programmatic AST validation and semantic heuristics were executed algorithmically; the 6-point rubric evaluation was executed via Antigravity agentic evaluation. No human reviewer performed line-by-line manual grading of the 396 sampled queries.

---

## 9. Final Retraining Recommendation: GO

All experimental controls, dataset reconciliations, dataloader step verifications, and regression tests are complete and verified.

### Recommendation Summary:
- **`A-matched` (825 queries, 2,475 triplets, 1,857 updates):** **GO**
- **`B` (825 queries, 2,475 triplets, 1,857 updates):** **GO**
- **`C-matched` (825 queries, 2,475 triplets, 1,857 updates):** **GO**
- **`C-matched-balanced` (825 queries, 2,475 triplets, 1,857 updates):** **GO**
- **`C-full` (2,257 queries, 6,771 triplets, 5,079 updates):** **GO**

**We are completely halted at the training gate. No adapter weights will be trained, and no evaluation benchmarks will be executed until explicit user approval is granted.**
