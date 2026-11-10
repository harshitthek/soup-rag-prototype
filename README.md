# Soup Documentation Retrieval: Maintainer Review Package

**Target Maintainer:** Alpamys (@MakazhanAlpamys)<br>
**Repository Branch:** `review/soup-integration`<br>
**Status:** Pre-PR Architecture Proposal & Empirical Review Package (Decoupled prototype; no upstream changes applied)<br>
**Scope:** Minimal, decoupled documentation retrieval component for the Soup CLI

---

## 1. The Practical Problem

As Soup has expanded to cover multiple training routines (SFT, DPO, GRPO, KTO, RMU unlearning), quantization schemes (NF4, AWQ, HQQ, GGUF), governance workflows (BOM, in-toto attestations, EU AI Act documentation), and execution backends (CUDA, MLX, vLLM), locating exact command syntax, configuration keys, and error diagnostics across 12 reference guides has become challenging for developers working in the terminal.

The goal of this project is to provide fast, reliable, and completely offline documentation search directly within the Soup CLI (`soup docs search "<query>"`), which can also feed grounded context to downstream commands (`soup advise`, `soup init`, or chat assistants) without introducing heavy external databases or services.

---

## 2. What the Retrieval Prototype Implements

The prototype implements a minimal, decoupled retriever (`DocumentationRetriever`, $\approx 300\text{--}350$ lines of clean Python) supporting:
- **Heading-Aware Markdown Chunking:** Deterministic section extraction (`#`, `##`, `###`) preserving document hierarchy, line bounds, and section paths across all 12 reference guides (1,068 canonical chunks).
- **Domain-Aware Lexical Indexing (BM25):** Custom regex tokenization preserving CLI flags (`--track-energy`, `--annex-xi`), compound identifiers (`bitnet_1.58`), and dotted config keys (`soup.yaml`).
- **Dense Semantic Retrieval:** Pretrained `intfloat/e5-small-v2` (33M parameters, 384 dimensions) providing conceptual and natural-language matching.
- **Reciprocal Rank Fusion (RRF $k=60$):** Unweighted rank-level score fusion combining lexical and dense candidate lists without learned weights.
- **Local Hermetic Cache:** File-based index caching in `.soup/cache/docs/` with SHA-256 corpus fingerprinting for automatic cache invalidation upon documentation edits.

---

## 3. Why BM25, Frozen E5, and Hybrid RRF Were Evaluated

Three retrieval paradigms were selected to evaluate the trade-off between implementation simplicity, execution speed, and ranking quality:
1. **Domain-Aware BM25:** Evaluated as a fast, zero-GPU baseline. Technical developer queries frequently contain exact CLI flags, error codes, and configuration parameters where exact token matching is optimal.
2. **Dense Semantic Retrieval (Frozen E5-small):** Evaluated to assess semantic matching when developers describe symptoms or concepts in natural language without using exact heading keywords. Pretrained base weights were evaluated because fine-tuning with synthetic triplets caused severe ranking regression on human queries.
3. **Hybrid RRF ($k=60$):** Evaluated to test whether combining lexical precision with dense semantic recall produces higher candidate retrieval accuracy without requiring score normalization or weight tuning.

---

## 4. Summary of Empirical Findings (Cohort 1, $N=28$ External Developer Queries)

The benchmark was officially executed on 28 genuine developer queries authored manually by three external contributors outside the prototype development team:

| System | Architecture / Mode | Hit@1 | Recall@3 | Recall@5 | MRR@10 (Primary) | Sec-Hit@1 | Sec-MRR@10 | Mean Warm Query | Median | P95 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hybrid RRF** | BM25 + Frozen E5 ($k=60$) | **0.8571** (24/28) | 0.7155 | 0.7869 | **0.9048** | **0.8929** | **0.9286** | 6.49 ms | 6.14 ms | 7.52 ms |
| **Frozen E5-small** | `intfloat/e5-small-v2` (frozen base) | 0.8214 (23/28) | **0.7214** | **0.8107** | 0.8869 | 0.8214 | 0.8929 | 4.94 ms | 4.93 ms | 5.13 ms |
| **Improved BM25** | Domain-aware regex ($k_1=1.5, b=0.75$) | 0.8214 (23/28) | 0.6679 | 0.7167 | 0.8845 | 0.8571 | 0.9033 | **0.80 ms** | **0.77 ms** | **1.00 ms** |

### Statistical Contrast Summary (10,000 Paired Resamples, Seed 42)
- **Primary Ranking Metric (MRR@10):** All three pairwise comparisons cross zero under both unadjusted 95% and Bonferroni multiplicity adjustments ($\alpha = 0.05 / 3 \approx 0.0167$):
  - *Improved BM25 vs Frozen E5:* $\Delta = -0.0024$, Bonferroni CI `[-0.1036, +0.0929]` (spans zero).
  - *Hybrid RRF vs Frozen E5:* $\Delta = +0.0179$, Bonferroni CI `[-0.0536, +0.1071]` (spans zero).
  - *Hybrid RRF vs Improved BM25:* $\Delta = +0.0202$, Bonferroni CI `[-0.0226, +0.0952]` (spans zero).
  - *Interpretation:* All three systems achieve strong top-1 accuracy ($\ge 0.88$ MRR@10). No confirmatory comparison detected a statistically significant difference on MRR@10. This failure to detect a difference is reported as confidence intervals crossing zero, **not** as proof of parity or equivalence.
- **Exploratory Secondary Metric (Recall@5):** Frozen E5 achieves higher observed Recall@5 than Improved BM25 ($\Delta = +0.0940$, Bonferroni CI `[+0.0042, +0.1935]` excluding zero). This is an exploratory secondary finding: MRR@10 was the sole confirmatory primary metric, and the Bonferroni adjustment accounted for 3 system comparisons on this metric but did not control family-wise error across multiple secondary endpoints.

Full experimental data, per-query breakdowns, and historical benchmark comparisons are documented in [`RESULTS.md`](RESULTS.md).

---

## 5. Why BM25 is Recommended as the Initial Integration Strategy

While Hybrid RRF achieved the highest ranking point estimate (0.9048 MRR@10, 24/28 top-1 hits, +1 query over BM25), **Domain-Aware BM25 is recommended as the default initial integration strategy** for the following architectural reasons:

1. **Top-1 Accuracy Parity on 82% of Queries:** BM25 achieves 0.8845 MRR@10 and 82.1% Hit@1 (23/28 correct at rank 1), matching Frozen E5.
2. **Sub-Millisecond Warm Retrieval:** Measured at **0.80 ms** mean query latency on Apple Silicon.
3. **Fast Cold CLI Startup:** Executes in an estimated **~250–350 ms** from a cold shell prompt (Python runtime startup + Click CLI dispatch + index unpickling), compared to **~1.5–2.5 s** for Dense/Hybrid which must import PyTorch and `transformers` and instantiate model weights.
4. **Zero GPU / Deep Learning Dependencies:** Requires only `rank-bm25` (a 50 KB pure Python package). Users can search documentation immediately without downloading Hugging Face model weights (~133 MB for `e5-small-v2`) or requiring PyTorch in non-training environments.

---

## 6. Proposed Minimal Soup CLI Integration

To adhere to Soup's clean architecture and Unix philosophy:
- **No External Databases:** Zero ChromaDB, Pinecone, Milvus, Qdrant, or Postgres dependencies.
- **No Background Services:** Strictly in-process CLI execution; zero daemons.
- **Decoupled Engine:** Search returns structured dataclasses (`RetrievedChunk`); prompt synthesis and LLM generation remain with the caller.
- **CI Testability:** Core retriever logic includes `retriever.fit_in_memory(...)`, allowing unit tests in Soup's CI suite to test retrieval without downloading Hugging Face weights or requiring GPU access.
- **Graceful Fallback:** If PyTorch or model weights are unavailable, the CLI automatically falls back to Domain-Aware BM25.

### Proposed Code Placement in Upstream Repository
- `src/soup_cli/retrieval/retriever.py` (Retriever engine and RRF logic, ~180 lines)
- `src/soup_cli/retrieval/tokenizer.py` (Domain-aware regex tokenizer, ~40 lines)
- `src/soup_cli/commands/docs.py` (Click CLI command registration, ~80 lines)

---

## 7. Three Decisions for Alpamys

Before preparing a clean pull request, please indicate your preferences on three design choices:

1. **CLI Command Naming:**
   - `soup docs search "<query>"` (Recommended: cleanly groups with `soup docs index` and avoids top-level CLI namespace pollution) vs. `soup search "<query>"`.
2. **Default Retrieval Strategy:**
   - **`bm25` (Recommended Default):** Fast cold startup (~250 ms), sub-millisecond warm query latency (0.80 ms), zero GPU/PyTorch requirement, 50 KB pure Python dependency (`rank-bm25`), zero model weight downloads.
   - **`hybrid`:** Highest ranking point estimate (0.9048 MRR@10, 85.7% Hit@1, +1 query over BM25) and higher secondary candidate recall (Recall@5 0.7869 vs 0.7167), but incurs a ~2 s cold process startup from importing PyTorch/transformers and requires downloading `e5-small-v2` (~133 MB).
3. **Upstream Packaging:**
   - Include `rank-bm25` in base `pyproject.toml` dependencies (~50 KB pure Python) vs. gating under an optional extra (e.g. `pip install soup-cli[docs]`).

---

## 8. Working Prototype vs. Proposed Upstream Functionality

- **Prototype Status:** The code and evaluation reported here represent an independent prototype and proposal for maintainer discussion. Upstream Soup has **not** been modified.
- **Underlying Research Records:** The complete implementation, evaluation runners, automated test suite (254 passing tests), frozen JSON artifacts, and forensic investigation records are retained on the research branch `chore/research-integrity-prep` and can be provided on request.
- **Optional Maintainer Replication (Cohort 2):** Whenever Alpamys supplies his own independent developer questions, they will be frozen in a separate manifest and evaluated independently to verify whether findings replicate on maintainer-authored queries without pooling or contamination.
