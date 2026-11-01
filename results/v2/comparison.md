# Evaluation v2 — Four-Way Retrieval Comparison (Manual Queries)

**Retrievers:** mini_lm_frozen, mini_lm_soup, bm25, e5_small  
**Queries:** 54 manual queries (owner-approved; manually crafted by the owner with AI assistance)  
**Corpus fingerprint:** 76ab5e88af6e82bb1892296c7d3a854b722466466b6ae2fb7dc8c4831be75b2c  
**Query-set fingerprint:** 971e157083c31e5e…  
**Bootstrap:** 10000 resamples, seed=42, paired document-stratified percentile intervals, one precomputed index plan shared across every metric and retriever.

> Four held-out documents are insufficient for population-level inference; all intervals describe uncertainty within this fixed query sample. No p-values and no significance claims are made.

## hit@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.5741 | 0.5647 | — | — | — |
| mini_lm_soup | 0.5370 | 0.5151 | -0.0370 [-0.1852, +0.1111] | +0.0556 [-0.1111, +0.2222] | -0.1481 [-0.2963, +0.0000] |
| bm25 | 0.4815 | 0.4821 | — | — | — |
| e5_small | 0.6852 | 0.6960 | — | — | — |

## hit@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7778 | 0.8054 | — | — | — |
| mini_lm_soup | 0.7037 | 0.6969 | -0.0741 [-0.2037, +0.0370] | +0.0000 [-0.1111, +0.1296] | -0.1667 [-0.2778, -0.0556] |
| bm25 | 0.7037 | 0.7116 | — | — | — |
| e5_small | 0.8704 | 0.8723 | — | — | — |

## hit@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.8704 | 0.8934 | — | — | — |
| mini_lm_soup | 0.7963 | 0.8090 | -0.0741 [-0.1852, +0.0185] | +0.0741 [-0.0370, +0.1852] | -0.0741 [-0.1852, +0.0185] |
| bm25 | 0.7222 | 0.7272 | — | — | — |
| e5_small | 0.8704 | 0.8723 | — | — | — |

## mrr@10

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6928 | 0.6956 | — | — | — |
| mini_lm_soup | 0.6501 | 0.6392 | -0.0427 [-0.1482, +0.0632] | +0.0548 [-0.0585, +0.1717] | -0.1333 [-0.2361, -0.0309] |
| bm25 | 0.5953 | 0.5967 | — | — | — |
| e5_small | 0.7834 | 0.7907 | — | — | — |

## recall@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.3448 | 0.3415 | — | — | — |
| mini_lm_soup | 0.3256 | 0.3114 | -0.0191 [-0.1123, +0.0750] | +0.0735 [-0.0321, +0.1815] | -0.0932 [-0.1951, +0.0086] |
| bm25 | 0.2522 | 0.2520 | — | — | — |
| e5_small | 0.4188 | 0.4270 | — | — | — |

## recall@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.5753 | 0.5833 | — | — | — |
| mini_lm_soup | 0.4951 | 0.4835 | -0.0802 [-0.1790, +0.0185] | +0.0454 [-0.0463, +0.1432] | -0.1744 [-0.2840, -0.0710] |
| bm25 | 0.4497 | 0.4524 | — | — | — |
| e5_small | 0.6694 | 0.6756 | — | — | — |

## recall@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6895 | 0.6971 | — | — | — |
| mini_lm_soup | 0.5790 | 0.5757 | -0.1105 [-0.2037, -0.0241] | +0.0676 [-0.0262, +0.1664] | -0.1512 [-0.2531, -0.0525] |
| bm25 | 0.5114 | 0.5144 | — | — | — |
| e5_small | 0.7302 | 0.7287 | — | — | — |

## sec_hit@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6296 | 0.6152 | — | — | — |
| mini_lm_soup | 0.5741 | 0.5464 | -0.0556 [-0.2037, +0.0926] | +0.0926 [-0.0741, +0.2593] | -0.1481 [-0.2963, +0.0000] |
| bm25 | 0.4815 | 0.4821 | — | — | — |
| e5_small | 0.7222 | 0.7308 | — | — | — |

## sec_hit@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7963 | 0.8246 | — | — | — |
| mini_lm_soup | 0.7593 | 0.7630 | -0.0370 [-0.1481, +0.0741] | +0.0000 [-0.0926, +0.1111] | -0.1296 [-0.2407, -0.0370] |
| bm25 | 0.7593 | 0.7621 | — | — | — |
| e5_small | 0.8889 | 0.8879 | — | — | — |

## sec_hit@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.8704 | 0.8934 | — | — | — |
| mini_lm_soup | 0.8333 | 0.8438 | -0.0370 [-0.1296, +0.0556] | +0.0741 [-0.0370, +0.1852] | -0.0741 [-0.1667, +0.0185] |
| bm25 | 0.7593 | 0.7621 | — | — | — |
| e5_small | 0.9074 | 0.9036 | — | — | — |

## sec_mrr@10

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7257 | 0.7260 | — | — | — |
| mini_lm_soup | 0.6822 | 0.6687 | -0.0435 [-0.1451, +0.0597] | +0.0695 [-0.0406, +0.1811] | -0.1343 [-0.2354, -0.0349] |
| bm25 | 0.6127 | 0.6126 | — | — | — |
| e5_small | 0.8165 | 0.8219 | — | — | — |

## sec_recall@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.4938 | 0.4810 | — | — | — |
| mini_lm_soup | 0.4506 | 0.4269 | -0.0432 [-0.1451, +0.0586] | +0.1358 [+0.0062, +0.2685] | -0.1111 [-0.2191, -0.0031] |
| bm25 | 0.3148 | 0.3145 | — | — | — |
| e5_small | 0.5617 | 0.5689 | — | — | — |

## sec_recall@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6481 | 0.6594 | — | — | — |
| mini_lm_soup | 0.6080 | 0.6006 | -0.0401 [-0.1327, +0.0525] | +0.0154 [-0.0710, +0.1049] | -0.1512 [-0.2531, -0.0525] |
| bm25 | 0.5926 | 0.5865 | — | — | — |
| e5_small | 0.7593 | 0.7549 | — | — | — |

## sec_recall@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7500 | 0.7585 | — | — | — |
| mini_lm_soup | 0.6636 | 0.6584 | -0.0864 [-0.1636, -0.0185] | +0.0216 [-0.0833, +0.1296] | -0.1481 [-0.2438, -0.0556] |
| bm25 | 0.6420 | 0.6372 | — | — | — |
| e5_small | 0.8117 | 0.7993 | — | — | — |

## Leave-One-Document-Out Sensitivity (micro deltas)

### hit@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0790 | +0.0526 | -0.2106 |
| compliance | 46 | -0.0218 | +0.0869 | -0.1087 |
| evaluation | 37 | -0.0270 | +0.0270 | -0.1621 |
| peft-and-efficiency | 41 | -0.0244 | +0.0488 | -0.1219 |

### hit@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1053 | -0.0527 | -0.2106 |
| compliance | 46 | -0.0217 | +0.0217 | -0.1522 |
| evaluation | 37 | -0.0811 | +0.0270 | -0.1351 |
| peft-and-efficiency | 41 | -0.0976 | +0.0000 | -0.1708 |

### hit@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1053 | +0.0526 | -0.1053 |
| compliance | 46 | -0.0652 | +0.0652 | -0.0870 |
| evaluation | 37 | -0.0811 | +0.1081 | -0.0270 |
| peft-and-efficiency | 41 | -0.0488 | +0.0732 | -0.0732 |

### mrr@10

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0768 | +0.0421 | -0.1750 |
| compliance | 46 | -0.0248 | +0.0715 | -0.1103 |
| evaluation | 37 | -0.0368 | +0.0473 | -0.1319 |
| peft-and-efficiency | 41 | -0.0365 | +0.0545 | -0.1217 |

### recall@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0360 | +0.0912 | -0.1105 |
| compliance | 46 | -0.0008 | +0.0971 | -0.0660 |
| evaluation | 37 | -0.0099 | +0.0532 | -0.1225 |
| peft-and-efficiency | 41 | -0.0325 | +0.0488 | -0.0813 |

### recall@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0921 | +0.0163 | -0.2302 |
| compliance | 46 | -0.0508 | +0.0641 | -0.1504 |
| evaluation | 37 | -0.0901 | +0.0460 | -0.1554 |
| peft-and-efficiency | 41 | -0.0935 | +0.0508 | -0.1667 |

### recall@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1350 | +0.0610 | -0.1885 |
| compliance | 46 | -0.0971 | +0.0794 | -0.1449 |
| evaluation | 37 | -0.1118 | +0.0738 | -0.1104 |
| peft-and-efficiency | 41 | -0.1016 | +0.0549 | -0.1606 |

### sec_hit@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1053 | +0.0526 | -0.2369 |
| compliance | 46 | -0.0435 | +0.1304 | -0.1087 |
| evaluation | 37 | -0.0541 | +0.0810 | -0.1622 |
| peft-and-efficiency | 41 | -0.0244 | +0.0976 | -0.0975 |

### sec_hit@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0789 | -0.0263 | -0.1579 |
| compliance | 46 | +0.0000 | +0.0000 | -0.1304 |
| evaluation | 37 | -0.0270 | +0.0270 | -0.0811 |
| peft-and-efficiency | 41 | -0.0488 | +0.0000 | -0.1463 |

### sec_hit@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0790 | +0.0526 | -0.0790 |
| compliance | 46 | -0.0217 | +0.0652 | -0.0869 |
| evaluation | 37 | -0.0270 | +0.1081 | -0.0270 |
| peft-and-efficiency | 41 | -0.0244 | +0.0732 | -0.0975 |

### sec_mrr@10

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0866 | +0.0433 | -0.1837 |
| compliance | 46 | -0.0275 | +0.0870 | -0.1124 |
| evaluation | 37 | -0.0375 | +0.0691 | -0.1337 |
| peft-and-efficiency | 41 | -0.0267 | +0.0744 | -0.1137 |

### sec_recall@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0570 | +0.1272 | -0.1491 |
| compliance | 46 | -0.0290 | +0.1703 | -0.0761 |
| evaluation | 37 | -0.0496 | +0.1171 | -0.1487 |
| peft-and-efficiency | 41 | -0.0406 | +0.1220 | -0.0813 |

### sec_recall@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0614 | +0.0131 | -0.1842 |
| compliance | 46 | -0.0145 | +0.0181 | -0.1449 |
| evaluation | 37 | -0.0496 | +0.0180 | -0.1216 |
| peft-and-efficiency | 41 | -0.0407 | +0.0122 | -0.1545 |

### sec_recall@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1271 | +0.0220 | -0.1710 |
| compliance | 46 | -0.0688 | +0.0254 | -0.1521 |
| evaluation | 37 | -0.0766 | +0.0315 | -0.0991 |
| peft-and-efficiency | 41 | -0.0772 | +0.0081 | -0.1667 |

## Failure Categories (mutually exclusive, one leaf per query)

| Category | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| empty_ranking | 0 | 0 | 0 | 0 |
| exact_relevant_chunk_top1 | 31 | 29 | 26 | 37 |
| relevant_section_unlabeled_chunk_top1 | 3 | 2 | 0 | 2 |
| relevant_chunk_below_top1 | 15 | 17 | 17 | 13 |
| relevant_section_below_top1 | 0 | 0 | 1 | 1 |
| wrong_section_same_document | 1 | 1 | 2 | 0 |
| wrong_document | 4 | 5 | 8 | 1 |
| no_relevant_result_top10 | 5 | 6 | 10 | 1 |

> `no_relevant_result_top10` is the aggregate of `wrong_section_same_document` + `wrong_document`.

## Regression Counts (candidate ranks first relevant item worse)

| Comparison | Chunk regressions | Section regressions |
|---|:---:|:---:|
| mini_lm_soup vs mini_lm_frozen | 13 | 12 |
| mini_lm_soup vs bm25 | 20 | 19 |
| mini_lm_soup vs e5_small | 8 | 8 |

> A sibling-first result (`relevant_section_unlabeled_chunk_top1`) is a chunk-level miss but a section-level hit and never counts as a section regression.

> The 18 original overlap labels were audited against training-chunk text on 2026-10-31 (`docs/EVALUATION_V2_OVERLAP_AUDIT.md`): 15 confirmed and 3 reclassified as primary with owner approval. The subset tables below use the final 39 primary / 15 overlap split.

## Overlap Subset (n=15)

| Metric | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| hit@1 | 0.4667 | 0.5333 | 0.6667 | 0.5333 |
| hit@3 | 0.8000 | 0.7333 | 0.8000 | 0.8667 |
| hit@5 | 0.8667 | 0.8667 | 0.8000 | 0.8667 |
| mrr@10 | 0.6389 | 0.6667 | 0.7280 | 0.7067 |
| recall@1 | 0.1689 | 0.2167 | 0.2522 | 0.2078 |
| recall@3 | 0.3822 | 0.3211 | 0.3800 | 0.3878 |
| recall@5 | 0.4433 | 0.4067 | 0.4189 | 0.5400 |
| sec_hit@1 | 0.5333 | 0.5333 | 0.6667 | 0.6667 |
| sec_hit@3 | 0.8667 | 0.8000 | 0.8000 | 0.9333 |
| sec_hit@5 | 0.8667 | 0.8667 | 0.8000 | 0.9333 |
| sec_mrr@10 | 0.6889 | 0.6833 | 0.7280 | 0.8111 |
| sec_recall@1 | 0.2222 | 0.2333 | 0.2778 | 0.2889 |
| sec_recall@3 | 0.4444 | 0.3778 | 0.4444 | 0.5778 |
| sec_recall@5 | 0.5111 | 0.4111 | 0.5556 | 0.6667 |

## Primary Subset (n=39)

| Metric | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| hit@1 | 0.6154 | 0.5385 | 0.4103 | 0.7436 |
| hit@3 | 0.7692 | 0.6923 | 0.6667 | 0.8718 |
| hit@5 | 0.8718 | 0.7692 | 0.6923 | 0.8718 |
| mrr@10 | 0.7135 | 0.6437 | 0.5443 | 0.8129 |
| recall@1 | 0.4124 | 0.3675 | 0.2521 | 0.5000 |
| recall@3 | 0.6496 | 0.5620 | 0.4765 | 0.7778 |
| recall@5 | 0.7842 | 0.6453 | 0.5470 | 0.8034 |
| sec_hit@1 | 0.6667 | 0.5897 | 0.4103 | 0.7436 |
| sec_hit@3 | 0.7692 | 0.7436 | 0.7436 | 0.8718 |
| sec_hit@5 | 0.8718 | 0.8205 | 0.7436 | 0.8974 |
| sec_mrr@10 | 0.7398 | 0.6818 | 0.5684 | 0.8186 |
| sec_recall@1 | 0.5983 | 0.5342 | 0.3291 | 0.6667 |
| sec_recall@3 | 0.7265 | 0.6966 | 0.6496 | 0.8291 |
| sec_recall@5 | 0.8419 | 0.7607 | 0.6752 | 0.8675 |

## Section-Cluster Bootstrap Decision

- Query-occupied sections: 73 (single-query: 70, multi-query: 3; multi-query fraction 0.0411, threshold 0.3)
- Decision: **skipped: most query-occupied sections contain a single query, so cluster resampling degenerates to query-level resampling**.

