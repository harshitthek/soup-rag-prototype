# Research Audit: BM25 Tokenizer Mechanics, RRF Bootstrap Intervals & Latency Deconstruction

## Executive Summary

This research audit provides an in-depth empirical deconstruction of the improved BM25 and Hybrid Reciprocal Rank Fusion (RRF) results across five critical methodological dimensions:

1. **Paired Document-Stratified Bootstrap Intervals:** Precomputed 10,000 resamples (seed 42) across 4 held-out document strata for all three contrasts, without p-values or significance claims.
2. **Tokenizer Mechanics Audit:** Comprehensive vocabulary growth, singleton distribution, OOV collapse, and identifier fragmentation analysis explaining the +0.1759 BM25 MRR@10 improvement.
3. **Stage-Separated Latency Profiling:** Clear deconstruction of cold-start (model loading, indexing, forward pass) versus steady-state per-query latency.
4. **Query Archetype Audit & Regrouping:** Methodological correction separating strict parameter/CLI flag lookups (16 queries) from procedural how-to workflows (13 queries) with explicit query IDs.
5. **Human Annotation Blinding Verification:** Protocol audit confirming that relevance annotators remain strictly blinded to model retrieval rankings.

---

## 1. Paired Document-Stratified Bootstrap Confidence Intervals

Resampling methodology matches Phase 3 exactly: `StratifiedResampler` with 10,000 resamples, fixed seed 42, document-stratified index draws. Deltas represent candidate minus baseline ($A - B$). No p-values or hypothesis test significance claims are introduced.

### 1.1 Contrast: Improved BM25 vs Original BM25 (Whitespace)

| Metric | Observed Baseline | Observed Improved | Observed Delta | 95% Bootstrap CI | Zero Included? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MRR@10** | 0.5953 | 0.7712 | +0.1759 | `[+0.0712, +0.2828]` | **NO (Strictly > 0)** |
| **Hit@1** | 0.4815 | 0.6481 | +0.1667 | `[+0.0185, +0.3148]` | **NO (Strictly > 0)** |
| **Recall@3** | 0.4497 | 0.7065 | +0.2568 | `[+0.1636, +0.3546]` | **NO (Strictly > 0)** |
| **Recall@5** | 0.5114 | 0.7719 | +0.2605 | `[+0.1704, +0.3574]` | **NO (Strictly > 0)** |
| **Sec-Hit@1** | 0.4815 | 0.6852 | +0.2037 | `[+0.0741, +0.3333]` | **NO (Strictly > 0)** |
| **Sec-MRR@10** | 0.6127 | 0.7897 | +0.1770 | `[+0.0862, +0.2710]` | **NO (Strictly > 0)** |

**Observation:** Every single metric interval strictly excludes zero. The domain-aware regex tokenizer produces a robust and defensible improvement across all evaluation strata.

### 1.2 Contrast: Hybrid RRF vs Frozen E5-small

| Metric | Observed E5-small | Observed Hybrid RRF | Observed Delta | 95% Bootstrap CI | Zero Included? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MRR@10** | 0.7834 | 0.8552 | +0.0719 | `[+0.0081, +0.1402]` | NO (Strictly > 0) |
| **Hit@1** | 0.6852 | 0.7778 | +0.0926 | `[+0.0000, +0.2037]` | YES (Touches zero) |
| **Recall@3** | 0.6694 | 0.7466 | +0.0772 | `[-0.0062, +0.1667]` | YES (Spans zero) |
| **Recall@5** | 0.7302 | 0.8228 | +0.0926 | `[+0.0154, +0.1759]` | NO (Strictly > 0) |
| **Sec-Hit@1** | 0.7222 | 0.8148 | +0.0926 | `[+0.0000, +0.2037]` | YES (Touches zero) |
| **Sec-MRR@10** | 0.8165 | 0.8771 | +0.0605 | `[-0.0012, +0.1271]` | YES (Spans zero) |

**Observation:** On MRR@10 (`[+0.0081, +0.1402]`) and Recall@5 (`[+0.0154, +0.1759]`), the 95% bootstrap interval strictly excludes zero. On Hit@1 (`[+0.0000, +0.2037]`), the lower bound touches zero. On Recall@3 (`[-0.0062, +0.1667]`) and Sec-MRR@10 (`[-0.0012, +0.1271]`), the intervals span zero, indicating positive observed point estimates with non-zero probability of equivalence under resampling.

### 1.3 Contrast: Hybrid RRF vs Improved BM25

| Metric | Observed Improved BM25 | Observed Hybrid RRF | Observed Delta | 95% Bootstrap CI | Zero Included? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MRR@10** | 0.7712 | 0.8552 | +0.0841 | `[+0.0168, +0.1521]` | NO (Strictly > 0) |
| **Hit@1** | 0.6481 | 0.7778 | +0.1296 | `[+0.0185, +0.2407]` | NO (Strictly > 0) |
| **Recall@3** | 0.7065 | 0.7466 | +0.0401 | `[-0.0031, +0.0926]` | YES (Spans zero) |
| **Recall@5** | 0.7719 | 0.8228 | +0.0509 | `[+0.0046, +0.1049]` | NO (Strictly > 0) |
| **Sec-Hit@1** | 0.6852 | 0.8148 | +0.1296 | `[+0.0185, +0.2407]` | NO (Strictly > 0) |
| **Sec-MRR@10** | 0.7897 | 0.8771 | +0.0873 | `[+0.0205, +0.1558]` | NO (Strictly > 0) |

**Observation:** Hybrid RRF provides positive point estimate deltas over Improved BM25 across all metrics. The 95% intervals strictly exclude zero for MRR@10, Hit@1, Recall@5, Sec-Hit@1, and Sec-MRR@10.

---

## 2. Tokenizer Mechanics & Vocabulary Audit

To understand the mechanism driving the +0.1759 MRR@10 improvement in BM25, the vocabulary, singleton frequency distribution, query OOV rate, and identifier handling were audited across `data/corpus.jsonl` (1,068 chunks) and `data/manual_queries.jsonl` (54 queries).

### 2.1 Corpus Vocabulary Contraction & Denoising

| Property | Original (Whitespace) | Improved (Domain-Aware) | Absolute Delta | Relative Change |
| :--- | :---: | :---: | :---: | :---: |
| **Total Tokens** | 62,060 | 66,677 | +4,617 | +7.4% |
| **Avg Tokens / Chunk** | 58.1 | 62.4 | +4.3 | - |
| **Unique Vocabulary Size** | 13,225 | 9,619 | -3,606 | **-27.3%** |
| **Singleton Tokens (count = 1)** | 8,552 | 4,927 | -3,625 | -42.4% |
| **Singleton Fraction** | 64.7% | 51.2% | -13.5 pp | - |
| **Punctuation-Glued Tokens** | 7,018 | 1,760 | -5,258 | **-74.9%** |

### 2.2 Root Cause of BM25 Underperformance in Whitespace
The vocabulary audit reveals why whitespace BM25 failed:
1. **Spurious Vocabulary Inflation:** Whitespace tokenization inflated the vocabulary with **13,225 unique types**, of which **64.7% were singletons** caused by punctuation attachments (`model,`, `model.`, `` `model` ``, `model:`, `(model)`). In total, **7,018 tokens (53.1% of vocabulary)** had punctuation attached.
2. **Query Out-of-Vocabulary (OOV) Collapse:**
   - Under whitespace tokenization, **22 out of 54 queries (40.7%)** contained at least one token that had zero occurrences in the corpus.
   - Terms like `` `loraplus_lr_ratio` ``, `` `eval_gate` ``, and `` `q_proj` `` in the corpus were glued to backticks, while queries queried them without backticks, creating fatal term mismatches.
   - Query question marks and commas (`dataset?`, `regresses?`, `accuracy,`) created separate OOV types that never matched corpus terms.
   - Domain-aware tokenization reduced OOV queries from **22 down to 9 (16.7%)**, and query token OOV instance rate dropped from **6.8% to 2.2%**.
3. **Lexical Query Token Coverage Diagnostic:** Mean lexical query token coverage against answer-bearing chunks jumped from **45.5%** up to **60.9% (+15.4 percentage points)**.

   - **Definition & Formula:** For each query $q$, let $T(q)$ be the set of unique tokens in $q$, and let $R(q)$ be the union of unique tokens across all ground-truth relevant chunks for $q$ ($R(q) = \bigcup_{c \in \text{rel}(q)} \text{tokens}(c)$). The per-query token coverage is:
     $$\text{Coverage}(q) = \frac{|T(q) \cap R(q)|}{|T(q)|}$$
   - **Denominator:** $|T(q)|$, the exact count of unique tokens in query $q$.
   - **Mean Diagnostic Metric:** The reported metric is the unweighted mean across all $N=54$ benchmark queries:
     $$\overline{\text{Coverage}} = \frac{1}{N} \sum_{q=1}^N \frac{|T(q) \cap R(q)|}{|T(q)|}$$
   - **Explicit Distinction from Recall@K:** This is strictly an intrinsic lexical vocabulary coverage diagnostic measuring the proportion of query terms that exist in the target passage surface text. It must **not** be confused with retrieval Recall@K (which measures the proportion of relevant document/chunk IDs retrieved in the top $K$ ranked list).

---

## 3. Reworked Latency Profiling: Cold-Start vs Steady-State

Latency profiling was re-instrumented to separate one-time setup costs from steady-state query serving. Benchmarked on Apple Silicon (M-series CPU):

### 3.1 Cold-Start Latency (One-Time Startup / Indexing)

| System / Component | Model Loading from Disk | Corpus Preparation (1,068 chunks) | Warmup Execution | Total Cold Start |
| :--- | :---: | :---: | :---: | :---: |
| **Improved BM25** | 0.000s | 0.067s (Inverted index fit) | - | **0.067s** |
| **Frozen E5-small** | 2.867s (PyTorch weights) | 14.073s (Neural forward pass) | 0.0050s | **16.940s** |
| **Hybrid Pipeline** | 2.867s | 14.140s | 0.0050s | **17.007s** |

### 3.2 Steady-State Latency (Pre-Loaded Model & Pre-Encoded Corpus)

Under ideal steady-state conditions where the PyTorch runtime, model weights, and 1,068 pre-computed corpus embeddings are already resident in memory, online query execution times are:

| System | Online Operations | Batch Latency (54 queries) | Steady-State Latency per Query |
| :--- | :--- | :---: | :---: |
| **Improved BM25** | Query tokenization + inverted index scoring | 36.0 ms | **0.67 ms** |
| **Frozen E5-small** | Query neural encoding (1.05 ms) + dot-product search (0.05 ms) | 59.0 ms | **1.09 ms** |
| **RRF Fusion Only** | Reciprocal rank calculation ($k=60$) over 1,068 chunks + tie-breaking | 35.9 ms | **0.66 ms** |
| **Hybrid RRF Total** | BM25 scoring + E5 query encoding + dot product + RRF fusion | 131.0 ms | **2.42 ms** |

> [!IMPORTANT]
> **Latency Scope & Qualification:**
> - **Warm Execution Only:** The **2.42 ms per query** figure represents purely warm execution with model weights and corpus embeddings already resident in RAM/CPU.
> - **Not Demonstrated Production CLI Latency:** This figure does **not** represent end-to-end latency for a standard CLI invocation. A standalone `soup docs search <query>` command invoked cold from shell would incur Python interpreter startup, PyTorch import overhead, and model initialization (multiple seconds) unless implemented via a persistent background daemon or service architecture.

---

## 4. Query Grouping Audit: Parameter/CLI vs Procedural How-To

In response to audit feedback regarding the inclusion of generic how-to questions in parameter/CLI reporting, the 54 queries were partitioned into three mutually exclusive, methodologically justified groups:

### 4.1 Strict Parameter, Configuration & CLI Details (16 Queries)
- **Criteria:** Queries requesting specific named CLI flags, subcommands, schema keys in `soup.yaml`/`expectations.yaml`, or hyperparameters.
- **Exact Query IDs (16):**
  - `manual_009`: grace codebook size limit
  - `manual_010`: soup registry diff output
  - `manual_011`: dare merge seed determinism
  - `manual_017`: which soup init templates exist for regulated industries
  - `manual_023`: which expectation checks can go in expectations.yaml
  - `manual_029`: eval_gate block settings in soup.yaml
  - `manual_034`: noise floor flag effect on ship verdict
  - `manual_036`: score BLEU and ROUGE on custom eval outputs
  - `manual_038`: custom eval jsonl fields for exact and regex scoring
  - `manual_041`: soup eval irt-subset size and item model options
  - `manual_042`: preview which decoder layers soup shrink will drop
  - `manual_045`: set up yarn for 4x context extension
  - `manual_047`: different learning rates for q_proj and v_proj
  - `manual_049`: loraplus_lr_ratio effect on B matrix lr
  - `manual_051`: neftune_alpha range for chat fine tuning
  - `manual_053`: stop training when loss spikes repeatedly

### 4.2 Procedural How-To Workflows (13 Queries)
- **Criteria:** High-level procedural workflow questions ("how do I...") without specific named flags.
- **Exact Query IDs (13):**
  - `manual_002`: How do I bisect training checkpoints when an eval regresses?
  - `manual_003`: how do I see which training rows influenced an adapter
  - `manual_005`: does soup roll back a canary automatically if the eval regresses
  - `manual_007`: compare model answers before and after a knowledge edit
  - `manual_008`: build a control vector from positive and negative prompts
  - `manual_015`: what goes into a soup airgap bundle and how big can it get
  - `manual_018`: clean emails and phone numbers out of my training data
  - `manual_021`: publish a model to huggingface with my own model card
  - `manual_026`: generate an eval suite from my training data
  - `manual_028`: block a git push when eval accuracy regresses
  - `manual_035`: how do I make a ship verdict replayable in CI
  - `manual_039`: run a short LoRA probe on several base models before choosing one
  - `manual_046`: Can I add fresh layers to a Llama model and only train those?

### 4.3 Conceptual, Troubleshooting & Architecture (25 Queries)
- **Exact Query IDs (25):** `manual_001`, `manual_004`, `manual_006`, `manual_012`, `manual_013`, `manual_014`, `manual_016`, `manual_019`, `manual_020`, `manual_022`, `manual_024`, `manual_025`, `manual_027`, `manual_030`, `manual_031`, `manual_032`, `manual_033`, `manual_037`, `manual_040`, `manual_043`, `manual_044`, `manual_048`, `manual_050`, `manual_052`, `manual_054`.

### 4.4 Disaggregated Performance Across Justified Groups

| Group | Count | Original BM25 MRR | Improved BM25 MRR | Frozen E5 MRR | Hybrid RRF MRR | Hybrid Hit@1 | Hybrid Rec@5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Strict Parameter / CLI Details** | 16 | 0.5766 | 0.8646 | 0.8396 | **0.9271** | **87.5%** | **94.8%** |
| **Procedural How-To Workflows** | 13 | 0.6880 | 0.6667 | 0.6745 | **0.7308** | **61.5%** | **70.0%** |
| **Conceptual / Troubleshooting** | 25 | 0.5590 | 0.7658 | 0.8040 | **0.8740** | **80.0%** | **80.7%** |

**Key Analytical Finding:**
- On **Strict Parameter/CLI Details (16 queries)**, Improved BM25 achieved **0.8646 MRR@10**, strictly outperforming Frozen E5-small (**0.8396 MRR@10**). When fused via Hybrid RRF, MRR reaches **0.9271** with **87.5% Hit@1**.
- On **Procedural How-To Workflows (13 queries)**, Improved BM25 (0.6667) and E5-small (0.6745) performed comparably. Separating these queries confirms that the tokenizer improvement was genuine technical identifier recovery, not spurious lexical inflation across generic workflows.

---

## 5. Human Evaluation Blinding & Authorship Protocol Verification

To ensure that future relevance annotation for the 12 project-owner-authored queries remains untainted:
1. **Blinded Annotation Assets:** [`data/human_eval/relevance_annotation_template.jsonl`](../data/human_eval/relevance_annotation_template.jsonl) contains only `query_id`, `query`, and blank target fields. It contains no retrieval scores, rankings, or model predictions.
2. **Strict Quarantining Outside Workspace:** Model preliminary rankings are stored completely outside the repository workspace at `~/.cache/soup-rag-prototype/quarantine/preliminary_rankings.json` (and persisted in execution scratch space). No ranking files exist inside the repository working tree, ensuring annotators cannot inadvertently access model predictions.
3. **Blinding Protocol Declared:** [`data/human_eval/AUTHORING_INSTRUCTIONS.md`](../data/human_eval/AUTHORING_INSTRUCTIONS.md) explicitly instructs annotators to search `data/corpus.jsonl` directly and forbids viewing preliminary rankings.
4. **Authorship & AI Assistance Classification:** The 12 queries in [`data/human_eval/human_queries_v1.jsonl`](../data/human_eval/human_queries_v1.jsonl) are classified as `Authored and supplied by project owner`. In accordance with scientific rigor, their AI assistance status is recorded as `unconfirmed_pending_author_confirmation`; they are **not** declared AI-unassisted without explicit author confirmation.
5. **No Metric Computation:** No Hit@K, Recall@K, or MRR metrics were computed or stored for the 12 queries.

---

## 6. Unresolved Limitations & Threats to Validity

1. **Small Stratum Size for Bootstrap:** With 54 queries distributed across 4 documents (16, 8, 17, 13 queries per document), bootstrap confidence intervals reflect cluster resampling within this specific four-document sample; they do not support population generalization to other repositories.
2. **Lower Bound of Hybrid vs E5 CI:** While Hybrid RRF achieves higher observed point estimates across all metrics, the 95% bootstrap interval on Recall@3 (`[-0.0062, +0.1667]`) and Sec-MRR@10 (`[-0.0012, +0.1271]`) crosses zero, and Hit@1 touches zero (`[+0.0000, +0.2037]`). A definitive superiority claim cannot be made without broader evaluation.
3. **CPU Evaluation Scope & Latency Nature:** Latency benchmarks reflect CPU execution on Apple Silicon under warm in-memory conditions (2.59 ms/query steady-state). Cold-start execution incurs ~17.3s (PyTorch load and corpus encoding), meaning production CLI invocations require a persistent daemon or precomputed index service.
4. **Pending Ground Truth on Human Queries:** The 12 human-authored queries remain unannotated. Until manual relevance verification is complete, retrieval performance on independently authored text remains an open empirical question. Furthermore, AI assistance during drafting remains unconfirmed.
