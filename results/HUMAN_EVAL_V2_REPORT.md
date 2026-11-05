# Independent Owner-Authored Evaluation Benchmark (v2) Report

**Date:** 2026-11-05 09:31:22 UTC
**Benchmark:** `data/human_eval/manifest_v2.json` (24 queries authored directly by project owner without AI assistance; target sections mechanically mapped to canonical chunk IDs; no third-party relevance annotation; not representative of production telemetry or sampled populations)
**Corpus:** `data/corpus.jsonl` (1,068 canonical chunks across 12 Soup documentation files)

---

## 1. Summary Benchmark Results

| System | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Cold Start (ms) | Steady State (ms) |
|---|---|---|---|---|---|---|---|---|
| **Hybrid RRF (BM25 + Frozen E5)** | 0.6250 | 0.4923 | 0.5551 | 0.7254 | 0.6250 | 0.7292 | 35,978.9 | 12.76 |
| **Frozen E5-small** | 0.6250 | 0.4562 | 0.5690 | 0.7101 | 0.6250 | 0.7240 | 35,871.9 | 10.38 |
| **C-matched-balanced (MiniLM)** | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 | 16,953.2 | 6.67 |
| **Improved BM25** | 0.6250 | 0.4929 | 0.5150 | 0.6921 | 0.6250 | 0.6921 | 107.0 | 2.37 |
| **Frozen MiniLM-L6-v2** | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 | 15,979.4 | 6.23 |
| **Fine-Tuned E5-small (lr=2e-5)** | 0.5417 | 0.5177 | 0.5591 | 0.6413 | 0.5417 | 0.6448 | 36,355.2 | 11.44 |
| **Original BM25 (whitespace, supplemental baseline)** | 0.2917 | 0.3153 | 0.3688 | 0.4140 | 0.2917 | 0.4200 | 31.3 | 2.12 |

---

## 2. Paired Document-Stratified Bootstrap Intervals (10,000 resamples, seed 42)

Values reported as `observed delta [95% CI lower, 95% CI upper]` with document stratification across all 12 documentation files:

| Comparison | Metric | Observed Delta | 95% CI Lower | 95% CI Upper | Zero in CI? |
|---|---|---|---|---|---|
| Improved BM25 vs Original BM25 | `hit@1` | +0.3333 | +0.2083 | +0.4583 | **No** |
| Improved BM25 vs Original BM25 | `recall@3` | +0.1776 | +0.0734 | +0.2956 | **No** |
| Improved BM25 vs Original BM25 | `recall@5` | +0.1462 | +0.0506 | +0.2424 | **No** |
| Improved BM25 vs Original BM25 | `mrr@10` | +0.2781 | +0.1685 | +0.3912 | **No** |
| Improved BM25 vs Original BM25 | `sec_hit@1` | +0.3333 | +0.2083 | +0.4583 | **No** |
| Improved BM25 vs Original BM25 | `sec_mrr@10` | +0.2722 | +0.1603 | +0.3873 | **No** |
| Hybrid RRF vs Frozen E5 | `hit@1` | +0.0000 | -0.1250 | +0.1250 | Yes |
| Hybrid RRF vs Frozen E5 | `recall@3` | +0.0361 | +0.0069 | +0.0653 | **No** |
| Hybrid RRF vs Frozen E5 | `recall@5` | -0.0139 | -0.1181 | +0.0833 | Yes |
| Hybrid RRF vs Frozen E5 | `mrr@10` | +0.0153 | -0.0687 | +0.0996 | Yes |
| Hybrid RRF vs Frozen E5 | `sec_hit@1` | +0.0000 | -0.1250 | +0.1250 | Yes |
| Hybrid RRF vs Frozen E5 | `sec_mrr@10` | +0.0052 | -0.0750 | +0.0867 | Yes |
| Hybrid RRF vs Improved BM25 | `hit@1` | +0.0000 | -0.1250 | +0.1250 | Yes |
| Hybrid RRF vs Improved BM25 | `recall@3` | -0.0006 | -0.0631 | +0.0619 | Yes |
| Hybrid RRF vs Improved BM25 | `recall@5` | +0.0401 | -0.0224 | +0.1050 | Yes |
| Hybrid RRF vs Improved BM25 | `mrr@10` | +0.0333 | -0.0427 | +0.1060 | Yes |
| Hybrid RRF vs Improved BM25 | `sec_hit@1` | +0.0000 | -0.1250 | +0.1250 | Yes |
| Hybrid RRF vs Improved BM25 | `sec_mrr@10` | +0.0370 | -0.0375 | +0.1079 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `hit@1` | -0.0833 | -0.1667 | +0.0000 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `recall@3` | +0.0615 | -0.0565 | +0.1796 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `recall@5` | -0.0099 | -0.1240 | +0.0972 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `mrr@10` | -0.0688 | -0.1740 | +0.0364 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `sec_hit@1` | -0.0833 | -0.1667 | +0.0000 | Yes |
| Fine-Tuned E5 (2e-5) vs Frozen E5 | `sec_mrr@10` | -0.0792 | -0.1806 | +0.0232 | Yes |
| C-matched-balanced vs Frozen MiniLM | `hit@1` | +0.0417 | -0.0833 | +0.1667 | Yes |
| C-matched-balanced vs Frozen MiniLM | `recall@3` | +0.0175 | -0.0812 | +0.1091 | Yes |
| C-matched-balanced vs Frozen MiniLM | `recall@5` | -0.0302 | -0.1069 | +0.0369 | Yes |
| C-matched-balanced vs Frozen MiniLM | `mrr@10` | +0.0417 | -0.0382 | +0.1215 | Yes |
| C-matched-balanced vs Frozen MiniLM | `sec_hit@1` | +0.0417 | -0.0833 | +0.1667 | Yes |
| C-matched-balanced vs Frozen MiniLM | `sec_mrr@10` | +0.0451 | -0.0347 | +0.1225 | Yes |
| Improved BM25 vs Frozen E5 | `hit@1` | +0.0000 | -0.1667 | +0.1667 | Yes |
| Improved BM25 vs Frozen E5 | `recall@3` | +0.0367 | -0.0327 | +0.1062 | Yes |
| Improved BM25 vs Frozen E5 | `recall@5` | -0.0540 | -0.1700 | +0.0591 | Yes |
| Improved BM25 vs Frozen E5 | `mrr@10` | -0.0180 | -0.1366 | +0.1020 | Yes |
| Improved BM25 vs Frozen E5 | `sec_hit@1` | +0.0000 | -0.1667 | +0.1667 | Yes |
| Improved BM25 vs Frozen E5 | `sec_mrr@10` | -0.0319 | -0.1467 | +0.0843 | Yes |

---

## 3. Evaluation Questions and Answers

### 1. Does the hybrid system outperform the best single retriever on human-authored queries?

**Yes in point estimates and Recall@3 over Frozen E5; overall MRR delta is statistically inconclusive on $N=24$.**
- **MRR@10:** Hybrid RRF achieves an observed MRR@10 of **0.7254** versus **0.7101** for Frozen E5-small (Observed Delta: **+0.0153**) and **0.6921** for Improved BM25 (Observed Delta: **+0.0333**).
- **Recall@3:** The paired 95% bootstrap confidence interval for Hybrid RRF versus Frozen E5 on top-3 recall strictly excludes zero: **0.4923** vs **0.4562** (Observed Delta: **+0.0361**, 95% bootstrap CI `[+0.0069, +0.0653]`). Note that across all systems, Fine-Tuned E5 achieved higher Recall@3 (0.5177) and Improved BM25 reached 0.4929.
- **Recall@5:** Hybrid RRF reaches **0.5551** vs **0.5690** for Frozen E5 (Delta: **-0.0139**, 95% CI `[-0.1181, +0.0833]`).
- **Hit@1:** Hit@1 is tied at **0.6250** (15 of 24 queries correct at rank 1) across Hybrid RRF, Frozen E5-small, and Improved BM25.
- **Sec-MRR@10:** Reaches **0.7292** vs **0.7240** for Frozen E5 (Delta: **+0.0052**, 95% CI `[-0.0750, +0.0867]`).
- **Inference:** Because the 95% bootstrap CI for MRR@10 includes zero (`[-0.0687, +0.0996]`), the overall ranking difference between Hybrid RRF and Frozen E5 alone cannot be asserted as statistically distinguishable on this 24-query sample. The empirical benefit of RRF fusion specifically over Frozen E5 on $N=24$ is confined to enhanced top-3 candidate recall.

### 2. Does fine-tuning E5-small with matched lr=2e-5 improve over frozen E5-small on human queries?

**No; results are statistically inconclusive with negative observed ranking performance.**
- **Ranking metrics:** Fine-Tuned E5-small (`lr=2e-5`) observed lower point estimates on ranking metrics: MRR@10 fell from **0.7101 to 0.6413** (Delta: **-0.0688**, 95% CI `[-0.1740, +0.0364]`), Hit@1 dropped from **0.6250 to 0.5417** (Delta: **-0.0833**, 95% CI `[-0.1667, +0.0000]`), and Sec-MRR@10 declined from **0.7240 to 0.6448** (Delta: **-0.0792**, 95% CI `[-0.1806, +0.0232]`).
- **Candidate coverage:** However, fine-tuning was not strictly inferior across all metrics: observed Recall@3 was higher for the fine-tuned adapter (**0.5177** vs **0.4562**, Delta: **+0.0615**, 95% CI `[-0.0565, +0.1796]`). Recall@5 was slightly lower (**0.5591** vs **0.5690**, Delta: **-0.0099**, 95% CI `[-0.1240, +0.0972]`).
- **Inference:** Because all 95% bootstrap confidence intervals include zero, the difference is statistically inconclusive on $N=24$. Directionally, fine-tuning on 2,475 synthetic triplets observed lower Hit@1 (0.5417 vs 0.6250) and lower MRR@10 (0.6413 vs 0.7101) while slightly broadening mid-tier candidate retrieval (Recall@3 of 0.5177 vs 0.4562). Frozen E5-small remains the more reliable out-of-the-box choice.

### 3. Does the MiniLM adapter advantage over frozen MiniLM replicate on human queries?

**Positive observed point estimates, but within sampling uncertainty on $N=24$.**
- **Point estimates:** `C-matched-balanced` achieved an MRR@10 of **0.7004** versus **0.6587** for Frozen MiniLM-L6-v2 (Observed Delta: **+0.0417**), Hit@1 of **0.5833** vs **0.5417** (Observed Delta: **+0.0417**), and Sec-MRR@10 of **0.7073** vs **0.6622** (Observed Delta: **+0.0451**).
- **Confidence intervals:** The 95% bootstrap confidence intervals for all metrics span zero (e.g. MRR@10 CI `[-0.0382, +0.1215]`, Hit@1 CI `[-0.0833, +0.1667]`).
- **Inference:** While the observed direction of improvement matches earlier observations (+0.0417 MRR@10), a sample size of $N=24$ does not provide sufficient statistical power to establish a reliable improvement over frozen MiniLM.

### 4. How does BM25 perform on human queries compared to the baseline?

**Domain-aware BM25 substantially outperforms original whitespace BM25; paired 95% bootstrap confidence intervals strictly exclude zero across all metrics.**
- **Supplemental baseline analysis:** The original whitespace BM25 baseline (`text.lower().split()`) was added during corrective research audit to isolate the impact of domain-aware tokenization against standard whitespace splitting over the identical frozen benchmark. It achieved an MRR@10 of **0.4140**, Hit@1 of **0.2917**, Recall@3 of **0.3153**, and Recall@5 of **0.3688**.
- **Improved BM25:** Domain-aware tokenization increased MRR@10 to **0.6921** (Observed Delta: **+0.2781**, 95% CI `[+0.1685, +0.3912]`), Hit@1 to **0.6250** (Observed Delta: **+0.3333**, 95% CI `[+0.2083, +0.4583]`), Recall@3 to **0.4929** (Observed Delta: **+0.1776**, 95% CI `[+0.0734, +0.2956]`), and Sec-MRR@10 to **0.6921** (Observed Delta: **+0.2722**, 95% CI `[+0.1603, +0.3873]`).
- **Observed Bootstrap Evidence:** The paired 95% bootstrap confidence interval strictly excludes zero for all metrics, indicating an observed gain from domain-aware tokenization.
- **Historical BM25 Reconciliation:** Both the 54 AI-assisted queries (`data/manual_queries.jsonl`) and the 24 owner-authored queries (`data/human_eval/human_queries_v2.jsonl`) were evaluated against the identical 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`). On the 54 AI-assisted queries (which targeted sections within 4 held-out documents), canonical Phase 3 recorded Whitespace BM25 at **0.5953 MRR@10** (0.4815 Hit@1) and Improved BM25 at **0.7712 MRR@10** (0.6481 Hit@1). Previously cited figures of 0.5755 MRR@10 and 0.4630 Hit@1 were unverified draft narrative artifacts and are formally retracted.

### 5. What does the contrast between the AI-assisted (54 queries) and owner-authored (24 queries) benchmarks indicate?

**Differences reflect differences in benchmark design, query formulation style, and relevance target distribution, while candidate retrieval operated over the identical 1,068-chunk corpus.**
- **Corpus Verification:** Inspection of Phase 3 execution records (`results/phase3/experiment_summary.json`, `results/phase3/retriever_bm25.json`, `results/phase3/per_query_ranked_results.json`) confirms that both evaluations searched the full 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`, SHA256: `d787703e...`). The figure of 307 chunks reflects only the subset of chunks belonging to the 4 held-out target documents, not the search space. Chunks outside those 4 documents routinely appeared in Phase 3 candidate rankings.
- **Key Benchmark Contrasts:**
  1. **Benchmark Design & Query Provenance:** The 54 queries were collaboratively drafted with AI assistance, whereas the 24 queries in `human_eval_v2` were authored directly by the project owner without AI assistance. Differences in observed scores reflect benchmark design and query formulation rather than query authorship alone.
  2. **Relevance Target Distribution:** The 54 AI-assisted queries targeted sections located exclusively within 4 held-out documents (representing 307 chunks), whereas the 24 owner-authored queries target sections across all 12 documentation files.
  3. **Exact Token Matching:** Authentic developer queries contain specific command flags, version numbers, and identifier strings (`--track-energy`, `check-safetensors`, `onebitllms`, `bitnet_1.58`, `pip install`, `OpenAPI`, `MCP`, `LISA`, `#353`), which domain-aware lexical tokenization indexes directly without semantic drift.
  4. **Evaluation Methodology:** `human_eval_v2` is an independent owner-authored query evaluation where target sections were identified by the owner and mechanically mapped to canonical chunk IDs without third-party relevance annotation; it does not represent production user query logs or a statistically sampled developer population.

---

## 4. Provenance & Audit Metadata

- **Evaluation Provenance:** Independent owner-authored query evaluation on Soup documentation.
- **Authorship & Assistance:** All 24 queries written by the project owner without AI assistance; target sections identified directly by the owner.
- **Relevance Mapping:** Section headings resolved mechanically to canonical chunk IDs in `data/corpus.jsonl`; no third-party annotation was conducted; does not represent production telemetry or sampled populations.
- **Supplemental Baseline:** Original whitespace BM25 evaluated as a supplemental baseline during corrective audit to isolate tokenization effects.
- **Query File:** `data/human_eval/human_queries_v2.jsonl` (SHA256: `6d917ef3e89e18d0e87084804d3598bf53ef51971ff77259a768150f3a730d58`)
- **Annotations File:** `data/human_eval/relevance_annotations_v2.jsonl` (SHA256: `51f66a794505c6e9cc18e3f8d8008850c4c114aabf3682304196e7dfba2426a5`)
- **Corpus File:** `data/corpus.jsonl` (SHA256: `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3`)
- **Query 4 Audit Resolution:** Owner reference cited `data/raw_docs/adapters-and-governance.md`, but 'Resume Training' section is located in `data/raw_docs/backends-and-ops.md` (`backends-and-ops::resume-training`). Resolved with status `resolved_with_source_correction` in manifest while preserving annotation byte hash.
- **Model Revisions:** `intfloat/e5-small-v2@ffb93f3bd4047442299a41ebb6fa998a38507c52`, `sentence-transformers/all-MiniLM-L6-v2@1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- **Checkpoint Hashes:**
  - `output/adapter_e5_exp_b_lr2e5/adapter_model.safetensors`: `04c48664fea942c25371bd5bad1c84d47e6630270777a5df42f075bce5bf47dd`
  - `output/adapter_exp_c_matched_balanced/adapter_model.safetensors`: `25e0064078516ff068b6db2bface1065059f0d44a7a33592e8c0eb2094367137`
- **Config Hashes:**
  - `config/embedding_e5_exp_b_lr2e5.yaml`: `d0055d8948d05ae481baf0dee9620da8d5d70ea25c09a8020c4c414921574298`
  - `config/embedding_exp_c_matched_balanced.yaml`: `b1c64fc741dda6eb6f72dd4187da86a898e1ac67b1b4e0c12f9562e602560c87`