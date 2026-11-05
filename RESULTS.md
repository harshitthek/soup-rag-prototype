# Experimental Results & Research Findings

This document provides the authoritative record of empirical findings, bootstrap confidence intervals, latency benchmarks, and methodological insights across all retrieval systems evaluated in the Soup RAG prototype.

---

## 1. Independent Owner-Authored Evaluation Benchmark (`human_eval_v2`)

The primary standard for retrieval effectiveness is the independent owner-authored evaluation benchmark (`data/human_eval/manifest_v2.json`), comprising **24 genuine queries** authored directly by the project owner without AI assistance, evaluated across all 12 files (1,068 chunks) of the Soup documentation corpus (`data/corpus.jsonl`). Target documentation sections were supplied directly by the project owner and mechanically mapped to canonical chunk IDs; no independent third-party relevance annotation was conducted, and the benchmark does not represent production telemetry or a sampled developer population.

### 1.1 Benchmark Results (24 Human Queries, Full 1,068-Chunk Corpus)

| System | Architecture / Configuration | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Cold Start | Steady State (Warm) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hybrid RRF** | **Improved BM25 + Frozen E5-small ($k=60$)** | **0.6250** | 0.4923 | 0.5551 | **0.7254** | **0.6250** | **0.7292** | 36.0 s | 12.76 ms / query |
| **Frozen E5-small** | `intfloat/e5-small-v2` (frozen, 384d) | **0.6250** | 0.4562 | **0.5690** | 0.7101 | **0.6250** | 0.7240 | 35.9 s | 10.38 ms / query |
| **C-matched-bal** | MiniLM + Exp C balanced LoRA adapter | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 | 17.0 s | 6.67 ms / query |
| **Improved BM25** | Domain-aware tokenization ($k_1=1.5, b=0.75$) | **0.6250** | 0.4929 | 0.5150 | 0.6921 | **0.6250** | 0.6921 | **0.11 s** | **2.37 ms / query** |
| **Frozen MiniLM** | `sentence-transformers/all-MiniLM-L6-v2` | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 | 16.0 s | 6.23 ms / query |
| **Fine-Tuned E5** | E5-small + Exp B LoRA (matched lr=2e-5) | 0.5417 | **0.5177** | 0.5591 | 0.6413 | 0.5417 | 0.6448 | 36.4 s | 11.44 ms / query |
| **Original BM25** | Whitespace baseline (`text.lower().split()`, supplemental baseline) | 0.2917 | 0.3153 | 0.3688 | 0.4140 | 0.2917 | 0.4200 | **0.03 s** | **2.12 ms / query** |

### 1.2 Paired Document-Stratified Bootstrap Intervals (10,000 resamples, seed 42)

Reported as `observed delta [95% CI lower, 95% CI upper]` with document stratification across all 12 documentation files:

| Contrast | Metric | Observed Delta | 95% Bootstrap CI | Zero in CI? | Interpretation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Improved BM25 vs Original BM25** | MRR@10 | +0.2781 | `[+0.1685, +0.3912]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero; observed positive gain** |
| | Hit@1 | +0.3333 | `[+0.2083, +0.4583]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (+33.3% top-1 accuracy improvement)** |
| | Recall@3 | +0.1776 | `[+0.0734, +0.2956]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (improved top-3 recall)** |
| | Sec-MRR@10 | +0.2722 | `[+0.1603, +0.3873]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero (section-level ranking gain)** |
| **Hybrid RRF vs Frozen E5** | MRR@10 | +0.0153 | `[-0.0687, +0.0996]` | Yes | Positive point estimate; interval includes zero on $N=24$ |
| | Recall@3 | +0.0361 | `[+0.0069, +0.0653]` | **NO** | **Paired 95% bootstrap CI strictly excludes zero** |
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
**Hybrid RRF achieves higher observed MRR@10 and improves Recall@3 over Frozen E5, while the MRR@10 confidence interval includes zero.**
Hybrid RRF achieves the highest observed MRR@10 (**0.7254** vs 0.7101 for Frozen E5 and 0.6921 for Improved BM25) and Sec-MRR@10 (**0.7292** vs 0.7240). On Recall@3, Hybrid RRF improves candidate coverage over Frozen E5 (**0.4923** vs **0.4562**); the paired 95% bootstrap confidence interval excludes zero (+0.0361, 95% bootstrap CI `[+0.0069, +0.0653]`). However, Hybrid RRF does not have the highest Recall@3 across all evaluated systems: Fine-Tuned E5 achieves **0.5177** and Improved BM25 achieves **0.4929**. The paired 95% bootstrap confidence interval for the MRR@10 difference includes zero (`[-0.0687, +0.0996]`).

### 2. Does fine-tuning E5-small with matched lr=2e-5 improve over frozen E5-small on human queries?
**The paired 95% bootstrap confidence intervals include zero across all evaluated metrics, with lower observed ranking point estimates.**
Fine-Tuned E5-small (`lr=2e-5`) observed lower point estimates on ranking metrics: MRR@10 declined from **0.7101 to 0.6413** (-0.0688 delta, 95% CI `[-0.1740, +0.0364]`), Hit@1 fell from **0.6250 to 0.5417** (-0.0833 delta, 95% CI `[-0.1667, +0.0000]`), and Sec-MRR@10 fell from **0.7240 to 0.6448** (-0.0792 delta, 95% CI `[-0.1806, +0.0232]`). However, the adapter was not strictly inferior across all metrics: observed Recall@3 was higher for the fine-tuned adapter (**0.5177** vs **0.4562**, +0.0615 delta, 95% CI `[-0.0565, +0.1796]`). The paired 95% bootstrap confidence interval includes zero for every evaluated metric. Directionally, fine-tuning on synthetic triplets observed lower Hit@1 (0.5417 vs 0.6250) and lower MRR@10 (0.6413 vs 0.7101), while Frozen E5-small remains the more reliable out-of-the-box choice.

### 3. Does the MiniLM adapter advantage over frozen MiniLM replicate on human queries?
**Positive observed point estimates, with confidence intervals including zero.**
`C-matched-balanced` achieved an observed MRR@10 of **0.7004** versus **0.6587** for Frozen MiniLM (+0.0417 delta) and Hit@1 of **0.5833** vs **0.5417** (+0.0417 delta). While the observed direction matches earlier findings, the paired 95% bootstrap confidence interval includes zero (`[-0.0382, +0.1215]`).

### 4. How does BM25 perform on human queries compared to the baseline?
**Domain-aware BM25 substantially outperforms original whitespace BM25; paired 95% bootstrap confidence intervals strictly exclude zero across all metrics.**
The original whitespace BM25 baseline (`text.lower().split()`) was evaluated as a supplemental baseline during corrective research audit to isolate tokenization effects over the identical frozen benchmark. It achieved an MRR@10 of **0.4140**, Hit@1 of **0.2917**, Recall@3 of **0.3153**, and Recall@5 of **0.3688** on the 24 technical queries. Improved domain-aware BM25 increased MRR@10 to **0.6921** (+0.2781 delta, 95% CI `[+0.1685, +0.3912]`), Hit@1 to **0.6250** (+0.3333 delta, 95% CI `[+0.2083, +0.4583]`), Recall@3 to **0.4929** (+0.1776 delta, 95% CI `[+0.0734, +0.2956]`), and Sec-MRR@10 to **0.6921** (+0.2722 delta, 95% CI `[+0.1603, +0.3873]`). The paired 95% bootstrap confidence interval strictly excludes zero across all metrics.

*Reconciliation of Historical Results:* Both the 54 AI-assisted queries (`data/manual_queries.jsonl`) and the 24 owner-authored queries (`data/human_eval/human_queries_v2.jsonl`) were evaluated against the identical 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`). On the 54 AI-assisted queries (which targeted sections within 4 held-out documents), canonical Phase 3 recorded Whitespace BM25 at **0.5953 MRR@10** (0.4815 Hit@1) and Improved BM25 at **0.7712 MRR@10** (0.6481 Hit@1). Previously cited figures of 0.5755 MRR@10 and 0.4630 Hit@1 were unverified draft narrative artifacts and are formally retracted.

### 5. What does the contrast between the AI-assisted (54 queries) and owner-authored (24 queries) benchmarks indicate?
**Differences reflect differences in benchmark design, query formulation style, and relevance target distribution, while candidate retrieval operated over the identical 1,068-chunk corpus.**
Inspection of Phase 3 execution records (`results/phase3/experiment_summary.json`, `results/phase3/retriever_bm25.json`, `results/phase3/per_query_ranked_results.json`) confirms that both evaluations searched the full 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`, SHA256: `d787703e...`). The figure of 307 chunks reflects only the subset of chunks belonging to the 4 held-out target documents, not the search space. Chunks outside those 4 documents routinely appeared in Phase 3 candidate rankings.

Key Benchmark Contrasts:
1. **Benchmark Design & Query Provenance:** The 54 queries were collaboratively drafted with AI assistance, whereas the 24 queries in `human_eval_v2` were authored directly by the project owner without AI assistance. Differences in observed scores reflect benchmark design and query formulation rather than query authorship alone.
2. **Target Document Distribution:** The 54 AI-assisted queries targeted sections located exclusively within 4 held-out documents (representing 307 chunks of the corpus), whereas the 24 owner-authored queries target sections across all 12 documentation files.
3. **Exact Token Matching:** Authentic developer queries contain specific command flags, version numbers, and identifier strings (`--track-energy`, `check-safetensors`, `onebitllms`, `bitnet_1.58`, `pip install`, `OpenAPI`, `MCP`, `LISA`, `#353`), which domain-aware lexical tokenization indexes directly without semantic drift.
4. **Evaluation Provenance:** `human_eval_v2` is an independent owner-authored query evaluation where target sections were identified by the owner and mechanically mapped to canonical chunk IDs without third-party relevance annotation; it does not represent production user query logs or a statistically sampled developer population.

---

## 3. Reference: Historical Benchmark (54 AI-Assisted Queries Across 4 Held-Out Documents, Full 1,068-Chunk Corpus)

For historical continuity, the table below records performance on the original 54 AI-assisted queries across the 4 held-out documents (`adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`), evaluated against the full 1,068-chunk canonical corpus:

| Model / System | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Benchmark Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Original BM25** (whitespace) | 0.4815 | 0.4497 | 0.5114 | 0.5953 | 0.4815 | 0.6127 | Baseline (canonical Phase 3) |
| **Improved BM25** (domain-aware) | 0.6481 | 0.7065 | 0.7719 | 0.7712 | 0.6852 | 0.7897 | Tokenizer evaluation |
| **Frozen MiniLM** | 0.5741 | 0.5898 | 0.6389 | 0.6928 | 0.6296 | 0.7301 | Pinned control baseline |
| **Adapter A-matched** (MiniLM) | 0.5185 | 0.5525 | 0.6358 | 0.6554 | 0.5926 | 0.7107 | Degraded heuristic adapter |
| **Adapter B** (MiniLM) | 0.6481 | 0.6312 | 0.7130 | 0.7434 | 0.7037 | 0.7831 | Observed gain over A-matched |
| **Adapter C-matched-bal** (MiniLM) | 0.6667 | 0.6898 | 0.7407 | 0.7681 | 0.7407 | 0.8148 | Highest candidate adapter on 54q |
| **Frozen E5-small** | 0.6852 | 0.6694 | 0.7302 | 0.7834 | 0.7222 | 0.8165 | Strongest single dense retriever |
| **Fine-Tuned E5** (lr=2e-5) | 0.5000 | 0.5506 | 0.6444 | 0.6458 | 0.5741 | 0.7087 | Regression vs frozen E5 (-0.1376 MRR) |
| **Fine-Tuned E5** (lr=2e-4) | 0.3148 | 0.3210 | 0.3210 | 0.3530 | 0.3333 | 0.3725 | Severe collapse from overshooting |
| **Hybrid RRF** (BM25 + Frozen E5) | **0.7778** | **0.7466** | **0.8228** | **0.8552** | **0.8148** | **0.8771** | **Highest benchmark score** |

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
> **Production Recommendation:** For interactive CLI commands where sub-second latency is critical without running a background daemon, **Improved BM25** delivers top-1 hit accuracy equal to Frozen E5 (**0.6250**) with only **107 ms** startup and **2.4 ms** query time. In server or daemon deployments where corpus embeddings are resident in memory, **Hybrid RRF** provides the highest ranking quality (**0.7254 MRR@10**).
