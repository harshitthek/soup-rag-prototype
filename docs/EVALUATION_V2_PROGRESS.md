# Evaluation v2 — Implementation Record

Living log of implementation progress, decisions, test results, and
outstanding dependencies. Canonical methodology: `docs/EVALUATION_V2_SPEC.md`.

## Status

| Phase | State | Notes |
|---|---|---|
| 0 — spec, contracts, branch | done 2026-10-30 | `feat/evaluation-v2` from `origin/main` (`a5d608f`) |
| 1 — vendoring, worksheet, validator | done (Qoder side) | **BLOCKED for Phase 4 only: owner must author + freeze 54 queries** |
| 2 — metrics, classifier, overlap detector | done (core) | `scripts/retrieval.py` + 21 tests; semantic overlap stage deferred to Phase 3 encoder |
| 3 — four retrievers | done (code + env) | E5 weights download deferred to Phase 4 run |
| 4 — four-way run | gated | requires frozen `data/manual_queries.jsonl` |
| 5 — analysis/report | code done; execution gated on Phase 4 | `scripts/compare_retrievers.py` + 10 tests; cluster-bootstrap decision made on frozen data |
| 6 — docs + hygiene | done (deletions + docs) | all five D3 gate conditions + tokenizer-requirement check verified; `.gitignore` rules added |
| 7 — verification | last | |

## Phase 0 — done

- Created branch `feat/evaluation-v2` from latest `origin/main` (= PR #2 merge
  `a5d608f`; correction 4).
- Wrote `docs/EVALUATION_V2_SPEC.md` incorporating all four final corrections:
  provisional (uncalibrated) overlap thresholds; classifier rename
  `relevant_section_unlabeled_chunk_top1` + `empty_ranking` leaf; v1 artifacts
  untouched (singleton-label hit/recall equivalence documented only in v2
  docs); branch from `origin/main`.

## Phase 1 — Qoder side done; human gate open

- **Vendored** `data/raw_docs/`: 12 upstream docs + `LICENSE-soup-upstream.txt`
  (Apache-2.0, verified via GitHub API) + `ATTRIBUTION.md`.
  - 11/12 files byte-identical to `data/source_manifest.json` (sha256 + size),
    stored with CRLF line endings because the corpus-era files were CRLF;
    `.gitattributes` pins `-text` for the vendored files.
  - **Open item (provenance):** `backends-and-ops.md` (a *training* doc) does
    not match any upstream version found in a bounded history search
    (pinned blob 34.1 KB, corpus-era file 35.8 KB, identical section
    headings). Vendored copy is the pinned-commit version; does not affect v2
    evaluation. Owner may know the original copy's source — see
    `data/raw_docs/ATTRIBUTION.md`.
- **Worksheet** `docs/EVALUATION_V2_COVERAGE.md`: per-document section tables
  (section_id, heading, level, chunk IDs), allocation targets
  (16/8/17/13), 54 blank query slots, writing rules, excluded degenerate
  sections. Contains no sample questions (per owner decision D2).
- **Validator** `scripts/validate_manual_queries.py` + 18 tests
  (`tests/test_manual_queries_validation.py`, all passing): schema, ID format,
  duplicates, heading-copy audit (4-grams), template audit, split/consistency
  checks, evidence subsetting, subset semantics, excluded sections,
  count/allocation globals, provisional lexical overlap flags, v1
  non-coupling scan.
- CLI smoke test at the gate: `INVALID — queries file not found` (expected
  until the owner supplies queries). Report:
  `data/manual_queries_validation_report.json`.

## Test results (this session)

```
.venv/bin/python -m pytest tests/test_manual_queries_validation.py -q   # 18 passed
.venv/bin/python -m pytest tests/test_retrieval_metrics.py -q           # 21 passed
.venv/bin/python -m pytest tests/test_retrievers.py -q                  # 14 passed (real MiniLM encode + BM25)
.venv/bin/python -m pytest tests/test_v1_dataset_invariants.py -q       # 5 passed (stdlib, locks v1 artifacts)
.venv/bin/python -m pytest tests/test_retrieval_pipeline.py::TestModelAdapter -q  # 1 passed → Phase 6 gate condition 3 verified in fresh venv
```

## Phase 3 — done (code + environment)

- `scripts/retrievers.py`: `DenseRetriever` (mean pooling, L2, revision-pinned
  MiniLM `1110a243…` / E5 `ffb93f3b…`, per-model query/passage prefixes,
  256/512 truncation, optional PEFT adapter) and `BM25Retriever`
  (BM25Okapi k1=1.5 b=0.75, lowercase whitespace tokenization, no tuning).
  Heavy imports are lazy; config is inspectable without loading models.
- `scripts/run_retrieval.py`: one shared ranking path for all retrievers,
  v2 result schema (retriever_config, fingerprints, chunk+section metrics,
  per-query failure category); hard gate on the missing frozen query dataset.
- `requirements.txt` (`pytest<9`) + project venv at `.venv` (gitignored).
- Tests: 14 retriever tests including a real MiniLM encode smoke test and the
  v1 adapter-load test — the latter also satisfies Phase 6 checkpoint-removal
  gate condition 3 (root adapter loads via the existing inference path in a
  fresh venv). E5's 127 MB weights are downloaded at the Phase 4 run.

## Phase 5 — code done; execution gated on Phase 4

- `scripts/compare_retrievers.py`: micro/macro metrics for all 14 metrics,
  doc-stratified paired bootstrap (10k, seed 42) with one shared
  `StratifiedResampler` applied to all retrievers (pairedness), three Soup
  deltas, leave-one-doc-out micro/macro sensitivity, failure-category tables
  with the `no_relevant_result_top10` aggregate, chunk/section regression
  counts (sibling-first never counts as a section regression), primary vs
  overlap subset tables, and a data-driven section-cluster bootstrap
  decision (implemented only if >= 30% of query-occupied sections hold >= 2
  queries; decision recorded in the report). Caveat text hardcoded: no
  p-values, four-document limitation.
- 10 fixture tests: micro/macro semantics, stratification preserving doc
  counts, resampler determinism, CI behavior on constant deltas,
  leave-one-doc-out, cluster decision both ways, sibling-not-section-
  regression, aggregate category counts, report content (disclaimer-only
  "p-value" occurrence) and report determinism.
- Validator gained the optional `--semantic` stage (frozen MiniLM cosine
  flags, provisional 0.65 threshold, review-only) — completing the deferred
  Phase 2/3 item; 2 additional tests.

## Phase 6 — done

- **Checkpoint removal (owner-approved, gates verified):** reversible
  rename-test proved the root `tokenizer.json`/`tokenizer_config.json` and
  `training_args.bin` are not required for inference (adapter-load + dense
  encode tests passed without them, then files were restored).
  `git rm -r` applied to `checkpoint-2300/2400/2427` and the redundant root
  tokenizer copies + `training_args.bin`; post-removal verification:
  adapter tests + full v2 suite green (20 + 70 tests). `.gitignore` now
  excludes future `output_embedding/checkpoint-*/`, `tokenizer*.json`, and
  `training_args.bin`. Root adapter (580 KB, MD5 `05e30132…`),
  `adapter_config.json`, `soup_run.json` remain tracked.
- **`output_embedding/README.md`** rewritten as a real model card (base
  revision, LoRA config, training data, seeds, run_id, reproduction steps).
- **`REVIEW.md`** rewritten: current architecture, key decisions, labeled
  "Historical decisions (v1)" section preserving durable reasoning (prefix
  bug, negative mining, val_split, margin math, ANCE/InfoNCE rationale),
  known limitations.
- **README/REPORT/REPRODUCE** gained additive "Evaluation v2" sections
  (existing v1 content untouched per correction 3); REPRODUCE documents the
  v2 venv, validator, four-way run, and comparison commands.

## v1 suite status (pre-existing condition, not a v2 regression)

12 of 15 v1 tests pass. The 3 `TestMiningRealCorpusIntegration` tests fail at
fixture collection: their `mined_results` fixture is declared
`@classmethod`-above-`@pytest.fixture`, which pytest >= 8.4 no longer
discovers. Evidence this predates v2: the original environment's
`.pytest_cache/v/cache/lastfailed` (committed-era artifact on this machine)
lists exactly these three tests as failed. Correction 3 forbids modifying v1
files, so the same invariants (3,234 triplets, 3 negatives/query, section
dedup, heading-prefix retention, dataset counts) are re-verified stdlib-only
in `tests/test_v1_dataset_invariants.py`.

## Phase 2 — done (core)

- `scripts/retrieval.py` (stdlib-only): `rank_corpus` (descending score,
  lexicographic chunk_id tie-break — identical ordering rule to v1
  `dense_retrieve`), `get_base_section`, `section_ranking` (unique sections,
  first-occurrence ranks), `compute_query_metrics`/`compute_metrics`
  (hit@k, recall@k fractional, mrr@10; chunk + section levels),
  `classify_failure` (7 mutually exclusive leaves incl. `empty_ranking`;
  `no_relevant_result_top10` aggregate = `wrong_section_same_document` +
  `wrong_document`).
- 21 tests cover the four spec edge cases (single item, multi-chunk one
  section, multi-section, |relevant| > K), MRR first-rank semantics,
  section-collapse ordering, classifier exclusivity/exhaustiveness, and
  derivation of section/doc from chunk IDs.
- **Decision (correction 3):** v1 scripts stay byte-identical; the shared
  module duplicates the 20-line ranking rule instead of refactoring
  `evaluate_retrieval.py`. The v1 exact-reproduction check is therefore
  trivially satisfied (v1 file unchanged).

## Decisions logged

- Overlap thresholds (0.25 lexical Jaccard, 0.65 semantic cosine) are
  **provisional review flags**, CLI-tunable; validator flags never relabel.
- Semantic overlap stage requires an encoder; deferred until Phase 3 wires
  the shared `DenseRetriever` (frozen MiniLM) into the validator.
- Failure classifier: `empty_ranking` is a defensive leaf (unreachable with
  the fixed 1,068-chunk corpus); `no_relevant_result_top10` is the aggregate
  of `wrong_section_same_document` + `wrong_document`.

## Outstanding dependencies

1. **Owner-authored 54 queries** (blocks Phase 4 only). Owner fills
   `docs/EVALUATION_V2_COVERAGE.md` slots; Qoder transcribes verbatim into
   `data/manual_queries.jsonl`, runs the validator, owner reviews flags and
   freezes.
2. ML environment for Phases 3+ — done: `.venv` created with `uv`, pinned
   `requirements.txt` installed (torch, transformers, peft, numpy, pyyaml,
   rank_bm25, pytest<9).
3. `backends-and-ops.md` provenance gap (see above) — cosmetic; owner input
   optional.
4. Cluster-bootstrap decision — deferred to Phase 5 on the frozen dataset.
