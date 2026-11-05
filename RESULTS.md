# Experimental Results & Research Findings

This document provides the authoritative record of empirical findings, bootstrap confidence intervals, latency benchmarks, and methodological insights across all retrieval systems evaluated in the Soup RAG prototype.

---

## 1. Independent Human Evaluation Benchmark (`human_eval_v2`)

The primary standard for retrieval effectiveness is the independent evaluation benchmark (`data/human_eval/manifest_v2.json`), comprising **24 genuine queries** authored by Pernav and Harshit without AI assistance, evaluated across all 12 files (1,068 chunks) of the Soup documentation corpus (`data/corpus.jsonl`). Target documentation sections were supplied by the authors and mechanically mapped to canonical chunk IDs; no independent third-party relevance annotation was conducted, and the benchmark does not represent production telemetry or a sampled developer population.

### 1.1 Summary Benchmark Results (24 Human Queries, Full 1,068-Chunk Corpus)

| System | Architecture / Configuration | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Cold Start | Steady State (Warm) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hybrid RRF** | **Improved BM25 + Frozen E5-small ($k=60$)** | **0.6250** | 0.4923 | 0.5551 | **0.7254** | **0.6250** | **0.7292** | 36.0 s | 12.76 ms / query |
| **Frozen E5-small** | `intfloat/e5-small-v2` (frozen, 384d) | **0.6250** | 0.4562 | **0.5690** | 0.7101 | **0.6250** | 0.7240 | 35.9 s | 10.38 ms / query |
| **C-matched-bal** | MiniLM + Exp C balanced LoRA adapter | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 | 17.0 s | 6.67 ms / query |
| **Improved BM25** | Domain-aware tokenization ($k_1=1.5, b=0.75$) | **0.6250** | 0.4929 | 0.5150 | 0.6921 | **0.6250** | 0.6921 | **0.11 s** | **2.37 ms / query** |
| **Frozen MiniLM** | `sentence-transformers/all-MiniLM-L6-v2` | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 | 16.0 s | 6.23 ms / query |
| **Fine-Tuned E5** | E5-small + Exp B LoRA (matched lr=2e-5) | 0.5417 | **0.5177** | 0.5591 | 0.6413 | 0.5417 | 0.6448 | 36.4 s | 11.44 ms / query |
| **Original BM25** | Whitespace baseline (`text.lower().split()`, supplemental baseline) | 0.2917 | 0.3153 | 0.3688 | 0.4140 | 0.2917 | 0.4200 | **0.03 s** | **2.12 ms / query** |

### 1.2 Document-Stratified Performance (Seen Training vs Unseen Held-Out Documents)

In `data/document_split.json`, the 12 documentation files are partitioned into:
- **8 Training Documents (Seen during adapter training):** `README.md`, `backends-and-ops.md`, `commands.md`, `data.md`, `models.md`, `performance-and-quantization.md`, `serving-and-export.md`, `training.md`.
- **4 Held-Out Test Documents (Unseen):** `adapters-and-governance.md`, `compliance.md`, `evaluation.md`, `peft-and-efficiency.md`.

Authoritative chunk-level resolution (`resolve_document_attribution`) partitions the 24 human queries into **16 queries targeting training documents** and **8 queries targeting held-out documents**. Query `soup_human_004` originally cited `adapters-and-governance.md`, but its target section "Resume Training" is located in `backends-and-ops.md` (`backends-and-ops::resume-training`), placing it in the training document set.

| System | Evaluation Split | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Original BM25** | All Queries ($N=24$) | 0.2917 | 0.3153 | 0.3688 | 0.4140 | 0.2917 | 0.4200 |
| (whitespace baseline) | Training Documents ($N=16$) | 0.2500 | 0.2646 | 0.2824 | 0.3589 | 0.2500 | 0.3678 |
| | Held-Out Documents ($N=8$) | 0.3750 | 0.4167 | 0.5417 | 0.5243 | 0.3750 | 0.5243 |
| **Improved BM25** | All Queries ($N=24$) | 0.6250 | 0.4929 | 0.5150 | 0.6921 | 0.6250 | 0.6921 |
| (domain-aware) | Training Documents ($N=16$) | 0.6250 | 0.4476 | 0.4670 | 0.6632 | 0.6250 | 0.6632 |
| | Held-Out Documents ($N=8$) | 0.6250 | 0.5833 | 0.6111 | 0.7500 | 0.6250 | 0.7500 |
| **Frozen E5-small** | All Queries ($N=24$) | 0.6250 | 0.4562 | 0.5690 | 0.7101 | 0.6250 | 0.7240 |
| (pretrained, 384d) | Training Documents ($N=16$) | 0.6875 | 0.4238 | 0.5167 | 0.7417 | 0.6875 | 0.7562 |
| | Held-Out Documents ($N=8$) | 0.5000 | 0.5208 | 0.6736 | 0.6470 | 0.5000 | 0.6597 |
| **Fine-Tuned E5** | All Queries ($N=24$) | 0.5417 | 0.5177 | 0.5591 | 0.6413 | 0.5417 | 0.6448 |
| (lr=2e-5) | Training Documents ($N=16$) | 0.4375 | 0.4536 | 0.5018 | 0.5557 | 0.4375 | 0.5592 |
| | Held-Out Documents ($N=8$) | 0.7500 | 0.6458 | 0.6736 | 0.8125 | 0.7500 | 0.8160 |
| **Hybrid RRF** | All Queries ($N=24$) | 0.6250 | 0.4923 | 0.5551 | 0.7254 | 0.6250 | 0.7292 |
| (BM25 + Frozen E5) | Training Documents ($N=16$) | 0.5625 | 0.4467 | 0.5271 | 0.6756 | 0.5625 | 0.6813 |
| | Held-Out Documents ($N=8$) | 0.7500 | 0.5833 | 0.6111 | 0.8250 | 0.7500 | 0.8250 |
| **Frozen MiniLM** | All Queries ($N=24$) | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 |
| (pretrained, 256d) | Training Documents ($N=16$) | 0.4375 | 0.4789 | 0.4878 | 0.5885 | 0.4375 | 0.5938 |
| | Held-Out Documents ($N=8$) | 0.7500 | 0.5208 | 0.6736 | 0.7991 | 0.7500 | 0.7991 |
| **C-matched-bal** | All Queries ($N=24$) | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 |
| (MiniLM LoRA) | Training Documents ($N=16$) | 0.4375 | 0.4113 | 0.4113 | 0.5818 | 0.4375 | 0.5923 |
| | Held-Out Documents ($N=8$) | **0.8750** | **0.7083** | **0.7361** | **0.9375** | **0.8750** | **0.9375** |

> [!WARNING]
> **Sample Size Limitations on Held-Out Subset ($N=8$):**
> The held-out subset comprises only 8 queries (2 per held-out document). At this sample size, a single query ranking change swings Hit@1 by **12.5 percentage points**. While `C-matched-bal` observed high point estimates on these 8 queries (0.8750 Hit@1, 0.9375 MRR@10), this reflects an exploratory sample and does not establish statistically significant cross-document generalization—especially since on the 16 training document queries, `C-matched-bal` scored lower than Frozen E5 (0.5818 vs 0.7417 MRR@10).
>
> **Mixed-Query Sensitivity Analysis:**
> Query `soup_human_019` spans both `README` (train) and `evaluation` (held-out). Excluding `soup_human_019` leaves a pure training subset of $N=15$, on which `C-matched-bal` achieves Hit@1 0.4667 and MRR@10 0.6111, while Frozen E5 achieves Hit@1 0.7333 and MRR@10 0.7778, and Improved BM25 achieves Hit@1 0.6667 and MRR@10 0.7074.

### 1.3 Paired Document-Stratified Bootstrap Intervals (10,000 resamples, seed 42)

Reported as `observed delta [95% CI lower, 95% CI upper]` with document stratification across all 12 documentation files:

| Contrast | Metric | Observed Delta | 95% Bootstrap CI | Zero in CI? | Interpretation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Improved BM25 vs Original BM25** | MRR@10 | +0.2781 | `[+0.1685, +0.3912]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero; observed positive gain** |
| | Hit@1 | +0.3333 | `[+0.2083, +0.4583]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (+33.3% top-1 accuracy improvement)** |
| | Recall@3 | +0.1776 | `[+0.0734, +0.2956]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (improved top-3 recall)** |
| | Sec-MRR@10 | +0.2722 | `[+0.1603, +0.3873]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (section-level ranking gain)** |
| **Hybrid RRF vs Frozen E5** | MRR@10 | +0.0153 | `[-0.0687, +0.0996]` | Yes | Positive point estimate; interval includes zero on $N=24$; systems perform on par |
| | Recall@3 | +0.0361 | `[+0.0069, +0.0653]` | **NO** | **Paired 95% bootstrap CI excludes zero; driven by 3 queries; spans zero under multiplicity correction** |
| | Hit@1 | +0.0000 | `[-0.1250, +0.1250]` | Yes | Identical top-1 accuracy (15 of 24 queries correct) |
| | Sec-MRR@10 | +0.0052 | `[-0.0750, +0.0867]` | Yes | Marginal positive section-level delta |
| **Hybrid RRF vs Improved BM25** | MRR@10 | +0.0333 | `[-0.0427, +0.1060]` | Yes | Positive point estimate; interval includes zero on $N=24$ |
| | Hit@1 | +0.0000 | `[-0.1250, +0.1250]` | Yes | Identical top-1 accuracy |
| | Recall@5 | +0.0401 | `[-0.0224, +0.1050]` | Yes | Directional candidate coverage improvement |
| **Fine-Tuned E5 vs Frozen E5** | MRR@10 | -0.0688 | `[-0.1740, +0.0364]` | Yes | Interval includes zero on $N=24$; negative observed ranking delta |
| | Hit@1 | -0.0833 | `[-0.1667, +0.0000]` | Yes | Interval includes zero on $N=24$; observed reduction in top-1 matches |
| | Recall@3 | +0.0615 | `[-0.0565, +0.1796]` | Yes | Interval includes zero on $N=24$; positive observed top-3 recall delta |
| | Sec-MRR@10 | -0.0792 | `[-0.1806, +0.0232]` | Yes | Interval includes zero on $N=24$; negative observed section ranking delta |
| **C-matched-bal vs Frozen MiniLM** | MRR@10 | +0.0417 | `[-0.0382, +0.1215]` | Yes | Positive point estimate; interval includes zero on $N=24$ |
| | Hit@1 | +0.0417 | `[-0.0833, +0.1667]` | Yes | Positive point estimate; interval includes zero on $N=24$ |
| | Sec-MRR@10 | +0.0451 | `[-0.0347, +0.1225]` | Yes | Positive section-level trend |
| **Improved BM25 vs Frozen E5** | MRR@10 | -0.0180 | `[-0.1366, +0.1020]` | Yes | Interval includes zero; competitive with dense encoder at 4x lower query latency |
| | Hit@1 | +0.0000 | `[-0.1667, +0.1667]` | Yes | Exact tie on top-1 accuracy |
| | Recall@3 | +0.0367 | `[-0.0327, +0.1062]` | Yes | Comparable top-3 candidate coverage |

---

## 2. Answers to Core Research Questions

### 1. How does Hybrid RRF compare with Frozen E5?
**Hybrid RRF and Frozen E5 perform broadly on par across ranking metrics; the MRR@10 confidence interval includes zero.**
Hybrid RRF achieves an observed MRR@10 of **0.7254** vs **0.7101** for Frozen E5 (Observed Delta: **+0.0153**) and identical Hit@1 of **0.6250** (15 of 24 queries correct). The paired 95% bootstrap confidence interval for MRR@10 (`[-0.0687, +0.0996]`) includes zero. On Recall@3, Hybrid RRF achieves **0.4923** vs **0.4562** for Frozen E5 (+0.0361, paired 95% bootstrap CI `[+0.0069, +0.0653]`), though across all systems Fine-Tuned E5 reached 0.5177 and Improved BM25 reached 0.4929. The Recall@3 difference is driven by positive improvements on only 3 of 24 queries (21 queries have identical rank coverage) and does not survive multiple testing correction (Bonferroni-adjusted CI `[-0.0039, +0.0761]` spans zero). Claiming general statistical superiority is unsupported; the systems perform on par.

### 2. Does fine-tuning E5-small with matched lr=2e-5 improve over frozen E5-small on human queries?
**The paired 95% bootstrap confidence intervals include zero across all evaluated metrics, with lower observed ranking point estimates.**
Fine-Tuned E5-small (`lr=2e-5`) was evaluated against Frozen E5-small across the 24 human queries:
- **Frozen E5-small:** MRR@10 **0.7101**, Hit@1 **0.6250**, Recall@3 **0.4562**.
- **Fine-Tuned E5-small (lr=2e-5):** MRR@10 **0.6413**, Hit@1 **0.5417**, Recall@3 **0.5177**.

Frozen E5-small achieved higher observed MRR@10 (-0.0688 delta, 95% CI `[-0.1740, +0.0364]`) and Hit@1 (-0.0833 delta, 95% CI `[-0.1667, +0.0000]`), while Fine-Tuned E5-small achieved higher observed Recall@3 (+0.0615 delta, 95% CI `[-0.0565, +0.1796]`). All paired 95% bootstrap confidence intervals between them include zero. Fine-tuning on 2,475 synthetic triplets observed lower Hit@1 and lower MRR@10 while slightly broadening top-3 candidate recall.

### 3. Does the MiniLM adapter advantage over frozen MiniLM replicate on human queries?
**Positive observed overall point estimates, but within sampling uncertainty on $N=24$ with divergent behavior across document splits.**
`C-matched-balanced` achieved an overall observed MRR@10 of **0.7004** versus **0.6587** for Frozen MiniLM (+0.0417 delta) and Hit@1 of **0.5833** vs **0.5417** (+0.0417 delta). The paired 95% bootstrap confidence interval spans zero (`[-0.0382, +0.1215]`). Stratified analysis reveals divergent behavior: on the 16 training document queries, `C-matched-bal` scored lower than Frozen E5 (0.5818 vs 0.7417 MRR@10) and on par with Frozen MiniLM (0.5818 vs 0.5885 MRR@10). While `C-matched-bal` achieved high observed scores on the 8 held-out document queries (0.9375 MRR@10), the sample size of 8 queries (2 per document) is exploratory and insufficient to establish cross-document generalization.

### 4. How does BM25 perform on human queries compared to the baseline?
**Domain-aware BM25 substantially outperforms original whitespace BM25; paired 95% bootstrap confidence intervals strictly exclude zero across all metrics.**
The original whitespace BM25 baseline (`text.lower().split()`) was evaluated as an unmodified baseline to isolate tokenization effects over the identical frozen benchmark. It achieved an MRR@10 of **0.4140**, Hit@1 of **0.2917**, Recall@3 of **0.3153**, and Recall@5 of **0.3688** on the 24 technical queries. Improved domain-aware BM25 increased MRR@10 to **0.6921** (+0.2781 delta, 95% CI `[+0.1685, +0.3912]`), Hit@1 to **0.6250** (+0.3333 delta, 95% CI `[+0.2083, +0.4583]`), Recall@3 to **0.4929** (+0.1776 delta, 95% CI `[+0.0734, +0.2956]`), and Sec-MRR@10 to **0.6921** (+0.2722 delta, 95% CI `[+0.1603, +0.3873]`). The paired 95% bootstrap confidence interval strictly excludes zero across all metrics.

*Tokenizer Chronology Disclosure:* Whitespace BM25 represents the unmodified baseline. Domain-aware tokenization (`tokenize_domain_aware`) was developed concurrently during the 24-query benchmark freeze and historical query evaluation. The benchmark manifest records a freeze timestamp of `2026-11-05T08:19:07Z`, and the earliest Git commit containing `tokenize_domain_aware` (`c644f1c`) was committed 11 minutes 56 seconds later at `2026-11-05T08:31:03Z`. Git commit timestamps record when changes entered version control and do not establish when uncommitted local prototyping occurred. Domain-aware BM25 is therefore an evaluated retrieval enhancement rather than a pre-existing blind baseline.

*Reconciliation of Historical Results:* Both the 54 AI-assisted queries (`data/manual_queries.jsonl`) and the 24 human-authored queries (`data/human_eval/human_queries_v2.jsonl`) were evaluated against the identical 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`). On the 54 AI-assisted queries (which targeted sections within 4 held-out documents), canonical Phase 3 recorded Whitespace BM25 at **0.5953 MRR@10** (0.4815 Hit@1) and Improved BM25 at **0.7712 MRR@10** (0.6481 Hit@1). Previously cited figures of 0.5755 MRR@10 and 0.4630 Hit@1 were unverified draft narrative artifacts and are formally retracted.

### 5. What does the contrast between the AI-assisted (54 queries) and human-authored (24 queries) benchmarks indicate?
**Differences reflect differences in benchmark design, query formulation style, and relevance target distribution, while candidate retrieval operated over the identical 1,068-chunk corpus.**
Inspection of Phase 3 execution records (`results/phase3/experiment_summary.json`, `results/phase3/retriever_bm25.json`, `results/phase3/per_query_ranked_results.json`) confirms that both evaluations searched the full 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`, SHA256: `d787703e...`). The figure of 307 chunks reflects only the subset of chunks belonging to the 4 held-out target documents, not the search space. Chunks outside those 4 documents routinely appeared in Phase 3 candidate rankings.

Key Benchmark Contrasts:
1. **Benchmark Design & Query Provenance:** The 54 queries were collaboratively drafted with AI assistance, whereas the 24 queries in `human_eval_v2` were authored by Pernav and Harshit without AI assistance. Differences in observed scores reflect benchmark design and query formulation rather than query authorship alone.
2. **Target Document Distribution:** The 54 AI-assisted queries targeted sections located exclusively within 4 held-out documents (representing 307 chunks of the corpus), whereas the 24 human-authored queries target sections across all 12 documentation files.
3. **Exact Token Matching:** Authentic developer queries contain specific command flags, version numbers, and identifier strings (`--track-energy`, `check-safetensors`, `onebitllms`, `bitnet_1.58`, `pip install`, `OpenAPI`, `MCP`, `LISA`, `#353`), which domain-aware lexical tokenization indexes directly without semantic drift.
4. **Evaluation Provenance:** `human_eval_v2` is an independent evaluation on 24 queries authored by Pernav and Harshit without AI assistance where target sections were designated and mechanically mapped to canonical chunk IDs without third-party relevance annotation; it does not represent production user query logs or a statistically sampled developer population.

---

## 3. Reference: Historical Benchmark (54 AI-Assisted Queries Across 4 Held-Out Documents, Full 1,068-Chunk Corpus)

For historical continuity, the table below records performance on the original 54 AI-assisted queries across the 4 held-out documents (`adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`), evaluated against the full 1,068-chunk canonical corpus (values verified against canonical JSON outputs in `results/phase3/experiment_summary.json`):

| Model / System | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Benchmark Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Original BM25** (whitespace) | 0.4815 | 0.4497 | 0.5114 | 0.5953 | 0.4815 | 0.6127 | Baseline (canonical Phase 3) |
| **Improved BM25** (domain-aware) | 0.6481 | 0.7065 | 0.7719 | 0.7712 | 0.6852 | 0.7897 | Tokenizer evaluation |
| **Frozen MiniLM** | 0.5741 | 0.5753 | 0.6895 | 0.6928 | 0.6296 | 0.7257 | Pinned control baseline |
| **Adapter A-matched** (MiniLM) | 0.5185 | 0.5228 | 0.6438 | 0.6554 | 0.5741 | 0.6957 | Degraded heuristic adapter |
| **Adapter B** (MiniLM) | 0.6481 | 0.6015 | 0.6552 | 0.7434 | 0.6667 | 0.7546 | Observed gain over A-matched |
| **Adapter C-matched-bal** (MiniLM) | 0.6852 | 0.5722 | 0.6599 | 0.7681 | 0.7037 | 0.7793 | Highest candidate adapter on 54q |
| **Frozen E5-small** | 0.6852 | 0.6694 | 0.7302 | 0.7834 | 0.7222 | 0.8165 | Strongest single dense retriever |
| **Fine-Tuned E5** (lr=2e-5) | 0.5000 | 0.5506 | 0.6444 | 0.6458 | 0.5741 | 0.7087 | Regression vs frozen E5 (-0.1376 MRR) |
| **Fine-Tuned E5** (lr=2e-4) | 0.3148 | 0.3210 | 0.3210 | 0.3530 | 0.3333 | 0.3725 | Severe collapse from overshooting |
| **Hybrid RRF** (BM25 + Frozen E5) | **0.7778** | **0.7466** | **0.8228** | **0.8552** | **0.8148** | **0.8771** | **Highest benchmark score** |

> [!NOTE]
> **Canonical Metrics Reconciliation:** The MiniLM family metrics above are transcribed directly from canonical Phase 3 JSON outputs (`results/phase3/experiment_summary.json`). Previously reported draft values in commit `23f198e0` (e.g. C-matched-balanced Hit@1 0.6667, Recall@3 0.6898, Sec-Hit@1 0.7407; Frozen MiniLM Recall@3 0.5898; Adapter B Recall@3 0.6312) were transcription errors from early draft working notes and are formally corrected here.

---

## 4. Latency & Resource Profile

Measured on Apple Silicon (warm steady-state vs cold start):

| Component | Model Loading | Corpus Indexing | Steady-State Query (Mean) | Steady-State Query (P95) | Operational Footprint |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Original BM25** | $<0.01$ ms | 31.3 ms | **2.12 ms** | **2.72 ms** | Whitespace supplemental baseline; zero GPU/torch |
| **Improved BM25** | $<0.01$ ms | 107.0 ms | **2.37 ms** | **4.21 ms** | Zero GPU/torch dependency; CPU only |
| **Frozen MiniLM** | $<0.01$ ms | 15,979 ms | **6.23 ms** | **7.15 ms** | 22M parameters, 256 dimensions |
| **C-matched-bal** | $<0.01$ ms | 16,953 ms | **6.67 ms** | **8.05 ms** | MiniLM + LoRA adapter weights |
| **Frozen E5-small** | $<0.01$ ms | 35,872 ms | **10.38 ms** | **11.98 ms** | 33M parameters, 384 dimensions |
| **Fine-Tuned E5** | $<0.01$ ms | 36,355 ms | **11.44 ms** | **14.12 ms** | E5-small + LoRA adapter weights |
| **Hybrid RRF** | $<0.02$ ms | 35,979 ms | **12.76 ms** | **16.20 ms** | BM25 + Frozen E5 + RRF ($k=60$) |

> [!NOTE]
> **Observed Latency Trade-offs:** All latency numbers reported above are prototype measurements on Apple Silicon with preloaded corpus embeddings, not production deployment measurements. Improved BM25 achieves a **107 ms** cold start and **2.37 ms** warm retrieval, matching Frozen E5 top-1 hit accuracy (0.6250). Hybrid RRF achieves **12.76 ms** warm retrieval and the highest observed MRR@10 (**0.7254**). While BM25 is the fastest single retriever and Hybrid RRF achieves the highest observed MRR@10 on this benchmark, these measurements reflect prototype code running on local hardware and do not constitute production SLAs.

