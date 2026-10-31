# Evaluation v2 — Four-Way Retrieval Comparison (Manual Queries)

**Retrievers:** mini_lm_frozen, mini_lm_soup, bm25, e5_small  
**Queries:** 54 manual queries (owner-approved; drafted by Qoder)  
**Corpus fingerprint:** 76ab5e88af6e82bb1892296c7d3a854b722466466b6ae2fb7dc8c4831be75b2c  
**Query-set fingerprint:** 116bd4c36a6b7747…  
**Bootstrap:** 10000 resamples, seed=42, paired document-stratified percentile intervals, shared indices across retrievers.

> Four held-out documents are insufficient for population-level inference; all intervals describe uncertainty within this fixed query sample. No p-values and no significance claims are made.

## hit@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.5926 | 0.5839 | — | — | — |
| mini_lm_soup | 0.5556 | 0.5464 | -0.0370 [-0.1852, +0.1111] | +0.0741 [-0.0926, +0.2407] | -0.1296 [-0.2778, +0.0185] |
| bm25 | 0.4815 | 0.4821 | — | — | — |
| e5_small | 0.6852 | 0.6960 | — | — | — |

## hit@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7778 | 0.8054 | — | — | — |
| mini_lm_soup | 0.7222 | 0.7282 | -0.0556 [-0.1667, +0.0556] | +0.0185 [-0.1111, +0.1481] | -0.1481 [-0.2593, -0.0556] |
| bm25 | 0.7037 | 0.7116 | — | — | — |
| e5_small | 0.8704 | 0.8723 | — | — | — |

## hit@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.8704 | 0.8934 | — | — | — |
| mini_lm_soup | 0.8148 | 0.8402 | -0.0556 [-0.1481, +0.0370] | +0.0926 [-0.0185, +0.2037] | -0.0556 [-0.1481, +0.0370] |
| bm25 | 0.7222 | 0.7272 | — | — | — |
| e5_small | 0.8704 | 0.8723 | — | — | — |

## mrr@10

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7021 | 0.7052 | — | — | — |
| mini_lm_soup | 0.6686 | 0.6705 | -0.0335 [-0.1302, +0.0641] | +0.0702 [-0.0465, +0.1870] | -0.1148 [-0.2124, -0.0194] |
| bm25 | 0.5984 | 0.5999 | — | — | — |
| e5_small | 0.7834 | 0.7907 | — | — | — |

## recall@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.3417 | 0.3323 | — | — | — |
| mini_lm_soup | 0.3133 | 0.3064 | -0.0284 [-0.1009, +0.0401] | +0.0704 [-0.0346, +0.1784] | -0.0840 [-0.1765, +0.0056] |
| bm25 | 0.2429 | 0.2442 | — | — | — |
| e5_small | 0.3972 | 0.3986 | — | — | — |

## recall@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.5691 | 0.5769 | — | — | — |
| mini_lm_soup | 0.4827 | 0.4784 | -0.0864 [-0.1775, +0.0000] | +0.0485 [-0.0463, +0.1488] | -0.1713 [-0.2716, -0.0772] |
| bm25 | 0.4343 | 0.4381 | — | — | — |
| e5_small | 0.6540 | 0.6536 | — | — | — |

## recall@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6741 | 0.6829 | — | — | — |
| mini_lm_soup | 0.5667 | 0.5706 | -0.1074 [-0.1954, -0.0250] | +0.0645 [-0.0355, +0.1648] | -0.1574 [-0.2485, -0.0694] |
| bm25 | 0.5022 | 0.5066 | — | — | — |
| e5_small | 0.7241 | 0.7222 | — | — | — |

## sec_hit@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6481 | 0.6344 | — | — | — |
| mini_lm_soup | 0.5926 | 0.5776 | -0.0556 [-0.1852, +0.0741] | +0.1111 [-0.0556, +0.2778] | -0.1296 [-0.2778, +0.0185] |
| bm25 | 0.4815 | 0.4821 | — | — | — |
| e5_small | 0.7222 | 0.7308 | — | — | — |

## sec_hit@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7963 | 0.8246 | — | — | — |
| mini_lm_soup | 0.7778 | 0.7943 | -0.0185 [-0.1296, +0.0926] | +0.0185 [-0.0926, +0.1296] | -0.1111 [-0.2037, -0.0185] |
| bm25 | 0.7593 | 0.7621 | — | — | — |
| e5_small | 0.8889 | 0.8879 | — | — | — |

## sec_hit@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.8704 | 0.8934 | — | — | — |
| mini_lm_soup | 0.8519 | 0.8751 | -0.0185 [-0.0926, +0.0556] | +0.0926 [-0.0185, +0.2037] | -0.0556 [-0.1481, +0.0370] |
| bm25 | 0.7593 | 0.7621 | — | — | — |
| e5_small | 0.9074 | 0.9036 | — | — | — |

## sec_mrr@10

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7349 | 0.7356 | — | — | — |
| mini_lm_soup | 0.7007 | 0.7000 | -0.0342 [-0.1286, +0.0584] | +0.0849 [-0.0278, +0.1996] | -0.1158 [-0.2145, -0.0212] |
| bm25 | 0.6158 | 0.6158 | — | — | — |
| e5_small | 0.8165 | 0.8219 | — | — | — |

## sec_recall@1

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.4938 | 0.4749 | — | — | — |
| mini_lm_soup | 0.4414 | 0.4251 | -0.0525 [-0.1389, +0.0247] | +0.1358 [+0.0062, +0.2654] | -0.1019 [-0.2037, -0.0093] |
| bm25 | 0.3056 | 0.3067 | — | — | — |
| e5_small | 0.5432 | 0.5437 | — | — | — |

## sec_recall@3

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.6481 | 0.6594 | — | — | — |
| mini_lm_soup | 0.5988 | 0.5988 | -0.0494 [-0.1358, +0.0340] | +0.0154 [-0.0710, +0.1111] | -0.1512 [-0.2438, -0.0679] |
| bm25 | 0.5833 | 0.5787 | — | — | — |
| e5_small | 0.7500 | 0.7392 | — | — | — |

## sec_recall@5

| Retriever | Micro | Macro | Δ vs mini_lm_frozen [95% CI] | Δ vs bm25 [95% CI] | Δ vs e5_small [95% CI] |
|---|:---:|:---:|:---:|:---:|:---:|
| mini_lm_frozen | 0.7407 | 0.7507 | — | — | — |
| mini_lm_soup | 0.6543 | 0.6566 | -0.0864 [-0.1543, -0.0216] | +0.0216 [-0.0864, +0.1358] | -0.1481 [-0.2377, -0.0586] |
| bm25 | 0.6327 | 0.6294 | — | — | — |
| e5_small | 0.8025 | 0.7915 | — | — | — |

## Leave-One-Document-Out Sensitivity (micro deltas)

### hit@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0790 | +0.0789 | -0.1843 |
| compliance | 46 | -0.0435 | +0.0869 | -0.1087 |
| evaluation | 37 | -0.0270 | +0.0540 | -0.1351 |
| peft-and-efficiency | 41 | +0.0000 | +0.0732 | -0.0975 |

### hit@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0790 | -0.0264 | -0.1843 |
| compliance | 46 | -0.0217 | +0.0217 | -0.1522 |
| evaluation | 37 | -0.0541 | +0.0540 | -0.1081 |
| peft-and-efficiency | 41 | -0.0732 | +0.0244 | -0.1464 |

### hit@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0790 | +0.0789 | -0.0790 |
| compliance | 46 | -0.0652 | +0.0652 | -0.0870 |
| evaluation | 37 | -0.0541 | +0.1351 | +0.0000 |
| peft-and-efficiency | 41 | -0.0244 | +0.0976 | -0.0488 |

### mrr@10

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0636 | +0.0640 | -0.1487 |
| compliance | 46 | -0.0357 | +0.0679 | -0.1103 |
| evaluation | 37 | -0.0233 | +0.0698 | -0.1049 |
| peft-and-efficiency | 41 | -0.0121 | +0.0789 | -0.0973 |

### recall@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0360 | +0.0868 | -0.0842 |
| compliance | 46 | -0.0333 | +0.0826 | -0.0768 |
| evaluation | 37 | -0.0235 | +0.0486 | -0.1090 |
| peft-and-efficiency | 41 | -0.0203 | +0.0610 | -0.0691 |

### recall@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0877 | +0.0206 | -0.2127 |
| compliance | 46 | -0.0688 | +0.0569 | -0.1685 |
| evaluation | 37 | -0.0991 | +0.0505 | -0.1509 |
| peft-and-efficiency | 41 | -0.0935 | +0.0630 | -0.1545 |

### recall@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1307 | +0.0566 | -0.1842 |
| compliance | 46 | -0.1043 | +0.0649 | -0.1630 |
| evaluation | 37 | -0.1072 | +0.0693 | -0.1194 |
| peft-and-efficiency | 41 | -0.0894 | +0.0671 | -0.1606 |

### sec_hit@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1053 | +0.0789 | -0.2106 |
| compliance | 46 | -0.0652 | +0.1304 | -0.1087 |
| evaluation | 37 | -0.0540 | +0.1081 | -0.1351 |
| peft-and-efficiency | 41 | +0.0000 | +0.1220 | -0.0731 |

### sec_hit@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0526 | +0.0000 | -0.1316 |
| compliance | 46 | +0.0000 | +0.0000 | -0.1304 |
| evaluation | 37 | +0.0000 | +0.0540 | -0.0541 |
| peft-and-efficiency | 41 | -0.0244 | +0.0244 | -0.1219 |

### sec_hit@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0527 | +0.0789 | -0.0527 |
| compliance | 46 | -0.0217 | +0.0652 | -0.0869 |
| evaluation | 37 | +0.0000 | +0.1351 | +0.0000 |
| peft-and-efficiency | 41 | +0.0000 | +0.0976 | -0.0731 |

### sec_mrr@10

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0734 | +0.0652 | -0.1574 |
| compliance | 46 | -0.0384 | +0.0834 | -0.1124 |
| evaluation | 37 | -0.0240 | +0.0916 | -0.1067 |
| peft-and-efficiency | 41 | -0.0023 | +0.0988 | -0.0893 |

### sec_recall@1

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0570 | +0.1272 | -0.1228 |
| compliance | 46 | -0.0616 | +0.1595 | -0.0869 |
| evaluation | 37 | -0.0631 | +0.1171 | -0.1351 |
| peft-and-efficiency | 41 | -0.0284 | +0.1342 | -0.0691 |

### sec_recall@3

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.0614 | +0.0131 | -0.1711 |
| compliance | 46 | -0.0362 | +0.0073 | -0.1666 |
| evaluation | 37 | -0.0631 | +0.0180 | -0.1216 |
| peft-and-efficiency | 41 | -0.0407 | +0.0244 | -0.1423 |

### sec_recall@5

| Dropped doc | n kept | Δ Soup−mini_lm_frozen | Δ Soup−bm25 | Δ Soup−e5_small |
|---|:---:|:---:|:---:|:---:|
| adapters-and-governance | 38 | -0.1271 | +0.0220 | -0.1710 |
| compliance | 46 | -0.0797 | +0.0145 | -0.1631 |
| evaluation | 37 | -0.0765 | +0.0316 | -0.0991 |
| peft-and-efficiency | 41 | -0.0650 | +0.0203 | -0.1545 |

## Failure Categories (mutually exclusive, one leaf per query)

| Category | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| empty_ranking | 0 | 0 | 0 | 0 |
| exact_relevant_chunk_top1 | 32 | 30 | 26 | 37 |
| relevant_section_unlabeled_chunk_top1 | 3 | 2 | 0 | 2 |
| relevant_chunk_below_top1 | 14 | 17 | 17 | 13 |
| relevant_section_below_top1 | 0 | 0 | 1 | 1 |
| wrong_section_same_document | 1 | 1 | 2 | 0 |
| wrong_document | 4 | 4 | 8 | 1 |
| no_relevant_result_top10 | 5 | 5 | 10 | 1 |

> `no_relevant_result_top10` is the aggregate of `wrong_section_same_document` + `wrong_document`.

## Regression Counts (candidate ranks first relevant item worse)

| Comparison | Chunk regressions | Section regressions |
|---|:---:|:---:|
| mini_lm_soup vs mini_lm_frozen | 12 | 11 |
| mini_lm_soup vs bm25 | 21 | 20 |
| mini_lm_soup vs e5_small | 8 | 8 |

> A sibling-first result (`relevant_section_unlabeled_chunk_top1`) is a chunk-level miss but a section-level hit and never counts as a section regression.

## Overlap Subset (n=18)

| Metric | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| hit@1 | 0.5000 | 0.6111 | 0.6111 | 0.5556 |
| hit@3 | 0.7778 | 0.7778 | 0.7778 | 0.8333 |
| hit@5 | 0.8889 | 0.8889 | 0.7778 | 0.8333 |
| mrr@10 | 0.6574 | 0.7222 | 0.6900 | 0.7080 |
| recall@1 | 0.1870 | 0.2546 | 0.2380 | 0.2194 |
| recall@3 | 0.4111 | 0.3417 | 0.3815 | 0.3880 |
| recall@5 | 0.4898 | 0.4130 | 0.4324 | 0.5426 |
| sec_hit@1 | 0.5556 | 0.6111 | 0.6111 | 0.6667 |
| sec_hit@3 | 0.8333 | 0.8333 | 0.7778 | 0.8889 |
| sec_hit@5 | 0.8889 | 0.8889 | 0.7778 | 0.9444 |
| sec_mrr@10 | 0.6991 | 0.7361 | 0.6900 | 0.7981 |
| sec_recall@1 | 0.2407 | 0.2778 | 0.2593 | 0.2963 |
| sec_recall@3 | 0.4815 | 0.3981 | 0.4537 | 0.5648 |
| sec_recall@5 | 0.5648 | 0.4259 | 0.5463 | 0.6944 |

## Primary Subset (n=36)

| Metric | mini_lm_frozen | mini_lm_soup | bm25 | e5_small |
|---|:---:|:---:|:---:|:---:|
| hit@1 | 0.6389 | 0.5278 | 0.4167 | 0.7500 |
| hit@3 | 0.7778 | 0.6944 | 0.6667 | 0.8889 |
| hit@5 | 0.8611 | 0.7778 | 0.6944 | 0.8889 |
| mrr@10 | 0.7244 | 0.6418 | 0.5526 | 0.8211 |
| recall@1 | 0.4190 | 0.3426 | 0.2454 | 0.4861 |
| recall@3 | 0.6481 | 0.5532 | 0.4606 | 0.7870 |
| recall@5 | 0.7662 | 0.6435 | 0.5370 | 0.8148 |
| sec_hit@1 | 0.6944 | 0.5833 | 0.4167 | 0.7500 |
| sec_hit@3 | 0.7778 | 0.7500 | 0.7500 | 0.8889 |
| sec_hit@5 | 0.8611 | 0.8333 | 0.7500 | 0.8889 |
| sec_mrr@10 | 0.7529 | 0.6830 | 0.5787 | 0.8257 |
| sec_recall@1 | 0.6204 | 0.5231 | 0.3287 | 0.6667 |
| sec_recall@3 | 0.7315 | 0.6991 | 0.6481 | 0.8426 |
| sec_recall@5 | 0.8287 | 0.7685 | 0.6759 | 0.8565 |

## Section-Cluster Bootstrap Decision

- Query-occupied sections: 53 (single-query: 52, multi-query: 1; multi-query fraction 0.0189, threshold 0.3)
- Decision: **skipped: most query-occupied sections contain a single query, so cluster resampling degenerates to query-level resampling**.

