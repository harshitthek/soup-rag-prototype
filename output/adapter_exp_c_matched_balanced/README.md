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

# Soup-LoRA MiniLM Retrieval Adapter (Experiment C-matched-balanced)

LoRA adapter for `sentence-transformers/all-MiniLM-L6-v2`, fine-tuned through [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` training path on Soup CLI technical documentation.

## Training Configuration

| Setting | Value |
|---|---|
| Task | embedding (triplet contrastive) |
| Base Model | `sentence-transformers/all-MiniLM-L6-v2` (revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) |
| Loss | TripletMarginLoss (margin 0.5) |
| Training Data | 2,475 triplets (825 queries over 31 docs, intent-stratified) from `data/triplets_exp_c_matched_balanced_v1_6.jsonl` |
| LoRA Rank / Alpha | $r=16, \alpha=32$, target modules `query` + `value` |
| Learning Rate | 2e-5 |
| Epochs / Steps | 3 epochs, 1,857 optimizer updates |
| Optimizer | AdamW, batch size 4 |
| Seed | 42 |
| Config | `config/embedding_exp_c_matched_balanced.yaml` |

## Evaluation Findings

- **Historical 54-query benchmark:** 0.7681 MRR@10 and 0.6667 Hit@1, the highest observed score among evaluated MiniLM adapters on that benchmark (subject to candidate selection bias).
- **Independent 24-query benchmark (`human_eval_v2`):** 0.7004 MRR@10 versus 0.6587 for Frozen MiniLM (+0.0417 delta; paired 95% bootstrap CI `[-0.0382, +0.1215]` includes zero).
