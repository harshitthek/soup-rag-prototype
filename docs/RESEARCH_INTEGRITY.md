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
| `data/manual_queries.jsonl` (54 queries) | Synthetic Evaluation Benchmark | Collaborative drafting with AI | Project owner drafted with LLM assistance | AI-assisted benchmark |
| `data/human_eval/human_queries_v2.jsonl` (24 queries) | Independent Evaluation Benchmark | Direct Human Authoring | Project owner authored without AI assistance | **Confirmed Unassisted Human** |

### Detailed Provenance (54-Query AI-Assisted Benchmark):
1. **Query Generation (AI-Assisted):** The 54 evaluation queries in `data/manual_queries.jsonl` were formulated in collaborative sessions between the project owner and an AI assistant. The exact prompts, model versions, and session transcripts used during query drafting were not formally logged in the repository and are **undocumented**.
2. **Relevance Label Assignment (Undocumented AI Involvement):** Candidate relevance labels (`relevant_chunk_ids`, `relevant_section_ids`, `evidence_chunk_ids`, `rationale`) are stored in `data/manual_queries.jsonl`. However, repository records do not establish whether relevance labels were initially proposed by the AI assistant or identified directly by the human author from the corpus. Because this cannot be verified from existing artifacts, AI involvement in candidate relevance annotation must be treated as **undocumented**.
3. **Internal Review:** The project owner verified and approved the final queries and relevance labels. However, this was an internal author review, **not an independent third-party annotation or external human audit**.
4. **Stylistic Phrasing Alignment Risk:** Because Gemini generated the training queries for Experiments B and C, and AI assistance was used in drafting the 54 evaluation queries, phrasing alignment exists between the AI-generated training data and the AI-assisted evaluation benchmark. This alignment favored models trained on LLM-generated queries over heuristic baselines or off-the-shelf encoders.

---

## 2. Independent Human Benchmark v2 (`human_eval_v2`)

### Provenance and Authorship:
The independent human evaluation benchmark comprises 24 queries (`soup_human_001` through `soup_human_024`) provided directly by the project owner.
- **Confirmed Unassisted Human Authorship:** The project owner authored these 24 questions directly without AI assistance. No LLM was used to generate questions, rewrite syntax, correct typos, or suggest alternatives. Real developer traits—including domain terminology, informal grammar, and typos (e.g. `breaked`, `guarentees`)—are preserved verbatim.
- **Full Corpus Breadth:** Unlike the 54-query set which was restricted to 4 held-out documents, the 24 human queries span all 12 Soup documentation files (`adapters-and-governance.md`, `backends-and-ops.md`, `commands.md`, `compliance.md`, `data.md`, `evaluation.md`, `models.md`, `peft-and-efficiency.md`, `performance-and-quantization.md`, `README.md`, `serving-and-export.md`, `training.md`).
- **No Artificial Category Quotas:** Queries reflect natural developer questions without forced document quotas or synthetic intent buckets.
- **Mechanical Annotation Resolution:** Alongside each query, the author provided a specific source document and reference portion (e.g. section heading or feature name). Annotations were resolved through **mechanical document mapping** to canonical indexed chunk IDs and base section IDs in `data/corpus.jsonl`. No AI model was involved in proposing, generating, or ranking relevance labels.

### Complete Withdrawal of 12-Query Draft:
An interim draft of 12 queries (`human_queries_v1.jsonl`) was initially collected. Because its AI-assistance status was unconfirmed and preliminary rankings had inadvertently been generated, the 12-query draft, its annotation templates, and its external quarantine cache (`~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json`) have been **completely withdrawn and deleted**. The 24-query v2 dataset replaces it entirely.

### Frozen Benchmark Artifacts:
- **Query File:** `data/human_eval/human_queries_v2.jsonl` (SHA256: `6d917ef3e89e18d0e87084804d3598bf53ef51971ff77259a768150f3a730d58`)
- **Annotation File:** `data/human_eval/relevance_annotations_v2.jsonl` (SHA256: `51f66a794505c6e9cc18e3f8d8008850c4c114aabf3682304196e7dfba2426a5`)
- **Corpus Fingerprint:** `data/corpus.jsonl` (SHA256: `d787703e048a641884274e57f5802e328e43c637a0971217601e6a37128393e3`)
- **Manifest:** `data/human_eval/manifest_v2.json` (`status: "frozen"`)

---

## 3. Separation of Benchmarks & Experimental Findings

| Benchmark | Query Count | Authorship | Corpus Scope | BM25 (Imp) MRR@10 | Frozen E5 MRR@10 | FT E5 (2e-5) MRR@10 | Hybrid RRF MRR@10 |
|---|---|---|---|---|---|---|---|
| **Synthetic Benchmark** (`manual_queries.jsonl`) | 54 | AI-Assisted collaborative drafting | 4 held-out docs (307 chunks) | 0.5755 | 0.7834 | 0.7634 | 0.7937 |
| **Independent Human Benchmark** (`human_queries_v2.jsonl`) | 24 | Confirmed Unassisted Human | Full corpus 12 docs (1,068 chunks) | 0.6921 | 0.7101 | 0.6413 | 0.7254 |

### Key Takeaways from the Human Evaluation:
1. **Hybrid RRF achieves the highest retrieval effectiveness:** Point estimates on human queries show Hybrid RRF (BM25 + Frozen E5) leading with MRR@10 **0.7254** and Sec-MRR@10 **0.7292**, with a strictly positive bootstrap gain on Recall@3 (+0.0361, 95% CI `[+0.0069, +0.0653]`).
2. **Fine-tuning E5-small does not improve over Frozen E5 on human queries:** Frozen E5-small achieved MRR@10 **0.7101** versus **0.6413** for Fine-Tuned E5 (Delta: -0.0688). Synthetic triplet training degraded performance on authentic developer phrasing.
3. **Lexical BM25 surges on authentic queries:** On human queries, Improved BM25 achieved MRR@10 **0.6921** and Hit@1 **0.6250** (tied with Frozen E5 and Hybrid RRF), operating at $<2.5$ ms query latency. Developer queries rely heavily on exact identifier tokens, making domain-aware lexical retrieval essential.
4. **Synthetic benchmarks overstate adapter gains:** Models fine-tuned on synthetic queries learn stylistic shortcuts that transfer poorly to human developers, demonstrating the critical necessity of independent, unaided human benchmarks.
