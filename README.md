# soup-rag-prototype

Embedding fine-tuning prototype for Soup CLI documentation retrieval.

Compares dense retrieval quality **before and after** fine-tuning `sentence-transformers/all-MiniLM-L6-v2` with LoRA through [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` training path on a held-out test set of real Markdown technical documentation.

---

## Benchmark Results

Evaluated on **497 held-out queries** from **4 unseen documents** the model never encountered during training or negative mining, retrieving against all **1,068 chunks** from 12 documents.

| Metric | Baseline (Frozen MiniLM) | Candidate v1 (Initial LoRA) | **Candidate v2 (Final LoRA)** | Total Gain vs Baseline | Gain vs v1 | p-value | Significant |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Recall@1** | 0.5453 | 0.6700 | **0.7565** | **+21.12%** (+0.2113) | **+8.65%** (+0.0865) | < 0.0001 | Yes |
| **Recall@3** | 0.7606 | 0.8551 | **0.9336** | **+17.30%** (+0.1730) | **+7.85%** (+0.0785) | < 0.0001 | Yes |
| **Recall@5** | 0.8209 | 0.9034 | **0.9718** | **+15.09%** (+0.1509) | **+6.84%** (+0.0684) | < 0.0001 | Yes |
| **MRR@10** | 0.6615 | 0.7706 | **0.8477** | **+18.62%** (+0.1862) | **+7.72%** (+0.0772) | < 0.0001 | Yes |

*Paired bootstrap evaluation (10,000 resamples, seed=42, $\alpha=0.05$). All 95% confidence intervals are strictly positive.*

---

## Prototype Setup & Specifications

- **Use Case:** High-precision dense retrieval over technical developer documentation (Soup CLI commands, configuration options, training workflows, and governance surfaces).
- **Corpus:** 12 Soup CLI documentation Markdown files (~368 KB total), token-bounded to $\le 220$ tokens per chunk using ATX heading boundaries with retained hierarchical heading prefixes.
- **Data Split:** **Document-level separation** (8 training docs / 4 strictly held-out test docs) to eliminate data leakage across adjacent chunks.
- **Base Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings, 22.86M total parameters).
- **Fine-Tuning:** LoRA adapter ($r=16, \alpha=32$, targeting query and value projections; 147,456 trainable parameters = 0.65% of model).
- **Loss & Contrastive Sampling:** Triplet margin loss ($m=0.5$), top-3 hard negatives mined per query with section deduplication (3,234 training triplets across 618 distinct negative chunks).
- **Training Runtime:** 3 epochs (2,427 steps), ~6 minutes on Apple Silicon MPS (Metal GPU) via Soup's native embedding trainer.
- **Retrieval Engine:** Dense cosine similarity (exact dot product on L2-normalized float32 vectors).

---

## Deliverables & Documentation

- **[`REPORT.md`](REPORT.md)**: Comprehensive prototype delivery report detailing use case requirements, Markdown parsing & chunking strategy, leak-free evaluation design, statistical significance, and failure analysis.
- **[`REPRODUCE.md`](REPRODUCE.md)**: Self-contained, step-by-step reproduction and verification guide with copy-pasteable commands.
- **[`improvement.md`](improvement.md)**: Engineering evolution report detailing how v2 resolved v1 bottlenecks (P0 heading prefix alignment, P1 multi-negative section deduplication, P2 data recovery).
- **[`tests/test_v2_changes.py`](tests/test_v2_changes.py)**: Automated unit and integration test suite (11 passing tests) covering formatting, section deduplication, and config integrity.

---

## Quickstart & Reproduction

```bash
# 1. Prepare corpus from Markdown docs (1,068 token-bounded chunks)
python scripts/prepare_corpus.py

# 2. Generate synthetic queries (1,078 train / 497 held-out test)
python scripts/generate_queries.py

# 3. Mine hard negatives (top-3 per query with section deduplication -> 3,234 triplets)
python scripts/mine_hard_negatives.py --num-negatives 3

# 4. Evaluate baseline retrieval (frozen base model)
python scripts/evaluate_retrieval.py --output results/baseline.json

# 5. Fine-tune LoRA adapter through Soup
soup train -y --config config/embedding_v2.yaml

# 6. Evaluate fine-tuned candidate v2
python scripts/evaluate_retrieval.py --adapter-dir output_embedding_v2 --output results/candidate_v2.json

# 7. Compare results with paired bootstrap significance
python scripts/compare_results.py \
    --baseline results/baseline.json \
    --candidate results/candidate_v2.json \
    --output results/comparison_v2.md
```

See [`REPRODUCE.md`](REPRODUCE.md) for full reproduction options, environment setup, and test commands.

---

## Requirements

- Python 3.10+
- PyTorch 2.0+, Transformers 4.40+, PEFT 0.10+
- [Soup CLI](https://github.com/MakazhanAlpamys/Soup) (for `soup train`)
