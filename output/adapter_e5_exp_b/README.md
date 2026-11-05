---
base_model: intfloat/e5-small-v2
base_model_revision: ffb93f3bd4047442299a41ebb6fa998a38507c52
library_name: peft
license: apache-2.0
tags:
  - lora
  - peft
  - feature-extraction
  - retrieval
  - soup
---

# Soup-LoRA E5-Small Retrieval Adapter (Experiment B, lr=2e-4)

LoRA adapter for `intfloat/e5-small-v2`, fine-tuned through [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` training path on Soup CLI technical documentation.

## Training Configuration

| Setting | Value |
|---|---|
| Task | embedding (triplet contrastive) |
| Base Model | `intfloat/e5-small-v2` (revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`) |
| Loss | TripletMarginLoss (margin 0.5) |
| Training Data | 2,475 triplets (825 queries, 3 negatives per query) from `data/triplets_exp_b_v1_5.jsonl` |
| LoRA Rank / Alpha | $r=16, \alpha=32$, target modules `query` + `value` |
| Learning Rate | 2e-4 |
| Epochs / Steps | 3 epochs, 1,857 optimizer updates |
| Optimizer | AdamW, batch size 4 |
| Seed | 42 |
| Config | `config/embedding_e5_exp_b.yaml` |

## Evaluation Findings

Evaluated on the historical 54-query benchmark:
- Recorded severe regression (0.3530 MRR@10) due to learning rate overshooting at 2e-4.
- Motivated retraining with matched learning rate 2e-5 (`output/adapter_e5_exp_b_lr2e5`).
