# Soup RAG Prototype: Retrieval & Embedding Fine-Tuning Experimentation

Configuration-driven RAG and dense retrieval experimentation prototype built around [Soup CLI](https://github.com/MakazhanAlpamys/Soup) technical documentation.

> [!IMPORTANT]
> **Prototype Status:** This repository is an experimental research prototype evaluating dense retrieval quality, embedding fine-tuning strategies, and alternative encoders on technical Markdown documentation. It is **not** a production-ready feature or fully integrated Soup CLI command.

---

## 1. The Use Case

Developer documentation for command-line tools and machine learning frameworks (such as Soup) presents unique retrieval challenges:
- **High Lexical Overlap:** Distinct commands share common terminology (`yaml`, `train`, `lora`, `quantization`, `checkpoint`, `eval`).
- **Hierarchical Option Syntax:** Nested sub-commands, global flags, and configuration schemas look syntactically similar across different feature areas.
- **Boilerplate Distractors:** Documentation files frequently repeat standard headers, common options, and setup recipes, confounding generic off-the-shelf retrieval models.

This prototype investigates:
1. Whether parameter-efficient fine-tuning (LoRA) of a lightweight embedding model (`sentence-transformers/all-MiniLM-L6-v2`) via Soup's native `task: embedding` training path improves retrieval accuracy over held-out technical documentation.
2. How synthetic template-based training queries compare against diverse LLM-generated training queries across distinct user intent classes.
3. How fine-tuned lightweight models compare against stronger off-the-shelf frozen encoders (`intfloat/e5-small-v2`) and classical lexical retrieval (BM25).

---

## 2. Implemented Architecture & Pipeline

The repository implements a modular, configuration-driven retrieval experimentation pipeline:

```
┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│  1. Document Ingestion  │ ──> │   2. Syntax Chunking   │ ──> │ 3. Query Generation    │
│  12 core / 23 candidate │     │  ATX heading split     │     │  Synthetic (A) vs      │
│  Markdown documents     │     │  ≤220 tokens, overlap  │     │  Diverse LLM (B, C)    │
└─────────────────────────┘     └────────────────────────┘     └────────────────────────┘
                                                                            │
┌─────────────────────────┐     ┌────────────────────────┐                  │
│  5. Retrieval & Eval    │ <── │ 4. Triplet Preparation │ <────────────────┘
│  9 retrievers benchmark │     │  Dense cosine mining   │
│  54 owner-approved q's  │     │  Section deduplication │
└─────────────────────────┘     └────────────────────────┘
```

1. **Document Ingestion:** Ingests Markdown technical documentation from the Soup CLI ecosystem. The core corpus comprises 12 documents (~368 KB). An expanded training corpus incorporates 23 additional candidate documents (~369 KB) while strictly preserving held-out evaluation documents.
2. **Markdown-Aware Chunking:** Splits documents on ATX headings (`#`, `##`, `###`), sub-splits sections exceeding 220 tokens with 28 tokens overlap, and retains hierarchical heading prefixes (`"{doc_name}: {heading}\n\n{body}"`) so every chunk preserves its structural context.
3. **Training Query Generation:**
   - *Strategy A (Synthetic templates):* Deterministic regex and template extraction over headings and command flags.
   - *Strategy B & C (Diverse LLM generation):* Context-grounded queries generated across four user intent categories: *How-To*, *Conceptual*, *Parameter Lookup*, and *Troubleshooting*.
4. **Triplet Preparation:** Hard negatives are mined using dense cosine similarity with strict **section-level deduplication** to ensure sibling paragraphs from the same section are never selected as false negatives.
5. **Optional Embedding Fine-Tuning:** Parameter-efficient fine-tuning (LoRA $r=16, \alpha=32$ on query/value projections; 147,456 trainable parameters = 0.65% of base) using Soup's native embedding trainer (`soup train --config <config.yaml>`, TripletMarginLoss with margin $m=0.5$).
6. **Retrieval & Evaluation:** Evaluates exact dot-product ranking over L2-normalized embeddings across a frozen benchmark of 54 owner-approved natural-language queries across 4 held-out documents.

---

## 3. Authoritative Benchmark Results (Phase 3)

The authoritative Phase 3 multi-retriever benchmark evaluated **nine distinct retrievers** on the identical frozen benchmark (54 owner-approved manual queries, 1,068 chunks across 12 documents, 4 held-out evaluation documents):

| ID | Retriever | Base Architecture / Checkpoint | Training Data & Query Strategy | Hit@1 | Recall@3 | MRR@10 |
|:---|:---|:---|:---|:---:|:---:|:---:|
| **R1** | BM25 | Fixed BM25 (`rank_bm25`) | Lexical baseline (no training) | 0.4815 | 0.4497 | 0.5953 |
| **R2** | Frozen MiniLM | `all-MiniLM-L6-v2` (frozen) | Off-the-shelf baseline (no training) | 0.5741 | 0.5753 | 0.6928 |
| **R3** | **Frozen E5-small** | `intfloat/e5-small-v2` (frozen) | **Strong off-the-shelf baseline** | **0.6852** | **0.6694** | **0.7834** |
| **R4** | A-full | MiniLM + Soup LoRA | Core corpus (8 docs), 1,078 synthetic queries | 0.5370 | 0.4951 | 0.6501 |
| **R5** | A-matched | MiniLM + Soup LoRA | Core corpus (8 docs), 825 synthetic queries | 0.5185 | 0.5228 | 0.6554 |
| **R6** | B | MiniLM + Soup LoRA | Core corpus (8 docs), 825 diverse LLM queries | 0.6481 | 0.6015 | 0.7434 |
| **R7** | C-matched | MiniLM + Soup LoRA | Expanded corpus (31 docs), 825 unstratified queries | 0.6111 | 0.5090 | 0.6844 |
| **R8** | **C-matched-balanced** | MiniLM + Soup LoRA | Expanded corpus (31 docs), 825 balanced queries | **0.6852** | 0.5722 | 0.7681 |
| **R9** | C-full | MiniLM + Soup LoRA | Expanded corpus (31 docs), 2,257 uncurated queries | 0.5556 | 0.4951 | 0.6310 |

*Full evaluation methodology, paired bootstrap uncertainty intervals, and leave-one-document-out analyses are detailed in [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md) and [`results/PHASE_3_1_INTEGRITY_AUDIT.md`](results/PHASE_3_1_INTEGRITY_AUDIT.md).*

### Key Empirical Findings

1. **Primary Negative Finding:** Fine-tuning MiniLM did **not** outperform frozen E5-small. Frozen `intfloat/e5-small-v2` remains the strongest retriever overall (0.7834 MRR@10, 0.6852 Hit@1). In practical settings, deploying a stronger pre-trained encoder out-of-the-box is substantially more effective than fine-tuning a smaller encoder on limited domain text.
2. **Best MiniLM Adapter:** `C-matched-balanced` was the top-performing MiniLM adapter (0.7681 MRR@10, 0.6852 Hit@1). It matched E5-small on Hit@1 (0.6852) and outperformed Frozen MiniLM (+0.0753 MRR@10), but trailed E5-small on overall ranking quality (MRR@10 0.7681 vs 0.7834) and top-3 recall (0.5722 vs 0.6694).
3. **Training Query Quality Outweighs Quantity:** Diverse LLM-generated training queries (Experiment B: 0.7434 MRR@10) substantially outperformed synthetic template-based queries (Experiment A-matched: 0.6554 MRR@10; $\Delta = +0.0880$ MRR@10). Synthetic template queries caused the model to overfit to formulaic heading structures, leading the baseline adapter `A-full` (0.6501 MRR@10) to perform **worse** than frozen MiniLM (0.6928 MRR@10) on natural user queries.
4. **Corpus Expansion Requires Careful Data Curation:** Expanding the training corpus to 31 documents with balanced intent sampling (`C-matched-balanced`) improved upon Experiment B (+0.0247 MRR@10). However, training on the uncurated full expanded corpus (`C-full`, 2,257 queries) degraded performance severely (0.6310 MRR@10; -0.0618 below frozen MiniLM), demonstrating that naive dataset scaling introduces significant domain noise.

---

## 4. Limitations & Scope

- **Evaluation Set Size:** The benchmark consists of 54 owner-approved manual queries evaluated across 4 held-out documents (307 chunks). While suitable for prototyping, four documents cannot support broad population-level statistical inference.
- **Document-Localized Improvements:** Adapter gains over Frozen MiniLM are concentrated predominantly in `adapters-and-governance` (MRR difference from Frozen MiniLM: C-matched-balanced $+0.2781$, B $+0.2448$) and `evaluation` (C-matched-balanced $+0.0402$, B $+0.0303$). On `peft-and-efficiency`, C-matched-balanced ties MiniLM ($0.7333$), and on `compliance`, observed scores are lower ($-0.1333$).
- **No Cross-Domain Generalization:** The results demonstrate domain adaptation within the Soup documentation corpus; generalization to completely unseen software domains or non-technical text is not established.
- **Retrieval vs Generation:** Retrieval metrics (Hit@K, Recall@K, MRR@10) measure chunk retrieval accuracy. They do not evaluate downstream response generation quality, prompt synthesis, or LLM hallucination rates.

---

## 5. Project Status & Roadmap

| Stage / Component | Status | Description |
|:---|:---:|:---|
| **Phase 0: Audit & Architecture** | **Completed** | Full corpus audit, leakage checks, document separation contracts (`docs/PHASE_0_AUDIT.md`). |
| **Phase 1: Dataset & Benchmark** | **Completed** | 54 owner-approved manual queries, diverse query generation (`results/PHASE_1_5_QUERY_QUALITY_REPORT.md`). |
| **Phase 2: Adapter Training Matrix** | **Completed** | 5 authorized LoRA adapters trained with isolated configs (`results/PHASE_2_TRAINING_EXECUTION_REPORT.md`). |
| **Phase 3: Multi-Retriever Benchmark** | **Completed** | 9-retriever benchmark evaluation, bootstrap CI, integrity audit (`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`). |
| *Phase 4: Hybrid BM25 + Dense Retrieval* | *Planned Future Work* | Reciprocal Rank Fusion (RRF) combining sparse lexical and dense representations. |
| *Phase 5: Cross-Encoder Reranking* | *Planned Future Work* | Two-stage pipeline evaluating cross-encoder rerankers (e.g. `bge-reranker-base`). |
| *Phase 6: Multi-Domain Generalization* | *Planned Future Work* | Evaluating fine-tuned adapters on third-party documentation sets. |
| *Phase 7: Soup CLI Integration* | *Planned Future Work* | Native integration into Soup CLI search commands (`soup docs search`). |

---

## 6. Repository Navigation & Deliverables

- **Core Documentation:**
  - [`results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`](results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md): Authoritative Phase 3 benchmark evaluation report across all 9 retrievers.
  - [`results/PHASE_3_1_INTEGRITY_AUDIT.md`](results/PHASE_3_1_INTEGRITY_AUDIT.md): Statistical verification, bootstrap invariant audit, and failure classification.
  - [`results/PHASE_3_DOCUMENTATION_AUDIT.md`](results/PHASE_3_DOCUMENTATION_AUDIT.md): Repository-wide documentation audit and consistency verification.
  - [`REPRODUCE.md`](REPRODUCE.md): Reproduction guide covering testing, result inspection, and evaluation workflows.
  - [`REVIEW.md`](REVIEW.md): Architectural review and experimental design decisions.
  - [`REPORT.md`](REPORT.md): Historical delivery report for the earlier Phase 1 synthetic evaluation (superseded by Phase 3).
- **Data & Config:**
  - `data/manual_queries.jsonl`: 54 owner-approved manual evaluation queries with multi-chunk relevance labels.
  - `data/corpus.jsonl`: 1,068 token-bounded chunks across 12 Soup documentation files.
  - `config/embedding_exp_*.yaml`: Independent training configurations for each adapter experiment.
  - `results/phase3/`: Audited raw evaluation results and bootstrap CI outputs for all 9 retrievers.

---

## 7. Quickstart & Verification

### Prerequisites

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 1. Run Verification Test Suite (182 Passing Tests)

Verify formatting, section deduplication, model loading, and dataset/statistical invariants:
```bash
pytest tests/ -v
```

### 2. Inspect Verified Phase 3 Benchmark Results

All 16 Phase 3 result artifacts are pinned and verified via SHA256 manifest:
```bash
cd results/phase3 && sha256sum -c manifest.sha256 && cd ../..
```

### 3. Run Read-Only Retrieval on Benchmark Queries

Run individual retrievers against the frozen 54-query benchmark:
```bash
# Evaluate Frozen MiniLM
python scripts/run_retrieval.py --retriever mini_lm_frozen --output results/test_minilm.json

# Evaluate Frozen E5-small
python scripts/run_retrieval.py --retriever e5_small --output results/test_e5.json

# Evaluate Baseline Soup Adapter (A-full)
python scripts/run_retrieval.py --retriever mini_lm_soup --output results/test_soup.json
```

See [`REPRODUCE.md`](REPRODUCE.md) for full instructions on reproducing training datasets and adapter runs.
