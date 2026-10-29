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
*Expected: 12 passed in ~20s.*

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
