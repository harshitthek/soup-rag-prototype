# Hybrid Retrieval Benchmark: BM25, E5-Small, and Reciprocal Rank Fusion

## Executive Summary

This evaluation benchmarks four retrieval systems on the frozen 54 manual evaluation queries (`data/manual_queries.jsonl`) over the 1,068-chunk canonical documentation corpus (`data/corpus.jsonl`):

1. **Original BM25**: Baseline lexical search using whitespace tokenization.
2. **Improved BM25**: Lexical search with domain-aware regex tokenization preserving CLI flags, code identifiers, dotted modules, paths, and version strings.
3. **Frozen E5-small**: Dense retrieval baseline (`intfloat/e5-small-v2`, 384d, mean pooling, frozen).
4. **Hybrid RRF**: Reciprocal Rank Fusion combining Improved BM25 and Frozen E5-small with fixed parameter $k=60$ and equal weights ($1.0 : 1.0$), without hyperparameter tuning.

### Key Empirical Findings

- **Hybrid RRF establishes the new state of the art on the benchmark**: MRR@10 reaches **0.8552** and Hit@1 reaches **77.78%**, outperforming both individual constituents (**+0.0719 MRR@10** over Frozen E5-small and **+0.0841 MRR@10** over Improved BM25).
- **Complementary Retrieval Strengths**: Improved BM25 excels on precise parameter names, CLI flags, and configuration fields (where dense embeddings encounter vocabulary drift), while Frozen E5-small excels on semantic questions and natural language phrasing. RRF fusion successfully synthesizes these strengths without learned weights.
- **Section-level Retrieval**: Sec-Hit@1 reaches **81.48%** and Sec-MRR@10 reaches **0.8771**.
- **Human-Authored Diagnostic Queries**: Preliminary rankings for all 12 independent project-owner-authored queries have been generated and quarantined outside the repository workspace (`~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json`). In accordance with research integrity and double-blind annotation protocols, metrics remain strictly uncomputed pending manual relevance verification.

---

## Full Metric Comparison

| Metric | Original BM25 (Whitespace) | Improved BM25 (Domain-Aware) | Frozen E5-small (Dense) | Hybrid RRF (BM25 + E5) | Delta vs E5-small | Delta vs Orig BM25 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hit@1** | 0.4815 (48.1%) | 0.6481 (64.8%) | 0.6852 (68.5%) | **0.7778 (77.8%)** | +0.0926 | +0.2963 |
| **Recall@1** | 0.2522 | 0.4043 | 0.4188 | **0.5046** | +0.0858 | +0.2525 |
| **Hit@3** | 0.7037 (70.4%) | 0.8889 (88.9%) | 0.8704 (87.0%) | **0.9074 (90.7%)** | +0.0370 | +0.2037 |
| **Recall@3** | 0.4497 | 0.7065 | 0.6694 | **0.7466** | +0.0772 | +0.2969 |
| **Hit@5** | 0.7222 (72.2%) | 0.9074 (90.7%) | 0.8704 (87.0%) | **0.9630 (96.3%)** | +0.0926 | +0.2407 |
| **Recall@5** | 0.5114 | 0.7719 | 0.7302 | **0.8228** | +0.0926 | +0.3114 |
| **MRR@10** | 0.5953 | 0.7712 | 0.7834 | **0.8552** | +0.0719 | +0.2599 |
| **Sec-Hit@1** | 0.4815 (48.1%) | 0.6852 (68.5%) | 0.7222 (72.2%) | **0.8148 (81.5%)** | +0.0926 | +0.3333 |
| **Sec-Recall@1** | 0.3148 | 0.5031 | 0.5617 | **0.6451** | +0.0833 | +0.3302 |
| **Sec-Hit@3** | 0.7593 (75.9%) | 0.8889 (88.9%) | 0.8889 (88.9%) | **0.9074 (90.7%)** | +0.0185 | +0.1481 |
| **Sec-Recall@3** | 0.5926 | 0.7870 | 0.7593 | **0.8179** | +0.0586 | +0.2253 |
| **Sec-Hit@5** | 0.7593 (75.9%) | 0.9074 (90.7%) | 0.9074 (90.7%) | **0.9630 (96.3%)** | +0.0556 | +0.2037 |
| **Sec-Recall@5** | 0.6420 | 0.8210 | 0.8117 | **0.8765** | +0.0648 | +0.2346 |
| **Sec-MRR@10** | 0.6127 | 0.7897 | 0.8165 | **0.8771** | +0.0605 | +0.2643 |
| **Latency (54 queries)** | 0.077s | 0.102s | 15.55s | 15.68s | +0.14s | - |

---

## Functional Breakdown by Query Type

| Query Archetype | Count | Orig BM25 MRR | Impr BM25 MRR | E5-small MRR | Hybrid RRF MRR | Best Single System | Hybrid vs Best Single |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `command_detail` | 6 | 0.8889 | 0.9167 | 0.8056 | **0.8889** | Impr BM25 (0.9167) | -0.0278 |
| `conceptual` | 14 | 0.5221 | 0.7246 | 0.8912 | **0.9286** | E5-small (0.8912) | +0.0374 |
| `config_behavior` | 10 | 0.3893 | 0.8333 | 0.8600 | **0.9500** | E5-small (0.8600) | +0.0900 |
| `how_to` | 13 | 0.6880 | 0.6667 | 0.6745 | **0.7308** | E5-small (0.6745) | +0.0563 |
| `relationship` | 4 | 0.5417 | 0.8750 | 0.8750 | **1.0000** | Impr BM25 (0.8750) | +0.1250 |
| `troubleshooting` | 7 | 0.6429 | 0.7857 | 0.5893 | **0.6929** | Impr BM25 (0.7857) | -0.0929 |

### Focus Group: Parameter, Configuration & CLI Queries

Aggregating `command_detail`, `config_behavior`, and `how_to` queries (29 queries):

- **Original BM25**: MRR@10 = 0.6266, Hit@1 = 55.2%, Recall@5 = 50.4%
- **Improved BM25**: MRR@10 = 0.7759, Hit@1 = 65.5%, Recall@5 = 82.0%
- **Frozen E5-small**: MRR@10 = 0.7656, Hit@1 = 65.5%, Recall@5 = 72.2%
- **Hybrid RRF**: MRR@10 = **0.8391**, Hit@1 = **75.9%**, Recall@5 = **83.7%**

On parameter and CLI queries, Improved BM25 already surpassed E5-small (MRR 0.7759 vs 0.7656). Fusing them via RRF boosts performance further to **0.8391 MRR@10** and **75.9% Hit@1**.

---

## Complementary Analysis: BM25 vs E5-Small

- **Queries where both systems hit Top-1**: 27 queries.
- **Queries where Improved BM25 succeeds at Top-1 but E5 fails**: 8 queries.
- **Queries where E5 succeeds at Top-1 but Improved BM25 fails**: 10 queries.
- **Queries where Hybrid RRF strictly improves rank over both individual systems**: 3 queries.
- **Queries where Hybrid RRF strictly hurts rank below both individual systems**: 1 queries.

### Queries Where Improved BM25 Hits Top 1 but E5 Fails

| Query ID | Query | BM25 MRR | E5 MRR | Hybrid MRR | Hybrid Top 1? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `manual_001` | why does soup lock check exit with code 3... | 1.00 | 0.50 | 0.25 | No (0.25) |
| `manual_002` | How do I bisect training checkpoints when an eval regre... | 1.00 | 0.14 | 1.00 | YES |
| `manual_008` | build a control vector from positive and negative promp... | 1.00 | 0.50 | 1.00 | YES |
| `manual_010` | soup registry diff output... | 1.00 | 0.50 | 1.00 | YES |
| `manual_021` | publish a model to huggingface with my own model card... | 1.00 | 0.12 | 0.50 | No (0.50) |
| `manual_022` | generated ci workflow steps... | 1.00 | 0.50 | 1.00 | YES |
| `manual_038` | custom eval jsonl fields for exact and regex scoring... | 1.00 | 0.50 | 1.00 | YES |
| `manual_050` | can dora and vera be enabled together... | 1.00 | 0.50 | 1.00 | YES |

### Queries Where Frozen E5 Hits Top 1 but Improved BM25 Fails

| Query ID | Query | BM25 MRR | E5 MRR | Hybrid MRR | Hybrid Top 1? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `manual_013` | can I merge adapters whose licenses conflict... | 0.50 | 1.00 | 1.00 | YES |
| `manual_014` | what stops a hijacked huggingface repo from being pulle... | 0.33 | 1.00 | 1.00 | YES |
| `manual_015` | what goes into a soup airgap bundle and how big can it ... | 0.50 | 1.00 | 1.00 | YES |
| `manual_020` | what ends up in the generated model card... | 0.20 | 1.00 | 0.50 | No (0.50) |
| `manual_023` | which expectation checks can go in expectations.yaml... | 0.50 | 1.00 | 1.00 | YES |
| `manual_026` | generate an eval suite from my training data... | 0.50 | 1.00 | 1.00 | YES |
| `manual_033` | Task accuracy went up but MMLU dropped, should I ship?... | 0.50 | 1.00 | 1.00 | YES |
| `manual_034` | noise floor flag effect on ship verdict... | 0.50 | 1.00 | 1.00 | YES |
| `manual_043` | how does longlora shifted sparse attention work... | 0.50 | 1.00 | 1.00 | YES |
| `manual_046` | Can I add fresh layers to a Llama model and only train ... | 0.50 | 1.00 | 0.50 | No (0.50) |

---

## Failure Category Distribution Across Systems

| Failure Category | Orig BM25 | Impr BM25 | E5-small | Hybrid RRF |
| :--- | :---: | :---: | :---: | :---: |
| `exact_relevant_chunk_top1` | 26 | 35 | 37 | **42** |
| `relevant_section_unlabeled_chunk_top1` | 0 | 2 | 2 | **2** |
| `relevant_chunk_below_top1` | 17 | 14 | 13 | **9** |
| `relevant_section_below_top1` | 1 | 0 | 1 | **0** |
| `wrong_section_same_document` | 2 | 0 | 0 | **0** |
| `wrong_document` | 8 | 3 | 1 | **1** |
| `empty_ranking` | 0 | 0 | 0 | **0** |

---

## Reproduction Commands

To reproduce the full 4-way evaluation and regenerate all hybrid artifacts:
```bash
./.venv/bin/python scripts/evaluate_hybrid.py
```
