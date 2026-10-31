# Reproduction Guide: Soup Embedding Fine-Tuning Prototype

This guide provides exact, copy-pasteable instructions to verify the benchmark numbers or reproduce the entire pipeline from scratch.

---

## 1. Quick Verification (Fast Path: ~30 Seconds)

If you already have the repository cloned and the fine-tuned adapter weights in `output_embedding/`, you can verify the benchmark numbers immediately without retraining:

### Step 1: Run the Automated Test Suite
Verify that all formatting, section deduplication, model adapter loading, and configuration invariants pass:
```bash
pytest tests/test_retrieval_pipeline.py -v
```
*Expected: 15 passed in ~23s.*

### Step 2: Evaluate the Fine-Tuned Model on Held-Out Queries
```bash
python scripts/evaluate_retrieval.py \
    --adapter-dir output_embedding \
    --output results/candidate.json
```
*Expected Terminal Output:*
```
==================================================
  Mode: candidate
  recall@1: 0.7565
  recall@3: 0.9336
  recall@5: 0.9718
  mrr@10: 0.8477
==================================================
```

### Step 3: Run Paired Bootstrap Comparison
```bash
python scripts/compare_results.py \
    --baseline results/baseline.json \
    --candidate results/candidate.json \
    --output results/comparison.md
```
*Check output in `results/comparison.md`: Recall@1 delta = +0.2113, 95% CI [+0.1650, +0.2555].*

---

## 2. Full Reproduction from Scratch (~7 Minutes)

To rebuild the corpus, regenerate queries, mine triplets, train the LoRA adapter with Soup, and re-evaluate from zero:

### Prerequisites & Environment Setup

Python 3.10+ is required. Install required dependencies:
```bash
pip install torch transformers "peft>=0.14.0" datasets numpy pyyaml rich pytest
pip install soup-cli
```

### Step 1: Chunk the Markdown Documentation
Reads the 12 Markdown files, applies ATX heading splitting, sub-splits sections exceeding 220 tokens, and assigns document-level train/test splits (8 train docs / 4 held-out test docs):
```bash
python scripts/prepare_corpus.py
```
*Output: `data/corpus.jsonl` (1,068 chunks) and `data/document_split.json`.*

### Step 2: Generate Synthetic Evaluation Queries
Deterministically synthesizes training queries and 497 held-out test queries from the document splits:
```bash
python scripts/generate_queries.py
```
*Output: `data/train_query_labels.jsonl` (1,078 train queries) and `data/eval_queries.jsonl` (497 test queries).*

### Step 3: Mine Hard Negatives with Section Deduplication
Computes cosine similarities on prefixed chunks, applies section deduplication (avoiding sibling and relevant sections), and generates top-3 negatives per query with prepended heading prefixes:
```bash
python scripts/mine_hard_negatives.py --num-negatives 3
```
*Output: `data/train_triplets.jsonl` (3,234 triplets) and `data/hard_negatives.jsonl` (3,234 records across 618 chunks).*

### Step 4: Evaluate Baseline Retrieval (Before Fine-Tuning)
Ranks all 1,068 chunks for the 497 test queries using the frozen `sentence-transformers/all-MiniLM-L6-v2` base model:
```bash
python scripts/evaluate_retrieval.py --output results/baseline.json
```
*Expected: Recall@1: 0.5453, Recall@3: 0.7606, Recall@5: 0.8209, MRR@10: 0.6615.*

### Step 5: Fine-Tune with Soup
Launches Soup's native embedding trainer (`val_split: 0.0`, triplet loss, LoRA $r=16, \alpha=32$):
```bash
soup train -y --config config/embedding.yaml
```
*Runtime:*
- **Apple Silicon (MPS)**: ~6 minutes (2,427 steps at ~6.5–8.5 it/s)
- **NVIDIA GPU (CUDA)**: ~2–4 minutes
- **CPU**: ~80 minutes
*Output: Checkpoints and final LoRA adapter in `output_embedding/`.*

### Step 6: Evaluate Fine-Tuned Retrieval (After Fine-Tuning)
Evaluates the newly trained LoRA adapter on the exact same 497 held-out test queries:
```bash
python scripts/evaluate_retrieval.py \
    --adapter-dir output_embedding \
    --output results/candidate.json
```
*Expected: Recall@1: 0.7565, Recall@3: 0.9336, Recall@5: 0.9718, MRR@10: 0.8477.*

### Step 7: Compute Paired Bootstrap Uncertainty Intervals
Runs paired bootstrap resampling (10,000 iterations) to compute 95% confidence intervals on paired metric deltas:
```bash
python scripts/compare_results.py \
    --baseline results/baseline.json \
    --candidate results/candidate.json \
    --output results/comparison.md
```

---

## 3. Troubleshooting & Notes

- **Apple Silicon Warning**: During training or matrix multiplication on macOS, you may see benign PyTorch/NumPy runtime warnings regarding BLAS floating-point exception status registers. These do not affect numerical correctness and are safely filtered in testing scripts.
- **Paths**: All configuration paths are relative to the repository root. Ensure commands are executed from the repository root directory.

---

## 4. Evaluation v2 (manual benchmark)

The v2 layer evaluates the existing adapter and baselines on 54 owner-approved
manual queries (drafted by Qoder). It never retrains the adapter and never modifies v1 data.

Environment (once):

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Dataset workflow (already complete; documented for revalidation):

```bash
# 1. Queries were drafted by Qoder and reviewed/frozen by the owner
#    (worksheet: docs/EVALUATION_V2_COVERAGE.md)
# 2. Verbatim transcription into data/manual_queries.jsonl; 54 records
# 3. Validate (errors block; overlap flags are provisional review material)
.venv/bin/python scripts/validate_manual_queries.py
.venv/bin/python scripts/validate_manual_queries.py --semantic   # optional embedding-based flags
# 4. Frozen: query-set fingerprint
#    116bd4c36a6b7747e86bb36b1836b4d1f9c4a552c2c8c752f14c066f38086f3d
```

Expected validator output: `checked 54 queries`, `errors: 0`, `warnings: 0`,
`overlap flags: 1` (`manual_010`, a provisional lexical flag against the
two-line training chunk `backends-and-ops::machine-readable-output`; the real
registry-diff duplicate is already labeled `overlap`).

Four-way retrieval run:

```bash
.venv/bin/python scripts/run_retrieval.py --retriever mini_lm_frozen --output results/v2/mini_lm_frozen.json
.venv/bin/python scripts/run_retrieval.py --retriever mini_lm_soup   --output results/v2/mini_lm_soup.json
.venv/bin/python scripts/run_retrieval.py --retriever bm25           --output results/v2/bm25.json
.venv/bin/python scripts/run_retrieval.py --retriever e5_small       --output results/v2/e5_small.json
.venv/bin/python scripts/compare_retrievers.py                       # -> results/v2/comparison.md
```

Expected micro metrics (Hit@1 / Hit@5 / MRR@10): E5-small-v2
0.6852 / 0.8704 / 0.7834; MiniLM frozen 0.5926 / 0.8704 / 0.7021;
MiniLM + Soup 0.5556 / 0.8148 / 0.6686; BM25 0.4815 / 0.7222 / 0.5984.
All four result files must share corpus fingerprint `76ab5e88…` and
query-set fingerprint `116bd4c3…`; the report must state the no-p-value,
four-document caveat. Clean-room verification is reproducible bit-exactly
(see `docs/EVALUATION_V2_PROGRESS.md`, Phase 7).

Methodology and gates: `docs/EVALUATION_V2_SPEC.md`.
