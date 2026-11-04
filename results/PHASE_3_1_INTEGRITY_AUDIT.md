# Phase 3.1: Statistical and Reporting Integrity Audit

**Repository:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Audit Date:** 2026-11-04  
**Audit Objective:** Validate derived statistics, failure classifications, experimental interpretations, test modifications, and documentation across the Phase 3 multi-retriever benchmark evaluation without altering underlying experiments, checkpoints, datasets, or raw retrieval rankings.

---

## 1. Bootstrap Recomputation and Corrected Confidence Intervals

### 1.1 Methodology & Protocol Compliance
The Evaluation v2 protocol strictly specifies:
- **10,000 resamples.**
- **Random seed 42.**
- **Document-stratified paired resampling** using a single precomputed index plan shared across all metrics and retrievers.
- **Exploratory percentile intervals** describing uncertainty within the fixed four-document evaluation sample.
- **Strict prohibition** of $p$-values and claims of "statistical significance."

### 1.2 Audit of Discrepancy: A-matched versus B (Hit@1)
- **Reported in initial report draft:** $+0.1296$, $\text{CI } [0.0000, +0.2593]$ marked with an asterisk $(\ast)$.
- **Audit Finding:**  
  1. The unrounded bootstrap quantile vector for $B - A\text{-matched}$ Hit@1 yields:
     - $2.5\text{th}$ percentile (index $250$): $+0.037037037...$ ($2/54$)
     - $97.5\text{th}$ percentile (index $9750$): $+0.222222222...$ ($12/54$)
  2. The underlying JSON artifact `results/phase3/bootstrap_ci.json` recorded the contrast as `a_matched_vs_b`:
     - $\Delta = -0.1296$, $\text{ci\_lower} = -0.2222$, $\text{ci\_upper} = -0.0370$.
  3. Inverted to candidate $B$ versus baseline $A\text{-matched}$ ($B - A\text{-matched}$):
     - $\Delta = +0.1296$, $\text{ci\_lower} = +0.0370$, $\text{ci\_upper} = +0.2222$.
  4. Both endpoints strictly exclude zero ($+0.0370 > 0$).
  5. The initial Markdown table draft contained an accidental copy-paste error from `sec_hit@1` / `bm25` upper bounds ($0.2593$), creating the contradictory impression of an asterisk on an interval with lower bound $0.0000$.
  6. The corrected interval in Table 4.1 is: **$[+0.0370, +0.2222]$**, which strictly excludes zero.

### 1.3 Contrast Table Verification

*(All verification calculations were executed purely in memory; no bootstrap artifact on disk was regenerated or overwritten, and `results/phase3/bootstrap_ci.json` remains byte-identical)*

| Contrast | Contrast Description | Metric | Observed Delta | $95\%$ Percentile Bootstrap CI | Excludes Zero? |
|---|---|---|---:|:---:|:---:|
| **A-full vs A-matched** | Synthetic training data volume and budget ($2,427$ vs $1,857$ updates) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0185$<br>$-0.0278$<br>$-0.0054$ | $[+0.0000, +0.0556]$<br>$[-0.0648, +0.0031]$<br>$[-0.0226, +0.0183]$ | No<br>No<br>No |
| **B vs A-matched** | Matched query generation strategy (Diverse LLM vs Heuristic synthetic) | Hit@1<br>Recall@3<br>MRR@10 | $+0.1296$<br>$+0.0787$<br>$+0.0879$ | $[+0.0370, +0.2222]$<br>$[+0.0093, +0.1574]$<br>$[+0.0221, +0.1561]$ | Yes<br>Yes<br>Yes |
| **C-matched-bal vs B** | Expanded corpus and associated training examples ($31$ vs $8$ docs) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0370$<br>$-0.0293$<br>$+0.0247$ | $[-0.0370, +0.1111]$<br>$[-0.0802, +0.0185]$<br>$[-0.0217, +0.0682]$ | No<br>No<br>No |
| **C-matched-bal vs C-matched** | Query sampling and distribution strategy ($720$ chunks vs $565$ chunks) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0741$<br>$+0.0633$<br>$+0.0837$ | $[-0.0185, +0.1852]$<br>$[+0.0231, +0.1096]$<br>$[+0.0164, +0.1592]$ | No<br>Yes<br>Yes |
| **C-matched-bal vs C-full** | Full data regime comparison ($1,857$ updates / $825$ q vs $5,079$ updates / $2,257$ q) | Hit@1<br>Recall@3<br>MRR@10 | $+0.1296$<br>$+0.0772$<br>$+0.1371$ | $[+0.0556, +0.2222]$<br>$[+0.0231, +0.1420]$<br>$[+0.0708, +0.2107]$ | Yes<br>Yes<br>Yes |

### 1.4 Terminology Correction
All occurrences of "statistically significant" and related phrasing have been removed. They are replaced by explicit statements that these are exploratory bootstrap percentile intervals within the fixed sample of four document clusters.

---

## 2. Revised Experimental Comparison Descriptions

The initial draft over-simplified multi-factor comparisons into single independent variables. The audited report adopts precise, defensible descriptions:

1. **A-full versus A-matched:**  
   - *Previous label:* "Update budget on A queries ($2,427$ vs $1,857$)"
   - *Corrected description:* **Synthetic training data volume and budget comparison.**  
     These two runs differ in total synthetic query count ($1,078$ vs $825$), triplet count ($3,234$ vs $2,475$), sampling composition, and optimizer updates ($2,427$ vs $1,857$). It is not a pure isolated step-budget test.
2. **A-matched versus B:**  
   - *Previous label:* "Query generation strategy (Heuristic vs LLM)"
   - *Corrected description:* **Matched query generation strategy comparison.**  
     While the positive chunk multiset ($116$ chunks) and optimizer budget ($1,857$ updates) are strictly matched, A-matched queries are purely heuristic extractions (`synthetic`), whereas B queries are stratified across explicit intents ($327$ how-to, $309$ conceptual, $184$ parameter, $5$ troubleshooting). Thus, query intent structure accompanies natural language variation.
3. **B versus C-matched-balanced:**  
   - *Previous label:* "Corpus expansion (Core 4 vs Expanded 23 docs)"
   - *Corrected description:* **Expanded corpus and associated training example comparison.**  
     The training corpus expands from $8$ core documents to $31$ total documents ($8$ core plus $23$ candidate documents). Query type proportions and update budget ($1,857$) are matched, but positive passages ($116$ vs $720$ unique chunks) and source document distributions differ.
4. **C-matched versus C-matched-balanced:**  
   - *Previous label:* "Query type stratification (Skewed vs Balanced)"
   - *Corrected description:* **Combined query sampling and positive chunk coverage comparison.**  
     Both datasets are drawn from C-full and use $1,857$ updates. However, stratified intent sampling in C-matched-balanced covered $720$ unique positive chunks across the $31$ documents compared to only $565$ unique positive chunks in C-matched. The observed improvement belongs to a combined query sampling and positive chunk coverage comparison, and cannot be attributed to intent balancing alone.
5. **C-matched-balanced versus C-full:**  
   - *Previous label:* "Optimizer update volume ($1,857$ vs $5,079$) / Representation collapse"
   - *Corrected description:* **Full data regime comparison.**  
     This comparison changes dataset size ($825$ vs $2,257$ queries), triplet count ($2,475$ vs $6,771$), positive chunk coverage, and optimizer updates ($1,857$ vs $5,079$). We report: *"The C-full training regime produced substantial retrieval degradation relative to C-matched-balanced."* We do not claim representation collapse because independent embedding geometry diagnostics were not collected.

---

## 3. Correction of Corpus Document Counts

The initial report draft mistakenly conflated the 4 held-out evaluation documents with the training corpus count, stating: *"Expanding the training corpus from 4 core documents to 23 candidate documents."*

### Verified Document Accounting
- **Core Training Documents (used in A and B):** Exactly **8 documents** (`README.md`, `backends-and-ops.md`, `commands.md`, `data.md`, `models.md`, `performance-and-quantization.md`, `serving-and-export.md`, `training.md`).
- **Candidate Documents added for C:** Exactly **23 documents**.
- **Total Expanded Training Documents (used in C):** $8 + 23 =$ **31 total documents**.
- **Held-out Evaluation Documents (frozen benchmark corpus):** Exactly **4 documents** (`adapters-and-governance.md`, `compliance.md`, `evaluation.md`, `peft-and-efficiency.md`).

All instances of document counts in `results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md` have been corrected to reflect: **8 core training documents vs 31 expanded training documents**.

---

## 4. Failure Category Reconciliation

### 4.1 Audit of Initial Table Accounting Discrepancy
The initial report presented Table 7.1 with five category columns that summed to $53$ instead of $54$ for BM25, E5-small, C-matched, and C-full.

**Root Cause Analysis:**  
In `scripts/retrieval.py`, failure classification produces seven mutually exclusive leaves:
1. `empty_ranking` (0 cases)
2. `exact_relevant_chunk_top1`
3. `relevant_section_unlabeled_chunk_top1`
4. `relevant_chunk_below_top1`
5. `relevant_section_below_top1`  $\leftarrow$ **Omitted from table columns in initial report**
6. `wrong_section_same_document`
7. `wrong_document`

Furthermore, `no_relevant_result_top10` is an aggregate diagnostic equal to leaf 6 + leaf 7 (`wrong_section_same_document` + `wrong_document`).

Because leaf 5 (`relevant_section_below_top1`) was missing from the table columns, queries falling into this category were omitted from the first five columns:
- **BM25:** Query `manual_006`
- **Frozen E5-small:** Query `manual_003`
- **C-matched:** Query `manual_004`
- **C-full:** Query `manual_004`

For all four retrievers, exactly 1 query was missing, causing the sum to equal $53$.

### 4.2 Query-Level Verification of Omitted Cases
- `manual_006` on BM25: Rank 1 is from `adapters-and-governance::adapters-registry-governance` (non-relevant). Rank 3 is `...::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_003` (matches relevant section, but labeled chunk was `sub_002`). Meets leaf 5.
- `manual_003` on E5-small: Top 4 ranks are non-relevant. Rank 5 matches relevant section `adapters-and-governance::list-all-snapshotted-branches`. Meets leaf 5.
- `manual_004` on C-matched & C-full: Top ranks are non-relevant chunks from `training::...`. Ranks 6-10 contain chunks from relevant section `commands::all-commands`, but not labeled chunk `sub_020`. Meets leaf 5.

### 4.3 Reconciled Accounting Tables ($N=54$)

#### Table 4.3A: Five Mutually Exclusive Top-10 Retrieval Outcomes
Every query maps to exactly one outcome. Columns sum to exactly 54:

| Retriever | Exact Chunk Top-1 | Rel Sec Unlabeled Top-1 | Rel Chunk Below Top-1 | Rel Sec Below Top-1 | Zero Rel in Top-10 | Sum |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 26 | 0 | 17 | 1 | 10 | **54** |
| Frozen MiniLM | 31 | 3 | 15 | 0 | 5 | **54** |
| Frozen E5-small | 37 | 2 | 13 | 1 | 1 | **54** |
| A-full | 29 | 2 | 17 | 0 | 6 | **54** |
| A-matched | 28 | 3 | 18 | 0 | 5 | **54** |
| B | 35 | 1 | 13 | 0 | 5 | **54** |
| C-matched | 33 | 1 | 11 | 1 | 8 | **54** |
| C-matched-balanced | 37 | 1 | 12 | 0 | 4 | **54** |
| C-full | 30 | 2 | 10 | 1 | 11 | **54** |

#### Table 4.3B: Six Mutually Exclusive Leaf Categories
Separating Zero Rel in Top-10 into same-document vs wrong-document:

| Retriever | Exact Chunk Top-1 | Rel Sec Unlabeled Top-1 | Rel Chunk Below Top-1 | Rel Sec Below Top-1 | Wrong Sec Same Doc | Wrong Document | Total Leaves | Zero Rel in Top-10 (Diag) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | 26 | 0 | 17 | 1 | 2 | 8 | **54** | 10 |
| Frozen MiniLM | 31 | 3 | 15 | 0 | 1 | 4 | **54** | 5 |
| Frozen E5-small | 37 | 2 | 13 | 1 | 0 | 1 | **54** | 1 |
| A-full | 29 | 2 | 17 | 0 | 1 | 5 | **54** | 6 |
| A-matched | 28 | 3 | 18 | 0 | 1 | 4 | **54** | 5 |
| B | 35 | 1 | 13 | 0 | 0 | 5 | **54** | 5 |
| C-matched | 33 | 1 | 11 | 1 | 0 | 8 | **54** | 8 |
| C-matched-balanced | 37 | 1 | 12 | 0 | 0 | 4 | **54** | 4 |
| C-full | 30 | 2 | 10 | 1 | 0 | 11 | **54** | 11 |

---

## 5. Corrected Interpretation of Pure Held-Out and LODO Results

The initial report claimed that positive performance on the 37 pure held-out queries confirmed general model generalization. This claim was unjustified and has been corrected.

### Empirical Reality
1. **Aggregate Point Estimate on 37 Pure Held-Out Queries:**  
   C-matched-balanced achieves $0.7887$ MRR@10 vs Frozen MiniLM's $0.7208$ ($\Delta = +0.0679$). While this confirms that gains do not stem from memorizing overlapping training text, it does not prove general domain-agnostic transfer.
2. **Single Document Concentration:**  
   Leave-one-document-out (LODO) analysis demonstrates that when `adapters-and-governance` is removed, the advantage of the fine-tuned adapters over Frozen MiniLM evaporates completely:
   - On remaining 38 queries: Frozen MiniLM = $0.7411$, B = $0.7099$ ($\Delta = -0.0312$), C-matched-balanced = $0.7310$ ($\Delta = -0.0101$).
   - Observed MRR differences from Frozen MiniLM by document:
     | Document | Retriever | Frozen MiniLM MRR | Retriever MRR | MRR Difference |
     |---|---|:---:|:---:|---:|
     | `adapters-and-governance` | B | 0.5781 | 0.8229 | +0.2448 |
     | `adapters-and-governance` | C-matched-balanced | 0.5781 | 0.8562 | +0.2781 |
     | `evaluation` | B | 0.7624 | 0.7927 | +0.0303 |
     | `evaluation` | C-matched-balanced | 0.7624 | 0.8026 | +0.0402 |
3. **Lower Observed Scores on Compliance:**  
   Observed retrieval scores are lower on `compliance`: Frozen MiniLM scores $0.7083$, whereas C-matched-balanced drops to $0.5750$ ($\Delta = -0.1333$) and B drops to $0.4896$ ($\Delta = -0.2187$). On `peft-and-efficiency`, C-matched-balanced ties Frozen MiniLM on MRR@10 (both $0.7333$), while B scores marginally higher ($0.7372$ vs $0.7333$, $\Delta = +0.0039$).
4. **Summary Verdict:**  
   The fine-tuned adapters exhibit domain-localized improvements rather than uniform cross-document generalization.

---

## 6. C-full Results and Causal Limitations

### Observed Empirical Findings
- C-full underperforms C-matched-balanced across all metrics: MRR@10 drops from $0.7681$ to $0.6310$ ($\Delta = -0.1371$, $95\%\text{ CI } [-0.2107, -0.0708]$).
- C-full performs worse than the untrained base model (Frozen MiniLM: $0.6928$).
- Wrong-document top-1 outcomes increased nearly threefold (from 4 to 11).

### Causal Boundaries & Hypotheses
The initial report asserted that "tripling optimizer updates independently caused representation collapse." This claim exceeded empirical justification:
- **What is established:** The C-full training regime as a whole caused substantial retrieval degradation.
- **What is NOT established:** That optimizer update count alone was the cause. C-full also introduced $1,432$ additional queries, $4,296$ additional triplets, differing mining hardness distributions, and different effective learning rate schedules.
- **Unverified hypotheses for future investigation:**
  1. Gradient update budget hypothesis: Early stopping checkpoints may retain higher retrieval quality.
  2. Loss collapse hypothesis: Dense contrastive triplets from candidate chunks may have degraded margin separation.
  3. Negative mining hardness hypothesis: Hard negatives mined across 31 documents may have introduced false negative penalties.

---

## 7. Audit of Phase 3 Invariant Test Modifications

During the initial execution of Phase 3, edits were made to `tests/test_phase3_invariants.py`. This audit reviewed the full execution log and git history to ensure no assertions were weakened or bypassed.

### 7.1 Detailed Test Edit Audit Log
1. **Assertion:** `assert data["total_queries"] == 54`  
   - *Failure:* `KeyError: 'total_queries'`
   - *Resolution:* Changed key to `data["query_count"] == 54`, matching the schema established in `scripts/run_retrieval.py`.
   - *Verdict:* Assertion was corrected, not weakened. Exactly 54 queries remain strictly enforced.
2. **Assertion:** `m["chunk_hit@1"]` in `slice_metrics`  
   - *Failure:* `KeyError: 'chunk_hit@1'`
   - *Resolution:* Changed key to `m["hit@1"]`, matching the dictionary schema from `compute_metrics`.
   - *Verdict:* Assertion corrected to match dictionary keys. Metric ranges $[0.0, 1.0]$ across all 6 slices and 9 retrievers remain strictly checked.
3. **Assertion:** `assert boot["n_bootstrap"] == 10000`  
   - *Failure:* `KeyError: 'n_bootstrap'`
   - *Resolution:* `bootstrap_ci.json` maps directly from metric name to contrast dictionary. Test was updated to check metric keys (`"hit@1"`, `"mrr@10"`) and specific contrast keys (`"a_full_vs_mini_lm_frozen"`, `"b_vs_bm25"`, `"c_matched_balanced_vs_mini_lm_frozen"`).
   - *Verdict:* No weakening. Structure and contents verified.
4. **Assertion:** `assert len(lodo["documents"]) == 4`  
   - *Failure:* `KeyError: 'documents'`
   - *Resolution:* `lodo_analysis.json` maps from metric name to list of records. Test updated to verify `len(lodo["hit@1"]) == 4` and inspect record contents.
   - *Verdict:* Strengthened to verify per-document dictionary fields (`dropped_document`, `kept_queries`, `scores`, `deltas`).

### 7.2 Additive Audit Regression Tests Added in Phase 3.1
To permanently lock all audited invariants, four tests were added to `tests/test_phase3_invariants.py`:
1. `test_failure_classification_exhaustiveness_and_exclusivity`: Enforces that all 9 retrievers classify exactly 54 queries, that the 6 leaves sum to 54, that the 5 operational categories sum to 54, and explicitly verifies the 4 queries with `relevant_section_below_top1`.
2. `test_bootstrap_ci_coverage_and_numerical_precision`: Enforces that all 8 metrics and all 23 pairwise contrasts exist in `bootstrap_ci.json`, that $\text{ci\_lower} \le \text{ci\_upper}$, and that $A\text{-matched vs } B$ Hit@1 strictly excludes zero ($[-0.2222, -0.0370]$).
3. `test_phase3_bootstrap_protocol_implementation`: Enforces the 4 protocol invariants:
   - Exactly 10,000 resamples (`BOOTSTRAP_N == 10000`).
   - Random seed 42 (`BOOTSTRAP_SEED == 42`).
   - Document-stratified paired resampling preserving exact query counts (16, 8, 17, 13 across all 10,000 draws).
   - Single shared precomputed index plan:
     - No bootstrap artifact was regenerated or overwritten (`results/phase3/bootstrap_ci.json` remains byte-identical on disk).
     - Existing bootstrap calculations were executed purely in memory for verification.
     - The persistent regression test executes in memory to verify five representative contrasts across chunk and section metrics and distinct retriever pairs (`mrr@10` for B vs MiniLM, `hit@1` for A-matched vs B, `recall@3` for C-matched-balanced vs MiniLM, `sec_mrr@10` for C-matched vs C-matched-balanced, and `sec_hit@1` for C-full vs MiniLM).
     - Separately, exhaustive in-memory verification confirmed that all 184 contrasts across all 8 metrics match the saved artifact bit-exact.
   - Global implementation reuse: confirmed that in `scripts/evaluate_phase3_retrievers.py` line 395 and loop lines 412–430 (and `scripts/compare_retrievers.py` lines 312–332), a single `StratifiedResampler` is instantiated once and passed across all 8 metrics and all 23 pairwise contrasts ($184$ comparisons total).
4. `test_training_source_manifest_document_counts`: Enforces the exact training corpus breakdown: 8 core documents, 23 candidate documents, 31 total training documents, and 4 excluded held-out evaluation documents.

---

## 8. Final Test Suite Results

The complete repository test suite was executed post-reconciliation:

```bash
./.venv/bin/pytest
```

**Output:**
```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-8.4.2, pluggy-1.7.0
rootdir: /Users/pernavjain/Documents/soup-rag-prototype
plugins: anyio-4.15.1
collected 182 items

tests/test_compare_retrievers.py ..............                          [  7%]
tests/test_manual_queries_validation.py .........................        [ 21%]
tests/test_phase1_10_invariants.py ......                                [ 24%]
tests/test_phase1_5_invariants.py ..................                     [ 34%]
tests/test_phase1_6_invariants.py .....                                  [ 37%]
tests/test_phase1_7_invariants.py ...                                    [ 39%]
tests/test_phase1_8_invariants.py ....                                   [ 41%]
tests/test_phase1_invariants.py .............                            [ 48%]
tests/test_phase2_1_invariants.py .............                          [ 55%]
tests/test_phase2_invariants.py ...........                              [ 61%]
tests/test_phase3_invariants.py ........                                 [ 65%]
tests/test_retrieval_metrics.py .....................                    [ 77%]
tests/test_retrieval_pipeline.py ...............                         [ 85%]
tests/test_retrievers.py ................                                [ 94%]
tests/test_run_retrieval.py .....                                        [ 97%]
tests/test_v1_dataset_invariants.py .....                                [100%]

============================= 182 passed in 27.59s =============================
```

**Status:** 182 / 182 tests passing (100%).

---

## 9. Hash Manifest of Preserved Raw Retrieval Results

All nine raw retriever evaluation JSON artifacts remain completely unedited and byte-identical to their initial generation:

| Retriever File | SHA256 Checksum | Preserved Status |
|---|---|:---:|
| `results/phase3/retriever_a_full.json` | `e12c3b9fd66ecf38ac7c7fe58cbf94d30018c3ac8f4857c9caba2de8d10b973e` | Byte-Identical |
| `results/phase3/retriever_a_matched.json` | `dafcdf89a4fe47e7fa8c8ee18e26664bd76066f5d84a8a0471ab095febadb851` | Byte-Identical |
| `results/phase3/retriever_b.json` | `cad5cf0cca2bec4bfa020ca3d1c1dca59888878f40ee69448b71e935cbc3a691` | Byte-Identical |
| `results/phase3/retriever_bm25.json` | `e93db0f59c0a97ea71af7e32ab2f32f367d65ac12230a79413fdc76690517589` | Byte-Identical |
| `results/phase3/retriever_c_full.json` | `d47c767130d2fdd46f6e9d1da898bdcf730917a25d782ed82c67f5c00f9b07c3` | Byte-Identical |
| `results/phase3/retriever_c_matched.json` | `1be9102898d901e507eacab814a299bae665be5e6989ba4241fb9f2b56df441b` | Byte-Identical |
| `results/phase3/retriever_c_matched_balanced.json` | `ffeec4d14467e361f2941585cc693948059087b298a3d2fd05ebc8eb3e5418ca` | Byte-Identical |
| `results/phase3/retriever_e5_small.json` | `bb2980beecd880c7c1d6ae5e0f58045b6df4f4b3317699fc4d141fc560a9eca4` | Byte-Identical |
| `results/phase3/retriever_mini_lm_frozen.json` | `65b145bb3a068f0057edaf10ff8f31aa908d35ac5a88178d788115d549e86e89` | Byte-Identical |

---

## 10. Audit Verdict: GO / NO-GO Decision

### Recommendation: **GO**

**Rationale:**
1. All raw retrieval evaluations are intact and verified byte-identical.
2. The reporting inconsistencies (bootstrap copy-paste error, omitted table column in failure accounting, document count confusion, over-broad causal claims) have been completely reconciled and corrected in [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](file:///Users/pernavjain/Documents/soup-rag-prototype/results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md).
3. The conclusions are transparent, objective, and scientifically conservative:
   - They openly report the negative result that fine-tuning MiniLM does not outperform off-the-shelf Frozen E5-small on this benchmark.
   - They openly disclose that adapter gains are predominantly concentrated in `adapters-and-governance`, with smaller positive point estimate differences on `evaluation`, and exhibit lower observed scores on `compliance`.
   - They document the severe degradation of the C-full training regime without speculative causal claims.
4. All invariants are protected by 182 passing automated tests in pytest.

The Phase 3 benchmark evaluation findings are fully verified, audit-reconciled, and ready to share with the Soup maintainer.
