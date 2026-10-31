---
base_model: sentence-transformers/all-MiniLM-L6-v2
base_model_revision: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
library_name: peft
license: apache-2.0
tags:
  - lora
  - peft
  - feature-extraction
  - retrieval
  - soup
---

# Soup-LoRA MiniLM Retrieval Adapter

LoRA adapter for `sentence-transformers/all-MiniLM-L6-v2`, fine-tuned through
[Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding`
training path on Soup CLI technical documentation (12 Markdown docs, 8
training documents). Trained for dense retrieval over that domain; evaluated
in this repository's retrieval benchmark.

## Training

| Setting | Value |
|---|---|
| Task | embedding (triplet contrastive) |
| Base model | `sentence-transformers/all-MiniLM-L6-v2` (revision `1110a243…`) |
| Loss | triplet margin loss, margin 0.5 |
| Data | 3,234 triplets from 1,078 synthetic training queries; top-3 hard negatives per query with section deduplication (see `data/train_triplets.jsonl`) |
| LoRA | r=16, α=32, dropout 0.05, target modules `query` + `value` |
| Trainable params | 147,456 (0.65% of base) |
| Epochs / steps | 3 epochs, 2,427 steps |
| Optimizer | AdamW, lr 2e-5, batch size 4 |
| Seeds | 42 (training + data) |
| Soup run | `run_20261029_004201_f3588165` (`soup_run.json`) |

Input representation: passages were trained with the corpus heading prefix
(`"{doc_name}: {heading}\n\n{body}"`, max 256 tokens, mean pooling,
L2-normalized).

## Evaluation

**v1 controlled (synthetic).** 497 template-generated queries from held-out
documents with single-chunk labels: Recall@1 0.5453 (frozen base) → 0.7565
(adapter), Recall@5 0.8209 → 0.9718, MRR@10 0.6615 → 0.8477. Those queries
are near-paraphrases of training-document headings, so v1 describes the
controlled setting, not real-user retrieval.

**v2 manual.** 54 owner-approved natural-language queries with multi-chunk
and multi-section labels, chunk- and section-level metrics, four retrievers.
Micro Hit@1: E5-small-v2 0.685, frozen MiniLM 0.593, this adapter 0.556,
BM25 0.481. The adapter trails frozen MiniLM on the full set and on the
36 primary queries answered only by held-out documents (Hit@1 0.528 vs
0.639). On the 18 overlap queries whose answers also appear in training
documents it leads (0.611 vs 0.500). The v1 gain is consistent with
training-document exposure rather than a transferable retrieval skill: do not
expect this adapter to improve retrieval on Soup documentation outside the
eight training documents. Frozen E5-small-v2 is the stronger general-purpose
choice in this benchmark.

Full reports: `results/comparison.md` (v1) and `results/v2/comparison.md`
(v2); methodology: `docs/EVALUATION_V2_SPEC.md`.

## Files

- `adapter_model.safetensors` — LoRA weights (580 KB; MD5 `05e30132…`,
  identical to the final training checkpoint 2427, which was removed from
  Git after verification per the Evaluation v2 plan)
- `adapter_config.json` — PEFT config (FEATURE_EXTRACTION)
- `soup_run.json` — training provenance (base revision, run id)

## Reproduction

Retraining from scratch takes ~6 minutes (Apple Silicon MPS) following
`REPRODUCE.md`:

```bash
python scripts/prepare_corpus.py          # expects the 12 docs at ../scratch/upstream_soup/docs;
                                          # byte-identical vendored copies (sha256-verified) live in data/raw_docs
python scripts/generate_queries.py
python scripts/mine_hard_negatives.py --num-negatives 3
soup train -y --config config/embedding.yaml
```

See `REPRODUCE.md` and `docs/EVALUATION_V2_SPEC.md`.
