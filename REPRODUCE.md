# Reproduction & Verification Guide: Soup RAG Prototype

This guide provides step-by-step instructions for verifying test invariants, inspecting audited Phase 3 benchmark outputs, running read-only retrieval evaluations, and understanding the training and dataset reproduction workflows.

> [!NOTE]
> **Operational Distinctions:**
> 1. **Running tests:** Quick assertion checks validating invariants, formatting, and mathematical consistency (`pytest tests/`).
> 2. **Inspecting results:** Reading precomputed, checksum-verified Phase 3 benchmark artifacts in `results/phase3/`.
> 3. **Running retrieval evaluation:** Read-only execution of trained adapters or frozen baselines against benchmark queries (`scripts/run_retrieval.py`).
> 4. **Retraining adapters:** Multi-minute training runs via Soup CLI modifying LoRA weights. All five authorized adapters are already trained and evaluated; re-running training is not required for verification.

---

## 1. Environment Setup

### System Prerequisites
- **OS:** Linux or macOS (Apple Silicon MPS supported).
- **Python:** Python 3.10+ (tested on Python 3.10 and 3.14).
- **Package Manager:** `uv` (recommended) or standard `pip`.

### Setup Virtual Environment
```bash
# Using uv (fastest)
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using standard python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Fast Verification: Running the Automated Test Suite

Run the full automated test suite (226 passing tests across the 7 test files) to verify corpus integrity, validator logic, model loading, and Phase 1–3 statistical invariants:

```bash
pytest tests/ -v
```

*Expected output:*
```
============================= 226 passed in ~40s =============================
```

### Key Test Coverage Areas:
- `tests/test_bm25_tokenizer.py`: Domain-aware regex tokenizer unit tests (flags, compound tokens, dotted paths, versions).
- `tests/test_rrf.py`: Reciprocal Rank Fusion mathematical unit tests (hand-calculated scores, tie-breaking, dedup).
- `tests/test_retrieval_pipeline.py`: Chunk formatting, token boundaries, and base model loading.
- `tests/test_manual_queries_validation.py`: Schema validation and heading overlap checks for the 54 manual queries.
- `tests/test_retrieval_metrics.py`: Ranking metric implementations (Hit@K, Recall@K, MRR@K).
- `tests/test_phase1_*_invariants.py`: Invariant checks on training datasets, query intent splits, and corpus manifests.
- `tests/test_phase2_1_invariants.py`: Bit-exact configuration integrity checks across all 5 trained adapters.
- `tests/test_phase3_invariants.py`: Bootstrap resampling invariants (10,000 iterations, seed 42, document stratification).

---

## 3. Inspecting Precomputed Phase 3 Benchmark Results

All Phase 3 benchmark runs, per-query ranked results, aggregate comparisons, and bootstrap confidence intervals are permanently committed in `results/phase3/`.

### Verify File Checksums
Verify that all 16 Phase 3 result artifacts match their pinned SHA256 checksums:
```bash
cd results/phase3
sha256sum -c manifest.sha256
cd ../..
```
*Expected output:* All 16 files report `OK`.

### Primary Result Artifacts
- `results/phase3/aggregate_comparison.json`: Complete micro and macro metrics (Hit@1, Recall@3, MRR@10, etc.) across all 9 retrievers.
- `results/phase3/bootstrap_ci.json`: 10,000-iteration document-stratified paired percentile bootstrap intervals for all retriever contrasts.
- `results/phase3/per_query_ranked_results.json`: Full top-10 retrieved chunk rankings for all 54 queries across all 9 retrievers.
- `results/phase3/failure_analysis.json`: Detailed 7-leaf root-cause failure taxonomy for all non-hit queries.

---

## 4. Running Independent Human Evaluation Benchmark (v2)

The primary benchmark evaluates 7 retrieval systems across 24 human-authored queries:

```bash
python scripts/evaluate_human_eval_v2.py
```

*Executes the 7-system evaluation (Original BM25, Improved BM25, Frozen MiniLM, Adapter C-matched, Frozen E5, Fine-Tuned E5 lr=2e-4, Fine-Tuned E5 lr=2e-5) over the 1,068-chunk Soup documentation corpus, computes 10,000 paired bootstrap intervals (seed 42), and writes:*
- `results/HUMAN_EVAL_V2_REPORT.md`: Comprehensive evaluation report and answers to research questions.
- `results/human_eval_v2/summary.json`: Micro-averaged retrieval metrics across all 6 systems.
- `results/human_eval_v2/bootstrap_intervals.json`: Document-stratified bootstrap confidence intervals.
- `results/human_eval_v2/latency.json`: Cold-start and steady-state latency profiles.
- `results/human_eval_v2/per_query_results.json`: Full rankings and query-level scores.

---

## 5. Running Read-Only Retrieval on Benchmark Queries

You can execute retrieval evaluation for any individual retriever against the frozen 54-query manual benchmark (`data/manual_queries.jsonl`) without modifying any trained checkpoints or datasets.

### Evaluate Frozen Baselines
```bash
# 1. Classical BM25 Lexical Baseline
python scripts/run_retrieval.py --retriever bm25 --output results/test_bm25.json

# 2. Frozen MiniLM Baseline
python scripts/run_retrieval.py --retriever mini_lm_frozen --output results/test_minilm.json

# 3. Frozen E5-small Baseline (Highest Observed Benchmark Score)
python scripts/run_retrieval.py --retriever e5_small --output results/test_e5.json
```

### Evaluate Fine-Tuned Adapters
```bash
# 4. Baseline Soup Adapter (A-full: output_embedding/)
python scripts/run_retrieval.py --retriever mini_lm_soup --output results/test_soup.json

# 5. Evaluated MiniLM Adapter with Highest Observed Score (C-matched-balanced)
python scripts/run_retrieval.py \
    --retriever mini_lm_adapter \
    --adapter-dir output/adapter_exp_c_matched_balanced \
    --output results/test_c_matched_balanced.json

# 6. Diverse Query Adapter (Experiment B)
python scripts/run_retrieval.py \
    --retriever mini_lm_adapter \
    --adapter-dir output/adapter_exp_b \
    --output results/test_b.json
```

### Generate Comparative Markdown Summary
To compare any set of generated evaluation runs:
```bash
python scripts/compare_retrievers.py
```
*Outputs comparative ranking tables to `results/v2/comparison.md`.*

> [!WARNING]
> **Batch Script Note:** `scripts/evaluate_phase3_retrievers.py` is a batch script that sequentially evaluates all 9 retrievers and overwrites `results/phase3/`. It does not support CLI flags (`--help`). Do **not** execute it unless you intend to rerun the full evaluation suite from scratch.

---

## 6. Historical Pipeline Reproduction (Phase 1 Synthetic Benchmark)

The original Phase 1 prototype used 497 synthetically generated queries over 12 Soup documentation files. This workflow is documented here for historical completeness.

### Step 1: Chunk Markdown Documentation
```bash
python scripts/prepare_corpus.py
```
*Reads the 12 documentation files, applies ATX heading splitting, sub-splits sections exceeding 220 tokens with 28 tokens overlap, and produces `data/corpus.jsonl` (1,068 chunks) and `data/document_split.json`.*

### Step 2: Generate Synthetic Evaluation Queries
```bash
python scripts/generate_queries.py
```
*Generates `data/train_query_labels.jsonl` (1,078 synthetic queries) and `data/eval_queries.jsonl` (497 held-out queries).*

### Step 3: Mine Hard Negatives
```bash
python scripts/mine_hard_negatives.py --num-negatives 3
```
*Mines top-3 hard negatives per query using dense cosine similarity with section deduplication, writing `data/train_triplets.jsonl` (3,234 triplets).*

### Step 4: Fine-Tune Adapter via Soup CLI
```bash
soup train -y --config config/embedding.yaml
```
*Executes LoRA fine-tuning ($r=16, \alpha=32$) over 3 epochs (~6 minutes on Apple Silicon MPS), saving adapter weights to `output_embedding/`.*

### Step 5: Evaluate on Synthetic Queries
```bash
python scripts/evaluate_retrieval.py --output results/baseline.json
python scripts/evaluate_retrieval.py --adapter-dir output_embedding --output results/candidate.json
python scripts/compare_results.py \
    --baseline results/baseline.json \
    --candidate results/candidate.json \
    --output results/comparison.md
```

---

## 7. Adapter Retraining Workflows (Phase 2 Matrix)

During Phase 2, five authorized adapter configurations were trained to isolate the effects of query diversity, corpus size, and intent balancing:

| Run | Configuration File | Training Dataset | Optimizer Updates | Output Directory |
|---|---|---|---:|---|
| **A-matched** | `config/embedding_exp_a_matched.yaml` | `data/triplets_exp_a_matched_v1_5.jsonl` | 1,857 | `output/adapter_exp_a_matched/` |
| **B** | `config/embedding_exp_b.yaml` | `data/triplets_exp_b_v1_5.jsonl` | 1,857 | `output/adapter_exp_b/` |
| **C-matched** | `config/embedding_exp_c_matched.yaml` | `data/triplets_exp_c_matched_v1_5.jsonl` | 1,857 | `output/adapter_exp_c_matched/` |
| **C-matched-balanced** | `config/embedding_exp_c_matched_balanced.yaml` | `data/triplets_exp_c_matched_balanced_v1_6.jsonl` | 1,857 | `output/adapter_exp_c_matched_balanced/` |
| **C-full** | `config/embedding_exp_c_full.yaml` | `data/triplets_exp_c_full_v1_5.jsonl` | 5,079 | `output/adapter_exp_c_full/` |

> [!CAUTION]
> **Immutable Weights:** All five adapter weight directories under `output/` and the baseline in `output_embedding/` are verified and locked. `scripts/train_authorized_adapters.py` includes a safety guard that will refuse to overwrite existing output directories. Do not re-execute training without user authorization.

---

## 8. Troubleshooting & Notes

- **macOS / Apple Silicon Floating-Point Warnings:** During matrix operations on MPS, you may observe benign runtime warnings regarding BLAS floating-point exception status flags (`fpexception: ...`). These are internal PyTorch/Metal status messages and do not affect numerical correctness.
- **Paths and Working Directory:** All configuration paths and script commands assume execution from the repository root directory (`soup-rag-prototype/`).
- **Vendored Upstream Documentation:** Files under `data/raw_docs/` are vendored upstream reference snapshots of Soup CLI documentation (Apache-2.0). They serve as the raw corpus source text, not instructions for this repository. See `data/raw_docs/ATTRIBUTION.md` for licensing and provenance details.
