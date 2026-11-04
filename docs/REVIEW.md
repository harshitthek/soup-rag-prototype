# Experiment Review — Soup RAG Retrieval Fine-Tuning

> [!NOTE]
> **Status:** Updated to reflect the completed Phase 3 multi-retriever benchmark evaluation. For the comprehensive evaluation report, see [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](../results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md) and [`results/PHASE_3_1_INTEGRITY_AUDIT.md`](../results/PHASE_3_1_INTEGRITY_AUDIT.md).

Concise review of the Soup embedding fine-tuning experiments in this repository.
- **Authoritative Phase 3 Benchmark:** [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](../results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md) (9-retriever benchmark on 54 owner-approved queries).
- **Integrity & Statistical Audit:** [`results/PHASE_3_1_INTEGRITY_AUDIT.md`](../results/PHASE_3_1_INTEGRITY_AUDIT.md).
- **Reproduction Guide:** [`REPRODUCE.md`](../REPRODUCE.md).
- **Historical Reports:** `../results/comparison.md` (v1 synthetic benchmark) and `../results/v2/comparison.md` (initial 4-retriever v2 comparison).

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

1. **Negative Result on Pre-trained vs Fine-Tuned:** Fine-tuning MiniLM did not outperform frozen E5-small. Frozen `intfloat/e5-small-v2` achieved the highest ranking quality overall (0.7834 MRR@10, 0.6694 Recall@3). Choosing a stronger out-of-the-box encoder provided higher retrieval gains than domain fine-tuning a smaller encoder.
2. **Query Diversity Overcomes Template Overfitting:** The baseline adapter `A-full` (0.6501 MRR@10) and `A-matched` (0.6554 MRR@10) degraded performance relative to frozen MiniLM (0.6928 MRR@10). Replacing synthetic template queries with diverse LLM-generated queries (Experiment B: 0.7434 MRR@10) yielded a $+0.0880$ MRR@10 improvement over synthetic queries and $+0.0506$ over frozen MiniLM.
3. **Intent Balancing & Corpus Scope:** `C-matched-balanced` achieved the highest performance among MiniLM adapters (0.7681 MRR@10, matching E5-small on Hit@1 at 0.6852). However, uncurated corpus scaling (`C-full`: 0.6310 MRR@10) severely degraded retrieval, underscoring that data quality and coverage curation are critical when expanding domain corpora.

---

## 4. Known Limitations

- **Benchmark Size:** 54 manual queries across 4 held-out documents (`adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`). Four documents are insufficient for population-level generalization claims; all bootstrap intervals are exploratory.
- **Document-Localized Effects:** Adapter improvements are predominantly concentrated in `adapters-and-governance` (MRR diff from Frozen MiniLM: C-matched-balanced $+0.2781$, B $+0.2448$) and `evaluation` (C-matched-balanced $+0.0402$, B $+0.0303$). On `peft-and-efficiency`, C-matched-balanced ties MiniLM ($0.7333$), and on `compliance`, observed scores are lower ($-0.1333$).
- **Retrieval vs Downstream RAG:** Evaluation measures ranking and retrieval accuracy of documentation passages. It does not measure generative response quality, synthesis faithfulness, or hallucination rates in an end-to-end RAG system.
