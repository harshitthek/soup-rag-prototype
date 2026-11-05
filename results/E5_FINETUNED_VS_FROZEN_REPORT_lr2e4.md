# E5-Small Fine-Tuning Evaluation: Frozen vs LoRA Fine-Tuned (e5_small_ft_lr2e4)

## Executive Summary & Core Empirical Finding

This evaluation directly benchmarks **Frozen E5-small** (`intfloat/e5-small-v2`) against **Fine-Tuned E5-small** (`e5_small_ft_lr2e4`, trained via Soup's native embedding trainer using 2,475 triplets, 1,857 updates, rank 16, triplet margin 0.5, mean pooling).

### Primary Result:
- **Fine-Tuning Did NOT Improve Over Frozen E5-small on the Benchmark:**
  - Frozen E5-small MRR@10: **0.7834**
  - Fine-Tuned E5-small MRR@10: **0.3530** (Observed Delta: **-0.4304**)
  - 95% Paired Document-Stratified Bootstrap CI: `[-0.5582, -0.3041]` (Strictly negative, excludes zero).
- **Observation:** Out of 54 benchmark queries, **4 queries improved**, while **34 queries degraded**, and **16 remained unchanged**.
- **Scientific Conclusion:** Fine-tuning an already strong pre-trained encoder (E5-small) with 2,475 domain triplets on hard negatives mined by MiniLM failed to produce a measurable retrieval improvement over the out-of-the-box frozen checkpoint. In technical documentation retrieval, frozen pre-trained representations provide high general semantic capabilities, and small-scale LoRA fine-tuning risks representation degradation or catastrophic forgetting on unrepresented query patterns.

---

## 1. Full Metric Comparison & Bootstrap Confidence Intervals

10,000 paired document-stratified bootstrap resamples with seed 42 across the 4 evaluation documents (canonical distribution: 16, 8, 17, 13 queries):

| Metric | Frozen E5-small (Control) | Fine-Tuned E5-small (Treatment) | Observed Delta | 95% Bootstrap Interval | Zero Included? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hit@1** | 0.6852 | 0.3148 | -0.3704 | `[-0.5185, -0.2222]` | NO (Strictly excludes zero) |
| **Recall@1** | 0.4188 | 0.1944 | -0.2244 | `[-0.3299, -0.1210]` | NO (Strictly excludes zero) |
| **Hit@3** | 0.8704 | 0.3704 | -0.5000 | `[-0.6296, -0.3704]` | NO (Strictly excludes zero) |
| **Recall@3** | 0.6694 | 0.2491 | -0.4204 | `[-0.5272, -0.3139]` | NO (Strictly excludes zero) |
| **Hit@5** | 0.8704 | 0.4074 | -0.4630 | `[-0.5926, -0.3333]` | NO (Strictly excludes zero) |
| **Recall@5** | 0.7302 | 0.3207 | -0.4096 | `[-0.5321, -0.2867]` | NO (Strictly excludes zero) |
| **MRR@10** | 0.7834 | 0.3530 | -0.4304 | `[-0.5582, -0.3041]` | NO (Strictly excludes zero) |
| **Sec-Hit@1** | 0.7222 | 0.3333 | -0.3889 | `[-0.5370, -0.2407]` | NO (Strictly excludes zero) |
| **Sec-MRR@10** | 0.8165 | 0.3904 | -0.4261 | `[-0.5460, -0.3084]` | NO (Strictly excludes zero) |

---

## 2. Canonical Per-Document Breakdown

| Document | Queries | Frozen Hit@1 | FT Hit@1 | Frozen Recall@3 | FT Recall@3 | Frozen MRR@10 | FT MRR@10 | MRR Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `adapters-and-governance.md` | 16 | 0.5000 | 0.2500 | 0.5312 | 0.2500 | 0.6507 | 0.2969 | -0.3538 |
| `compliance.md` | 8 | 0.7500 | 0.1250 | 0.6875 | 0.0625 | 0.8281 | 0.1250 | -0.7031 |
| `evaluation.md` | 17 | 0.7647 | 0.4118 | 0.7157 | 0.2892 | 0.8431 | 0.4412 | -0.4020 |
| `peft-and-efficiency.md` | 13 | 0.7692 | 0.3846 | 0.7679 | 0.3103 | 0.8410 | 0.4470 | -0.3940 |

---

## 3. Failure Category Distribution

| Failure Category | Frozen E5-small | Fine-Tuned E5-small | Delta |
| :--- | :---: | :---: | :---: |
| `exact_relevant_chunk_top1` | 37 | 17 | -20 |
| `relevant_chunk_below_top1` | 13 | 6 | -7 |
| `relevant_section_below_top1` | 1 | 1 | +0 |
| `relevant_section_unlabeled_chunk_top1` | 2 | 1 | -1 |
| `wrong_document` | 1 | 22 | +21 |
| `wrong_section_same_document` | 0 | 7 | +7 |

---

## 4. Disaggregated Query Transitions

- **Improved Queries (4):**
  - `manual_010` (adapters-and-governance): "soup registry diff output" (MRR: 0.5000 → 1.0000, Δ=+0.5000)
  - `manual_038` (evaluation): "custom eval jsonl fields for exact and regex scoring" (MRR: 0.5000 → 1.0000, Δ=+0.5000)
  - `manual_042` (peft-and-efficiency): "preview which decoder layers soup shrink will drop" (MRR: 0.3333 → 1.0000, Δ=+0.6667)
  - `manual_047` (peft-and-efficiency): "different learning rates for q_proj and v_proj" (MRR: 0.1000 → 0.2000, Δ=+0.1000)

- **Degraded Queries (34):**
  - `manual_001` (adapters-and-governance): "why does soup lock check exit with code 3" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_002` (adapters-and-governance): "How do I bisect training checkpoints when an eval regresses?" (MRR: 0.1429 → 0.0000, Δ=-0.1429)
  - `manual_004` (adapters-and-governance): "what does soup loop automate" (MRR: 0.1429 → 0.0000, Δ=-0.1429)
  - `manual_005` (adapters-and-governance): "does soup roll back a canary automatically if the eval regresses" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_007` (adapters-and-governance): "compare model answers before and after a knowledge edit" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_008` (adapters-and-governance): "build a control vector from positive and negative prompts" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_009` (adapters-and-governance): "grace codebook size limit" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_012` (adapters-and-governance): "how do signed attestations get embedded in a soup can" (MRR: 1.0000 → 0.2500, Δ=-0.7500)
  - `manual_013` (adapters-and-governance): "can I merge adapters whose licenses conflict" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_014` (adapters-and-governance): "what stops a hijacked huggingface repo from being pulled" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_016` (adapters-and-governance): "Soup refuses to load a .bin adapter, what formats are allowed?" (MRR: 0.1250 → 0.0000, Δ=-0.1250)
  - `manual_017` (compliance): "which soup init templates exist for regulated industries" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_018` (compliance): "clean emails and phone numbers out of my training data" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_020` (compliance): "what ends up in the generated model card" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_021` (compliance): "publish a model to huggingface with my own model card" (MRR: 0.1250 → 0.0000, Δ=-0.1250)
  - `manual_022` (compliance): "generated ci workflow steps" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_023` (compliance): "which expectation checks can go in expectations.yaml" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_024` (compliance): "what steps does soup's compliance workflow cover" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_025` (evaluation): "Should I fine-tune with DPO or SFT for my dataset?" (MRR: 0.3333 → 0.0000, Δ=-0.3333)
  - `manual_026` (evaluation): "generate an eval suite from my training data" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_027` (evaluation): "do two eval designs with the same content hash the same" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_028` (evaluation): "block a git push when eval accuracy regresses" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_029` (evaluation): "eval_gate block settings in soup.yaml" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_030` (evaluation): "how does soup ab decide when to stop collecting samples" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_033` (evaluation): "Task accuracy went up but MMLU dropped, should I ship?" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_035` (evaluation): "how do I make a ship verdict replayable in CI" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_036` (evaluation): "score BLEU and ROUGE on custom eval outputs" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_043` (peft-and-efficiency): "how does longlora shifted sparse attention work" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_044` (peft-and-efficiency): "difference between multipack and packing" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_045` (peft-and-efficiency): "set up yarn for 4x context extension" (MRR: 1.0000 → 0.0000, Δ=-1.0000)
  - `manual_046` (peft-and-efficiency): "Can I add fresh layers to a Llama model and only train those?" (MRR: 1.0000 → 0.5000, Δ=-0.5000)
  - `manual_050` (peft-and-efficiency): "can dora and vera be enabled together" (MRR: 0.5000 → 0.0000, Δ=-0.5000)
  - `manual_052` (peft-and-efficiency): "does lisa actually use less memory than lora" (MRR: 1.0000 → 0.1111, Δ=-0.8889)
  - `manual_054` (peft-and-efficiency): "Can GaLore run with quantized weights?" (MRR: 1.0000 → 0.0000, Δ=-1.0000)

---

## 5. Latency & Resource Profile

Benchmarked on Apple Silicon (M-series CPU):

### 5.1 Cold-Start Overhead
- **Model & LoRA Adapter Loading:** 0.000s
- **Corpus Pre-Encoding (1,068 chunks):** 13.918s
- **Total Cold Start:** **13.918s**

### 5.2 Steady-State Online Serving (In-Memory Pre-Loaded)
- **Query Neural Encoding:** 1.53 ms / query
- **Matrix Search (Dot Product):** 0.080 ms / query
- **Total Steady-State Latency:** **1.61 ms / query**

---

## 6. Methodological Limitations & Confounders

1. **Hard Negatives Mined with MiniLM:** The Experiment B hard negatives were mined using frozen MiniLM embeddings. While this provides a strictly controlled comparison across training datasets, those negative passages may not correspond to the most informative contrastive negatives for E5's representation space.
2. **Exploratory Benchmark Context:** As documented in the research integrity protocol, the 54 queries in `data/manual_queries.jsonl` were drafted with AI assistance, and candidate relevance annotation provenance is undocumented. Therefore, neither frozen nor fine-tuned E5 results should be treated as population-level truths.
3. **Pending Ground-Truth Human Queries:** Evaluation on the 12 project-owner-authored queries (`data/human_eval/human_queries_v1.jsonl`) remains pending manual relevance annotation to prevent circularity and bias.
