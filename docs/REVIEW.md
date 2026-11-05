# Experiment Review — Soup RAG Retrieval Fine-Tuning

> [!NOTE]
> **Status:** Updated to reflect the completed Phase 3 multi-retriever benchmark evaluation and the independent owner-authored evaluation (`human_eval_v2`). For the authoritative benchmark results, see [`RESULTS.md`](../RESULTS.md) and [`results/HUMAN_EVAL_V2_REPORT.md`](../results/HUMAN_EVAL_V2_REPORT.md). Historical Phase 3 reports are preserved on git branch [`archive/research-history`](https://github.com/harshitthek/soup-rag-prototype/blob/archive/research-history/results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md).

Concise review of the Soup embedding fine-tuning experiments in this repository.
- **Authoritative Results:** [`RESULTS.md`](../RESULTS.md) (independent 24-query owner-authored evaluation across 1,068 chunks and historical 54-query benchmark).
- **Historical Phase 3 Benchmark Report:** [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](https://github.com/harshitthek/soup-rag-prototype/blob/archive/research-history/results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md) (on branch `archive/research-history`).
- **Historical Statistical Audit:** [`results/PHASE_3_1_INTEGRITY_AUDIT.md`](https://github.com/harshitthek/soup-rag-prototype/blob/archive/research-history/results/PHASE_3_1_INTEGRITY_AUDIT.md) (on branch `archive/research-history`).
- **Reproduction Guide:** [`REPRODUCE.md`](../REPRODUCE.md).
- **Historical Reports:** Preserved on branch `archive/research-history` (`results/comparison.md` for v1 synthetic benchmark, `results/v2/comparison.md` for initial 4-retriever v2 comparison).

---

## 1. Experimental Architecture

1. **Corpus:**
   - *Core Corpus (12 docs):* Vendored with SHA256 provenance in `data/raw_docs/`; split on ATX headings, sub-split to $\le 220$-token bodies with 28-token overlap; every chunk embeds as `"{doc_name}: {heading}\n\n{body}"` (`scripts/prepare_corpus.py`).
   - *Expanded Corpus (31 docs):* 8 core training documents + 23 candidate documents (`data/training_corpus.jsonl`). The 4 held-out evaluation documents are strictly excluded from all training sets.
2. **Document Split:** Document-level separation: 8 training docs / 4 strictly held-out test docs (1,068 chunks: 761 train / 307 test).
3. **Training Data Strategies:**
   - *Exp A (Synthetic):* 1,078 synthetic queries (A-full) or 825 queries (A-matched) generated from heading/command patterns.
   - *Exp B (Diverse LLM, Core):* 825 Gemini-generated queries across 4 intent classes (how-to, conceptual, parameter, troubleshooting) over the 8 core training docs.
   - *Exp C-matched (Expanded, Unstratified):* 825 queries over 31 documents (conceptual-heavy candidate pool, 565 positive chunks).
   - *Exp C-matched-balanced (Expanded, Stratified):* 825 queries over 31 documents with stratified intent sampling matching Experiment B's distribution (720 positive chunks).
   - *Exp C-full (Expanded, Uncurated):* 2,257 queries across 31 documents (6,771 triplets, 1,522 positive chunks).
4. **Hard Negative Mining:** Dense cosine mining using frozen `all-MiniLM-L6-v2` with strict section-level deduplication to prevent false negatives from sibling paragraphs (`scripts/mine_hard_negatives.py`).
5. **Fine-Tuning:** Native Soup embedding trainer (`soup train --config <config.yaml>`, `task: embedding`), TripletMarginLoss ($m=0.5$), LoRA $r=16, \alpha=32$ on query and value projections (147,456 trainable parameters = 0.65% of base), lr 2e-5, seed 42. Base model revision pinned to `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
6. **Benchmark Evaluation:** Evaluated against 54 owner-approved manual queries (`data/manual_queries.jsonl`) with multi-chunk relevance labels over 4 held-out documents. Metrics include Hit@K, Recall@K, MRR@10, and paired document-stratified percentile bootstrap intervals (10,000 resamples, seed 42).

---

## 2. Key Experimental Decisions

- **Document-Level Split:** Random chunk splitting leaks authorial style, identical headings, and adjacent content between train and test. A strict document-level split prevents leakage and tests true generalization to unseen documentation files.
- **Consistent Heading Prefixing:** Passage text prepends hierarchical heading context (`"{doc_name}: {heading}\n\n{body}"`) identically in negative mining, training, and evaluation inference.
- **Triplet Margin Loss with Mined Hard Negatives:** In-batch negatives (InfoNCE) on small domain corpora pose a high risk of false-negative collisions. Triplet loss with section-deduplicated negatives guarantees clean negative supervision.
- **Matched-Budget Experimental Design:** Experiments A-matched, B, C-matched, and C-matched-balanced share an identical budget of 825 queries and 1,857 optimizer updates (3 epochs), isolating the effects of query diversity, corpus scope, and intent balancing.

---

## 3. Phase 3 Multi-Retriever Benchmark Results

The 9-retriever benchmark on the 54 owner-approved manual evaluation queries:

| ID | Retriever | Description | Hit@1 | Recall@3 | MRR@10 |
|---|---|---|---:|---:|---:|
| **R1** | BM25 | Fixed lexical baseline (`rank_bm25`) | 0.4815 | 0.4497 | 0.5953 |
| **R2** | Frozen MiniLM | `all-MiniLM-L6-v2` (frozen base) | 0.5741 | 0.5753 | 0.6928 |
| **R3** | **Frozen E5-small** | `intfloat/e5-small-v2` (frozen baseline) | **0.6852** | **0.6694** | **0.7834** |
| **R4** | A-full | Baseline Soup LoRA (1,078 synthetic queries) | 0.5370 | 0.4951 | 0.6501 |
| **R5** | A-matched | MiniLM + Soup LoRA (825 synthetic queries) | 0.5185 | 0.5228 | 0.6554 |
| **R6** | B | MiniLM + Soup LoRA (825 diverse LLM queries) | 0.6481 | 0.6015 | 0.7434 |
| **R7** | C-matched | MiniLM + Soup LoRA (31 docs, unstratified queries) | 0.6111 | 0.5090 | 0.6844 |
| **R8** | **C-matched-balanced** | MiniLM + Soup LoRA (31 docs, balanced queries) | **0.6852** | 0.5722 | 0.7681 |
| **R9** | C-full | MiniLM + Soup LoRA (31 docs, 2,257 uncurated queries) | 0.5556 | 0.4951 | 0.6310 |

### Key Findings & Insights

1. **Frozen E5-small vs Fine-Tuned MiniLM:** Frozen `intfloat/e5-small-v2` achieved the highest observed score on the benchmark (0.7834 MRR@10, 0.6694 Recall@3). Comparing `C-matched-balanced` against E5-small yields an observed MRR@10 delta of -0.0153 (95% bootstrap CI `[-0.1044, +0.0740]`), which includes zero; the benchmark does not establish a clear difference or general superiority over `C-matched-balanced`.
2. **MiniLM Adapter Observations & Selection Bias:** `C-matched-balanced` achieved the highest observed MRR@10 among the five evaluated MiniLM adapters on this benchmark (0.7681 MRR@10, 0.6852 Hit@1). This is an exploratory result subject to selection bias from choosing the maximum across five candidates on the same 54 queries; independent validation is required. Its observed difference over frozen MiniLM is +0.0753 MRR@10, but its 95% bootstrap interval `[-0.0135, +0.1652]` includes zero. On the subsequent independent 24-query benchmark (`human_eval_v2`), the `C-matched-balanced` adapter was evaluated against frozen MiniLM, but all 5 MiniLM adapters were not re-evaluated against each other on that benchmark.
3. **Diverse LLM Queries vs Heuristic Synthetic Queries (B vs A-matched):** In the matched comparison, diverse LLM-generated training queries (Experiment B: 0.7434 MRR@10) outperformed heuristic synthetic queries (Experiment A-matched: 0.6554 MRR@10; delta +0.0879 MRR@10, 95% bootstrap CI `[+0.0221, +0.1561]`). While intervals strictly exclude zero, the experiment simultaneously changes natural language query generation and intent distribution; the difference cannot be attributed exclusively to linguistic diversity. For the independent 24-query evaluation (`human_eval_v2`), the project owner confirmed that all 24 queries were written manually without AI assistance, and that the earlier 12-query draft was withdrawn; it does not prove that Gemini-generated queries are inherently superior or that linguistic diversity alone caused the original improvement. Furthermore, AI assistance was used in evaluation query authoring on the 54-query benchmark while B used Gemini training queries, introducing potential phrasing alignment. Heuristic synthetic adapters (`A-full` at 0.6501, `A-matched` at 0.6554) both performed worse than frozen MiniLM (0.6928).
4. **Corpus Expansion and Data Regimes:** In the expanded corpus comparison under matched update budget (31 vs 8 docs), `C-matched-balanced` achieved a higher observed point estimate than Experiment B (0.7681 vs 0.7434 MRR@10; delta +0.0247), but its 95% bootstrap interval `[-0.0217, +0.0682]` includes zero. Comparing `C-matched-balanced` against `C-matched`, observed MRR@10 (+0.0837, 95% CI `[+0.0164, +0.1592]`) and Recall@3 (+0.0633, 95% CI `[+0.0231, +0.1096]`) intervals exclude zero, but the comparison simultaneously changes query sampling and positive chunk coverage (720 vs 565 chunks). Meanwhile, the complete uncurated training regime (`C-full`, 2,257 queries, 5,079 updates) resulted in substantially lower observed performance (0.6310 MRR@10), reflecting the complete C-full training regime rather than isolating single variables.

---

## 4. Known Limitations

- **Benchmark Size & Scoped Bootstrap:** 54 manual queries across 4 held-out documents (`adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`). Four documents are insufficient for population-level generalization claims; all bootstrap intervals are exploratory and scoped to the four fixed document clusters.
- **Selection Bias on Candidate Adapters:** Choosing the top-scoring adapter across five candidates on the same 54 queries introduces selection bias; independent validation is required.
- **AI Assistance & Phrasing Alignment:** Because Gemini generated the training queries for Experiments B and C, and AI assistance was used in drafting the evaluation queries, phrasing alignment is an uncontrolled factor in the historical 54-query benchmark. For the independent evaluation benchmark (`human_eval_v2`), the project owner confirmed that all 24 queries were written manually without AI assistance, and the previous 12-query draft was withdrawn. Relevance targets were identified directly by the project owner and mechanically mapped to canonical chunk IDs; no independent third-party annotation was conducted. See [`RESEARCH_INTEGRITY.md`](RESEARCH_INTEGRITY.md) for full provenance disclosures.
- **Document-Localized Effects:** Adapter improvements are predominantly concentrated in `adapters-and-governance` (MRR diff from Frozen MiniLM: C-matched-balanced $+0.2781$, B $+0.2448$) and `evaluation` (C-matched-balanced $+0.0402$, B $+0.0303$). On `peft-and-efficiency`, C-matched-balanced ties MiniLM ($0.7333$), and on `compliance`, observed scores are lower ($-0.1333$). When `adapters-and-governance` is dropped, neither fine-tuned adapter outperforms frozen MiniLM.
- **Retrieval vs Downstream RAG:** Evaluation measures ranking and retrieval accuracy of documentation passages. It does not measure generative response quality, synthesis faithfulness, or hallucination rates in an end-to-end RAG system.
