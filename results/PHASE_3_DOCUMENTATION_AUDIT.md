# Phase 3 Repository-Wide Documentation Audit & Consistency Report

**Repository:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Target Recipient:** Soup Maintainer (Alpamys)  
**Date:** 2026-11-04  
**Audit Status:** Complete — Verified Against Codebase, Checksums, and Experimental Evidence

---

## 1. Documentation Inventory

Every maintained documentation artifact in the repository has been surveyed, categorized, and audited against the codebase and experimental evidence.

### Classification Categories:
- **Category 1:** Correct and current.
- **Category 2:** Correct but needed clarity or formatting improvements.
- **Category 3:** Outdated and requiring updates.
- **Category 4:** Factually inconsistent with implementation or experimental results.
- **Category 5:** Historical documentation that should remain unchanged but needs clearer historical labeling.

| # | File Path | Primary Purpose | Category | Issues Identified Before Audit | Action Taken |
|---|---|---|:---:|---|---|
| 1 | `README.md` | Primary landing page & entry point | **3** | Displayed outdated v1 synthetic results (+21.12% Recall@1); omitted prominent negative result (Frozen E5-small outperformed fine-tuned MiniLM); showed partial 4-retriever comparison rather than all 9 retrievers; lacked clear separation between completed prototype and future work. | Overhauled to position project as a configuration-driven RAG prototype; added full 9-retriever Phase 3 scorecard; highlighted negative result; added explicit limitations, pipeline architecture, and roadmap distinctions. |
| 2 | `REPRODUCE.md` | Reproduction & verification guide | **3** | Lacked clear separation between running tests, inspecting precomputed results, running read-only retrieval, and retraining; omitted instructions for the 182-test invariant suite; missing warning about batch scripts. | Restructured into 4 functional operational modes; added test suite instructions; added SHA256 manifest verification steps; documented batch script execution caveats. Retained at root as core entry point. |
| 3 | `docs/README.md` | Master technical documentation index | **1** | Did not exist previously. | Created master index providing concise up-front summaries of query coverage, implementation progress, pre-training audits, and navigation map. |
| 4 | `docs/REVIEW.md` | Architectural review & design decisions | **3** | Stated only v1 and initial 4-retriever v2 results; omitted the Phase 2 training matrix (Exp B, C-matched, C-matched-balanced, C-full) and Phase 3 9-retriever findings. Located at root (`REVIEW.md`). | Moved to `docs/REVIEW.md` via `git mv`; added status banner; updated architecture, dataset strategies, and full 9-retriever results table; integrated links to Phase 3 reports. |
| 5 | `docs/reports/PHASE_1_DELIVERY_REPORT.md` | Phase 1 prototype delivery report | **5** | Historical delivery report based on 497 synthetic queries; risk of readers confusing synthetic heading-overlap metrics with real retrieval performance. Located at root (`REPORT.md`). | Moved to `docs/reports/PHASE_1_DELIVERY_REPORT.md` via `git mv`; added prominent historical warning banner explaining synthetic heading shortcuts; updated Section 11 to link to Phase 3. |
| 6 | `docs/EVALUATION_V2_SPEC.md` | Canonical specification for v2 benchmark | **5** | Historical specification for the initial 54-query manual benchmark milestone (Phases 0–7); lacked explicit link to subsequent Phase 1.5–3.1 expansion. | Added historical milestone banner clarifying relationship to subsequent Phase 1.5–3.1 multi-retriever benchmark. |
| 7 | `docs/EVALUATION_V2_OVERLAP_AUDIT.md` | Audit of 18 candidate overlap queries | **1** | None. Authoritative record of the 18 candidate overlap queries (15 confirmed, 3 reclassified as primary with owner approval). | Preserved at current path to satisfy test invariant in `tests/test_compare_retrievers.py`. |
| 8 | `docs/evaluation/EVALUATION_V2_COVERAGE.md` | Manual query authoring worksheet (1,305 lines) | **1** | Cluttered top-level `docs/` with massive 1,305-line chunk allocation tables. | Moved to `docs/evaluation/EVALUATION_V2_COVERAGE.md` via `git mv`; summarized up-front in `docs/README.md`. |
| 9 | `docs/progress/EVALUATION_V2_PROGRESS.md` | Implementation progress log (458 lines) | **5** | Living log terminating at PR #3 review fixes (2026-11-01); cluttered top-level `docs/`. | Moved to `docs/progress/EVALUATION_V2_PROGRESS.md` via `git mv`; added historical record banner; summarized up-front in `docs/README.md`. |
| 10 | `docs/phase0/PHASE_0_AUDIT.md` | Pre-training corpus & split audit (372 lines) | **1** | Pre-training audit located at top-level `docs/`. | Moved to `docs/phase0/PHASE_0_AUDIT.md` via `git mv`; summarized in `docs/README.md`. |
| 11 | `docs/phase0/PHASE_0_RECOMMENDATION.md` | Architectural recommendations for split (216 lines) | **1** | Architectural recommendation at top-level `docs/`. | Moved to `docs/phase0/PHASE_0_RECOMMENDATION.md` via `git mv`; summarized in `docs/README.md`. |
| 12 | `docs/phase0/PHASE_0_CORPUS_INVENTORY.csv` | Inventory of 23 candidate expansion docs (733 lines) | **1** | Large CSV catalog at top-level `docs/`. | Moved to `docs/phase0/PHASE_0_CORPUS_INVENTORY.csv` via `git mv`. |
| 13 | `results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md` | Authoritative Phase 3 benchmark report | **1** | None. Authoritative, audited evaluation report across all 9 retrievers on 54 manual queries. | Preserved without changes (Authoritative Source of Truth). |
| 14 | `results/PHASE_3_1_INTEGRITY_AUDIT.md` | Statistical verification & invariant audit | **1** | None. Authoritative audit of bootstrap CI, failure classifications, and test invariants. | Preserved without changes (Authoritative Source of Truth). |
| 15 | `results/PHASE_2_TRAINING_EXECUTION_REPORT.md` | Training execution report for 5 adapters | **1** | None. Complete training metrics, batch accounting, and execution times for authorized runs. | Preserved without changes. |
| 16 | `results/PHASE_2_1_ARTIFACT_VERIFICATION_REPORT.md` | Post-training artifact integrity check | **1** | None. Verified checksums, configuration normalization, and PEFT invariants. | Preserved without changes. |
| 17 | `results/PHASE_1_10_FINAL_EXPERIMENT_LOCK.md` | Final experiment lock & model revision | **1** | None. Pinned HuggingFace base model commit and authorized Path A training. | Preserved without changes. |
| 18 | `results/PHASE_1_9_CONFIG_AND_PROVENANCE_LOCK.md` | Config & provenance audit | **1** | None. Complete verification of YAML configs and source manifests. | Preserved without changes. |
| 19 | `results/PHASE_1_8_FINAL_RUN_MANIFEST.md` | Run manifest for experimental matrix | **2** | Positive chunk count column in Section 2 listed 586 for C-matched-balanced (copy-pasted from B) instead of actual 720 positive chunks. | Updated table entry to `720*` and added explicit footnote clarifying the sampling coverage. |
| 20 | `results/PHASE_1_7_TRAINING_READINESS_REPORT.md` | Training readiness audit | **1** | None. Verification of triplets, negative mining, and training configs. | Preserved without changes. |
| 21 | `results/PHASE_1_6_RECONCILIATION_REPORT.md` | Candidate corpus reconciliation | **1** | None. Accurate accounting of expanded corpus chunks and intent distributions. | Preserved without changes. |
| 22 | `results/PHASE_1_5_QUERY_QUALITY_REPORT.md` | Diverse query quality audit | **1** | None. Semantic quality and intent class distribution analysis. | Preserved without changes. |
| 23 | `results/query_partitions_reconciliation_table.md` | Partition reconciliation table | **1** | None. Tabular breakdown of query allocations across documents. | Preserved without changes. |
| 24 | `results/comparison.md` | Historical v1 synthetic bootstrap report | **5** | Historical artifact comparing Frozen MiniLM vs Soup LoRA on 497 synthetic queries. | Preserved without changes (Historical record). |
| 25 | `results/v2/comparison.md` | Historical v2 4-way retriever report | **5** | Historical artifact comparing initial 4 retrievers before Phase 2 retraining. | Preserved without changes (Historical record). |
| 26 | `data/raw_docs/README.md` | Upstream Soup documentation index | **5** | Vendored upstream document index; relative links point to upstream structure. | Documented in `ATTRIBUTION.md` and `REPRODUCE.md` as vendored upstream source text; left untouched to preserve byte-exact SHA256 checksum against `data/source_manifest.json`. |
| 27 | `data/raw_docs/ATTRIBUTION.md` | License & provenance attribution | **1** | None. Documents Apache-2.0 license, upstream commit hash (`8ab2664`), and file checksums. | Preserved without changes. |

---

## 2. Structural Restructuring & Length Reduction (Alpamys Review Feedback)

### Maintainer Feedback Addressed
> *"The docs got heavy for a prototype (progress and coverage files are 1000+ lines). A short summary up front and the rest under docs/ is enough."*

To address this feedback directly, the repository documentation architecture was restructured around the core principle:
- **Repository Root:** Concise introduction, architecture diagram, headline Phase 3 results, limitations, quickstart, and navigation front door.
- **`docs/README.md`:** Concise executive summaries up front for query coverage (54 queries across 4 documents), progress milestones (Phases 0–3), and pre-training audits, providing clear links to detailed files.
- **`docs/` Subdirectories:** Detailed tracking, massive coverage tables, and phase records organized logically into `docs/evaluation/`, `docs/progress/`, `docs/phase0/`, and `docs/reports/`.

### Before and After Structural Comparison

| Document | Before Path | Before Location | After Path | After Location | Lines | Purpose / Content |
|---|---|---|---|---|---:|---|
| **`README.md`** | `README.md` | Root | `README.md` | Root | 164 | Concise front-door overview, results, quickstart |
| **`REPRODUCE.md`** | `REPRODUCE.md` | Root | `REPRODUCE.md` | Root | 187 | Entry-point verification and reproduction guide |
| **`REPORT.md`** | `REPORT.md` | Root | `docs/reports/PHASE_1_DELIVERY_REPORT.md` | `docs/reports/` | 253 | Historical Phase 1 delivery report |
| **`REVIEW.md`** | `REVIEW.md` | Root | `docs/REVIEW.md` | `docs/` | 69 | Architectural review & key decisions |
| **`docs/README.md`** | *(New)* | N/A | `docs/README.md` | `docs/` | 102 | Master index & up-front executive summaries |
| **`EVALUATION_V2_COVERAGE.md`** | `docs/EVALUATION_V2_COVERAGE.md` | `docs/` root | `docs/evaluation/EVALUATION_V2_COVERAGE.md` | `docs/evaluation/` | 1,305 | Detailed chunk allocation tables & query worksheet |
| **`EVALUATION_V2_PROGRESS.md`** | `docs/EVALUATION_V2_PROGRESS.md` | `docs/` root | `docs/progress/EVALUATION_V2_PROGRESS.md` | `docs/progress/` | 458 | Detailed milestone commit diary & rehearsal logs |
| **`PHASE_0_AUDIT.md`** | `docs/PHASE_0_AUDIT.md` | `docs/` root | `docs/phase0/PHASE_0_AUDIT.md` | `docs/phase0/` | 372 | Pre-training corpus audit |
| **`PHASE_0_RECOMMENDATION.md`** | `docs/PHASE_0_RECOMMENDATION.md` | `docs/` root | `docs/phase0/PHASE_0_RECOMMENDATION.md` | `docs/phase0/` | 216 | Pre-training architectural recommendations |
| **`PHASE_0_CORPUS_INVENTORY.csv`**| `docs/PHASE_0_CORPUS_INVENTORY.csv`| `docs/` root | `docs/phase0/PHASE_0_CORPUS_INVENTORY.csv`| `docs/phase0/` | 733 | Candidate document inventory catalog |
| **`EVALUATION_V2_SPEC.md`** | `docs/EVALUATION_V2_SPEC.md` | `docs/` root | `docs/EVALUATION_V2_SPEC.md` | `docs/` | 246 | Evaluation benchmark specification |
| **`EVALUATION_V2_OVERLAP_AUDIT.md`**| `docs/EVALUATION_V2_OVERLAP_AUDIT.md`| `docs/` root | `docs/EVALUATION_V2_OVERLAP_AUDIT.md`| `docs/` | 181 | Query overlap audit (retained for test invariant) |

### Rationale for Files Retained at Root
- **`README.md`:** Standard primary entry point for any open-source repository; provides immediate clarity for Alpamys on prototype status, architecture, and headline findings.
- **`REPRODUCE.md`:** Essential for maintainer review, enabling immediate, copy-pasteable verification (`pytest tests/`) and precomputed result checks without navigating into subfolders.

All other detailed tracking documents, large worksheets (1,305 lines), and historical delivery reports were removed from the root and placed into appropriate subdirectories under `docs/`.

---

## 3. Summary of Major Inconsistencies Found

During the repository-wide audit, five major categories of inconsistencies and misleading presentations were identified and resolved:

1. **Outdated Headline Claims in `README.md`:**
   - *Issue:* The root README prominently displayed the Phase 1 v1 synthetic benchmark (+21.12% Recall@1, +18.62% MRR@10) as current performance, while the subsequent manual evaluation demonstrated that these gains were an artifact of synthetic heading-overlap shortcuts.
   - *Resolution:* Completely replaced the headline scorecard with the authoritative Phase 3 multi-retriever benchmark table, clearly presenting the negative result and document-localized gains.

2. **Omission of the Primary Negative Result:**
   - *Issue:* The README previously presented fine-tuning as an unmitigated success without noting that Frozen E5-small (`intfloat/e5-small-v2`) outperformed all fine-tuned MiniLM models across ranking quality and recall.
   - *Resolution:* The README, REVIEW, and audit documents now prominently highlight this negative finding: pre-trained encoder capability outweighs domain fine-tuning of smaller encoders on limited text.

3. **Incomplete Retriever Coverage (4 vs 9 Retrievers):**
   - *Issue:* `README.md` and `REVIEW.md` only described the initial 4-retriever comparison (BM25, Frozen MiniLM, Frozen E5-small, baseline Soup adapter), ignoring the five authorized adapters trained in Phase 2 (A-matched, B, C-matched, C-matched-balanced, C-full).
   - *Resolution:* Updated `README.md` and `REVIEW.md` with the full 9-retriever matrix, documenting the impacts of diverse LLM query generation and corpus expansion.

4. **Ambiguity Between Operational Modes in `REPRODUCE.md`:**
   - *Issue:* `REPRODUCE.md` mixed unit testing, benchmark evaluation, synthetic query generation, and adapter training in a single sequential flow without distinguishing fast verification from training.
   - *Resolution:* Structured `REPRODUCE.md` into distinct operational sections: fast test suite execution (182 tests), precomputed artifact verification via SHA256 manifest, read-only retrieval evaluation, and historical reproduction.

5. **Minor Manifest Positive Chunk Count Typo:**
   - *Issue:* In `results/PHASE_1_8_FINAL_RUN_MANIFEST.md`, the positive chunk count for `C-matched-balanced` was listed as 586 (copy-pasted from Experiment B), whereas the actual stratified sample covered 720 unique positive chunks across the 31 candidate documents.
   - *Resolution:* Corrected the table entry to `720*` and added a footnote documenting the actual coverage verified in Phase 1.6 and Phase 3.1 reports.

---

## 4. Verification Sources of Truth

Every factual correction and reported metric was verified directly against authoritative repository artifacts:

| Domain / Information Type | Authoritative Source of Truth | Verification Method |
|---|---|---|
| **Phase 3 Benchmark Metrics** | `results/phase3/aggregate_comparison.json`<br>`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md` | SHA256 manifest check (`results/phase3/manifest.sha256`); direct inspection of micro and macro metrics. |
| **Statistical & Bootstrap Invariants** | `results/phase3/bootstrap_ci.json`<br>`results/PHASE_3_1_INTEGRITY_AUDIT.md` | Verified 10,000 bootstrap resamples, random seed 42, document-stratified paired resampling plan. |
| **Adapter Training Hyperparameters** | `config/embedding_exp_*.yaml`<br>`results/PHASE_2_1_ARTIFACT_VERIFICATION_REPORT.md` | Inspected YAML configs and adapter JSON files (`output/adapter_exp_*/adapter_config.json`). |
| **Base Model & Revision Locks** | `results/PHASE_1_10_FINAL_EXPERIMENT_LOCK.md` | Pinned commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (`all-MiniLM-L6-v2`) and `ffb93f3bd4047442299a41ebb6fa998a38507c52` (`e5-small-v2`). |
| **Manual Evaluation Queries & Labels** | `data/manual_queries.jsonl`<br>`docs/evaluation/EVALUATION_V2_COVERAGE.md` | Verified 54 queries, query-set hash `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3`. |
| **Corpus Integrity & Chunk Splits** | `data/corpus.jsonl`<br>`data/source_manifest.json` | Verified 1,068 chunks (761 train / 307 test); corpus hash `76ab5e884d6dd21e86971a8ea97a95b871c53e878788915aa4ad04a621ed0f90`. |
| **Test Suite Invariants** | `tests/test_*_invariants.py` | Executed full pytest suite (182 passed in ~24s). |

---

## 5. Broken Links and Commands Discovered & Resolved

1. **Relative Links in `data/raw_docs/` and Candidate Benchmarks:**
   - *Observation:* Upstream files in `data/raw_docs/` and `data/candidate_docs/` contain relative links written for upstream repository structures (e.g. `[← Back to the main README](../README.md)`).
   - *Resolution:* Left vendored documents untouched to preserve their byte-exact SHA256 checksums (`data/source_manifest.json`). Documented in `ATTRIBUTION.md` and `REPRODUCE.md` that these are vendored snapshots.
2. **Updated Relative Paths Across Moved Documents:**
   - *Observation:* Moving documents into subdirectories (`docs/reports/`, `docs/progress/`, `docs/evaluation/`, `docs/phase0/`) altered relative depths to `results/` and root files.
   - *Resolution:* Audited and corrected all relative links in `docs/README.md`, `docs/REVIEW.md`, `docs/reports/PHASE_1_DELIVERY_REPORT.md`, `docs/progress/EVALUATION_V2_PROGRESS.md`, `docs/EVALUATION_V2_SPEC.md`, and root `README.md`.
3. **Preservation of `docs/EVALUATION_V2_OVERLAP_AUDIT.md`:**
   - *Observation:* `tests/test_compare_retrievers.py` line 292 contains a strict test assertion: `assert "docs/EVALUATION_V2_OVERLAP_AUDIT.md" in report`.
   - *Resolution:* Retained `docs/EVALUATION_V2_OVERLAP_AUDIT.md` at its exact path directly under `docs/` to guarantee that all 182 test assertions continue passing without modifying test code.

---

## 6. Remaining Documentation Limitations & Scope Boundaries

1. **Upstream Vendored Docs (`data/raw_docs/`):**
   - As noted in `data/raw_docs/ATTRIBUTION.md`, `backends-and-ops.md` in `data/raw_docs/` differs slightly in whitespace/size from the pinned commit blob in the upstream repo, though its headings and content are structurally identical. This is a historical artifact of how the initial corpus was extracted and does not affect the evaluation or test suite.
2. **Generalization Across Diverse Domains:**
   - The current prototype evaluations are restricted to Soup CLI technical documentation across 4 held-out documents. The documentation explicitly disclaims population-level generalizability to unrelated domains.
3. **Evaluation Granularity:**
   - The benchmark measures passage retrieval accuracy (Hit@K, Recall@K, MRR@10). The documentation clearly notes that retrieval metrics do not measure end-to-end RAG answer quality, grounding, or generation faithfulness.

---

## 7. Validation Commands Executed and Outcomes

| # | Validation Command | Scope / Purpose | Outcome |
|---|---|---|---|
| 1 | `pytest tests/ -v` | Full repository test suite | **PASS** — 182 passed in 23.70s. |
| 2 | `cd results/phase3 && sha256sum -c manifest.sha256` | Phase 3 result artifact integrity | **PASS** — All 16 Phase 3 result files report `OK`. |
| 3 | `python scripts/validate_manual_queries.py` | Manual query dataset validation | **PASS** — 54 queries checked, 0 errors, 0 warnings. |
| 4 | Markdown Link Validator (Python script) | Internal relative link verification | **PASS** — All relative links in prototype documentation resolve to valid paths. |
| 5 | `git status` | Working tree cleanliness check | **PASS** — Only documentation files modified/moved. |

---

## 8. Final Git Diff Summary

The changes in the working tree are strictly limited to documentation updates and file reorganizations:

- **Root Cleared of Heavy Tracking Docs:** Only `README.md` and `REPRODUCE.md` remain at root.
- **`docs/README.md` Created:** 102-line master index with up-front executive summaries.
- **Git-Aware Moves Executed:**
  - `git mv REPORT.md docs/reports/PHASE_1_DELIVERY_REPORT.md`
  - `git mv REVIEW.md docs/REVIEW.md`
  - `git mv docs/EVALUATION_V2_COVERAGE.md docs/evaluation/EVALUATION_V2_COVERAGE.md`
  - `git mv docs/EVALUATION_V2_PROGRESS.md docs/progress/EVALUATION_V2_PROGRESS.md`
  - `git mv docs/PHASE_0_AUDIT.md docs/phase0/PHASE_0_AUDIT.md`
  - `git mv docs/PHASE_0_RECOMMENDATION.md docs/phase0/PHASE_0_RECOMMENDATION.md`
  - `git mv docs/PHASE_0_CORPUS_INVENTORY.csv docs/phase0/PHASE_0_CORPUS_INVENTORY.csv`

---

## 9. Confirmation of Experimental Artifact Preservation

It is confirmed that:
- **NO** model training was executed.
- **NO** retrieval evaluations were rerun.
- **NO** model weights or LoRA adapter checkpoints were altered.
- **NO** dataset files, queries, triplets, or relevance labels were modified.
- **NO** raw Phase 3 retrieval JSON files or bootstrap confidence interval artifacts were regenerated.
- **NO** source code or test implementations were changed.

All 16 result files in `results/phase3/` remain 100% bit-exact identical to their pinned SHA256 checksums in `manifest.sha256`.

---

## 10. Readiness Assessment for Maintainer Review

**Verdict: READY FOR MAINTAINER SUBMISSION**

The repository is now in an optimal state for review by Alpamys:
1. **Uncluttered Root:** The root directory is clean, presenting only a focused `README.md` and `REPRODUCE.md`.
2. **Short Summaries Up Front:** `docs/README.md` summarizes query coverage, milestone progress, and pre-training audits up front, preventing reviewer fatigue from 1,000+ line tracking files.
3. **Honest, Evidence-Backed Findings:** The README and reports clearly state the primary negative result: off-the-shelf Frozen E5-small is the strongest retriever, and fine-tuning MiniLM did not surpass it.
4. **Data Quality Insights:** The findings demonstrate clear, actionable insights for Soup: diverse LLM-generated training queries drastically outperform synthetic template queries, and corpus expansion requires careful curation to prevent noise.
5. **Preserved Technical Depth:** All detailed 1,000+ line allocation worksheets, historical logs, and audits remain fully accessible under logical subdirectories in `docs/`.
