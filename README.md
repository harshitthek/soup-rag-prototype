# Soup Documentation Retrieval Prototype

This repository contains an empirical investigation into documentation retrieval for [Soup](https://github.com/MakazhanAlpamys/Soup) CLI and agent workflows. The goal is to provide fast, reliable technical documentation search across Soup's reference files without requiring complex infrastructure.

## Proposed Architecture

The proposed pipeline is a hybrid retrieval architecture combining:
1. **Domain-Aware BM25:** A lightweight regex tokenizer preserving CLI flags (`--track-energy`), dotted module paths (`soup.yaml`), and version strings (`bitnet_1.58`).
2. **Dense Semantic Retrieval:** Pretrained `intfloat/e5-small-v2` (frozen, 384d) for natural language semantic search.
3. **Reciprocal Rank Fusion (RRF):** Rank-level score fusion ($k=60$) combining lexical and dense ranking lists without learned weights.

## Key Findings

Evaluated against 24 unassisted owner-authored technical queries over the complete 1,068-chunk Soup documentation corpus:
- **Hybrid RRF** achieved the highest observed MRR@10 (**0.7254**) and Sec-MRR@10 (**0.7292**), improving top-3 recall over Frozen E5 (**0.4923** vs **0.4562**; the paired 95% bootstrap CI excludes zero: `[+0.0069, +0.0653]`). The paired 95% bootstrap interval for the MRR@10 difference against Frozen E5 includes zero (`[-0.0687, +0.0996]`).
- **Fine-Tuned E5-small (lr=2e-5):** Evaluated against Frozen E5-small across the 24 human queries (Frozen E5: MRR@10 0.7101, Hit@1 0.6250, Recall@3 0.4562 vs Fine-Tuned E5: MRR@10 0.6413, Hit@1 0.5417, Recall@3 0.5177). Frozen E5-small achieved higher observed MRR@10 and Hit@1, while Fine-Tuned E5-small achieved higher observed Recall@3, and all paired 95% bootstrap confidence intervals between them include zero.
- **Domain-Aware BM25** substantially outperformed the standard whitespace baseline (MRR@10 **0.6921** vs **0.4140**; the paired 95% bootstrap CI excludes zero), matching Frozen E5 top-1 accuracy (**0.6250**) at **2.4 ms** query latency and **107 ms** index cold-start.

## Observed Latency Trade-offs

All latency numbers are prototype measurements on Apple Silicon with preloaded corpus embeddings, not production deployment measurements:
- **Improved BM25:** 107 ms cold start, 2.37 ms warm retrieval.
- **Hybrid RRF:** 12.76 ms warm retrieval, MRR@10 0.7254.
While BM25 is the fastest single retriever and Hybrid RRF achieves the highest observed MRR@10 on this benchmark, these measurements reflect prototype code running on local hardware and do not constitute production SLAs.

## Evaluation Limitations

- **Benchmark Size:** Evaluated on 24 owner-authored queries; sample size limits statistical resolution between high-performing systems.
- **Annotation Methodology:** Relevance targets were identified directly by the project owner and mechanically mapped to canonical chunk IDs; no independent third-party annotation was conducted.
- **Telemetry:** Queries reflect project owner authoring, not production user query telemetry.

## Upstream Integration Status

This repository is an independent prototype and proposal for maintainer discussion. Upstream integration into Soup has **not** been approved or implemented.

## Documentation & Supporting Branches

- Authoritative empirical data, confidence intervals, and latency benchmarks: [`RESULTS.md`](RESULTS.md)
- Complete implementation, scripts, models, and test suite: [`chore/research-integrity-prep`](https://github.com/harshitthek/soup-rag-prototype/tree/chore/research-integrity-prep)
- Historical research logs and preliminary experiment reports: [`archive/research-history`](https://github.com/harshitthek/soup-rag-prototype/tree/archive/research-history)
