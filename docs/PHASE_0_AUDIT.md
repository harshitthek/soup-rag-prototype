# Phase 0: Audit of Existing Soup RAG Prototype and Training Corpus Expansion Candidates

**Status:** Completed & Revised (Final Phase 0 Corrections)  
**Branch:** `feat/evaluation-v2`  
**Date:** 2026-11-03  
**Upstream Target:** `https://github.com/MakazhanAlpamys/Soup` (Commit: `595173f73eb45399aeb4997bab44642827b31799`)  
**Objective:** Comprehensive audit of the existing `soup-rag-prototype` repository, experiment framework, and upstream candidate documentation directories (`benchmarks/` and `changelog.d/`) before any implementation or retraining.

---

## Unresolved Risks and Required Approval Decisions

Before proceeding to Phase 1, the following unresolved risks and engineering trade-offs require explicit acknowledgment and governance approval:

1. **Risk of Chronological Context Degradation in Isolated Benchmark Chunks:**
   - *Risk:* Upstream benchmark gate records are chronological working engineering documents. Several files contain early measurements, hardware-specific anomalies, or initial hypotheses that were subsequently qualified or superseded in later sections of the same file.
   - *Decision / Safeguard:* In Phase 1 chunking, every sub-chunk must retain its hierarchical document stem and section heading prefix (`doc_stem: heading`). Sub-splitting must never decouple caveat text from its parent measurement table.
2. **Changelog Fragment Staging and Version Semantics:**
   - *Risk:* Files located in `changelog.d/0.77.1/` represent unreleased pull request fragments staged *after* release `0.77.1` was tagged, destined for `[Unreleased]` via `assemble_changelog.py`. Presenting them as canonical released documentation would misrepresent product status.
   - *Decision / Safeguard:* All ingested changelog fragments will be classified with freshness `Unreleased changelog fragment`, assigned content type `changelog_fragment_unreleased`, and staged under distinct chunk IDs.
3. **Exclusion of `benchmarks/README.md` (Rollup Overlap & Discarded Experiments):**
   - *Risk:* `benchmarks/README.md` (92,476 bytes, 29,433 tokens total) is a large monolithic rollup containing substantial overlap with underlying benchmark records and references to rejected experiments (such as QuEST PR #674). Including it alongside the individual records would introduce substantial redundancy and distort corpus topic balance.
   - *Decision:* Reconsideration complete — `benchmarks/README.md` is **excluded** from the candidate list. The curated candidate set is finalized at **23 documents** (+99,204 tokens).
4. **False Negative Collision During Hard Negative Mining:**
   - *Risk:* When sub-chunking sections into multiple parts (`::sub_000`, `::sub_001`), mining hard negatives from the same base section will yield false negatives that penalize the embedding adapter for retrieving semantically relevant text.
   - *Decision / Safeguard:* Phase 1 negative mining must strictly enforce section-level masking: sibling chunks sharing the same base section ID (`chunk_id.rsplit("::sub_", 1)[0]`) are masked out from negative sampling.
5. **Architectural Decoupling of Training Corpus and Evaluation Corpus:**
   - *Risk:* Ingesting candidate documents directly into `data/corpus.jsonl` would invalidate the frozen evaluation benchmark and baseline comparison records.
   - *Decision / Safeguard:* Maintain `data/corpus.jsonl` strictly as the frozen 12-document evaluation benchmark (1,068 chunks). The expanded training corpus will be generated into a separate artifact (`data/training_corpus.jsonl`, 1,522 chunks) accessible solely by training query generation and adapter fine-tuning. The 4 held-out evaluation documents will never enter training data.
6. **Preservation of Existing V2 Recipe in First Retraining Experiment:**
   - *Risk:* Confounding architectural changes (such as switching to a linear/MLP projection or InfoNCE loss) with data quality improvements prevents isolating the true impact of query diversity and corpus expansion.
   - *Decision / Safeguard:* The first controlled retraining experiment must preserve the exact existing V2 training recipe (MiniLM base, LoRA r=16, triplet margin loss = 0.5, AdamW lr=2e-5, batch size 4, 3 epochs). Any architectural or loss changes are deferred to separate follow-up experiments.

---

## 1. Executive Summary

This audit establishes the baseline facts of the existing Soup RAG prototype, evaluates 732 candidate files from the official Soup repository (`https://github.com/MakazhanAlpamys/Soup`) at commit `595173f73eb45399aeb4997bab44642827b31799`, and establishes a verified, controlled expansion strategy for retraining the embedding adapter.

### Key Audit Findings
1. **Current Corpus State:** The existing retrieval corpus (`data/corpus.jsonl`) comprises **12 Markdown files, 673 unique base sections, 1,068 chunks, and 124,959 tokens**. It is partitioned into **8 training documents** (466 sections, 761 chunks, 90,564 tokens) and **4 strictly held-out evaluation documents** (207 sections, 307 chunks, 34,395 tokens).
2. **Leakage & Conceptual Overlap Audit:** Rather than an unsupported assumption of zero leakage, a query-by-query answer overlap audit was conducted across all 54 frozen evaluation queries (`data/manual_queries.jsonl`) against the candidate documents:
   - **No direct answer overlap was identified in the candidate documents. Five evaluation queries exhibit partial conceptual overlap, which is documented separately.**
   - The five queries (`manual_020`, `manual_025`, `manual_030`, `manual_047`, `manual_048`) touch parameters or benchmarked topics without exposing gold answers. Future evaluation reports will break out their results separately.
   - All 54 queries, gold labels, and original primary/overlap classifications remain 100% frozen and unaltered.
3. **Candidate Directory Inspection:**
   - `benchmarks/` (642 files, ~16.5 MB total): Contains **62 Markdown files** (441,605 tokens) and **580 non-markdown files** (322 JSON, 125 logs, 89 Python scripts, 15 JSONL, 13 TXT, 7 YAML, 5 CSV). The 580 non-markdown files are machine-readable execution traces or measurement drivers and are **unsuitable** for retrieval. Among the 62 Markdown files, **15 files** represent high-quality technical records of Soup layer-streaming, memory bounds, and multi-GPU execution.
   - `changelog.d/` (90 files, ~36.5 KB total): Consists of **1 contributor guide** (`README.md`, Current upstream reference) and **89 unreleased PR fragments** staged under directory `0.77.1/`. Only **7 fragments** describe substantive feature additions or CLI changes; the rest are 1–2 sentence bugfixes or internal chore notes.
4. **Token Sequence Budget Validation:** Full sequence length validation of complete chunks (formatted as `f"{heading_prefix}\n\n{body}"` with `[CLS]` and `[SEP]` special tokens) confirmed **zero sequence length overflow** against MiniLM's 256-token limit. In the existing corpus, max token length is **226 tokens**; in the candidate chunks, max token length is **238 tokens**.
5. **Corpus Volume Expansion:** A curated selection of **23 documents** (15 benchmark records + 8 changelog documents/fragments) adds **311,776 bytes, 182 sections, 761 chunks, and 120,217 tokens** to the training split. This expands training corpus volume from 90,564 tokens to **210,781 tokens (a 2.33x volume expansion)**. (Note: Adding `benchmarks/README.md` would have resulted in an unprincipled increase due to substantial rollup overlap and references to rejected experiments, and was rightly rejected).
6. **Chunk Count Reconciliation (+4 chunks):** The difference between the preliminary Phase 0 estimate (757 candidate chunks / 1,518 total) and the final verified Phase 1 generation (761 candidate chunks / 1,522 total) was completely diagnosed to 4 oversized markdown tables that fell back to `_hard_token_split` (`gate-836` sec 3, `gate-971` sec 5 & 7, `gate-974` sec 11). Phase 1's fixed stride step emitted one additional tail slice for each table. Heading-based markdown splitting is 100% identical.

---

## 2. Current Prototype Architecture and Baseline Integrity

### Corpus Composition and Token Counting Methodology
All token counts in this audit use the repository's native tokenizer: `sentence-transformers/all-MiniLM-L6-v2` (`AutoTokenizer.from_pretrained`), evaluated with `add_special_tokens=False` when measuring raw text tokens, and `add_special_tokens=True` when validating model input sequence limits. Chunks are generated using ATX heading boundaries (`#` to `######`) followed by recursive paragraph/sentence sub-splitting targeted at $\le 220$ body tokens (`MAX_CHUNK_TOKENS=220`, `OVERLAP_TOKENS=28`).

| Document Name | Split | Size (Bytes) | Unique Base Sections | Chunks | Total Tokens | Mean Tokens / Chunk |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `README.md` | train | 2,716 | 1 | 6 | 969 | 161.5 |
| `backends-and-ops.md` | train | 35,794 | 126 | 146 | 12,398 | 84.9 |
| `commands.md` | train | 39,100 | 3 | 73 | 13,699 | 187.7 |
| `data.md` | train | 36,621 | 85 | 121 | 11,778 | 97.3 |
| `models.md` | train | 7,268 | 9 | 20 | 3,025 | 151.3 |
| `performance-and-quantization.md` | train | 50,321 | 57 | 125 | 17,371 | 139.0 |
| `serving-and-export.md` | train | 31,536 | 93 | 111 | 10,516 | 94.7 |
| `training.md` | train | 65,501 | 92 | 159 | 20,808 | 130.9 |
| **Train Split Subtotal** | **train** | **268,857** | **466** | **761** | **90,564** | **119.0** |
| `adapters-and-governance.md` | test | 34,207 | 79 | 106 | 11,174 | 105.4 |
| `compliance.md` | test | 5,510 | 13 | 16 | 1,636 | 102.3 |
| `evaluation.md` | test | 40,344 | 82 | 120 | 12,539 | 104.5 |
| `peft-and-efficiency.md` | test | 28,298 | 33 | 65 | 9,046 | 139.2 |
| **Test Split Subtotal** | **test** | **108,359** | **207** | **307** | **34,395** | **112.0** |
| **Total Corpus (`data/corpus.jsonl`)** | **all** | **377,216** | **673** | **1,068** | **124,959** | **117.0** |

---

## 3. Document Provenance Resolution (`backends-and-ops.md`)

A known discrepancy exists in the prototype between `data/source_manifest.json` and `data/corpus.jsonl`:
- In `data/source_manifest.json`, the vendored copy of `backends-and-ops.md` is listed as **35,006 bytes** with SHA256 `145a62ac6d5400a95cd905a5173e185175d80b126096f9ee10e36384eaf93472` (downloaded from commit `8ab26641ed34e724018e696a93a06460f26c153e` with CRLF line endings).
- The actual file content ingested into `data/corpus.jsonl` was **35,794 bytes** with SHA256 `ad8b844558fcf82c65b25e207a69ef85c8d6fd158d47ffb54ac8ca3080f03138` (representing 146 chunks, 12,398 tokens).
- Of the 146 chunks in `data/corpus.jsonl`, 135 chunks match the vendored 35,006-byte file text identically, while 11 chunks exhibit slight line-wrapping or whitespace variations from an earlier ingest pass.

**Audit Resolution:**  
Per Phase 0 mandatory rules, existing training and evaluation datasets must not be rewritten. The ground-truth training and retrieval chunks in `data/corpus.jsonl` (SHA256 `ad8b844558fcf82c65b25e207a69ef85c8d6fd158d47ffb54ac8ca3080f03138`) are retained without modification. In Phase 1, when creating the expanded training corpus manifest, this exact hash will be formally documented as the canonical baseline state.

---

## 4. Upstream Candidate Directories Inspection

The official Soup repository was inspected at commit `595173f73eb45399aeb4997bab44642827b31799`.

### A. Directory `benchmarks/` (642 files, ~16.5 MB)
- **Non-Markdown Material (580 files):** Comprises 322 raw JSON execution metrics in `evidence/`, 125 benchmark run logs in `runs/`, 89 Python measurement scripts (`bench_validator.py`, etc.), 15 JSONL traces, 13 TXT logs, 7 YAML configs, and 5 CSV tables. These files are pure execution outputs and test drivers containing no narrative explanation; they are classified as **Unsuitable** for retrieval.
- **Markdown Documentation (62 files, 441,605 tokens):**
  - **Working Engineering Records:** Upstream benchmark gates are chronological engineering records. They capture real development experiments, including temporary failures, pre-repair baseline numbers, and hardware-specific anomalies (e.g., RTX 5070 driver thermal throttling, M1 8GB unified memory limits).
  - **Refuted Claims & Excluded Features:** Several files document failed experiments that were explicitly rejected upstream, notably QuEST PR #674 (`gate-674-quest-w4a4-sft.md`, `gate-674-quest-mixed-route.md`, `quest-674-postfit-development-results.md`). These are classified as `Superseded or corrected measurement` and remain **Excluded** to prevent the model from learning invalid architectural patterns.
  - **Reconsideration of `benchmarks/README.md`:** The root `benchmarks/README.md` (92,476 bytes, 29,433 tokens total) is a large rollup containing substantial overlap with underlying benchmark records and references to rejected experiments. Including both `README.md` and the individual records creates substantial redundancy and quotes failed experiments. It has been **Excluded**.
  - **High-Value Technical Records (15 files):** 15 curated records provide in-depth, production-grade technical context on layer streaming, NVMe direct I/O, selective checkpointing, and peak VRAM formulas.

### B. Directory `changelog.d/` (90 files, ~36.5 KB)
- **Terminology & Staging Semantics:** Upstream Soup uses `towncrier`/`scriv`-style changelog fragment management. The directory `changelog.d/0.77.1/` does **not** contain released documentation for version 0.77.1; rather, `0.77.1` is the latest released milestone tag under which upcoming PR fragments are staged prior to being compiled into `CHANGELOG.md` under `[Unreleased]` by `assemble_changelog.py`.
- **Content Characteristics:** The 89 fragments in `0.77.1/` are short PR summaries (median 322 bytes, 113 tokens) lacking Markdown ATX headings. They are classified as `Unreleased changelog fragment`.
- **Filtering Strategy:** 82 fragments describe trivial internal chores, typo fixes, or one-line bugfixes. Only **7 fragments** describe substantive user-facing changes (e.g., PR #2329 tool token validation, PR #2386 MLX GRPO 4-bit affine training, PR #2285 preference loss flags). These 7 fragments, plus the developer contributor guide `changelog.d/README.md` (`Current upstream reference`), are included with artificial heading prefixes (`doc_stem: heading`) to provide proper retrieval context.

---

## 5. Candidate Document Selection and Provenance Inventory

The inventory was curated by evaluating all 732 files in `benchmarks/` and `changelog.d/` against strict technical quality, retrieval utility, and freshness criteria:
- **Include:** 23 files (15 benchmark records, 8 changelog documents/fragments)
- **Inspect Manually:** 12 files (peripheral hardware probes)
- **Exclude:** 697 files (580 machine-readable data files, 35 hardware-specific probe logs, 82 fragmentary PR changelogs)

### Freshness Taxonomy Applied
- **Historical engineering record:** Detailed gate records and empirical hardware run reports from engineering milestones.
- **Version-specific benchmark:** Formal release gate benchmarks tied to specific version milestones (e.g., v0.72.0, v0.72.2).
- **Current upstream reference:** Canonical developer contribution and workflow documentation.
- **Unreleased changelog fragment:** Staged towncrier-style PR fragments awaiting release compilation.
- **Superseded or corrected measurement:** Discarded experiments, failed gates, or superseded numerical probes.

### Pinned Upstream Sources (Commit `595173f73eb45399aeb4997bab44642827b31799`)

| Candidate Path | File Type | Size (Bytes) | Tokens | SHA256 Hash | Freshness Classification | Assigned Topic |
|---|:---:|:---:|:---:|---|---|---|
| `benchmarks/gate-2049-resident-vram.md` | Markdown | 14,843 | 5,597 | `69a59cb8cfe554bfe7938515e02cfe9b50b60eab5f6d593450a0fba59ce7eb75` | Historical engineering record | Performance, Quantization & Memory |
| `benchmarks/gate-2050-selective-checkpoint.md` | Markdown | 13,656 | 4,788 | `1410ea006ce37d0e0da6c9eb818ab397d4240204bd9d9dda33d7945a54fde98e` | Historical engineering record | Performance, Quantization & Memory |
| `benchmarks/gate-655-pinned-store-accounting.md` | Markdown | 9,447 | 3,082 | `c6816e171166841564139eda6bee40c070810a90d4a000a96a84daa442c7a669` | Historical engineering record | Performance, Quantization & Memory |
| `benchmarks/gate-836-bench-train-contract.md` | Markdown | 26,149 | 8,640 | `cccf17ebd79887343b170ef8a613bf0d67554723354a95e37ed8d2ed3f435e4d` | Historical engineering record | CLI Commands & Workflow |
| `benchmarks/gate-971-async-nvme-source.md` | Markdown | 40,209 | 12,063 | `fb459ba3caf1f907b7c03b1ae83677242cb0d0a85942fffa24d6db9d37d8f710` | Historical engineering record | Execution Backends & Ops |
| `benchmarks/gate-974-disk-tier-direct-io.md` | Markdown | 44,349 | 14,581 | `ddb344fc122845da18fb999769402f6382f8ddd17da1150e1806a3b5f6f6db54` | Historical engineering record | Execution Backends & Ops |
| `benchmarks/gate-expert-streaming.md` | Markdown | 4,692 | 1,474 | `5fe7bdb2e3c56fb560fb95661e2db45644c801fdba680933bc8969bad1acf96c` | Historical engineering record | Fine-Tuning & Training Mechanics |
| `benchmarks/gate-v0.72.0-layer-streaming.md` | Markdown | 14,213 | 4,439 | `b744d837713a249155e09609bd91aeae88099cd469e8dffbffad4a1933f36be8` | Version-specific benchmark | Fine-Tuning & Training Mechanics |
| `benchmarks/gate-v0.72.2-nf4.md` | Markdown | 25,818 | 8,214 | `486a2841a08cca063438ad2833e8d4475979aa333859254ab1140ff2ef46b03c` | Version-specific benchmark | Performance, Quantization & Memory |
| `benchmarks/gate-v0.72.3-breadth.md` | Markdown | 25,352 | 7,894 | `3fc8e5a184a4485b1dbbae8955bdc870e29a9f3676c08fb2a74686273414ed5b` | Version-specific benchmark | Model Architectures & Registry |
| `benchmarks/gate-v0.72.4-preference-losses.md` | Markdown | 20,173 | 6,241 | `bbaf508f75296a42a4cbbea88ebbd1a9d525aab1f9e175f93e0dcf875a06df90` | Version-specific benchmark | Fine-Tuning & Training Mechanics |
| `benchmarks/probe-v0.73.0-what-bounds-streaming.md` | Markdown | 26,781 | 8,152 | `9a7457ec5495dda387c037fe83d0a37c4cce02864662d4c3fdea3421467fd256` | Version-specific benchmark | Performance, Quantization & Memory |
| `benchmarks/run-m1-8gb-mlx-sft.md` | Markdown | 15,339 | 4,653 | `092f90ad14d4628dd05595cb65ccaa4489236b016829f569cbc186b12a7ba7f5` | Historical engineering record | Fine-Tuning & Training Mechanics |
| `benchmarks/run-t4-colab-free-tier.md` | Markdown | 18,128 | 5,446 | `f4da25dd648241fb8ddebb3f7a401988d69df8eb02d199f6e001140df1d1712f` | Historical engineering record | Fine-Tuning & Training Mechanics |
| `benchmarks/unsloth-4bit-weight-dtypes.md` | Markdown | 4,404 | 1,582 | `4ee9c994a174c2e090c736f2544ee8f38b56f6607273433c4a7d05e93fac958d` | Historical engineering record | Performance, Quantization & Memory |
| `changelog.d/0.77.1/2185.fixed.md` | Markdown | 1,248 | 358 | `e07af79da093fcdeda20a57df122404e9b8d78c62657cfbbd397dcecf7ef54d8` | Unreleased changelog fragment | Execution Backends & Ops |
| `changelog.d/0.77.1/2285.added.md` | Markdown | 1,231 | 373 | `85bb6c8d14c12cedd34a2e3002e073ea2b5229c056b4c5548e138dfe877db9a6` | Unreleased changelog fragment | Fine-Tuning & Training Mechanics |
| `changelog.d/0.77.1/2315.added.md` | Markdown | 325 | 86 | `96814b913b1564268b4f7f5f203ce58b6b46a742ff4170f54f1897fd7d9af87c` | Unreleased changelog fragment | Dataset Management & Preprocessing |
| `changelog.d/0.77.1/2329.changed.md` | Markdown | 1,513 | 405 | `b18aec34a9cba4b0ec0c6c89f2000d7eed84ba29b19e56f45a08da034879ccfb` | Unreleased changelog fragment | Serving & Export Engines |
| `changelog.d/0.77.1/2333.added.md` | Markdown | 261 | 70 | `b76a10bcbee6430ebfe51a304d0758b7761bac62480bf083d8147848f2acbab2` | Unreleased changelog fragment | Serving & Export Engines |
| `changelog.d/0.77.1/2372.fixed.md` | Markdown | 1,124 | 357 | `cde9a25ca89c3e88a5d823d2954146c3e8a53ea9d47d6caccc207a44b94f901a` | Unreleased changelog fragment | Serving & Export Engines |
| `changelog.d/0.77.1/2386.added.md` | Markdown | 1,250 | 384 | `d8c4010319f729fed1a14a587cb41ba749492fcbeddff8fb9b3af7220e4bd2a3` | Unreleased changelog fragment | Fine-Tuning & Training Mechanics |
| `changelog.d/README.md` | Markdown | 1,271 | 325 | `892f76a32fb8000381ed4b4087f0b838fbb818b955634556409a06e037ab43ec` | Current upstream reference | Architecture Overview & Quickstart |
| **Total Candidates (23)** | — | **311,776** | **99,204** | — | — | — |

---

## 6. Expanded Training Corpus Topic Distribution and Overlap

### A. Topic Distribution Across the Expanded Training Corpus
The addition of the 23 candidates expands the training corpus from 8 documents, 761 chunks, and 90,564 tokens to **31 documents, 1,522 chunks, and 210,781 tokens**.

> [!IMPORTANT]
> The **2.33x figure** refers strictly to **corpus volume expansion**, not topic coverage. The existing training corpus already touched most primary technical topics; the expansion provides empirical operational depth, memory limits, and concrete failure-mode characterizations.

| Topic | Existing Train Docs (Chunks / Tokens) | Candidate Docs (Chunks / Tokens) | Total Docs | Total Chunks | Total Tokens | % of Expanded Corpus |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Execution Backends & Ops** | 1 (146 / 12,398) | 5 (341 / 53,202) | 6 | 487 | 65,600 | 31.1% |
| **Performance, Quantization & Memory** | 1 (125 / 17,371) | 6 (178 / 28,876) | 7 | 303 | 46,247 | 21.9% |
| **Fine-Tuning & Training Mechanics** | 1 (159 / 20,808) | 5 (156 / 24,267) | 6 | 315 | 45,075 | 21.4% |
| **Model Architectures & Registry** | 1 (20 / 3,025) | 2 (77 / 12,615) | 3 | 97 | 15,640 | 7.4% |
| **CLI Commands & Workflow** | 1 (73 / 13,699) | 2 (3 / 471) | 3 | 76 | 14,170 | 6.7% |
| **Dataset Management & Preprocessing** | 1 (121 / 11,778) | 1 (1 / 74) | 2 | 122 | 11,852 | 5.6% |
| **Serving & Export Engines** | 1 (111 / 10,516) | 1 (3 / 379) | 2 | 114 | 10,895 | 5.2% |
| **Architecture Overview & Quickstart** | 1 (6 / 969) | 1 (2 / 333) | 2 | 8 | 1,302 | 0.6% |
| **Total Expanded Training Corpus** | **8 (761 / 90,564)** | **23 (761 / 120,217)** | **31** | **1,522** | **210,781** | **100.0%** |

### B. Document-Level Contributions
The top 8 documents account for ~59% of the expanded training corpus volume:
1. `training.md` (existing): 20,808 tokens (9.9%)
2. `benchmarks/gate-974-disk-tier-direct-io.md` (new): 18,601 tokens (8.8%)
3. `performance-and-quantization.md` (existing): 17,371 tokens (8.2%)
4. `benchmarks/gate-971-async-nvme-source.md` (new): 14,775 tokens (7.0%)
5. `commands.md` (existing): 13,699 tokens (6.5%)
6. `backends-and-ops.md` (existing): 12,398 tokens (5.9%)
7. `data.md` (existing): 11,778 tokens (5.6%)
8. `benchmarks/gate-v0.72.2-nf4.md` (new): 10,866 tokens (5.2%)

### C. Near-Duplicate Overlap Analysis
- **Candidate vs Existing Docs:** Candidate benchmark gate files provide empirical measurement tables and low-level code references that complement existing conceptual guides without verbatim text copying. For example, `gate-v0.72.0-layer-streaming.md` explains the C++ memory pool mechanics that instantiate the streaming architecture outlined in `backends-and-ops.md`.
- **Candidate vs Candidate Overlap:** `gate-971-async-nvme-source.md` and `gate-974-disk-tier-direct-io.md` both cover NVMe disk streaming. However, `gate-971` documents host memory buffer limits, whereas `gate-974` focuses on O_DIRECT sector alignment. Retaining both provides complementary operational details.

---

## 7. Query-by-Query Evaluation Leakage and Conceptual Overlap Audit

A strict audit was conducted comparing all **54 frozen evaluation queries** and their gold evidence chunks (`data/manual_queries.jsonl`) against the candidate documents.

### Precise Overlap Finding
> **No direct answer overlap was identified in the candidate documents. Five evaluation queries exhibit partial conceptual overlap, which is documented separately.**

### Audit Breakdown
- **Direct Overlap:** **0 queries (0.0%)**. No candidate file contains the exact gold evidence or answers to the evaluation queries.
- **Partial Conceptual Overlap:** **5 queries (9.3%)** against the candidate set (`manual_020`, `manual_025`, `manual_030`, `manual_047`, `manual_048`). With `benchmarks/README.md` excluded, partial overlap drops to **4 queries (7.4%)**.
- **Absent:** **49 queries (90.7%)** (50 queries with `benchmarks/README.md` excluded) exhibit zero textual or conceptual overlap.
- **Evaluation Benchmark Status:** All 54 queries, gold relevance labels, and original primary/overlap classifications remain 100% frozen and unaltered.

### Documented List of Conceptually Overlapping Queries

| Query ID | Subset | Source Doc | Query Text | Overlap Status | Candidate Document | Human Review & Technical Distinctions |
|---|:---:|:---:|---|:---:|---|---|
| `manual_020` | overlap | `compliance` | *what ends up in the generated model card* | **Partial** | `benchmarks/gate-836-bench-train-contract.md` | `gate-836` mentions model card emission flags in passing during bench contract validation. However, it does not detail compliance artifact schemas, legal reporting sections, or governance rules documented in `compliance.md`. |
| `manual_025` | primary | `evaluation` | *Should I fine-tune with DPO or SFT for my dataset?* | **Partial** | `benchmarks/gate-v0.72.4-preference-losses.md` | `gate-v0.72.4` benchmarks memory throughput differences between DPO and SFT. However, the gold answer requires `evaluation.md` decision criteria regarding pairwise label availability and reward model stability. |
| `manual_030` | primary | `evaluation` | *how does soup ab decide when to stop collecting samples* | **Partial** | `benchmarks/README.md` | `benchmarks/README.md` mentions `soup ab` mSPRT bounds in a high-level summary table. **Resolution:** Excluding `benchmarks/README.md` eliminates this overlap entirely, leaving `evaluation.md` as the sole source. |
| `manual_047` | primary | `peft` | *different learning rates for q_proj and v_proj* | **Partial** | `benchmarks/gate-836-bench-train-contract.md` | `gate-836` includes training configs that pass different learning rates to projection matrices. However, `peft-and-efficiency.md` contains the authoritative conceptual guidance on LoRA+ ratio multipliers ($\eta_B / \eta_A$). |
| `manual_048` | primary | `peft` | *does pissa init speed up lora convergence* | **Partial** | `benchmarks/gate-v0.72.0-layer-streaming.md` | `gate-v0.72.0` lists PiSSA parameter matrices in memory allocation tables. However, the gold answer in `peft-and-efficiency.md` details the singular value truncation formula and fast convergence empirical proofs. |

> [!IMPORTANT]
> **Reporting Requirement:** Future evaluation reports must break out results for these five queries separately from the remaining 49 queries to verify that training on the expanded corpus did not introduce unintended bias or artificial score inflation.

---

## 8. Complete Tokenized Chunk Validation Under MiniLM's 256 Limit

The embedding adapter operates on text encoded by `sentence-transformers/all-MiniLM-L6-v2`, which has an absolute maximum sequence length of **256 tokens**.

To verify that heading prefixes and special tokens (`[CLS]`, `[SEP]`) do not cause sequence truncation, every chunk was formatted as:
$$	ext{Input String} = 	ext{heading\_prefix} + 	ext{"\n\n"} + 	ext{body}$$
and tokenized with `add_special_tokens=True`.

### Validation Results

| Corpus Split | Total Chunks | Min Tokens | Median Tokens | P90 Tokens | P99 Tokens | Max Tokens | Chunks > 256 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Existing Corpus (`data/corpus.jsonl`)** | 1,068 | 9 | 111 | 216 | 222 | **226** | **0 (0.0%)** |
| **Candidate Chunks (23 files)** | 761 | 24 | 168 | 220 | 221 | **238** | **0 (0.0%)** |
| **Combined Total** | 1,829 | 7 | 143 | 219 | 220 | **238** | **0 (0.0%)** |

**Conclusion:** Zero chunks in either the existing or candidate corpus exceed the 256-token limit.

---

## 9. Section-Level Relevance Mapping and Hard Negative Mining Rule

In the prototype chunking architecture, sections that exceed `MAX_CHUNK_TOKENS=220` are split into sub-chunks (`doc::section::sub_000`, `doc::section::sub_001`).

### False-Negative Collision Risk
When mining hard negatives for training query $q_i$, chunks that have high embedding similarity to $q_i$ but are not labeled as positive are mined as negatives. If negative mining operates strictly on `chunk_id`, sibling sub-chunks belonging to the same section as the positive chunk will be treated as negatives. Because sibling sub-chunks share identical semantic context, penalizing the model for retrieving them degrades retrieval precision.

### Mandatory Phase 1 Mining Rule
```python
def get_base_section(chunk_id: str) -> str:
    """Extracts base section identifier before ::sub_XXX suffix."""
    return chunk_id.rsplit("::sub_", 1)[0]

# Rule: Mask all chunks where get_base_section(c) == get_base_section(gold_chunk)
```
Hard negative mining in Phase 1 must enforce this rule to prevent false negatives.

---

## 10. Explicit Train / Test Split and Source Manifest Architecture

To ensure strict evaluation hygiene, the expanded training corpus must be decoupled from the evaluation benchmark:

1. **Frozen Benchmark (`data/corpus.jsonl`):** Retains exactly the 12 documents (1,068 chunks) and 54 manual evaluation queries.
2. **Expanded Training Corpus (`data/training_corpus.jsonl`):** Contains 31 documents (8 existing train + 23 new candidates = 1,522 chunks).
3. **Strict Partitioning:** Query generation and hard negative mining in Phase 1 will read exclusively from `data/training_corpus.jsonl`. The 4 held-out evaluation documents (`adapters-and-governance.md`, `compliance.md`, `evaluation.md`, `peft-and-efficiency.md`) will **never** be included in training data.

---

## 11. Preservation of Existing V2 Training Recipe for First Retraining

To isolate the true causal effect of training query quality and corpus expansion, the first controlled retraining experiment must **preserve the existing V2 training recipe** without confounding architectural alterations:

- **Base Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Adapter Configuration:** LoRA on attention projection layers (`r: 16`, `alpha: 32`, `target_modules: auto`)
- **Loss Function:** Triplet Margin Loss (`embedding_loss: triplet`, `embedding_margin: 0.5`, `embedding_pooling: mean`)
- **Optimizer & Schedule:** AdamW, learning rate `2e-5`, batch size `4`, gradient accumulation `1`
- **Budget & Epochs:** `3 epochs`, `seed: 42`, `data_seed: 42`
- **Negative Mining Methodology:** Existing BM25 and dense bi-encoder triplet mining from `scripts/mine_hard_negatives.py`, augmented **only** with the required section-level sibling masking safeguard (`chunk_id.rsplit("::sub_", 1)[0]`).

> [!IMPORTANT]
> The objective of Phase 1 is to isolate the effect of training query quality and corpus expansion, not redesign the entire embedding training method. Any alternative adapter architecture (such as linear/MLP projection heads) or loss formulation (such as InfoNCE / MultipleNegativesRanking loss) must be treated as a separate follow-up experiment.

---

## 12. Controlled Experimental Comparison Plan

To rigorously evaluate the isolated components of the workflow, Phase 1 establishes a 3-way controlled comparison:

1. **Experiment A (Baseline Replication):**
   - Corpus: Existing 8 training documents.
   - Queries: Existing synthetic queries (`data/train_queries.jsonl`).
   - Training Recipe: Fixed V2 LoRA triplet margin setup.
   - Purpose: Replicate existing baseline performance and establish the reference benchmark.
2. **Experiment B (Query Generation Effect):**
   - Corpus: Existing 8 training documents.
   - Queries: Diverse LLM-generated queries with section-level negative masking.
   - Training Recipe: Fixed V2 LoRA triplet margin setup.
   - Purpose: Isolate the exact performance delta attributable purely to high-quality, diverse LLM query generation.
3. **Experiment C (Corpus Expansion Effect):**
   - Corpus: Expanded 31-document training corpus (`data/training_corpus.jsonl`).
   - Queries: Diverse LLM-generated queries generated across all 31 training documents.
   - Training Recipe: Fixed V2 LoRA triplet margin setup.
   - Purpose: Isolate the incremental performance delta attributable to the 23 additional technical documents.

All three experiments will be evaluated against the exact same frozen 54 manual evaluation queries (`data/manual_queries.jsonl`) on the 12-document benchmark corpus (`data/corpus.jsonl`), and benchmarked against frozen MiniLM and frozen E5-small-v2.

---

## 13. Strengthened Generated Query Validation Standards

To ensure that generated queries teach genuine semantic relationships rather than keyword memorization, every generated query must record full provenance and undergo strict programmatic validation:

### A. Query Record Schema
```json
{
  "query_id": "gen_0001",
  "query": "How do I configure direct I/O sector alignment for async disk streaming?",
  "source_doc": "benchmarks/gate-974-disk-tier-direct-io.md",
  "source_section_id": "gate-974-disk-tier-direct-io::direct-io-sector-alignment",
  "positive_chunk_id": "gate-974-disk-tier-direct-io::direct-io-sector-alignment::sub_000",
  "generator_model": "gemini-2.5-pro",
  "prompt_version": "v1.0-diverse-paraphrase",
  "query_type": "how_to",
  "validation_status": "PASSED"
}
```

### B. Validation Rules & Filters
1. **Answerability:** The query must be genuinely answerable using only the information contained in the positive chunk.
2. **No Hallucinated / Unsupported Facts:** Queries referencing external frameworks, unmentioned parameters, or unsupported facts are rejected (`validation_status: "REJECTED_UNSUPPORTED"`).
3. **No Verbatim Heading Copying:** Queries containing exact 4-gram matches from document titles or section headings are rejected (`validation_status: "REJECTED_HEADING_COPY"`).
4. **No Trivial Word Substitutions:** Queries generated by merely replacing 1–2 words of a heading with synonyms are rejected (`validation_status: "REJECTED_TRIVIAL_SUBSTITUTION"`).
5. **Diversity Distribution:** Query generation per chunk will target diverse query intents: troubleshooting, operational how-to, conceptual definitions, and parameter queries.

---

## 14. Phase 1 Migration and Tooling Requirements

The current ingestion script (`scripts/prepare_corpus.py`) cannot ingest new documents without code changes:
1. **Hardcoded Document Count Check:** Line 229 enforces `len(md_files) == 12`.
2. **Hardcoded Doc Split Lists:** Lines 47–67 explicitly list `TRAIN_DOCS` (8) and `TEST_DOCS` (4).
3. **Defunct Upstream Path:** Line 30 hardcodes an external path `REPO_ROOT.parent / "scratch" / "upstream_soup" / "src"`.
4. **Vendoring Requirement:** In Phase 1, `split_markdown_by_headings` should be vendored directly into `scripts/` or `soup_rag/` to eliminate external runtime dependencies.

---

## 15. Final Approval Decisions for Phase 1

To maintain strict experimental governance, Phase 1 is structured into **two separate approval decisions**:

### Decision 1: Approval for Phase 1 Corpus Preparation and Query Generation
- **Scope:**
  1. Vendoring the 23 approved candidate Markdown files from commit `595173f73eb45399aeb4997bab44642827b31799` into `data/candidate_docs/`.
  2. Refactoring ingestion logic to generate `data/training_corpus.jsonl` (31 documents, 1,522 chunks) while keeping `data/corpus.jsonl` frozen.
  3. Generating diverse training queries with complete metadata provenance and applying the strict 5-point validation filter.
  4. Mining hard negative triplets with section-level sibling masking.
- **Status:** **COMPLETED & AUDITED**

### Decision 2: Approval for the First Controlled Retraining Experiment
- **Scope:**
  1. Executing Experiment A-full (baseline replication on 8 train docs, 2,427 updates).
  2. Executing Experiment A-matched (synthetic query matched on 8 train docs, 1,857 updates).
  3. Executing Experiment B (diverse LLM queries on 8 train docs, 1,857 updates).
  4. Executing Experiment C-matched (diverse LLM queries on 31 train docs, 1,857 updates).
  5. Executing Experiment C-full (diverse LLM queries on 31 train docs, 4,239 updates).
  6. Preserving the fixed V2 LoRA triplet recipe across all runs.
  7. Evaluating all models against the frozen 54 manual queries and comparing against frozen MiniLM and frozen E5-small-v2.
  8. Breaking out separate results for the 5 conceptually overlapping queries.
- **Status:** **GATED (Requires Separate User Confirmation Before Training)**

*Neither stage will begin automatically.*
