# Phase 3: Multi-Retriever Benchmark Evaluation Report

**Repository:** `soup-rag-prototype`  
**Branch:** `feat/evaluation-v2`  
**Execution Date:** 2026-11-04 (Audited: Phase 3.1)  
**Status:** Evaluation Completed, Audited & Verified  

---

## 1. Executive Summary

This report documents the empirical evaluation of nine retrieval configurations on the frozen 54-query manual retrieval benchmark for the Soup prototype. The evaluation was conducted to answer the central research question:

> **Can diverse LLM-generated training queries and an expanded training corpus improve embedding retrieval compared with frozen MiniLM, the original Soup adapter, and frozen E5-small?**

All reported confidence intervals are exploratory $95\%$ document-stratified paired percentile bootstrap intervals ($10,000$ resamples, random seed $42$) describing uncertainty across the four fixed evaluation document clusters. Following the project's evaluation standards, no $p$-values or claims of statistical significance are made.

### Key Findings

1. **Matched Query Generation Strategy Comparison (A-matched $\to$ B):**  
   Holding the positive chunk multiset ($116$ unique chunks) and optimizer update budget ($1,857$ updates) strictly identical, training on diverse LLM-generated queries (**Retriever B**) substantially outperforms heuristic/regex-generated queries (**Retriever A-matched**):
   - **MRR@10:** $0.7434$ vs $0.6554$ ($\Delta = +0.0879$, $95\%\text{ CI } [+0.0221, +0.1561]$).
   - **Hit@1:** $0.6481$ vs $0.5185$ ($\Delta = +0.1296$, $95\%\text{ CI } [+0.0370, +0.2222]$).
   - **Recall@3:** $0.6015$ vs $0.5228$ ($\Delta = +0.0787$, $95\%\text{ CI } [+0.0093, +0.1574]$).  
   Both endpoints of the $95\%$ bootstrap intervals are strictly positive. In addition to natural language phrasing diversity, Retriever B benefits from intent stratification (how-to, conceptual, parameter, troubleshooting) which was absent in A-matched's purely synthetic heuristic extraction.

2. **Combined Query Sampling and Positive Chunk Coverage Comparison (C-matched $\to$ C-matched-balanced):**  
   On the expanded 31-document corpus ($8$ core plus $23$ candidate documents) under an identical budget of $1,857$ updates, stratifying queries across how-to, conceptual, and parameter intents while simultaneously expanding unique positive chunk coverage from $565$ to $720$ chunks (**C-matched-balanced**) delivers an observed improvement over the unstratified, conceptual-heavy candidate pool (**C-matched**):
   - **MRR@10:** $0.7681$ vs $0.6844$ ($\Delta = +0.0837$, $95\%\text{ CI } [+0.0164, +0.1592]$).
   - **Recall@3:** $0.5722$ vs $0.5090$ ($\Delta = +0.0633$, $95\%\text{ CI } [+0.0231, +0.1096]$).
   - **Hit@1:** $0.6852$ vs $0.6111$ ($\Delta = +0.0741$, $95\%\text{ CI } [-0.0185, +0.1852]$).  
   This comparison reflects the joint effect of balancing query intent proportions and broadening positive chunk coverage across the candidate documents.

3. **Full Data Regime Comparison (C-matched-balanced $\to$ C-full):**  
   The C-full training regime ($2,257$ queries, $6,771$ triplets, $5,079$ optimizer updates across $31$ documents) produced substantial retrieval degradation relative to C-matched-balanced ($825$ queries, $2,475$ triplets, $1,857$ updates):
   - **MRR@10:** drops from $0.7681$ to $0.6310$ ($\Delta = -0.1371$, $95\%\text{ CI } [-0.2107, -0.0708]$).
   - **Hit@1:** drops from $0.6852$ to $0.5556$ ($\Delta = -0.1296$, $95\%\text{ CI } [-0.2222, -0.0556]$).
   - **Wrong-Document Top-1 Outcomes:** surged from $4$ in C-matched-balanced to $11$ in C-full.  
   C-full performs lower than the untrained **Frozen MiniLM** baseline ($0.6310$ vs $0.6928$). While consistent with overfitting or representation distortion, the exact causal mechanism (triplet volume, learning rate schedule, or negative mining density) remains an unverified hypothesis requiring independent embedding-space diagnostics.

4. **Expanded Corpus and Associated Example Comparison (B $\to$ C-matched-balanced):**  
   Expanding the training corpus from $8$ core documents ($116$ positive chunks) to $31$ total documents ($8$ core plus $23$ candidate documents, $720$ positive chunks) under an identical update budget ($1,857$ updates) and matched query intent distribution produced a modest positive point estimate that spans zero in bootstrap resampling:
   - **MRR@10:** $0.7681$ vs $0.7434$ ($\Delta = +0.0247$, $95\%\text{ CI } [-0.0217, +0.0682]$).
   - **Hit@1:** $0.6852$ vs $0.6481$ ($\Delta = +0.0370$, $95\%\text{ CI } [-0.0370, +0.1111]$).  
   Because positive passages, source documents, and individual query instances differ, corpus expansion alone cannot be isolated as a pure independent variable, and the relevant $95\%$ bootstrap intervals include zero.

5. **No Adapter Outperforms Frozen E5-small (R3):**  
   The frozen off-the-shelf baseline `intfloat/e5-small-v2` (**R3**) achieved the best overall retrieval performance among tested retrievers on this benchmark:
   - **MRR@10:** $0.7834$ (vs $0.7681$ for C-matched-balanced, $\Delta = -0.0153$, $95\%\text{ CI } [-0.1044, +0.0740]$).
   - **Recall@3:** $0.6694$ (vs $0.5722$ for C-matched-balanced, $\Delta = -0.0972$, $95\%\text{ CI } [-0.1944, +0.0000]$).
   - **Sec-MRR@10:** $0.8165$ (vs $0.7793$ for C-matched-balanced).
   - **Failure Diagnostic:** E5-small experienced only 1 wrong-document top-1 ranking and only 1 query with no relevant result in the top 10 across all 54 benchmark queries.

6. **Adapter Gains Over Frozen MiniLM are Fragile and Document-Dependent:**  
   Leave-one-document-out (LODO) analysis reveals that the aggregate point-estimate advantage of B and C-matched-balanced over Frozen MiniLM is driven predominantly by a single document: `adapters-and-governance` (where Retriever B gained $+0.2448$ MRR@10 and C-matched-balanced gained $+0.2781$ MRR@10 over Frozen MiniLM). On `evaluation`, observed MRR gains over Frozen MiniLM are much smaller ($+0.0303$ for B and $+0.0402$ for C-matched-balanced).  
   When `adapters-and-governance` is excluded:
   - **Frozen MiniLM MRR@10 on remaining 38 queries:** $0.7411$
   - **Retriever B MRR@10:** $0.7099$ ($\Delta = -0.0312$)
   - **C-matched-balanced MRR@10:** $0.7310$ ($\Delta = -0.0101$)  
   Furthermore, observed retrieval scores on `compliance` are lower for the fine-tuned adapters than for Frozen MiniLM (MRR@10 of $0.5750$ for C-matched-balanced and $0.4896$ for B, versus $0.7083$ for Frozen MiniLM), while on `peft-and-efficiency` C-matched-balanced ties Frozen MiniLM on MRR@10 (both $0.7333$) and B is marginally higher ($0.7372$ vs $0.7333$, $\Delta = +0.0039$). Therefore, cross-document generalization is not established.

---

## 2. Experimental Setup and Provenance

### 2.1 Benchmark Retrievers

| ID | Retriever | Base Architecture / Model ID | Adapter Path / Source | Revision / Hash | Param Count (Trainable) |
|---|---|---|---|---|---:|
| **R1** | BM25 | BM25Okapi ($k_1=1.5, b=0.75$) | None (Lexical Baseline) | Fixed defaults | 0 |
| **R2** | Frozen MiniLM | `sentence-transformers/all-MiniLM-L6-v2` | None (Zero-Shot Base) | `1110a243fdf4...` | 0 / 22.7M |
| **R3** | Frozen E5-small | `intfloat/e5-small-v2` | None (Zero-Shot Base) | `ffb93f3bd404...` | 0 / 33.4M |
| **R4** | A-full | `sentence-transformers/all-MiniLM-L6-v2` | `output_embedding/` | `4dceadcba8d9...` | 147,456 (0.65%) |
| **R5** | A-matched | `sentence-transformers/all-MiniLM-L6-v2` | `output/adapter_exp_a_matched/` | `81c35eeda777...` | 147,456 (0.65%) |
| **R6** | B | `sentence-transformers/all-MiniLM-L6-v2` | `output/adapter_exp_b/` | `7ce33a504a50...` | 147,456 (0.65%) |
| **R7** | C-matched | `sentence-transformers/all-MiniLM-L6-v2` | `output/adapter_exp_c_matched/` | `6fe28922b07e...` | 147,456 (0.65%) |
| **R8** | C-matched-balanced | `sentence-transformers/all-MiniLM-L6-v2` | `output/adapter_exp_c_matched_balanced/` | `25e00640d2f0...` | 147,456 (0.65%) |
| **R9** | C-full | `sentence-transformers/all-MiniLM-L6-v2` | `output/adapter_exp_c_full/` | `145df32609eb...` | 147,456 (0.65%) |

### 2.2 Frozen Benchmark Datasets

The evaluation inputs were verified bit-exact prior to and following evaluation:
- **Corpus:** `data/corpus.jsonl` (1,068 chunks, 303 sections, 4 source documents: `adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`).  
  `SHA256: d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3`
- **Queries:** `data/manual_queries.jsonl` (54 queries with multi-chunk and multi-section relevance labels).  
  `SHA256: 971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3`

### 2.3 Evaluation Slices

1. **Full Benchmark (54 queries):** Complete frozen evaluation benchmark.
2. **Core Primary (39 queries):** Queries with zero overlap with original candidate document sources.
3. **Core Overlap (15 queries):** Queries targeting sections that overlapped with the original candidate set.
4. **Candidate Clean (52 queries):** All queries excluding the 2 candidate partial overlap queries.
5. **Candidate Partial Overlap (2 queries):** `manual_025` and `manual_048`.
6. **Pure Held-Out (37 queries):** Strict intersection of Core Primary $\cap$ Candidate Clean.

---

## 3. Primary Benchmark Results (Full 54-Query Benchmark)

### Table 3.1: Chunk-Level Retrieval Metrics (Full Benchmark, $N=54$)

| ID | Retriever | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Macro Hit@1 | Macro Rec@3 | Macro MRR@10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **R1** | BM25 | 0.4815 | 0.4497 | 0.5114 | 0.5953 | 0.4821 | 0.4309 | 0.5983 |
| **R2** | Frozen MiniLM | 0.5741 | 0.5753 | 0.6895 | 0.6928 | 0.5647 | 0.5748 | 0.6955 |
| **R3** | **Frozen E5-small** | **0.6852** | **0.6694** | **0.7302** | **0.7834** | **0.6960** | **0.6850** | **0.7907** |
| **R4** | A-full | 0.5370 | 0.4951 | 0.5790 | 0.6501 | 0.5144 | 0.4947 | 0.6394 |
| **R5** | A-matched | 0.5185 | 0.5228 | 0.6438 | 0.6554 | 0.4990 | 0.5225 | 0.6478 |
| **R6** | B | 0.6481 | 0.6015 | 0.6552 | 0.7434 | 0.5950 | 0.5898 | 0.7107 |
| **R7** | C-matched | 0.6111 | 0.5090 | 0.5512 | 0.6844 | 0.5925 | 0.5110 | 0.6711 |
| **R8** | C-matched-balanced | **0.6852** | 0.5722 | 0.6599 | 0.7681 | 0.6413 | 0.5759 | 0.7419 |
| **R9** | C-full | 0.5556 | 0.4951 | 0.5735 | 0.6310 | 0.5178 | 0.4851 | 0.5999 |

### Table 3.2: Section-Level Retrieval Metrics (Full Benchmark, $N=54$)

| ID | Retriever | Sec-Hit@1 | Sec-Recall@3 | Sec-Recall@5 | Sec-MRR@10 | Macro Sec-Hit@1 | Macro Sec-MRR@10 |
|---|---|---:|---:|---:|---:|---:|---:|
| **R1** | BM25 | 0.4815 | 0.5926 | 0.6420 | 0.6127 | 0.4821 | 0.6151 |
| **R2** | Frozen MiniLM | 0.6296 | 0.6481 | 0.7377 | 0.7257 | 0.6173 | 0.7262 |
| **R3** | **Frozen E5-small** | **0.7222** | **0.7593** | **0.8025** | **0.8165** | **0.7304** | **0.8236** |
| **R4** | A-full | 0.5741 | 0.6080 | 0.6759 | 0.6822 | 0.5484 | 0.6698 |
| **R5** | A-matched | 0.5741 | 0.6204 | 0.7222 | 0.6957 | 0.5484 | 0.6845 |
| **R6** | B | 0.6667 | 0.6944 | 0.7469 | 0.7546 | 0.6166 | 0.7247 |
| **R7** | C-matched | 0.6296 | 0.6358 | 0.6728 | 0.7014 | 0.6110 | 0.6882 |
| **R8** | C-matched-balanced | 0.7037 | 0.6975 | 0.7593 | 0.7793 | 0.6599 | 0.7542 |
| **R9** | C-full | 0.5926 | 0.5833 | 0.6512 | 0.6577 | 0.5518 | 0.6267 |

---

## 4. Paired Statistical Comparisons & Bootstrap Analysis

All confidence intervals are derived from **10,000 document-stratified paired percentile bootstrap resamples** (random seed: 42) over the 54 benchmark queries. These intervals represent exploratory uncertainty across the 4 fixed evaluation documents. Intervals strictly excluding zero are denoted with $(\ast)$.

### Table 4.1: Five Authorized Experimental Comparisons

| Comparison | Contrast Description | Metric | Observed Delta | $95\%$ Percentile Bootstrap CI | Excludes Zero? |
|---|---|---|---:|:---:|:---:|
| **A-full vs A-matched** | Synthetic training data volume and budget comparison ($2,427$ vs $1,857$ updates) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0185$<br>$-0.0278$<br>$-0.0054$ | $[+0.0000, +0.0556]$<br>$[-0.0648, +0.0031]$<br>$[-0.0226, +0.0183]$ | No<br>No<br>No |
| **B vs A-matched** | Matched query generation strategy comparison (Diverse LLM vs Heuristic synthetic) | Hit@1<br>Recall@3<br>MRR@10 | $+0.1296$<br>$+0.0787$<br>$+0.0879$ | $[+0.0370, +0.2222]$<br>$[+0.0093, +0.1574]$<br>$[+0.0221, +0.1561]$ | $\ast$<br>$\ast$<br>$\ast$ |
| **C-matched-bal vs B** | Expanded corpus and associated training example comparison ($31$ vs $8$ docs) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0370$<br>$-0.0293$<br>$+0.0247$ | $[-0.0370, +0.1111]$<br>$[-0.0802, +0.0185]$<br>$[-0.0217, +0.0682]$ | No<br>No<br>No |
| **C-matched-bal vs C-matched** | Query sampling and distribution strategy comparison (Balanced $720$ chunks vs Skewed $565$ chunks) | Hit@1<br>Recall@3<br>MRR@10 | $+0.0741$<br>$+0.0633$<br>$+0.0837$ | $[-0.0185, +0.1852]$<br>$[+0.0231, +0.1096]$<br>$[+0.0164, +0.1592]$ | No<br>$\ast$<br>$\ast$ |
| **C-matched-bal vs C-full** | Full data regime comparison ($1,857$ updates / $825$ queries vs $5,079$ updates / $2,257$ queries) | Hit@1<br>Recall@3<br>MRR@10 | $+0.1296$<br>$+0.0772$<br>$+0.1371$ | $[+0.0556, +0.2222]$<br>$[+0.0231, +0.1420]$<br>$[+0.0708, +0.2107]$ | $\ast$<br>$\ast$<br>$\ast$ |

### Table 4.2: Adapters vs Baselines

| Comparison | Delta Hit@1 | $95\%$ CI Hit@1 | Delta MRR@10 | $95\%$ CI MRR@10 |
|---|---:|:---:|---:|:---:|
| **A-full vs Frozen MiniLM** | $-0.0370$ | $[-0.1852, +0.1111]$ | $-0.0427$ | $[-0.1482, +0.0632]$ |
| **A-matched vs Frozen MiniLM** | $-0.0556$ | $[-0.2037, +0.0926]$ | $-0.0374$ | $[-0.1376, +0.0644]$ |
| **B vs Frozen MiniLM** | $+0.0741$ | $[-0.0370, +0.1852]$ | $+0.0506$ | $[-0.0267, +0.1326]$ |
| **C-matched vs Frozen MiniLM** | $+0.0370$ | $[-0.1111, +0.1852]$ | $-0.0084$ | $[-0.1226, +0.1062]$ |
| **C-matched-bal vs Frozen MiniLM** | $+0.1111$ | $[-0.0185, +0.2407]$ | $+0.0753$ | $[-0.0135, +0.1652]$ |
| **C-full vs Frozen MiniLM** | $-0.0185$ | $[-0.1667, +0.1296]$ | $-0.0618$ | $[-0.1715, +0.0493]$ |
| **B vs BM25** | $+0.1667$ | $[+0.0185, +0.3148]^\ast$ | $+0.1481$ | $[+0.0302, +0.2676]^\ast$ |
| **C-matched-bal vs BM25** | $+0.2037$ | $[+0.0370, +0.3704]^\ast$ | $+0.1728$ | $[+0.0377, +0.3066]^\ast$ |
| **B vs Frozen E5-small** | $-0.0370$ | $[-0.1667, +0.0926]$ | $-0.0400$ | $[-0.1258, +0.0442]$ |
| **C-matched-bal vs Frozen E5-small** | $0.0000$ | $[-0.1296, +0.1296]$ | $-0.0153$ | $[-0.1044, +0.0740]$ |
| **C-full vs Frozen E5-small** | $-0.1296$ | $[-0.2778, +0.0185]$ | $-0.1524$ | $[-0.2692, -0.0361]^\ast$ |

---

## 5. Sliced Analysis and Overlap Verification

### Table 5.1: Performance Across Slices (MRR@10 / Hit@1)

| Slice | $N$ | BM25 | Frozen MiniLM | Frozen E5-small | A-matched | B | C-matched-bal | C-full |
|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Full Benchmark** | 54 | 0.5953 / 0.4815 | 0.6928 / 0.5741 | **0.7834** / **0.6852** | 0.6554 / 0.5185 | 0.7434 / 0.6481 | 0.7681 / **0.6852** | 0.6310 / 0.5556 |
| **Core Primary** | 39 | 0.5443 / 0.4103 | 0.7135 / 0.6154 | **0.8129** / **0.7436** | 0.6490 / 0.5128 | 0.7494 / 0.6667 | 0.7789 / 0.7179 | 0.6536 / 0.6154 |
| **Core Overlap** | 15 | 0.7280 / 0.6667 | 0.6389 / 0.4667 | 0.7067 / 0.5333 | 0.6722 / 0.5333 | 0.7278 / 0.6000 | **0.7400** / 0.6000 | 0.5722 / 0.4000 |
| **Candidate Clean** | 52 | 0.6086 / 0.5000 | 0.6983 / 0.5769 | **0.7879** / **0.6923** | 0.6614 / 0.5192 | 0.7527 / 0.6538 | 0.7763 / **0.6923** | 0.6361 / 0.5577 |
| **Candidate Overlap** | 2 | 0.2500 / 0.0000 | 0.5500 / 0.5000 | **0.6667** / 0.5000 | 0.5000 / 0.5000 | 0.5000 / 0.5000 | 0.5500 / 0.5000 | 0.5000 / 0.5000 |
| **Pure Held-Out** | 37 | 0.5597 / 0.4324 | 0.7208 / 0.6216 | **0.8190** / **0.7568** | 0.6552 / 0.5135 | 0.7601 / 0.6757 | 0.7887 / 0.7297 | 0.6601 / 0.6216 |

### Sliced Analysis Findings

- **Pure Held-Out Slice ($N=37$):**  
  On the strictly held-out partition (Core Primary $\cap$ Candidate Clean), C-matched-balanced achieves an aggregate point estimate of $0.7887$ MRR@10 and $0.7297$ Hit@1 (vs $0.7208$ and $0.6216$ for Frozen MiniLM). However, as shown in Section 6, this aggregate number is heavily skewed by a single document and does not demonstrate uniform cross-document generalization. Furthermore, Frozen E5-small retains the highest performance on this slice ($0.8190$ MRR@10, $0.7568$ Hit@1).
- **Candidate Overlap Queries ($N=2$):**  
  On `manual_025` and `manual_048`, all dense adapters score identically ($0.5000$ Hit@1, $0.5000-0.5500$ MRR@10). There is zero concentration of performance on these queries.
- **Core Overlap ($N=15$):**  
  BM25 scores high ($0.7280$ MRR@10) due to exact parameter keyword matches. Adapters B and C-matched-balanced achieve $0.7278-0.7400$.

---

## 6. Cross-Document Generalization and LODO Sensitivity Analysis

### Table 6.1: Per-Document Performance Breakdown (MRR@10 / Hit@1)

| Document | $N$ | BM25 | Frozen MiniLM | Frozen E5-small | B | C-matched-bal | C-full |
|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `adapters-and-governance` | 16 | 0.5315 / 0.4375 | 0.5781 / 0.4375 | 0.6507 / 0.5000 | 0.8229 / 0.7500 | **0.8562** / **0.8125** | 0.7521 / 0.6875 |
| `evaluation` | 17 | 0.6359 / 0.5294 | 0.7624 / 0.7059 | **0.8431** / **0.7647** | 0.7927 / **0.7647** | 0.8026 / **0.7647** | 0.6422 / 0.5882 |
| `peft-and-efficiency` | 13 | 0.6154 / 0.4615 | 0.7333 / 0.6154 | **0.8410** / **0.7692** | 0.7372 / 0.6154 | 0.7333 / 0.6154 | 0.6378 / 0.5385 |
| `compliance` | 8 | 0.6042 / 0.5000 | 0.7083 / 0.5000 | **0.8281** / **0.7500** | 0.4896 / 0.2500 | 0.5750 / 0.3750 | 0.3542 / 0.2500 |

### Table 6.2: Leave-One-Document-Out (LODO) Sensitivity Analysis (MRR@10)

| Dropped Document | Evaluated Queries | Frozen MiniLM | B | C-matched-bal | Frozen E5-small | Delta (C-bal vs MiniLM) | Delta (C-bal vs E5) |
|---|---:|:---:|:---:|:---:|:---:|---:|---:|
| `adapters-and-governance` | 38 | **0.7411** | 0.7099 | 0.7310 | **0.8393** | **-0.0101** | -0.1083 |
| `compliance` | 46 | 0.6901 | 0.7875 | **0.8017** | 0.7756 | **+0.1116** | +0.0261 |
| `evaluation` | 37 | 0.6608 | 0.7207 | **0.7523** | 0.7559 | **+0.0915** | -0.0036 |
| `peft-and-efficiency` | 41 | 0.6799 | 0.7454 | **0.7791** | 0.7651 | **+0.0992** | +0.0140 |

### LODO Analysis Insights

1. **Extreme Sensitivity to `adapters-and-governance`:**  
   When `adapters-and-governance` is excluded, the apparent aggregate retrieval advantage of the fine-tuned adapters completely vanishes: Frozen MiniLM scores $0.7411$, whereas Retriever B scores $0.7099$ ($\Delta = -0.0312$) and C-matched-balanced scores $0.7310$ ($\Delta = -0.0101$). The aggregate advantage is driven by `adapters-and-governance` where MiniLM scored $0.5781$, while B gained $+0.2448$ ($0.8229$) and C-matched-balanced gained $+0.2781$ ($0.8562$). In contrast, on `evaluation`, gains over Frozen MiniLM ($0.7624$) are modest: B gained $+0.0303$ ($0.7927$) and C-matched-balanced gained $+0.0402$ ($0.8026$).

   | Document | Retriever | Frozen MiniLM MRR | Retriever MRR | MRR Difference |
   |---|---|:---:|:---:|---:|
   | `adapters-and-governance` | B | 0.5781 | 0.8229 | +0.2448 |
   | `adapters-and-governance` | C-matched-balanced | 0.5781 | 0.8562 | +0.2781 |
   | `evaluation` | B | 0.7624 | 0.7927 | +0.0303 |
   | `evaluation` | C-matched-balanced | 0.7624 | 0.8026 | +0.0402 |
2. **Lower Scores on Compliance:**  
   On `compliance` ($N=8$), observed retrieval scores are lower for the fine-tuned adapters than for the base model: Frozen MiniLM scores $0.7083$ MRR@10, whereas C-matched-balanced drops to $0.5750$ ($\Delta = -0.1333$) and B drops to $0.4896$ ($\Delta = -0.2187$). In contrast, Frozen E5-small scores $0.8281$ on compliance.
3. **Performance on PEFT:**  
   On `peft-and-efficiency`, C-matched-balanced ties Frozen MiniLM on MRR@10 (both $0.7333$), while B scores marginally higher ($0.7372$ vs $0.7333$).
4. **No Systematic Generalization Across Document Domains:**  
   Because observed score differences are positive on two documents, tied or marginal on one, and lower on another, the adapters do not exhibit cross-document domain generalization.

---

## 7. Failure Mode Classification & Reconciliation

In the shared retrieval implementation (`scripts/retrieval.py`), query failure modes are classified into mutually exclusive leaf categories based on hierarchical rank evaluation.

### Table 7.1A: Five Mutually Exclusive Top-10 Retrieval Outcomes ($N=54$)

Every query is assigned to exactly one of five operational outcome categories. The five columns sum to exactly 54 for every retriever:

| ID | Retriever | Exact Chunk Top-1 | Rel Sec Unlabeled Top-1 | Rel Chunk Below Top-1 | Rel Sec Below Top-1 | Zero Rel in Top-10 | Sum |
|---|---|---:|---:|---:|---:|---:|---:|
| **R1** | BM25 | 26 | 0 | 17 | 1 | 10 | **54** |
| **R2** | Frozen MiniLM | 31 | 3 | 15 | 0 | 5 | **54** |
| **R3** | Frozen E5-small | 37 | 2 | 13 | 1 | 1 | **54** |
| **R4** | A-full | 29 | 2 | 17 | 0 | 6 | **54** |
| **R5** | A-matched | 28 | 3 | 18 | 0 | 5 | **54** |
| **R6** | B | 35 | 1 | 13 | 0 | 5 | **54** |
| **R7** | C-matched | 33 | 1 | 11 | 1 | 8 | **54** |
| **R8** | C-matched-balanced | 37 | 1 | 12 | 0 | 4 | **54** |
| **R9** | C-full | 30 | 2 | 10 | 1 | 11 | **54** |

### Table 7.1B: Six Mutually Exclusive Leaf Categories ($N=54$)

Subdividing the "Zero Rel in Top-10" outcome into top-1 document origin:

| ID | Retriever | Exact Chunk Top-1 | Rel Sec Unlabeled Top-1 | Rel Chunk Below Top-1 | Rel Sec Below Top-1 | Wrong Sec Same Doc | Wrong Document | Total Leaves | Zero Rel in Top-10 (Diag) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **R1** | BM25 | 26 | 0 | 17 | 1 | 2 | 8 | **54** | 10 |
| **R2** | Frozen MiniLM | 31 | 3 | 15 | 0 | 1 | 4 | **54** | 5 |
| **R3** | Frozen E5-small | 37 | 2 | 13 | 1 | 0 | 1 | **54** | 1 |
| **R4** | A-full | 29 | 2 | 17 | 0 | 1 | 5 | **54** | 6 |
| **R5** | A-matched | 28 | 3 | 18 | 0 | 1 | 4 | **54** | 5 |
| **R6** | B | 35 | 1 | 13 | 0 | 0 | 5 | **54** | 5 |
| **R7** | C-matched | 33 | 1 | 11 | 1 | 0 | 8 | **54** | 8 |
| **R8** | C-matched-balanced | 37 | 1 | 12 | 0 | 0 | 4 | **54** | 4 |
| **R9** | C-full | 30 | 2 | 10 | 1 | 0 | 11 | **54** | 11 |

### Reconciliation of Previous Accounting Discrepancy

The earlier draft of Table 7.1 omitted the column `Rel Sec Below Top-1` (`relevant_section_below_top1`). Exactly four queries fell into this leaf:
- **BM25:** `manual_006` ("ROME vs MEMIT vs AlphaEdit differences"). Rank 1 was an irrelevant chunk, but rank 3 was an unlabeled chunk from the relevant section.
- **Frozen E5-small:** `manual_003` ("how do I see which training rows influenced an adapter"). Ranks 1-4 were non-relevant, but rank 5 matched the relevant section.
- **C-matched:** `manual_004` ("what does soup loop automate"). A relevant section passage appeared in ranks 6-10 without any labeled chunk in the top 10.
- **C-full:** `manual_004` ("what does soup loop automate"). Same pattern as C-matched.

Because `Rel Sec Below Top-1` was omitted from the previous table columns, BM25, E5-small, C-matched, and C-full previously summed to 53. With this category restored, every retriever sums to exactly 54.

---

## 8. Resolution of Core Research Questions

### Question 1: Does any trained adapter outperform frozen MiniLM?
**Answer: Observed mean point estimates are higher for B and C-matched-balanced, but their 95% bootstrap intervals include zero, and gains are concentrated predominantly in adapters-and-governance, with smaller positive point estimate differences on evaluation.**  
- Retriever B ($0.7434$ MRR@10) and C-matched-balanced ($0.7681$ MRR@10) achieve higher point estimates than Frozen MiniLM ($0.6928$).
- However, their $95\%$ bootstrap intervals for MRR span zero (B: $[-0.0267, +0.1326]$; C-matched-balanced: $[-0.0135, +0.1652]$).
- Adapters A-full ($0.6501$), A-matched ($0.6554$), and C-full ($0.6310$) perform worse than Frozen MiniLM.
- When `adapters-and-governance` is dropped, neither B nor C-matched-balanced outperforms MiniLM.

### Question 2: Does any trained adapter outperform BM25?
**Answer: Both B and C-matched-balanced show positive observed deltas over BM25 with 95% bootstrap intervals strictly above zero.**  
Both Retriever B ($\Delta \text{MRR} = +0.1481$, $95\%\text{ CI } [+0.0302, +0.2676]$) and C-matched-balanced ($\Delta \text{MRR} = +0.1728$, $95\%\text{ CI } [+0.0377, +0.3066]$) outperform BM25 ($0.5953$) with $95\%$ bootstrap confidence intervals strictly above zero. BM25 suffers from 10 zero-relevant top-10 queries, whereas C-matched-balanced suffers only 4.

### Question 3: Does any trained adapter outperform frozen E5-small?
**Answer: No.**  
Frozen E5-small achieves higher MRR@10 ($0.7834$ vs $0.7681$), substantially higher Recall@3 ($0.6694$ vs $0.5722$), higher Section-MRR@10 ($0.8165$ vs $0.7793$), and only $1$ query with zero relevant results in the top 10. E5-small achieved the best overall performance among tested retrievers on this benchmark without fine-tuning.

### Question 4: Does the expanded corpus improve retrieval over the original core corpus?
**Answer: Inconclusive under matched budget.**  
Comparing B (Core corpus, 8 training docs, $116$ positive chunks) against C-matched-balanced (Expanded corpus, 31 training docs, $720$ positive chunks) under a matched update budget ($1,857$ updates):
- MRR@10 delta is $+0.0247$ ($95\%\text{ CI } [-0.0217, +0.0682]$).
- Hit@1 delta is $+0.0370$ ($95\%\text{ CI } [-0.0370, +0.1111]$).  
Because positive passages and document distributions differ, corpus expansion is not isolated as a pure variable, and the relevant 95% bootstrap intervals include zero.

### Question 5: How does C-matched-balanced compare with C-matched?
**Answer: C-matched-balanced demonstrates higher observed retrieval performance than C-matched in a combined query sampling and positive chunk coverage comparison.**  
Comparing C-matched-balanced (balanced intent distribution across how-to, conceptual, and parameter queries, covering $720$ unique positive chunks) against C-matched (unstratified conceptual-heavy candidate pool covering $565$ unique positive chunks) under the identical $1,857$ update budget:
- MRR@10 delta is $+0.0837$ ($95\%\text{ CI } [+0.0164, +0.1592]$).
- Recall@3 delta is $+0.0633$ ($95\%\text{ CI } [+0.0231, +0.1096]$).  
Both $95\%$ bootstrap intervals strictly exclude zero. This observed improvement belongs to a combined query sampling and positive chunk coverage comparison ($720$ vs $565$ chunks), so the gain cannot be attributed to intent balancing alone.

### Question 6: Does the larger C-full training regime offer an advantage over matched budget training?
**Answer: No. The C-full training regime produced substantial retrieval degradation.**  
Comparing C-full ($5,079$ updates, $2,257$ queries) against C-matched-balanced ($1,857$ updates, $825$ queries):
- MRR@10 collapses from $0.7681$ to $0.6310$ ($\Delta = -0.1371$, $95\%\text{ CI } [-0.2107, -0.0708]$).
- Wrong-document top-1 outcomes surge from $4$ to $11$.  
Observed performance is lower across all metrics, with 95% bootstrap intervals strictly negative for deltas relative to C-matched-balanced. However, whether this degradation was caused specifically by over-training steps, contrastive loss collapse, or hard negative distribution shifts is not independently established and remains a hypothesis.

### Question 7: Are improvements consistent across all four evaluation source documents?
**Answer: No. Observed improvements are heavily concentrated in a single document, with lower observed scores on another.**  
- In `adapters-and-governance`, B gains $+0.2448$ MRR@10 ($0.8229$ vs $0.5781$) and C-matched-balanced gains $+0.2781$ MRR@10 ($0.8562$ vs $0.5781$) over Frozen MiniLM.
- In `evaluation`, B gains $+0.0303$ MRR@10 ($0.7927$ vs $0.7624$) and C-matched-balanced gains $+0.0402$ MRR@10 ($0.8026$ vs $0.7624$) over Frozen MiniLM.
- In `peft-and-efficiency`, C-matched-balanced ties Frozen MiniLM on MRR@10 (both $0.7333$), while B scores marginally higher ($0.7372$ vs $0.7333$, $\Delta = +0.0039$).
- In `compliance`, adapters exhibit lower observed scores (MRR@10: $0.5750$ for C-matched-balanced vs $0.7083$ for MiniLM, $\Delta = -0.1333$; $0.4896$ for B, $\Delta = -0.2187$).

### Question 8: Does any improvement survive evaluation on the 37 pure held-out queries?
**Answer: Yes in aggregate point estimate, but not as uniform cross-document generalization.**  
On the 37 pure held-out queries (Core Primary $\cap$ Candidate Clean):
- C-matched-balanced achieves MRR@10 $0.7887$ vs Frozen MiniLM $0.7208$ ($\Delta = +0.0679$).
- However, as demonstrated by LODO analysis, this aggregate score remains dependent on `adapters-and-governance`. Furthermore, Frozen E5-small scores higher ($0.8190$ MRR@10).

### Question 9: Are apparent improvements concentrated in the candidate partial overlap or core overlap queries?
**Answer: No.**  
- On the two candidate partial overlap queries (`manual_025`, `manual_048`), all dense models perform virtually identically (Hit@1 = $0.5000$, MRR $\approx 0.50-0.55$).
- On the 15 core overlap queries, BM25 scores highest ($0.7280$), while adapter gains over MiniLM are actually strongest on the non-overlapping Core Primary slice ($+0.0654$ MRR@10).

---

## 9. Engineering Recommendations & Strategic Conclusions

1. **Prototype Default Recommendation: Select Frozen E5-small as Prototype Default.**  
   `intfloat/e5-small-v2` achieved the best overall retrieval performance among tested retrievers on this benchmark without requiring adapter maintenance or exhibiting lower observed scores on specialized documentation (scoring $0.8281$ on `compliance` where adapters scored lower). It achieves the highest ranking accuracy and the lowest failure rate ($1$ query with zero relevant results in the top 10). Because this benchmark evaluates 54 queries across 4 documents, broader validation across additional repositories, corpora, and operational domains is required before a production deployment decision.
2. **If Fine-Tuning MiniLM is Architecturally Mandated:**  
   - Use intent-stratified LLM query generation (**C-matched-balanced**), never heuristic regex queries (**A-matched**).
   - Cap training updates conservatively ($\sim 1,800$ updates); avoid extended training regimes (**C-full**).
   - Evaluate against multi-document score degradation before deployment.
3. **Hybrid Search Exploration:**  
   Because BM25 performs strongly on parameter/CLI queries (Core Overlap slice MRR $0.7280$), a hybrid BM25 + Dense (E5-small or C-matched-balanced) ensemble using Reciprocal Rank Fusion (RRF) is the most promising path for further retrieval optimization in the Soup CLI.

---

## 10. Preserved Raw Artifacts

All original raw retrieval JSON outputs in `results/phase3/` are preserved byte-identical with verified SHA256 hashes:

```
e12c3b9fd66ecf38ac7c7fe58cbf94d30018c3ac8f4857c9caba2de8d10b973e  retriever_a_full.json
dafcdf89a4fe47e7fa8c8ee18e26664bd76066f5d84a8a0471ab095febadb851  retriever_a_matched.json
cad5cf0cca2bec4bfa020ca3d1c1dca59888878f40ee69448b71e935cbc3a691  retriever_b.json
e93db0f59c0a97ea71af7e32ab2f32f367d65ac12230a79413fdc76690517589  retriever_bm25.json
d47c767130d2fdd46f6e9d1da898bdcf730917a25d782ed82c67f5c00f9b07c3  retriever_c_full.json
1be9102898d901e507eacab814a299bae665be5e6989ba4241fb9f2b56df441b  retriever_c_matched.json
ffeec4d14467e361f2941585cc693948059087b298a3d2fd05ebc8eb3e5418ca  retriever_c_matched_balanced.json
bb2980beecd880c7c1d6ae5e0f58045b6df4f4b3317699fc4d141fc560a9eca4  retriever_e5_small.json
65b145bb3a068f0057edaf10ff8f31aa908d35ac5a88178d788115d549e86e89  retriever_mini_lm_frozen.json
```
