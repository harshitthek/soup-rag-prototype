# Soup RAG Evaluation v2 — Experiment Specification

Canonical methodology for the v2 evaluation. Implementation branches from this
document; when they conflict, this document wins. Approved 2026-10-30.

## 1. Final corrections incorporated (2026-10-30)

1. **Overlap thresholds are provisional review flags, not calibrated
   thresholds.** The lexical (default 0.25) and semantic (default 0.65)
   thresholds in the cross-corpus overlap detector are starting points for
   human review, tunable via CLI flags. The train/test chunk similarity
   statistics observed during planning do **not** calibrate
   query-to-training-chunk overlap thresholds; they only showed that
   chunk-level near-duplication across the split is rare.
2. **Failure classifier naming and empty-ranking handling.** The category
   `relevant_sibling_top1` is renamed `relevant_section_unlabeled_chunk_top1`.
   The classifier handles an empty ranking defensively with the dedicated leaf
   `empty_ranking` (unreachable with the fixed 1,068-chunk corpus; unit-tested).
3. **v1 artifacts stay completely unchanged.** No v1 data file, result file,
   script, config, or training artifact is modified for v2. The historical
   singleton-label equivalence of v1's binary "recall@k" with Hit@K is
   explained only here and in new v2 documentation, never in v1 files.
4. **Implementation branch** is `feat/evaluation-v2`, created from latest
   `origin/main` (= PR #2 merge `a5d608f`).

## 2. Goal

Determine whether the Soup LoRA fine-tuned `all-MiniLM-L6-v2` adapter
(`output_embedding`, r=16/α=32, query+value, triplet margin 0.5) improves
retrieval on **natural-language (non-synthetic) queries** over the four
held-out documents, measured at chunk and section granularity, against BM25
and frozen `intfloat/e5-small-v2`. The query set is owner-approved
(machine-drafted, see the §4 amendment). A negative result is acceptable.

## 3. Frozen inputs (v1, never modified)

- Corpus: `data/corpus.jsonl` (1,068 chunks; 761 train / 307 test).
- Split: `data/document_split.json` (8 train / 4 test docs).
- v1 queries: `data/eval_queries.jsonl` (497 synthetic), `data/train_query_labels.jsonl` (1,078).
- Training data: `data/train_triplets.jsonl`, `data/hard_negatives.jsonl`.
- Adapter: `output_embedding/adapter_model.safetensors` + `adapter_config.json` + `soup_run.json`.
- v1 results: `results/baseline.json`, `results/candidate.json`, `results/comparison.md`.
- v1 scripts: `scripts/generate_queries.py`, `scripts/mine_hard_negatives.py`, `config/embedding.yaml`.
- Base model revisions: MiniLM `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
  (from `soup_run.json`); E5-small-v2 `ffb93f3bd4047442299a41ebb6fa998a38507c52`.

## 4. Manual query dataset (Phase 1; owner-approved, see amendment)

- 54 queries. Original rule (superseded by the amendment at the end of this
  list): authored exclusively by the project owner, no LLM generation, no
  drafting, no paraphrasing of owner wording by the tooling.
- Allocation: adapters-and-governance 16 · compliance 8 · evaluation 17 ·
  peft-and-efficiency 13 (tolerance ±2 per document).
- ≥6 queries must target multi-chunk sections.
- Query types (controlled vocabulary): `conceptual`, `how_to`,
  `troubleshooting`, `config_behavior`, `relationship`, `command_detail`.
- Leakage rules: no copied heading phrases (≥4 consecutive normalized tokens
  from any held-out heading), no mechanical template phrasing, no unnecessary
  repetition of distinctive chunk phrases; legitimate command/flag/concept
  terminology is allowed.
- Excluded degenerate sections: `evaluation::1-0`, `evaluation::0-5`.

> **Amendment (2026-10-31).** The owner originally required exclusive human
> authorship and later instructed Qoder to draft all 54 queries. The dataset is
> machine-drafted at the owner's explicit request, then owner-reviewed and
> owner-frozen. This weakens the human-authorship property of the benchmark
> relative to the original design; it is recorded here rather than silently
> changed. All other rules in this section remain in force.

### Record schema (`data/manual_queries.jsonl`, one JSON object per line)

```json
{
  "query_id": "manual_001",
  "query": "<frozen query wording>",
  "source_document": "evaluation",
  "query_type": "troubleshooting",
  "subset": "primary",
  "relevant_section_ids": ["evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json"],
  "relevant_chunk_ids": ["evaluation::offline-…::sub_001"],
  "evidence_chunk_ids": ["evaluation::offline-…::sub_001"],
  "rationale": "<annotation rationale>",
  "cross_corpus_overlap": null
}
```

- `subset`: `primary` (answer-bearing content genuinely held out) or
  `overlap` (equivalent answer exists in a training document; relevant IDs may
  then include train chunks; `cross_corpus_overlap` required).
- Annotation rules: a section/chunk is relevant only if it carries
  answer-bearing information (not a mere mention); siblings are never labeled
  relevant automatically; `evidence_chunk_ids ⊆ relevant_chunk_ids`;
  every labeled chunk's base section must be in `relevant_section_ids`.

## 5. Metrics (Phase 2)

Ranking: exact dot product on L2-normalized vectors (dense) or BM25 scores;
stable sort with lexicographic `chunk_id` tie-break; top-10 returned.

Chunk level (over ranked chunks):
- `hit@K = 1[any relevant chunk in top-K]`
- `recall@K = |top-K ∩ relevant_chunks| / |relevant_chunks|`
- `mrr@10 = 1 / first rank of any relevant chunk within top 10`

Section level (chunks collapsed to unique canonical sections via
`get_base_section` = `chunk_id.rsplit("::sub_", 1)[0]`, preserving
first-occurrence rank):
- `sec_hit@K = 1[any relevant section in top-K unique sections]`
- `sec_recall@K = |top-K unique sections ∩ relevant_sections| / |relevant_sections|`
- `sec_mrr@10 = 1 / first rank of any relevant section within top 10 unique sections`

Edge cases (unit-tested): single item (recall == hit); multiple chunks in one
section (fractional chunk recall, binary section recall); multiple sections;
`|relevant| > K` (recall capped below 1).

v1 note (documented in v2 docs only): v1's binary "recall@k" was computed over
singleton label sets, where hit == recall. v1 files are not relabeled.

## 6. Failure classification (Phase 2)

Deterministic, mutually exclusive; exactly one leaf per (retriever, query):

```
classify(R, q):
    top10 = R.ranked[:10]
    if not top10:                                      return empty_ranking
    if top10[0].chunk_id in q.relevant_chunk_ids:      return exact_relevant_chunk_top1
    if top10[0].section_id in q.relevant_section_ids:  return relevant_section_unlabeled_chunk_top1
    if any top10[1:].chunk_id in q.relevant_chunk_ids: return relevant_chunk_below_top1
    if any top10.section_id in q.relevant_section_ids: return relevant_section_below_top1
    if top10[0].doc_name == q.source_document:         return wrong_section_same_document
    return wrong_document
```

- `no_relevant_result_top10` is the aggregate count of the last two leaves
  (`wrong_section_same_document` + `wrong_document`).
- `relevant_section_unlabeled_chunk_top1` is a chunk-level miss but a
  section-level hit; never counted as a section-level regression.
- Chunk-level and section-level regression summaries are separate tables:
  chunk regression = first relevant chunk rank worsens or leaves top-10;
  section regression = first relevant section rank worsens or leaves top-10.
- `empty_ranking` is defensive: unreachable with the fixed corpus, but handled
  and unit-tested.

## 7. Cross-corpus overlap policy (Phase 1/2)

- Retrieval corpus: all 1,068 chunks (parity with v1).
- Every query's motivating evidence must be in a held-out document
  (`source_document`).
- Overlap detector in `scripts/validate_manual_queries.py` **flags** candidate
  training-document answer passages for human review; it never relabels.
  - Stage 1 (lexical, stdlib): normalized-token Jaccard/containment of the
    query vs train chunk text ≥ `--lex-overlap-threshold` (default 0.25).
  - Stage 2 (semantic, optional): embedding cosine vs train chunks ≥
    `--sem-overlap-threshold` (default 0.65), via `--encoder` (frozen
    MiniLM). Skipped with a report note when no encoder is provided.
  - Thresholds are **provisional review flags** (correction 1), not
    calibration. Flagged pairs go to the owner for the primary/overlap
    decision; the author's decision is recorded in `subset` and
    `cross_corpus_overlap`.
- Reporting: primary and overlap subsets are reported separately.

## 8. Retrievers (Phase 3)

| retriever_id | Config |
|---|---|
| `mini_lm_frozen` | `all-MiniLM-L6-v2` @ pinned revision, mean pool, L2, max_len 256, passage `{heading_prefix}\n\n{body}`, query raw |
| `mini_lm_soup` | identical + `output_embedding` LoRA adapter |
| `bm25` | BM25Okapi, same prefixed passage text, lowercase whitespace tokenization, `k1=1.5, b=0.75`, no tuning |
| `e5_small` | `intfloat/e5-small-v2` @ `ffb93f3b…`, mean pool (verified), L2, max_len 512, query `"query: " + q`, passage `"passage: " + prefixed text` |

E5 verified facts: MIT license; bert, 384-dim, 12 layers,
`max_position_embeddings` 512; `model_max_length` 512; fp32 weights 127.3 MB
(`pytorch_model.bin` / `model.safetensors`). Mean-pooling math is shared with
the MiniLM path; tokenization, revision pinning, truncation (512 vs 256), and
prefix formatting are explicit new code with tests.

Fairness: identical queries, corpus, labels, metric code, cutoffs; per-model
formatting serialized into `retriever_config`; BM25 parameters frozen (no dev
set exists — tuning prohibited).

## 9. Statistical reporting (Phase 5)

- Micro-average (all queries equally) and macro-average (mean of the four
  per-document scores) for every metric; reported side by side; stated
  non-interchangeable.
- Paired doc-stratified bootstrap (10,000 resamples, seed 42): resample query
  indices within each document preserving counts; **one shared resampler
  applies identical indices to all four retrievers**; deltas for
  Soup−frozen, Soup−BM25, Soup−E5. Percentile intervals, exploratory.
- Macro uncertainty: range of the four leave-one-doc-out macro values
  (descriptive; a 4-cluster doc bootstrap is degenerate).
- Leave-one-doc-out: drop each document's queries; recompute micro and macro
  metrics and all three deltas.
- Section-cluster bootstrap: conditional. Inspect the frozen manual set's
  query-per-section distribution; implement only if ≥30% of query-occupied
  sections contain ≥2 queries; otherwise document why it is skipped.
- Standing statement (hardcoded in the report template): four held-out
  documents are insufficient for population-level inference; all intervals
  are exploratory; no p-values, no significance claims.

## 10. Phases and gates

| Phase | Content | Gate |
|---|---|---|
| 0 | Spec, data contracts, branch | this document |
| 1 | Vendor raw docs (Apache-2.0), coverage worksheet, validator; owner authors 54 queries | owner freezes dataset (blocks Phase 4 only) |
| 2 | Metrics (hit/recall/mrr, chunk+section), failure classifier, overlap detector | unit tests; v1 reproduction check |
| 3 | Four retrievers, `run_retrieval.py`, `requirements.txt` | retriever tests |
| 4 | Run four-way experiment on frozen manual dataset | **owner-frozen 54 queries** |
| 5 | Micro/macro, bootstraps, leave-one-doc-out, failure tables, report | report tests |
| 6 | Docs (REVIEW rewrite, model card), `.gitignore`, checkpoint removal gated on adapter load test | pytest green before/after deletion |
| 7 | Clean-room rerun, full verification, PR (only on instruction) | acceptance checklist |

Phase 6 checkpoint-removal gates were all verified before deletion on
2026-10-30 (conditions 1, 2, 4: root adapter exists, MD5 `05e30132…` ==
checkpoint-2427 adapter, `adapter_config.json`/`soup_run.json` intact;
condition 3: root adapter loads through the existing inference path in a
fresh venv; condition 5: pytest green apart from the three pre-existing v1
fixture-collection errors documented in `docs/EVALUATION_V2_PROGRESS.md`).
Deletion used `git rm` only after those checks. Phase 7 re-verified
conditions 3 and 5 in a second clean-room venv on 2026-10-31, and the v1
candidate evaluation reproduces exactly.

## 11. Repository layout for v2

```
data/raw_docs/                  vendored sources + LICENSE + attribution
data/manual_queries.jsonl       owner-approved (frozen at gate; drafted by Qoder)
data/manual_queries_validation_report.json
docs/EVALUATION_V2_SPEC.md      this file
docs/EVALUATION_V2_COVERAGE.md  query worksheet (no sample queries)
docs/EVALUATION_V2_PROGRESS.md  implementation record
scripts/retrieval.py            shared metrics, section mapping, classifier
scripts/run_retrieval.py        multi-retriever CLI
scripts/compare_retrievers.py   N-way analysis
scripts/validate_manual_queries.py
results/v2/                     four result JSONs + comparison.md
```
