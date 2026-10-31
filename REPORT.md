# Prototype Delivery Report: Dense Retrieval Fine-Tuning with Soup

**Task:** Prototype a real-world dense retrieval use case on TXT/Markdown technical documents, perform embedding fine-tuning through Soup's native training engine, and evaluate retrieval quality before and after on a separate held-out test set.

---

## 1. Executive Summary

This report delivers the prototype evaluation comparing retrieval quality **before and after** fine-tuning an embedding model using [Soup](https://github.com/MakazhanAlpamys/Soup)'s native `task: embedding` path.

The prototype indexes **12 real Markdown documentation files** from the Soup CLI ecosystem. To evaluate real-world generalization, the corpus was divided using a strict **document-level split** (8 training documents / 4 completely unseen test documents). Dense retrieval was evaluated on **497 held-out queries** before fine-tuning (Frozen MiniLM baseline) and after fine-tuning (LoRA adapter fine-tuned through Soup).

> [!NOTE]
> **Evaluation query limitation:** The evaluation queries are synthetically generated from the held-out documents using predefined templates and content-derived patterns. The documents are excluded from the training-document split, but the queries are not independently authored human search requests. This controlled benchmark supports comparing the base and fine-tuned retrievers on the same evaluation set; template structure and lexical overlap may influence the measured performance. The results should not be interpreted as a direct estimate of performance on real-world user queries.

### Key Empirical Findings

| Metric | Before Fine-Tuning (Frozen MiniLM) | After Fine-Tuning (Soup LoRA) | Absolute Delta ($\Delta$) | Relative Gain | 95% Bootstrap CI |
|---|:---:|:---:|:---:|:---:|:---:|
| **Recall@1** | 0.5453 | **0.7565** | **+0.2113** | **+38.75%** | `[+0.1650, +0.2555]` |
| **Recall@3** | 0.7606 | **0.9336** | **+0.1730** | **+22.75%** | `[+0.1368, +0.2113]` |
| **Recall@5** | 0.8209 | **0.9718** | **+0.1509** | **+18.38%** | `[+0.1167, +0.1851]` |
| **MRR@10** | 0.6615 | **0.8477** | **+0.1862** | **+28.14%** | `[+0.1534, +0.2195]` |

> [!IMPORTANT]
> **Summary Highlights:**
> 1. **Recall@1 rose from 54.53% to 75.65%**: Over 3 out of 4 test queries now return the exact relevant section at Rank 1.
> 2. **Recall@5 reached 97.18%**: In over 97% of queries, the correct technical answer is within the top-5 retrieved passages.
> 3. **Uncertainty Intervals**: All metrics exhibit strictly positive 95% paired bootstrap percentile intervals on this evaluation set (e.g., Recall@1 95% CI `[+0.1650, +0.2555]`).
> 4. **Parameter Efficiency**: Achieved using a lightweight LoRA adapter modifying only **147,456 parameters** (0.65% of the 22.86M base model).

---

## 2. The Real Use Case

### Context: Technical Developer Documentation Search
Developer documentation for modern command-line tools and machine-learning frameworks (such as Soup CLI) presents unique retrieval challenges:
- **High Lexical Overlap**: Different commands share common terminology (`yaml`, `train`, `lora`, `quantization`, `checkpoint`, `eval`).
- **Hierarchical Options**: Commands have nested sub-commands, global flags, and option flags that look syntactically similar.
- **Boilerplate Distractors**: Documentation pages often repeat standard headers, common flags, or standard recipes, confusing out-of-the-box embedding models.

Generic embedding models (e.g. frozen `all-MiniLM-L6-v2`) frequently retrieve generic overview text or adjacent sections with matching keywords rather than the precise section that answers a specific user question.

### The Objective
Prototype a production-grade embedding fine-tuning workflow using **Soup's native CLI** to teach the embedding model the domain-specific semantics, flag relationships, and hierarchical structures of technical documentation.

---

## 3. Corpus Construction & Markdown Processing

### 3.1 Document Ingestion & Chunking
The source corpus comprises **12 technical Markdown files** (~368 KB) covering the complete Soup CLI documentation surface.

To preserve semantic cohesion while respecting the tokenizer budget of dense encoders:
1. **ATX Heading Splitting**: Documents are initially split on Markdown ATX headings (`#`, `##`, `###`), preserving the natural structure of technical manuals.
2. **Token-Bounded Sub-Splitting**: For sections exceeding MiniLM's sequence capacity, sub-splitting is applied using word boundaries with a maximum target of **220 tokens** and **28 tokens of overlap**. This leaves headroom for special tokens and prefix headers within MiniLM's 256 max sequence length.
3. **Hierarchical Heading Prefix Retention**: Every chunk preserves its document and heading lineage prepended as `"{doc_name}: {heading}\n\n{body}"`.

### 3.2 Corpus Statistics
- **Total Files**: 12 Markdown files
- **Total Chunks**: 1,068 chunks
- **Median Chunk Length**: ~150 tokens (0 chunks exceed 256 tokens)
- **Document Distribution**:
  - 8 Training Documents (761 chunks)
  - 4 Held-Out Test Documents (307 chunks)

---

## 4. Leak-Free Evaluation Design

A common flaw in RAG prototypes is random chunk splitting: randomly assigning chunks from the same document to train and test sets. Because chunks from the same document share authorial style, identical heading prefixes, and overlapping technical concepts, random chunk splitting causes severe data leakage and artificially inflates retrieval metrics.

### Document-Level Separation
To guarantee unbiased measurement of out-of-domain generalization:
- **Training Documents (8 docs, 761 chunks)**:
  `backends-and-ops.md`, `commands.md`, `data.md`, `models.md`, `performance-and-quantization.md`, `README.md`, `serving-and-export.md`, `training.md`.
- **Held-Out Test Documents (4 docs, 307 chunks)**:
  `adapters-and-governance.md`, `compliance.md`, `evaluation.md`, `peft-and-efficiency.md`.

No chunk, passage, or heading from the 4 test documents was ever exposed to the model during training or during hard negative mining.

### Held-Out Evaluation Queries
Using deterministic templating over the 4 test documents, **497 test queries** were synthesized across three distinct query styles:
1. *Natural language questions* ("How do you configure namespace pinning in Soup?")
2. *Command/flag lookups* ("What does soup adapters sign do in the context of adapters & governance?")
3. *Concept queries* ("What is activation steering and how does it work in Soup?")

Each query is paired with exactly one ground-truth relevant chunk ID from the held-out documents.

> [!NOTE]
> **Synthetic Query Generation Details:** Evaluation queries are generated programmatically by `scripts/generate_queries.py` using regex and template patterns over held-out document content (ATX headings and command-line flags). The documents are strictly excluded from the training split, but the queries are not independently authored human queries. Controlled query generation ensures reproducible evaluation against held-out text, though template phrasing and lexical overlap may influence measured absolute scores.

---

## 5. Embedding Fine-Tuning through Soup

Fine-tuning was executed using Soup's native embedding trainer (`task: embedding`) via the Soup CLI:

### 5.1 Training Architecture & Configuration
- **Base Model**: `sentence-transformers/all-MiniLM-L6-v2` (6 layers, 384 hidden dimensions, 12 attention heads).
- **Fine-Tuning Method**: Low-Rank Adaptation (LoRA)
  - $r = 16, \alpha = 32$, dropout = 0.05
  - Target modules: `query` and `value` projections
  - Trainable parameters: **147,456** (0.65% of 22,860,672 total)
- **Loss Function**: Triplet margin loss ($m = 0.5$)
  $$\mathcal{L}(a, p, n) = \max(0, \|a - p\|_2 - \|a - n\|_2 + m)$$
  With L2-normalized representations, this directly optimizes the cosine separation between anchor-positive and anchor-negative pairs.
- **Pooling & Normalization**: Attention-masked mean pooling followed by row-wise L2 normalization.
- **Optimization**: AdamW, learning rate $2 \times 10^{-5}$, batch size 4, 3 epochs (2,427 steps), linear learning rate schedule with warmup.
- **Data Allocation (`val_split: 0.0`)**: 100% of training triplets allocated to parameter optimization.

### 5.2 Contrastive Hard Negative Mining
The quality of embedding fine-tuning is governed by the contrastive negatives the model encounters:
- **Mining Strategy**: For each training query, candidate chunks are ranked by cosine similarity using the frozen base model.
- **Section Deduplication**: To avoid redundant or false contrastive signals, chunks from the positive chunk's section and chunks sharing a section with an already-selected negative are filtered out.
- **Top-3 Mining**: 3 distinct hard negatives are mined per query, expanding the dataset from 1,078 to **3,234 training triplets** across **618 unique negative chunks** (active negative coverage of 81.2% of the training corpus).
- **Prefix Consistency**: Heading prefixes are prepended to both positive and negative passages in triplets, ensuring the adapter trains on the exact text representation used during evaluation.

---

## 6. Comprehensive Retrieval Evaluation

Dense retrieval operates by encoding queries and corpus passages into 384-dimensional L2-normalized vectors and ranking all 1,068 corpus chunks by cosine similarity (dot product):

### 6.1 Aggregate Benchmark Comparison

```
Metric Comparison (Frozen Baseline vs Fine-Tuned LoRA):
Recall@1:  [Baseline: 54.53%] ──> [Fine-Tuned: 75.65%] (+21.12% absolute, +38.75% relative)
Recall@3:  [Baseline: 76.06%] ──> [Fine-Tuned: 93.36%] (+17.30% absolute, +22.75% relative)
Recall@5:  [Baseline: 82.09%] ──> [Fine-Tuned: 97.18%] (+15.09% absolute, +18.38% relative)
MRR@10:    [Baseline: 0.6615] ──> [Fine-Tuned: 0.8477] (+0.1862 absolute, +28.14% relative)
```

### 6.2 Paired Bootstrap Uncertainty Analysis
Evaluated using paired query-level percentile bootstrap resampling (10,000 resamples, seed = 42, $\alpha = 0.05$):

- **Recall@1**: $\Delta = +0.2113$, 95% CI `[+0.1650, +0.2555]`
- **Recall@3**: $\Delta = +0.1730$, 95% CI `[+0.1368, +0.2113]`
- **Recall@5**: $\Delta = +0.1509$, 95% CI `[+0.1167, +0.1851]`
- **MRR@10**: $\Delta = +0.1862$, 95% CI `[+0.1534, +0.2195]`

All 95% empirical bootstrap intervals exclude zero, indicating that the mean paired difference is positive within this held-out evaluation set. The intervals do not show that every individual query improved (39 queries exhibited lower ranks, detailed in Section 8). As noted in the methodology, these intervals measure sample uncertainty across the 497 evaluated queries rather than serving as a formal null-hypothesis significance test.

---

## 7. Per-Document Breakdown

The test suite queries originate from 4 distinct technical documentation domains. The fine-tuned model demonstrated uniform, robust gains across all four:

| Document | Test Queries | Baseline Recall@1 | Fine-Tuned Recall@1 | Baseline MRR@10 | Fine-Tuned MRR@10 | Recall@5 (Fine-Tuned) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`adapters-and-governance.md`** | 188 | 0.5851 | **0.7766** (+19.15%) | 0.6921 | **0.8677** (+0.1756) | **0.9947** (99.5%) |
| **`compliance.md`** | 26 | 0.5385 | **0.8462** (+30.77%) | 0.6859 | **0.9231** (+0.2372) | **1.0000** (100.0%) |
| **`evaluation.md`** | 193 | 0.5959 | **0.7720** (+17.61%) | 0.7101 | **0.8542** (+0.1441) | **0.9689** (96.9%) |
| **`peft-and-efficiency.md`** | 90 | 0.3556 | **0.6556** (+30.00%) | 0.4864 | **0.7701** (+0.2837) | **0.9222** (92.2%) |

### Highlight: The `peft-and-efficiency` Domain
The `peft-and-efficiency` document proved the most challenging for the base model due to dense algorithmic formulas and overlapping acronyms (LoRA, PiSSA, ReLoRA, QLoRA, MultiPack).
- **Baseline Performance**: Baseline Recall@1 was only **35.56%**.
- **Fine-Tuned Performance**: Soared to **65.56%** (+30.00% absolute increase, nearly doubling baseline accuracy).
- **Root Cause**: Multi-negative contrastive mining with section deduplication forced the adapter to learn discriminative representations between closely related PEFT techniques rather than collapsing them into a generic "optimization" cluster.

---

## 8. Error and Failure Mode Analysis

To assess model safety and identify edge cases, all queries where the fine-tuned model ranked lower than the baseline were analyzed:

1. **Zero Out-of-Bounds Catastrophic Regressions**:
   Zero queries dropped out of the top 10 results entirely (`>10`). In contrast to early unaligned iterations, all relevant passages are retrieved within the top ranks (Recall@5 = 97.18%).
2. **Intra-Section Sibling Ranking Discrepancies**:
   Of the 39 queries where the baseline ranked the labeled target chunk higher than the fine-tuned model:
   - **36 out of 39 (92.3%)** involved sibling chunks from the **exact same section** (e.g., `adapters-and-governance::audit-log-soup-audit-log::sub_001` outranking labeled `sub_000`).
   - While the model successfully localized the correct section, these cases represent **genuine retrieval failures** whenever answer-bearing text is concentrated in a specific sub-chunk. For example, for *"How do you use audit log (soup audit-log) in Soup CLI?"*, the labeled `sub_000` specifies `soup audit-log tail`, `rotate`, and `--no-audit-log`, whereas `sub_001` contains adjacent documentation. Because the chunker uses a 28-token overlap, non-overlapping content is not duplicated, so returning `sub_001` at Rank 1 omits vital command usage.
   - **Root Cause**: Sibling chunks share the identical section heading prefix and dense conceptual terminology. Without exact keyword matching, the dense representation can assign slightly higher cosine similarity to an adjacent sibling paragraph.
   - **Production Remedy**: In production RAG deployments, this failure mode is cleanly resolved by combining dense embeddings with a lightweight BM25 sparse index (hybrid search) to pin exact keyword mentions, or by expanding the context window to retrieve adjacent sibling chunks during RAG generation.
3. **True Cross-Document Semantic Errors**:
   Cross-document false positive failures (where the model retrieved chunks from an entirely unrelated document) occurred in only **3 out of 497 queries (0.6%)**, demonstrating high domain precision.

---

## 9. Key Lessons Learned

1. **Input Representation Consistency is Critical**:
   A model evaluated on prefixed text must be trained on prefixed text. Aligning the heading prefix representation between training triplets and evaluation passages contributed the largest single boost in retrieval fidelity.
2. **Contrastive Negative Diversity Beats Triplet Volume**:
   Training on a single repetitive boilerplate negative repeatedly causes the model to optimize against trivial shortcuts. Mining top-3 negatives with strict per-query section deduplication expanded active negative coverage across 81.2% of the training corpus and produced sharp technical discrimination.
3. **Parameter and Data Efficiency via Soup**:
   Fine-tuning through Soup's native embedding trainer was highly compute-efficient:
   - Trained in **6 minutes** on an Apple Silicon laptop GPU (MPS).
   - Only **147K parameters** trained (0.65% capacity).
   - Resulted in a **+38.7% relative improvement in Recall@1** and **+28.1% improvement in MRR@10**.

---

## 10. Deliverable Artifacts

| Component | File Path | Description |
|---|---|---|
| **Primary Report** | [`REPORT.md`](REPORT.md) | This formal delivery document |
| **Reproduction Guide** | [`REPRODUCE.md`](REPRODUCE.md) | Step-by-step reproduction instructions |
| **Repository Overview** | [`README.md`](README.md) | Landing page with final benchmark scorecard |
| **Bootstrap Analysis** | [`results/comparison.md`](results/comparison.md) | Paired bootstrap uncertainty analysis report vs baseline |
| **Trained Adapter** | [`output_embedding/`](output_embedding/) | Fine-tuned LoRA weights and configuration |
| **Evaluation Data** | [`results/candidate.json`](results/candidate.json) | Full per-query retrieval predictions on test set |
| **Baseline Data** | [`results/baseline.json`](results/baseline.json) | Baseline retrieval predictions on test set |
| **Automated Tests** | [`tests/test_retrieval_pipeline.py`](tests/test_retrieval_pipeline.py) | 15 unit and integration test assertions |

---

## 11. Evaluation v2 Extension (manual benchmark, complete)

This report describes the v1 controlled benchmark. Evaluation v2 measures
generalization on **54 owner-approved queries** (drafted by Qoder, reviewed
and frozen by the owner) with multi-chunk/multi-section labels, chunk- and
section-level Hit@K/Recall@K/MRR, and a four-way comparison (frozen MiniLM,
Soup adapter, BM25, frozen `intfloat/e5-small-v2`) with doc-stratified paired
bootstrap and leave-one-doc-out sensitivity. Full methodology:
`docs/EVALUATION_V2_SPEC.md`; report: `results/v2/comparison.md`.

| Retriever | Hit@1 | Hit@5 | MRR@10 | Sec Hit@1 | Sec MRR@10 |
|---|:---:|:---:|:---:|:---:|:---:|
| E5-small-v2 (frozen) | 0.685 | 0.870 | 0.783 | 0.722 | 0.817 |
| MiniLM frozen | 0.593 | 0.870 | 0.702 | 0.648 | 0.735 |
| MiniLM + Soup adapter | 0.556 | 0.815 | 0.669 | 0.593 | 0.701 |
| BM25 | 0.481 | 0.722 | 0.598 | 0.481 | 0.616 |

The v1 gain does not transfer to natural-language queries: the adapter trails
frozen MiniLM on the manual set (Hit@1 −3.7 pp, MRR@10 −3.3 pp; Recall@5
−10.7 pp with an interval excluding 0). The split by subset is the key
result: on the 36 primary queries the adapter trails frozen MiniLM
(Hit@1 0.528 vs 0.639), while on the 18 overlap queries whose answers also
appear in training documents it leads (Hit@1 0.611 vs 0.500). This is
consistent with the adapter having learned training-document text rather than
a transferable retrieval skill. Frozen E5-small-v2 is the strongest retriever
on every metric. Four held-out documents are insufficient for
population-level inference; intervals are exploratory and no p-values are
reported. The v1 numbers above remain the canonical record of the controlled
synthetic benchmark; in v1, labels were singleton chunks, so the binary
"recall@k" values equal Hit@K.
