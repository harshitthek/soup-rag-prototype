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

# Soup-LoRA E5-Small Retrieval Adapter (Experiment B, lr=2e-5)

LoRA adapter for `intfloat/e5-small-v2`, fine-tuned through [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` training path on Soup CLI technical documentation.

## Training Configuration

| Setting | Value |
|---|---|
| Task | embedding (triplet contrastive) |
| Base Model | `intfloat/e5-small-v2` (revision `ffb93f3bd4047442299a41ebb6fa998a38507c52`) |
| Loss | TripletMarginLoss (margin 0.5) |
| Training Data | 2,475 triplets (825 queries, 3 negatives per query) from `data/triplets_exp_b_v1_5.jsonl` |
| LoRA Rank / Alpha | $r=16, \alpha=32$, target modules `query` + `value` |
| Learning Rate | 2e-5 |
| Epochs / Steps | 3 epochs, 1,857 optimizer updates |
| Optimizer | AdamW, batch size 4 |
| Seed | 42 |
| Config | `config/embedding_e5_exp_b_lr2e5.yaml` |

## Evaluation Findings

Evaluated against Frozen E5-small on the independent 24-query owner-authored benchmark (`data/human_eval/manifest_v2.json`):
- **Frozen E5-small:** MRR@10 0.7101, Hit@1 0.6250, Recall@3 0.4562.
- **Fine-Tuned E5-small (lr=2e-5):** MRR@10 0.6413, Hit@1 0.5417, Recall@3 0.5177.
- Frozen E5-small observed higher MRR@10 and Hit@1, while Fine-Tuned E5-small observed higher Recall@3; all paired 95% bootstrap confidence intervals include zero.
