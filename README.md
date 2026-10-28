# soup-rag-prototype

Embedding fine-tuning prototype for Soup CLI documentation retrieval.

Compares retrieval quality **before and after** fine-tuning `sentence-transformers/all-MiniLM-L6-v2` with LoRA through [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` training path.

## Results

| Metric | Baseline (Frozen) | Fine-Tuned (LoRA) | Delta | p-value |
|--------|-------------------|--------------------|-------|---------|
| Recall@1 | 0.5453 | **0.6700** | **+12.5%** | < 0.0001 |
| Recall@3 | 0.7606 | **0.8551** | **+9.5%** | < 0.0001 |
| Recall@5 | 0.8209 | **0.9034** | **+8.3%** | < 0.0001 |
| MRR@10 | 0.6615 | **0.7706** | **+10.9%** | < 0.0001 |

Evaluated on 497 held-out queries from 4 documents the model never saw during training, retrieving against all 1,068 chunks from 12 documents.

## Setup

- **Corpus:** 12 Soup CLI documentation Markdown files (~368 KB)
- **Split:** 8 train docs / 4 held-out test docs (document-level, not random chunks)
- **Base model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 22.86M params)
- **Fine-tuning:** LoRA r=16, α=32 (147K trainable params, 0.65%), triplet loss with mined hard negatives
- **Training:** 3 epochs, 729 steps, 28 minutes on CPU
- **Retrieval:** Dense cosine similarity (exact dot product on L2-normalized vectors)

## Reproduce

```bash
# 1. Prepare corpus (chunks the 12 docs)
python scripts/prepare_corpus.py

# 2. Generate queries
python scripts/generate_queries.py

# 3. Mine hard negatives
python scripts/mine_hard_negatives.py

# 4. Baseline evaluation
python scripts/evaluate_retrieval.py --output results/baseline.json

# 5. Fine-tune through Soup
soup train --config config/embedding.yaml

# 6. Candidate evaluation
python scripts/evaluate_retrieval.py --adapter-dir output_embedding --output results/candidate.json

# 7. Compare
python scripts/compare_results.py --baseline results/baseline.json --candidate results/candidate.json
```

## Requirements

- Python 3.11+
- PyTorch, Transformers, PEFT
- soup-cli (for `soup train`)
- Soup CLI docs in `../scratch/upstream_soup/docs/` (or adjust path in `prepare_corpus.py`)
