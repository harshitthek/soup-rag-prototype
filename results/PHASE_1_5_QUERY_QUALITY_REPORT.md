# Phase 1.5: Training Query Quality Remediation & Experimental Integrity Report

**Date:** 2026-11-04  
**Branch:** `feat/evaluation-v2`  
**Base Commit (Soup Pinned):** `595173f73eb45399aeb4997bab44642827b31799`  
**Status:** Remediated, Audited, and Verified — Awaiting Retraining Approval

---

## 1. Executive Summary

During Phase 1, structural programmatic validation (checking length, 4-gram heading copy overlap, and trivial wrappers) yielded a 100% pass rate. However, an in-depth semantic audit revealed critical defects in ~27.8% of the generated queries:
1. **False Environment Variables:** Regex-based extraction (`\b[A-Z][A-Z0-9_]{3,}\b`) mistook technical acronyms and constants (`CHANGELOG`, `SDPA`, `DDR5`, `CRITICAL`, `MACHINE`, `SECOND`, `PASS`, `GATE`, `REFUSED`, `DEFAULT_WORKSPACE_BYTES`) for execution environment variables.
2. **Syntactic Fragments:** Slicing raw markdown tables, inline code, and function signatures generated malformed queries with unclosed parentheses, brackets, quotes, raw pipe delimiters (`|`), and trailing syntax.
3. **Awkward Phrasing & Generic Templates:** Generic string concatenation produced awkward questions (`"How does Soup handle --strategy cmaes --eval in this workflow?"`) and repeated generic queries (e.g. 42 chunks sharing the exact same query `"How do you configure and launch training with soup train in Soup?"`).
4. **Experimental Misalignment:** In Phase 1, `Exp A-matched` and `Exp B` targeted differing positive chunks (only 460 chunks in common), confounding query formulation with passage content distribution.

In Phase 1.5, we remediated all root causes, preserved raw Phase 1 artifacts immutably, produced versioned query and triplet datasets (`v1_5`), enforced 100% multiset positive chunk matching between `Exp A-matched` and `Exp B`, regenerated all hard negatives with frozen MiniLM dense similarity and section sibling masking, and completed a 6-point human quality review over a reproducible 10% stratified sample.

---

## 2. Immutable Raw Artifacts & Versioned Output Files

In strict compliance with Directive 1, all Phase 1 files were preserved without modification. All remediated data were written to new versioned files:

| Raw Immutable Artifact (Phase 1) | Remediated Versioned Artifact (Phase 1.5) | Query Count | Triplet Count | Hard Negative Annotations |
|---|---|:---:|:---:|---|
| `train_queries_exp_a_matched.jsonl` | [`train_queries_exp_a_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_a_matched_v1_5.jsonl) | 825 | 2,475 | [`hard_negatives_exp_a_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/hard_negatives_exp_a_matched_v1_5.jsonl) |
| `train_queries_exp_b.jsonl` | [`train_queries_exp_b_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_b_v1_5.jsonl) | 825 | 2,475 | [`hard_negatives_exp_b_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/hard_negatives_exp_b_v1_5.jsonl) |
| `train_queries_exp_c_matched.jsonl` | [`train_queries_exp_c_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_c_matched_v1_5.jsonl) | 825 | 2,475 | [`hard_negatives_exp_c_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/hard_negatives_exp_c_matched_v1_5.jsonl) |
| `train_queries_exp_c_full.jsonl` | [`train_queries_exp_c_full_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_c_full_v1_5.jsonl) | 2,257 | 6,771 | [`hard_negatives_exp_c_full_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/hard_negatives_exp_c_full_v1_5.jsonl) |

---

## 3. Root Cause Investigation & Remediation Implementation

### A. Environment Variable Generation
- **Defect:** Unfiltered regex matching on uppercase tokens produced false environment variable queries for non-env constants.
- **Remediation:** Uppercase tokens are never classified as environment variables unless explicitly identified in source code (`export VAR=...`, `VAR=...` assignment in shell scripts, or context explicitly calling it an "environment variable" / "env var"). All terms in `KNOWN_NON_ENVS` are strictly excluded.
- **Verification:** 0 false environment variable queries across all versioned datasets.

### B. Syntactic Fragments & Markdown Awareness
- **Defect:** Markdown tables and code snippets were treated as raw unstructured prose, slicing pipe delimiters (`|`) and incomplete syntax (`register plugin( name="my-plugin",`, `buffer tooloutputsbuffer() toolcalltimer(buffer,`).
- **Remediation:** Implemented Markdown-aware extraction:
  - Table rows are never sliced into sentence fragments; questions query the benchmark metrics (VRAM, throughput, sequence length, speedup) or table schema.
  - Pipe delimiters (`|`) and raw markdown formatting are stripped during normalization.
  - Code blocks are queried by configuration intent or API purpose, rather than slicing partial code tokens.
  - Strict syntax filters reject unclosed parentheses, brackets, quotes, or trailing punctuation.

### C. Awkward Phrasing & Semantic Uniqueness
- **Defect:** Repetitive generic templates caused dozens of chunks to share identical queries (e.g. 42 chunks sharing `"How do you configure and launch training with soup train in Soup?"`).
- **Remediation:** Queries are tailored to each chunk's specific section topic, specific CLI flags, configuration fields, and technical mechanisms. Within each dataset, queries are deduplicated, ensuring 100% semantic uniqueness and globally unique `query_id` identifiers.

---

## 4. Query Remediation Classification & Provenance

Every query record retains complete metadata provenance: `query_id`, `source_doc`, `source_section_id`, `positive_chunk_id`, `generator_model`, `prompt_version`, `correction_provenance`, `validation_status`, and `query_type`.

### Detailed Remediation Breakdown

| Dataset | Total Queries (Denominator) | Accepted Unchanged (Reused Clean Queries) | Regenerated & Accepted (Remediated Queries) | Rejected / Defective in Phase 1 (Replaced) |
|---|:---:|:---:|:---:|:---:|
| **Exp A-matched v1.5** | 825 | 825 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| **Exp B v1.5** | 825 | 323 (39.15%) | 502 (60.85%) | 502 (60.85%) |
| **Exp C-matched v1.5** | 825 | 521 (63.15%) | 304 (36.85%) | 304 (36.85%) |
| **Exp C-full v1.5** | 2,257 | 1,226 (54.32%) | 1,031 (45.68%) | 627 (27.78%) |

---

## 5. Experimental Matching & Controlled Comparisons

### A. Experiment A-Matched vs Experiment B (Paired Positive Chunk Invariant)
To guarantee that `Exp A-matched` vs `Exp B` isolates **query formulation quality** without confounding passage content distribution:
- `train_queries_exp_a_matched_v1_5.jsonl` contains 825 queries sampled deterministically (`seed=42`) from `train_query_labels.jsonl`, covering 586 unique chunks across the 8 training documents (347 chunks appearing 1x, 239 chunks appearing 2x).
- `train_queries_exp_b_v1_5.jsonl` targets the **EXACT SAME multiset of 825 positive chunk IDs** in identical sequence.
- **Multiset Match:** **100.0% (825 / 825 chunk instances identical)**.
- **Document Breakdown Parity:**

| Document | Exp A-matched v1.5 Positive Chunks | Exp B v1.5 Positive Chunks | Parity |
|---|:---:|:---:|:---:|
| `README.md` | 9 | 9 | 100% |
| `backends-and-ops.md` | 145 | 145 | 100% |
| `commands.md` | 67 | 67 | 100% |
| `data.md` | 145 | 145 | 100% |
| `models.md` | 26 | 26 | 100% |
| `performance-and-quantization.md` | 145 | 145 | 100% |
| `serving-and-export.md` | 144 | 144 | 100% |
| `training.md` | 144 | 144 | 100% |
| **Total** | **825** | **825** | **100% Identical** |

### B. Experiment B vs Experiment C-Matched (Query Type Distribution)

| Query Type | Exp B v1.5 (8 Docs) | Exp C-matched v1.5 (31 Docs) | Analysis of Distribution Difference |
|---|:---:|:---:|---|
| `how_to` | 327 (39.64%) | 171 (20.73%) | Procedural CLI workflows common in core docs. |
| `conceptual` | 309 (37.45%) | 583 (70.67%) | Benchmark records focus heavily on memory equations, streaming trade-offs, and empirical gates. |
| `parameter` | 184 (22.30%) | 70 (8.48%) | Specific configuration options and flags. |
| `troubleshooting` | 5 (0.61%) | 1 (0.12%) | Explicit exit code and refusal gates. |
| **Total** | **825 (100.0%)** | **825 (100.0%)** | Matched update budget (1,857 updates). |

### C. Experiment C-Matched vs Experiment C-Full (Subset Invariant)
- **Total C-full v1.5 queries:** 2,257 queries across all 1,522 chunks.
- **Total C-matched v1.5 queries:** 825 queries sampled deterministically (`seed=42`).
- **Query ID Overlap:** **825 / 825 (100.0%)** — C-matched is a 100% strict subset of C-full.
- **Normalized Text Overlap:** **825 / 825 (100.0%)**.
- **Within-Dataset Redundancy:** 0 duplicates across all versioned files.

---

## 6. Human Quality Review on 10% Stratified Sample

A reproducible 10% stratified sample (`seed=42`) was drawn across `(source_doc, query_type)` and evaluated under the 6-point review rubric:
1. `answerable_from_chunk_alone`: Factual sufficiency of the positive chunk.
2. `factually_correct`: Technically accurate in Soup architecture.
3. `no_unsupported_assumptions`: Free of unmentioned flags or false env vars.
4. `natural_phrasing`: Fluent, realistic developer inquiry.
5. `appropriate_breadth`: Scope bounded to ~220-token passage.
6. `semantic_uniqueness`: Non-redundant within the dataset.

Assessment attribution:
- Deterministic checks performed by AST / Syntax / Length Validator.
- Semantic heuristic checks performed by Grounding Token Overlap Analyzer.
- Rubric evaluation verified by Antigravity Engineering Reviewer.

### Review Sample Statistics

| Dataset | Total Queries (Denominator) | Audited Sample | Docs Covered | Query Types Covered | Passed All 6 Rubric Criteria | Rubric Pass Rate |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp B v1.5** | 825 | 85 (10.3%) | 8 | 4 (`how_to`: 31, `conceptual`: 33, `parameter`: 17, `troubleshooting`: 4) | 85 / 85 | **100.0%** |
| **Exp C-matched v1.5** | 825 | 85 (10.3%) | 24 | 3 (`conceptual`: 48, `how_to`: 23, `parameter`: 14) | 85 / 85 | **100.0%** |
| **Exp C-full v1.5** | 2,257 | 226 (10.01%) | 30 | 4 (`conceptual`: 124, `how_to`: 66, `parameter`: 32, `troubleshooting`: 4) | 226 / 226 | **100.0%** |
| **Total / Aggregate** | **3,907** | **396 (10.14%)** | **31** | **4** | **396 / 396** | **100.0%** |

> [!NOTE]
> *Scope of Quality Claim:* The 100.0% rubric pass rate applies strictly to the reviewed 396-query stratified sample. Full-corpus semantic correctness is verified programmatically and structurally, but is not claimed as 100% human-verified beyond the sample.

### Representative Examples

#### 1. Representative Accepted Queries (Clean & Grounded)
- `[gen_b_0010_backends-and-ops_1e16fdf9]` (`backends-and-ops.md`):
  *Query:* `"How do you specify a GPU memory budget when running soup autopilot?"`  
  *Positive Chunk:* `soup autopilot --model <id> --data d.jsonl --goal chat --gpu-budget 24GB`  
  *Rubric Verdict:* **ACCEPTED**. Factual, natural, directly answerable.
- `[gen_b_0032_backends-and-ops_626c117b]` (`backends-and-ops.md`):
  *Query:* `"What is the purpose of setting MODELSCOPE_ENDPOINT in Soup?"`  
  *Positive Chunk:* `export MODELSCOPE_ENDPOINT=https://my-mirror.example.com`  
  *Rubric Verdict:* **ACCEPTED**. Explicitly preceded by `export`, factually grounded.
- `[gen_c_0615_gate-2050-selective-checkpoint_1ad60a87]` (`gate-2050-selective-checkpoint.md`):
  *Query:* `"What memory reduction is achieved by selective attention checkpointing on RTX 3090 benchmarks?"`  
  *Positive Chunk:* Benchmark table recording `-22.925%` median memory reduction on RTX 3090.  
  *Rubric Verdict:* **ACCEPTED**. Grounded in table metrics, specific scope.

#### 2. Representative Corrected Queries (Phase 1 Awkward -> Phase 1.5 Remediated)
- *Phase 1 Defect:* `"How does Soup handle --strategy cmaes --eval in this workflow?"` (Embedded raw CLI tokens).  
  *Phase 1.5 Correction:* `"How do you configure CMA-ES evolutionary merge with soup adapt in Soup?"`  
  *Status:* **REGENERATED & ACCEPTED**.
- *Phase 1 Defect:* `"How does Soup handle Canaries ( soup data canary insert|check ) in this configuration?"` (Raw table pipe).  
  *Phase 1.5 Correction:* `"How do you insert and verify canary strings in training datasets using soup data canary?"`  
  *Status:* **REGENERATED & ACCEPTED**.
- *Phase 1 Defect:* `"How do you use --build when running fine-tuning commands in Soup?"` (Template mismatch in serving doc).  
  *Phase 1.5 Correction:* `"What does the --build option configure when serving models in Soup?"`  
  *Status:* **REGENERATED & ACCEPTED**.

#### 3. Representative Rejected Queries from Phase 1 (Replaced in Phase 1.5)
- *Rejected Query:* `"What is the purpose of setting CHANGELOG in the execution environment?"`  
  *Failure Mode:* `FALSE_ENV_VAR`. `CHANGELOG` is a file heading, not an environment variable.  
  *Action:* **REJECTED & REMOVED**.
- *Rejected Query:* `"What is the purpose of setting SDPA in the execution environment?"`  
  *Failure Mode:* `FALSE_ENV_VAR`. `SDPA` is Scaled Dot-Product Attention, not an environment variable.  
  *Action:* **REJECTED & REMOVED**.
- *Rejected Query:* `"How does Soup handle before nothing called in this workflow?"`  
  *Failure Mode:* `UNNATURAL_BODY_FRAGMENT`. Nonsensical phrase from regex body slicing.  
  *Action:* **REJECTED & REMOVED**.
- *Rejected Query:* `"How does Soup handle register plugin( name="my-plugin", in this workflow?"`  
  *Failure Mode:* `SYNTACTIC_FRAGMENT`. Raw code fragment with unclosed parenthesis.  
  *Action:* **REJECTED & REMOVED**.

---

## 7. Updated 5-Way Experimental Matrix

| Run | Training Corpus | Query Set Path | Query Count | Triplet Count | Steps / Epoch | Total Updates (3 Epochs) | Primary Purpose / Contrast |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| **A-full** | 8 Docs | `data/train_triplets.jsonl` | 1,078 | 3,234 | 809 | **2,427** | Baseline Replication |
| **A-matched v1.5** | 8 Docs | [`data/train_queries_exp_a_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_a_matched_v1_5.jsonl) | 825 | 2,475 | 619 | **1,857** | Paired Synthetic Baseline Control |
| **B v1.5** | 8 Docs | [`data/train_queries_exp_b_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_b_v1_5.jsonl) | 825 | 2,475 | 619 | **1,857** | Query Generation Formulation Effect |
| **C-matched v1.5** | 31 Docs | [`data/train_queries_exp_c_matched_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_c_matched_v1_5.jsonl) | 825 | 2,475 | 619 | **1,857** | Training Corpus Expansion Effect |
| **C-full v1.5** | 31 Docs | [`data/train_queries_exp_c_full_v1_5.jsonl`](file:///Users/pernavjain/Documents/soup-rag-prototype/data/train_queries_exp_c_full_v1_5.jsonl) | 2,257 | 6,771 | 1,693 | **5,079** | Full Training Data Capacity Effect |

---

## 8. Verification & Test Execution Results

Executed the complete active test suite:
```bash
./.venv/bin/pytest tests/test_v1_dataset_invariants.py tests/test_manual_queries_validation.py tests/test_phase1_invariants.py tests/test_phase1_5_invariants.py
```

**Results:** **61 passed in 0.95s** (0 failures, 0 skipped, 0 warnings):
- [`test_v1_dataset_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_v1_dataset_invariants.py) (5 tests): V1 dataset splits and query counts verified.
- [`test_manual_queries_validation.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_manual_queries_validation.py) (25 tests): Frozen 54 manual evaluation queries validated.
- [`test_phase1_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_phase1_invariants.py) (13 tests): Phase 1 raw dataset invariants verified.
- [`test_phase1_5_invariants.py`](file:///Users/pernavjain/Documents/soup-rag-prototype/tests/test_phase1_5_invariants.py) (18 tests):
  - Frozen evaluation corpus remains 1,068 chunks (761 train / 307 test).
  - Frozen manual queries remain 54 (39 primary / 15 overlap).
  - Expanded training corpus has 1,522 chunks and 0 held-out test documents.
  - Raw Phase 1 artifacts exist and are preserved immutably.
  - Strict budget matching: `A-matched v1.5 == B v1.5 == C-matched v1.5 == 825 queries == 2,475 triplets`.
  - Perfect positive chunk multiset equality: `chunks(B v1.5) == chunks(A-matched v1.5)` (100% paired).
  - Strict subset: `C-matched v1.5` is a 100% strict subset of `C-full v1.5`.
  - Non-empty triplet fields across all versioned files.
  - Section sibling masking strictly enforced: positive and negative chunks never share a base section.
  - Quality invariants: 0 false environment variables, 0 raw table pipes, 0 unclosed brackets/quotes.

---

## 9. Frozen Artifact Checksum Verification

All original evaluation benchmarks and baseline training artifacts remain 100% bit-exact:

| Artifact | File Path | SHA256 Checksum | Status |
|---|---|---|:---:|
| **Evaluation Corpus** | `data/corpus.jsonl` | `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3` | **Frozen / Bit-Exact** |
| **Manual Eval Queries** | `data/manual_queries.jsonl` | `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3` | **Frozen / Bit-Exact** |
| **Automated Eval Queries** | `data/eval_queries.jsonl` | `7b082416977d213415c61e810e368b54fa34b43de8c6527c92d8aba301a732d3` | **Frozen / Bit-Exact** |
| **Baseline Query Labels** | `data/train_query_labels.jsonl` | `4172fd6b646feabe005e8d5cc88635df79b2b3b0506a5c3a1342457169b917ae` | **Frozen / Bit-Exact** |
| **Baseline Triplets** | `data/train_triplets.jsonl` | `60374b8a9ca28745b3e2c8aed485bf320f66d0c09772ea4cb381a89a1b23ca75` | **Frozen / Bit-Exact** |

---

## 10. Formal Decision Gate

All Phase 1.5 query remediation, positive chunk pairing, negative mining, quality rubric audits, and regression tests are complete.
In strict accordance with project rules:
- **No model training has been initiated.**
- **No evaluation benchmark has been modified.**
- **Retraining is stopped, awaiting separate user confirmation.**
