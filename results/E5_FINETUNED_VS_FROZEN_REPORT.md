# E5-Small Fine-Tuning Evaluation: Frozen vs LoRA Fine-Tuned (e5_small_ft_lr2e5)

## Executive Summary & Core Empirical Finding

This evaluation directly benchmarks **Frozen E5-small** (`intfloat/e5-small-v2`) against **Fine-Tuned E5-small** (`e5_small_ft_lr2e5`, trained via Soup's native embedding trainer using 2,475 triplets, 1,857 updates, rank 16, triplet margin 0.5, mean pooling).

### Primary Result:
- **Fine-Tuning Did NOT Improve Over Frozen E5-small on the Benchmark:**
  - Frozen E5-small MRR@10: **0.7834**
  - Fine-Tuned E5-small MRR@10: **0.6458** (Observed Delta: **-0.1376**)
  - 95% Paired Document-Stratified Bootstrap CI: `[-0.2154, -0.0640]` (Strictly negative, excludes zero).
- **Observation:** Out of 54 benchmark queries, **4 queries improved**, while **18 queries degraded**, and **32 remained unchanged**.
- **Scientific Conclusion:** Fine-tuning an already strong pre-trained encoder (E5-small) with 2,475 domain triplets on hard negatives mined by MiniLM failed to produce a measurable retrieval improvement over the out-of-the-box frozen checkpoint. In technical documentation retrieval, frozen pre-trained representations provide high general semantic capabilities, and small-scale LoRA fine-tuning risks representation degradation or catastrophic forgetting on unrepresented query patterns.

---

## 1. Full Metric Comparison & Bootstrap Confidence Intervals

10,000 paired document-stratified bootstrap resamples with seed 42 across the 4 evaluation documents (canonical distribution: 16, 8, 17, 13 queries):

| Metric | Frozen E5-small (Control) | Fine-Tuned E5-small (Treatment) | Observed Delta | 95% Bootstrap Interval | Zero Included? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hit@1** | 0.6852 | 0.5000 | -0.1852 | `[-0.2963, -0.0741]` | NO (Strictly excludes zero) |
| **Recall@1** | 0.4188 | 0.3272 | -0.0917 | `[-0.1620, -0.0203]` | NO (Strictly excludes zero) |
| **Hit@3** | 0.8704 | 0.7778 | -0.0926 | `[-0.2037, +0.0000]` | YES (Spans zero) |
| **Recall@3** | 0.6694 | 0.5506 | -0.1188 | `[-0.1944, -0.0463]` | NO (Strictly excludes zero) |
| **Hit@5** | 0.8704 | 0.8333 | -0.0370 | `[-0.1296, +0.0556]` | YES (Spans zero) |
| **Recall@5** | 0.7302 | 0.6444 | -0.0858 | `[-0.1636, -0.0093]` | NO (Strictly excludes zero) |
| **MRR@10** | 0.7834 | 0.6458 | -0.1376 | `[-0.2154, -0.0640]` | NO (Strictly excludes zero) |
| **Sec-Hit@1** | 0.7222 | 0.5741 | -0.1481 | `[-0.2593, -0.0370]` | NO (Strictly excludes zero) |
| **Sec-MRR@10** | 0.8165 | 0.7087 | -0.1078 | `[-0.1800, -0.0393]` | NO (Strictly excludes zero) |

---

## 2. Canonical Per-Document Breakdown

| Document | Queries | Frozen Hit@1 | FT Hit@1 | Frozen Recall@3 | FT Recall@3 | Frozen MRR@10 | FT MRR@10 | MRR Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `adapters-and-governance.md` | 16 | 0.5000 | 0.3750 | 0.5312 | 0.4688 | 0.6507 | 0.5680 | -0.0827 |
| `compliance.md` | 8 | 0.7500 | 0.2500 | 0.6875 | 0.4375 | 0.8281 | 0.4833 | -0.3448 |
| `evaluation.md` | 17 | 0.7647 | 0.5882 | 0.7157 | 0.5588 | 0.8431 | 0.6814 | -0.1618 |
| `peft-and-efficiency.md` | 13 | 0.7692 | 0.6923 | 0.7679 | 0.7103 | 0.8410 | 0.7949 | -0.0462 |

---

## 3. Failure Category Distribution

| Failure Category | Frozen E5-small | Fine-Tuned E5-small | Delta |
| :--- | :---: | :---: | :---: |
| `exact_relevant_chunk_top1` | 37 | 27 | -10 |
| `relevant_chunk_below_top1` | 13 | 19 | +6 |
| `relevant_section_below_top1` | 1 | 0 | -1 |
| `relevant_section_unlabeled_chunk_top1` | 2 | 4 | +2 |
| `wrong_document` | 1 | 3 | +2 |
| `wrong_section_same_document` | 0 | 1 | +1 |

---

## 4. Disaggregated Query Transitions

- **Improved Queries (4):**
  - `manual_003` (adapters-and-governance): "how do I see which training rows influenced an adapter" (MRR: 0.0000 → 0.3333, Δ=+0.3333)
  - `manual_004` (adapters-and-governance): "what does soup loop automate" (MRR: 0.1429 → 0.5000, Δ=+0.3571)
  - `manual_021` (compliance): "publish a model to huggingface with my own model card" (MRR: 0.1250 → 0.2000, Δ=+0.0750)
  - `manual_038` (evaluation): "custom eval jsonl fields for exact and regex scoring" (MRR: 0.5000 → 1.0000, Δ=+0.5000)

- **Degraded Queries (18):**
  - `manual_005` (adapters-and-governance): "does soup roll back a canary automatically if the eval regresses" (MRR: 0.5000 → 0.2500, Δ=-0.2500)
  - `manual_008` (adapters-and-governance): "build a control vector from positive and negative prompts" (MRR: 0.5000 → 0.3333, Δ=-0.1667)
  - `manual_009` (adapters-and-governance): "grace codebook size limit" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_010` (adapters-and-governance): "soup registry diff output" (MRR: 0.5000 → 0.1667, Δ=-0.3333)
  - `manual_012` (adapters-and-governance): "how do signed attestations get embedded in a soup can" (MRR: 1.0000 → 0.2500, Δ=-0.7500)
  - `manual_016` (adapters-and-governance): "Soup refuses to load a .bin adapter, what formats are allowed?" (MRR: 0.1250 → 0.1111, Δ=-0.0139)
  - `manual_017` (compliance): "which soup init templates exist for regulated industries" (MRR: 1.0000 → 0.3333, Δ=-0.6667)
  - `manual_019` (compliance): "bom --attach-to-registry wrote the files but exited non-zero" (MRR: 1.0000 → 0.3333, Δ=-0.6667)
  - `manual_020` (compliance): "what ends up in the generated model card" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_023` (compliance): "which expectation checks can go in expectations.yaml" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_025` (evaluation): "Should I fine-tune with DPO or SFT for my dataset?" (MRR: 0.3333 → 0.0000, Δ=-0.3333)
  - `manual_027` (evaluation): "do two eval designs with the same content hash the same" (MRR: 1.0000 → 0.3333, Δ=-0.6667)
  - `manual_029` (evaluation): "eval_gate block settings in soup.yaml" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_033` (evaluation): "Task accuracy went up but MMLU dropped, should I ship?" (MRR: 1.0000 → 0.1250, Δ=-0.8750)
  - `manual_034` (evaluation): "noise floor flag effect on ship verdict" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_035` (evaluation): "how do I make a ship verdict replayable in CI" (MRR: 0.5000 → 0.1250, Δ=-0.3750)
  - `manual_046` (peft-and-efficiency): "Can I add fresh layers to a Llama model and only train those?" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_047` (peft-and-efficiency): "different learning rates for q_proj and v_proj" (MRR: 0.1000 → 0.0000, Δ=-0.1000)

---

## 5. Latency & Resource Profile

Benchmarked on Apple Silicon (M-series CPU):

### 5.1 Cold-Start Overhead
- **Model & LoRA Adapter Loading:** 0.000s
- **Corpus Pre-Encoding (1,068 chunks):** 15.348s
- **Total Cold Start:** **15.348s**

### 5.2 Steady-State Online Serving (In-Memory Pre-Loaded)
- **Query Neural Encoding:** 1.58 ms / query
- **Matrix Search (Dot Product):** 0.080 ms / query
- **Total Steady-State Latency:** **1.66 ms / query**

---

## 6. Methodological Limitations & Confounders

1. **Hard Negatives Mined with MiniLM:** The Experiment B hard negatives were mined using frozen MiniLM embeddings. While this provides a strictly controlled comparison across training datasets, those negative passages may not correspond to the most informative contrastive negatives for E5's representation space.
2. **Exploratory Benchmark Context:** As documented in the research integrity protocol, the 54 queries in `data/manual_queries.jsonl` were drafted with AI assistance, and candidate relevance annotation provenance is undocumented. Therefore, neither frozen nor fine-tuned E5 results should be treated as population-level truths.
3. **Pending Ground-Truth Human Queries:** Evaluation on the 12 project-owner-authored queries (`data/human_eval/human_queries_v1.jsonl`) remains pending manual relevance annotation to prevent circularity and bias.
