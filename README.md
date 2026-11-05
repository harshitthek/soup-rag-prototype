# Soup Documentation Retrieval Prototype

This repository contains an empirical investigation into documentation retrieval for [Soup](https://github.com/MakazhanAlpamys/Soup) CLI and agent workflows. The goal is to provide fast, reliable technical documentation search across Soup's reference files without requiring complex infrastructure.

## Proposed Architecture

The proposed pipeline is a hybrid retrieval architecture combining:
1. **Domain-Aware BM25:** A lightweight regex tokenizer preserving CLI flags (`--track-energy`), dotted module paths (`soup.yaml`), and version strings (`bitnet_1.58`).
2. **Dense Semantic Retrieval:** Pretrained `intfloat/e5-small-v2` (frozen, 384d) for natural language semantic search.
3. **Reciprocal Rank Fusion (RRF):** Rank-level score fusion ($k=60$) combining lexical and dense ranking lists without learned weights.

## Key Findings

Evaluated against 24 technical queries authored by Pernav and Harshit without AI assistance over the complete 1,068-chunk Soup documentation corpus:
- **Hybrid RRF and Frozen E5 Perform on Par Across Ranking Metrics:** Reciprocal Rank Fusion ($k=60$) combining domain-aware BM25 and frozen E5-small achieves an observed MRR@10 of **0.7254** (vs **0.7101** for Frozen E5) and ties top-1 hit accuracy at **0.6250** (15 of 24 queries correct). The paired 95% bootstrap confidence interval for MRR@10 includes zero (`[-0.0687, +0.0996]`). On Recall@3, Hybrid RRF improves top-3 candidate coverage over Frozen E5 (**0.4923** vs **0.4562**; paired 95% bootstrap CI `[+0.0069, +0.0653]`), though this gain is driven by positive differences on only 3 queries and does not survive multiple testing correction. Claiming general statistical superiority is unsupported.
- **Fine-Tuned E5-small (lr=2e-5):** Evaluated against Frozen E5-small across the 24 human queries (Frozen E5: MRR@10 0.7101, Hit@1 0.6250, Recall@3 0.4562 vs Fine-Tuned E5: MRR@10 0.6413, Hit@1 0.5417, Recall@3 0.5177). Frozen E5-small achieved higher observed MRR@10 and Hit@1, while Fine-Tuned E5-small achieved higher observed Recall@3, and all paired 95% bootstrap confidence intervals between them include zero.
- **Domain-Aware BM25 Substantially Outperforms Whitespace Baseline:** Moving from whitespace tokenization to domain-aware parsing increased MRR@10 from **0.4140 to 0.6921** (paired 95% bootstrap CI `[+0.1685, +0.3912]` strictly excludes zero), matching Frozen E5 top-1 accuracy (**0.6250**) at **2.4 ms** query latency and **107 ms** index cold-start. Whitespace BM25 represents the unmodified baseline; domain-aware tokenization was introduced concurrently during the benchmark development cycle (earliest Git commit 11m 56s after the manifest freeze timestamp).

## Observed Latency Trade-offs

All latency numbers are prototype measurements on Apple Silicon with preloaded corpus embeddings, not production deployment measurements:
- **Improved BM25:** 107 ms cold start, 2.37 ms warm retrieval.
- **Hybrid RRF:** 12.76 ms warm retrieval, MRR@10 0.7254.
While BM25 is the fastest single retriever and Hybrid RRF achieves the highest observed MRR@10 on this benchmark, these measurements reflect prototype code running on local hardware and do not constitute production SLAs.

## Evaluation Limitations

- **Document Stratification & Generalization:** 16 queries target training documents (seen during adapter training) and only 8 queries target held-out documents (unseen). The held-out subset ($N=8$, 2 queries per document) is exploratory and sample-constrained (each query represents 12.5 percentage points in Hit@1); it does not establish statistically significant cross-document generalization.
- **Annotation Methodology:** Relevance targets were designated by prototype authors and mechanically mapped to canonical chunk IDs; no independent third-party annotation was conducted.
- **Telemetry:** Queries reflect author formulation (Pernav and Harshit without AI assistance), not production user query telemetry.

## Upstream Integration Status

This repository is an independent prototype and proposal for maintainer discussion. Upstream integration into Soup has **not** been approved or implemented.

## Documentation & Supporting Branches

- Authoritative empirical data, confidence intervals, and latency benchmarks: [`RESULTS.md`](RESULTS.md)
- Complete implementation, scripts, models, and test suite: [`chore/research-integrity-prep`](https://github.com/harshitthek/soup-rag-prototype/tree/chore/research-integrity-prep)
- Historical research logs and preliminary experiment reports: [`archive/research-history`](https://github.com/harshitthek/soup-rag-prototype/tree/archive/research-history)
