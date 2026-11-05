# Research Integrity, AI Disclosure & Independent Evaluation Protocol

This document establishes dataset provenance, discloses AI assistance across dataset authoring, records corrected experimental claims, and specifies the protocol and findings of the independent human-authored evaluation benchmark.

---

## 1. AI Assistance & Dataset Provenance Disclosure

Dataset construction across the prototype utilized distinct generation strategies:

| Dataset | Role in Research | Generation Method | Generator / Strategy | Provenance Status |
|:---|:---|:---|:---|:---|
| `data/train_queries_exp_a_matched.jsonl` | Training (A-matched) | Heuristic / Template | Deterministic regex on headings & CLI flags | Heuristic / Rule-based |
| `data/train_queries_exp_b.jsonl` | Training (B) | LLM Generation | `gemini-2.5-flash` (`v2.1-diverse-paraphrase`) | Synthetic LLM |
| `data/train_queries_exp_c_matched_balanced_v1_6.jsonl` | Training (C-bal) | LLM Generation | `gemini-2.5-flash` (`v1.5-markdown-aware`) | Synthetic LLM |
| `data/train_queries_exp_c_full.jsonl` | Training (C-full) | LLM Generation | `gemini-2.5-flash` (uncurated 31 docs) | Synthetic LLM |
| `data/manual_queries.jsonl` (54 queries) | AI-Assisted Evaluation Benchmark | Collaborative drafting with AI | Project owner drafted with LLM assistance | AI-assisted benchmark |
| `data/human_eval/human_queries_v2.jsonl` (24 queries) | Independent Evaluation Benchmark | Direct Human Authoring | Project owner authored without AI assistance | **Confirmed Unassisted Human** |

### Detailed Provenance (54-Query AI-Assisted Benchmark):
1. **Query Generation (AI-Assisted):** The 54 evaluation queries in `data/manual_queries.jsonl` were formulated in collaborative sessions between the project owner and an AI assistant. The exact prompts, model versions, and session transcripts used during query drafting were not formally logged in the repository and are **undocumented**.
2. **Relevance Label Assignment (Undocumented AI Involvement):** Candidate relevance labels (`relevant_chunk_ids`, `relevant_section_ids`, `evidence_chunk_ids`, `rationale`) are stored in `data/manual_queries.jsonl`. However, repository records do not establish whether relevance labels were initially proposed by the AI assistant or identified directly by the human author from the corpus. Because this cannot be verified from existing artifacts, AI involvement in candidate relevance annotation must be treated as **undocumented**.
3. **Internal Review:** The project owner verified and approved the final queries and relevance labels. However, this was an internal author review, **not an independent third-party annotation or external human audit**.
4. **Stylistic Phrasing Alignment Risk:** Because Gemini generated the training queries for Experiments B and C, and AI assistance was used in drafting the 54 evaluation queries, overlapping AI-assisted phrasing created a potential style alignment risk between the AI-generated training data and the AI-assisted evaluation benchmark, but its impact was not independently isolated or measured.

---

## 2. Independent Owner-Authored Benchmark v2 (`human_eval_v2`)

### Provenance and Authorship:
The evaluation benchmark comprises 24 queries (`soup_human_001` through `soup_human_024`) provided directly by the project owner.
- **Confirmed Unassisted Human Authorship:** The project owner authored these 24 questions directly without AI assistance. No LLM was used to generate questions, rewrite syntax, correct typos, or suggest alternatives. Real developer traits—including domain terminology, informal grammar, and typos (e.g. `breaked`, `guarentees`)—are preserved verbatim.
- **Target Section Identification & Mechanical Mapping:** Alongside each query, the owner provided a specific source document and reference portion (e.g. section heading or feature name). Annotations were resolved through **mechanical document mapping** from owner-supplied target sections to canonical indexed chunk IDs and base section IDs in `data/corpus.jsonl`.
- **Annotation Boundaries & Non-Representativeness:** No independent third-party relevance annotation was performed. The benchmark does not represent production user query logs or a statistically sampled population of developers.
- **Supplemental Baseline Analysis:** Original whitespace BM25 was evaluated as a supplemental baseline analysis during the post-freeze corrective audit to isolate the impact of domain-aware tokenization against standard whitespace splitting over the identical frozen benchmark.
- **Full Corpus Breadth:** Unlike the 54-query set which targeted content exclusively within 4 held-out documents, the 24 human queries span targets across all 12 Soup documentation files (`adapters-and-governance.md`, `backends-and-ops.md`, `commands.md`, `compliance.md`, `data.md`, `evaluation.md`, `models.md`, `peft-and-efficiency.md`, `performance-and-quantization.md`, `README.md`, `serving-and-export.md`, `training.md`).
- **No Artificial Category Quotas:** Queries reflect natural developer questions without forced document quotas or synthetic intent buckets.

### Complete Withdrawal of 12-Query Draft:
An interim draft of 12 queries (`human_queries_v1.jsonl`) was initially collected. Because its AI-assistance status was unconfirmed and preliminary rankings had inadvertently been generated, the 12-query draft, its annotation templates, and its external quarantine cache (`~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json`) have been **completely withdrawn and deleted**. The 24-query v2 dataset replaces it entirely.

### Frozen Benchmark Artifacts:
- **Query File:** `data/human_eval/human_queries_v2.jsonl` (SHA256: `6d917ef3e89e18d0e87084804d3598bf53ef51971ff77259a768150f3a730d58`)
- **Annotation File:** `data/human_eval/relevance_annotations_v2.jsonl` (SHA256: `51f66a794505c6e9cc18e3f8d8008850c4c114aabf3682304196e7dfba2426a5`)
- **Corpus Fingerprint:** `data/corpus.jsonl` (SHA256: `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3`)
- **Manifest:** `data/human_eval/manifest_v2.json` (`status: "frozen"`)

---

## 3. Separation of Benchmarks & Experimental Findings

| Benchmark | Query Count | Authorship | Corpus Scope | BM25 (Orig) MRR@10 | BM25 (Imp) MRR@10 | Frozen E5 MRR@10 | FT E5 (2e-5) MRR@10 | Hybrid RRF MRR@10 |
|---|---|---|---|---|---|---|---|---|
| **AI-Assisted Benchmark** (`manual_queries.jsonl`) | 54 | AI-Assisted collaborative drafting | Full 1,068 chunks (targets in 4 docs) | 0.5953 | 0.7712 | 0.7834 | 0.6458 | 0.8552 |
| **Independent Owner Benchmark** (`human_queries_v2.jsonl`) | 24 | Confirmed Unassisted Human | Full 1,068 chunks (targets across 12 docs) | 0.4140 | 0.6921 | 0.7101 | 0.6413 | 0.7254 |

### Key Takeaways from the Human Evaluation:
1. **Hybrid RRF achieves the highest observed point estimates, with top-3 candidate recall CI excluding zero:** Point estimates on human queries show Hybrid RRF (BM25 + Frozen E5) leading with MRR@10 **0.7254** and Sec-MRR@10 (**0.7292**). The paired 95% bootstrap confidence interval for Recall@3 improvement over Frozen E5 excludes zero (+0.0361, 95% CI `[+0.0069, +0.0653]`). The paired 95% bootstrap confidence interval for the MRR@10 difference against Frozen E5 includes zero (`[-0.0687, +0.0996]`). Note that Fine-Tuned E5 achieved higher Recall@3 (0.5177) and Improved BM25 reached 0.4929 than Hybrid RRF (0.4923).
2. **Fine-tuning E5-small observed lower ranking point estimates on human queries:** Frozen E5-small observed MRR@10 **0.7101** versus **0.6413** for Fine-Tuned E5 (Delta: -0.0688, 95% CI `[-0.1740, +0.0364]`), though Recall@3 was higher (0.5177 vs 0.4562). The paired 95% bootstrap confidence interval includes zero for every evaluated metric.
3. **Domain-aware lexical BM25 substantially outperforms whitespace baseline:** On human queries, Improved BM25 achieved MRR@10 **0.6921** vs **0.4140** for whitespace BM25 (+0.2781, 95% CI `[+0.1685, +0.3912]`), matching Frozen E5 Hit@1 (**0.6250**) at $<2.5$ ms query latency. The paired 95% bootstrap confidence interval strictly excludes zero across all metrics.
4. **Benchmark Scope and Design Distinctions:** Both benchmarks evaluated candidate retrieval over the complete 1,068-chunk canonical corpus. Differences between the 54-query and 24-query results reflect benchmark design, query formulation style, query set size (54 vs 24), and relevance target distribution (restricted to 4 held-out documents vs spanning all 12 corpus documents), rather than query authorship alone. Independent evaluation on owner-authored queries provides an essential empirical check against overfitting to automated query distributions.
