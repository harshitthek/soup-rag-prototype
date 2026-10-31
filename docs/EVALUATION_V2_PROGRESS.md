# Evaluation v2 — Implementation Record

Living log of implementation progress, decisions, test results, and
outstanding dependencies. Canonical methodology: `docs/EVALUATION_V2_SPEC.md`.

## Status

| Phase | State | Notes |
|---|---|---|
| 0 — spec, contracts, branch | done 2026-10-30 | `feat/evaluation-v2` from `origin/main` (`a5d608f`) |
| 1 — vendoring, worksheet, validator | done | 54 queries frozen 2026-10-31; final split 39 primary / 15 overlap after the owner-approved overlap audit; dataset + validator report in place |
| 2 — metrics, classifier, overlap detector | done (core) | `scripts/retrieval.py` + 21 tests; semantic overlap stage deferred to Phase 3 encoder |
| 3 — four retrievers | done (code + env) | E5 weights download deferred to Phase 4 run |
| 4 — four-way run | done 2026-10-31 | 4 result files in `results/v2/`; shared corpus+query fingerprints; E5 best, Soup adapter below frozen MiniLM |
| 5 — analysis/report | done 2026-10-31 | `results/v2/comparison.md` (332 lines); primary/overlap reversal; E5 strongest |
| 6 — docs + hygiene | done 2026-10-31 | checkpoint gates, model card, REVIEW/README/REPORT/REPRODUCE updated with v2 results |
| 7 — verification | done 2026-10-31 | clean-room rerun bit-exact; full suite 85 pass + 3 pre-existing v1 collection errors; v1 numbers exact; PR #3 opened on owner instruction |
| PR #3 review fixes (P1) | done 2026-10-31 (local) | authorship docs corrected, 18-query overlap audit (15/2/1), shared precomputed bootstrap plan; not pushed |

## Phase 0 — done

- Created branch `feat/evaluation-v2` from latest `origin/main` (= PR #2 merge
  `a5d608f`; correction 4).
- Wrote `docs/EVALUATION_V2_SPEC.md` incorporating all four final corrections:
  provisional (uncalibrated) overlap thresholds; classifier rename
  `relevant_section_unlabeled_chunk_top1` + `empty_ranking` leaf; v1 artifacts
  untouched (singleton-label hit/recall equivalence documented only in v2
  docs); branch from `origin/main`.

## Phase 1 — dataset frozen

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

## Phase 1 — query development (2026-10-31)

- The 54 natural language evaluation queries were manually crafted by the
  project owner with AI assistance. The owner used the source documentation,
  the coverage worksheet, and AI-assisted analysis to develop the queries,
  review their relevance annotations, and finalize the dataset. All 54 slots
  in `docs/EVALUATION_V2_COVERAGE.md` are filled, and the final wording was
  reviewed and approved by the owner before freeze. This is owner review,
  not independent third-party annotation or independent validation.
- Allocation: adapters 16, compliance 8, evaluation 17,
  peft-and-efficiency 13. Types: conceptual 14, how_to 13, config_behavior 10,
  troubleshooting 7, command_detail 6, relationship 4.
- Cross-corpus review: 18 queries were initially labeled `overlap` with train
  chunk IDs because a training passage appeared to carry an equivalent answer
  (terse command-table entries, the README template list, the expectations
  guide, and the architecture-knobs training section); 36 were initially
  `primary`. Primary per document at that time: adapters 10, compliance 3,
  evaluation 13, peft 10. The 2026-10-31 overlap audit re-checked all 18
  against actual chunk text; the owner approved 15 confirmations and 3
  reclassifications, giving the final 39 / 15 split recorded in
  `docs/EVALUATION_V2_OVERLAP_AUDIT.md`.
- Validator on the draft (`/tmp/manual_queries_draft.jsonl`, not committed):
  54 checked, 0 errors, 0 warnings, 1 provisional lexical flag
  (`manual_010` vs `backends-and-ops::machine-readable-output`, a two-line
  `soup version --json` chunk; false positive — the real registry-diff
  duplicate is already labeled in `commands::all-commands::sub_022`).
  Semantic top-5 review found no threshold-crossing overlap.
- The owner approved the query set on 2026-10-31; wording was transcribed
  verbatim into `data/manual_queries.jsonl` (54 records; initially 36 primary
  / 18 overlap, final 39 / 15 after the owner-approved audit). Canonical
  validation report:
  `data/manual_queries_validation_report.json` — 54 checked, 0 errors,
  0 warnings, 1 provisional lexical flag (`manual_010`, short-chunk false
  positive; the real registry-diff duplicate is labeled in the overlap
  subset).

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

## Phase 4 — four-way run (final rerun 2026-11-01)

Four retrievers ran on the final dataset after the owner-approved overlap
reclassification (54 queries, 1,068 chunks, top-10). All four result files
share the corpus fingerprint `76ab5e88…` and query-set fingerprint
`971e1570…`; each has `query_count=54` and the unchanged
`retriever_config` (MiniLM revision `1110a243…`, Soup adapter dir
`output_embedding`, BM25 k1=1.5/b=0.75, E5 revision `ffb93f3b…` with
query/passage prefixes).

| Retriever | Hit@1 | Hit@3 | Hit@5 | MRR@10 | Sec Hit@1 | Sec MRR@10 |
|---|---|---|---|---|---|---|
| E5-small-v2 | 0.6852 | 0.8704 | 0.8704 | 0.7834 | 0.7222 | 0.8165 |
| MiniLM frozen | 0.5741 | 0.7778 | 0.8704 | 0.6928 | 0.6296 | 0.7257 |
| MiniLM + Soup adapter | 0.5370 | 0.7037 | 0.7963 | 0.6501 | 0.5741 | 0.6822 |
| BM25 | 0.4815 | 0.7037 | 0.7222 | 0.5953 | 0.4815 | 0.6127 |

Headline: E5 is strongest; the Soup adapter scores below frozen MiniLM on the
manual set (−3.7 pp Hit@1, −4.3 pp MRR@10) despite its large v1
synthetic-benchmark gain. The manual queries are natural-language and
distributionally different from the heading-derived synthetic v1 queries;
this is a substantive negative result to report, not a bug.

The pre-reclassification run (36 primary / 18 overlap, query-set fingerprint
`116bd4c3…`) is superseded; those numbers remain in the PR #3 history.

Artifacts: `results/v2/{mini_lm_frozen,mini_lm_soup,bm25,e5_small}.json`.

## Phase 5 — code done; ready to run on Phase 4 results

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

### Phase 5 results (final dataset)

- Report: `results/v2/comparison.md` (334 lines), 10,000 paired
  document-stratified resamples, seed 42; one precomputed plan is shared by
  every metric, retriever, and comparison.
- Micro headline: E5 strongest on every metric. Soup adapter vs frozen MiniLM:
  Hit@1 −0.037 [−0.185, +0.111], MRR@10 −0.043 [−0.148, +0.063] — intervals
  include 0; recall@5 −0.111 [−0.204, −0.024] and sec_recall@5 −0.086
  [−0.164, −0.019] exclude 0 on the negative side. Soup vs E5 is negative
  with intervals excluding 0 for Hit@3, MRR@10, recall@3/5, and several
  section metrics.
- **Subset reversal (key finding):** on the 39 primary queries the Soup
  adapter trails frozen MiniLM (Hit@1 0.538 vs 0.615; MRR@10 0.644 vs 0.714),
  while on the 15 remaining overlap queries it leads frozen MiniLM
  (Hit@1 0.533 vs 0.467; MRR@10 0.667 vs 0.639), though BM25 is strongest on
  that subset (Hit@1 0.667; MRR@10 0.728). The adapter's advantage is confined
  to queries whose answers also exist in training documents.
- Leave-one-document-out: Soup−frozen Hit@1 is ≤ 0 for every dropped document
  (range −0.079 to −0.022), Soup−E5 is negative throughout, Soup−BM25 is
  positive throughout — direction stable, descriptively.
- Failure categories: E5 37 exact-top-1 and 1 no-relevant-top-10; BM25 10
  no-relevant; frozen 5, Soup 6. Soup has more
  relevant-chunk-below-top-1 (17 vs 15) than frozen.
- Section-cluster bootstrap skipped: 1 of 53 query-occupied sections holds
  ≥2 queries (1.9% < 30%), so resampling would degenerate to query-level.
- Caveat honored: four documents are insufficient for population inference;
  intervals describe this fixed sample; no p-values (exactly one mention, the
  disclaimer). Report header states owner-approved; manually crafted by the
  owner with AI assistance.

## Verification evidence (2026-10-30, continued)

- **v1 exact reproduction: PASS.** The unchanged v1 pipeline
  (`scripts/evaluate_retrieval.py`, frozen baseline, 497 queries, 1068
  chunks) reproduces the canonical v1 metrics exactly: recall@1 0.5453,
  recall@3 0.7606, recall@5 0.8209, mrr@10 0.6615 — acceptance criterion
  verified with fresh output, not the saved file.
- **Overlap detector on real data.** Probe queries against the known
  near-duplicate pair (`evaluation::install-eval-dependencies` vs
  `serving-and-export::install-server-dependencies`): frozen-MiniLM cosine
  similarities on this corpus peak around 0.35–0.57, below the provisional
  0.65 semantic flag — the known counterpart still appears at the top of the
  similarity ranking. The validator's `--semantic` stage now always reports
  per-query top-5 train-chunk matches with scores (threshold-crossing flags
  remain provisional), so the author gets full review material either way.
- **Non-coupling scan fix.** The scan now whitelists the six v1 scripts
  instead of blacklisting one file; it previously false-flagged v2's own
  `run_retrieval.py`. Regression test added (v2 scripts exempt, v1 scripts
  still caught).
- **E5 real-encode test.** Added and passing: `DenseRetriever` with the E5
  revision pin and prefixes produces 384-dim unit-norm vectors (weights
  cached from the rehearsal).
- Full v2 suite: 72 tests green (22 validator, 21 metrics, 15 retrievers,
  10 comparison, 5 invariants — plus the 12 passing v1 tests).

## Phase 4/5 rehearsal (smoke fixtures, /tmp only — not the benchmark)

A clean-room rehearsal of the Phase 4+5 command paths ran against 3 temporary
smoke queries in `/tmp/v2_smoke/` (clearly labeled fixtures; never committed,
never part of the manual dataset):

- `run_retrieval.py` executed for all four retrievers: frozen MiniLM (11.0 s),
  Soup adapter (9.9 s), BM25 (0.05 s), E5-small-v2 (99.5 s, weights
  downloaded and cached; revision `ffb93f3b…` confirmed in
  `retriever_config`). All four result files parse, share identical corpus
  and query-set fingerprints, and carry per-query failure categories.
- `compare_retrievers.py` produced a 299-line report with all sections
  (metric tables, leave-one-doc-out, failure categories, regression counts,
  subset tables, cluster-bootstrap decision).
- Observed behavior sanity-checked: fixtures labeled one sub-chunk of
  multi-chunk sections, and retrievers correctly returned siblings at top-1 —
  classified `relevant_section_unlabeled_chunk_top1` (chunk miss, section
  hit), exactly the intended multi-label semantics.

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
- **Query authorship (2026-10-31):** the 54 queries were manually crafted by
  the project owner with AI assistance; the owner reviewed and approved the
  final wording, relevance annotations, and dataset freeze. This is owner
  review, not independent third-party annotation. Recorded in the worksheet
  header, spec §4, and the public docs.
- **Cross-corpus subsetting (2026-10-31, resolved 2026-11-01):** 18 queries
  were initially labeled `overlap` because a training chunk appeared to carry
  an equivalent answer (terse command-table entries, README template list,
  expectations guide, architecture-knobs section); 36 were initially
  `primary`. The 2026-10-31 overlap audit re-checked every classification
  against chunk text and the owner approved 15 confirmations plus 3
  reclassifications to `primary`, giving the final 39 / 15 split. The
  comparison report separates subset tables.

## Phase 7 — verification (2026-10-31, pre-reclassification)

This clean-room run predates the owner-approved overlap reclassification. The
capabilities it verified still hold; final numbers are in the reclassification
section above.

Clean room built from the repo requirements only:

```
uv venv /tmp/v2_phase7_venv
uv pip install --python /tmp/v2_phase7_venv/bin/python -r requirements.txt
# Python 3.14.7, torch 2.15.0, transformers 5.22.1, peft 0.21.2,
# numpy 2.5.4, pytest 8.4.2, rank-bm25 0.2.2 (41 packages)
```

- **Validator:** `checked 54 queries; errors: 0; warnings: 0; overlap flags: 1`
  — byte-equivalent outcome to the canonical report (`manual_010` flag only).
- **Four-retriever rerun** into `/tmp/v2_phase7/results/`: all four files
  match `results/v2/` exactly — same corpus/query fingerprints, query_count,
  corpus_size, top_k, retriever_id, retriever_config, metrics, per-query
  ranked chunk lists, failure categories; max absolute score delta 0.00e+00
  for every retriever. Reproduction is bit-exact even on the newer
  torch/transformers/Python stack, so no package pinning was needed.
- **Comparison report:** regenerated with 10,000 resamples, seed 42; 332
  lines; `diff` against `results/v2/comparison.md` empty (identical file).
- **Full test suite:** `85 passed, 3 errors` in both venvs — the three
  errors are the pre-existing `TestMiningRealCorpusIntegration` fixture
  collection failures (pytest ≥ 8.4; v1 files untouchable per correction 3),
  identical in the original `.venv` (85 passed, 3 errors).
- **v1 exact reproduction in the fresh venv:** baseline recall@1/3/5,
  mrr@10 = 0.5453 / 0.7606 / 0.8209 / 0.6615; adapter = 0.7565 / 0.9336 /
  0.9718 / 0.8477 — matches canonical v1 numbers exactly. This also
  re-confirms Phase 6 gate condition 3 (root adapter loads through the
  existing inference path in a fresh venv).
- **Artifact integrity:** `output_embedding/adapter_model.safetensors` MD5
  `05e301327de2278a040319d69394229f`; `git diff HEAD` over all v1 scripts,
  data, results, config, and `output_embedding/` is empty; checkpoints remain
  absent; no v1 file is modified in the working tree (only v2 files are).
- **PR:** opened later on owner instruction as PR #3
  (`feat/evaluation-v2` → `main`, 9 commits, 75 files). The P1 review fixes
  below are local working-tree changes and are not pushed.

## P1 review fixes for PR #3 (2026-10-31, local; not pushed)

- **Authorship documentation corrected.** All public descriptions now state
  that the 54 natural-language queries were manually crafted by the project
  owner with AI assistance, and that the owner reviewed and approved the
  final wording and relevance annotations. The earlier tool-drafting and
  machine-drafting wording and the superseded authorship amendment were
  removed. The docs also state that this is owner review, not independent
  third-party annotation or independent validation. Files: README, REPORT,
  REVIEW, REPRODUCE, the adapter model card, spec §2/§4, the coverage
  worksheet header, this log, and the report generator header.
- **Overlap audit.** `docs/EVALUATION_V2_OVERLAP_AUDIT.md` re-checked all 18
  overlap labels against the actual held-out and training chunk text: 15
  confirmed, 2 questionable (`manual_002`, `manual_023`), 1 unsupported
  (`manual_043`). At that stage no dataset, query, label, or split change was
  made; the cases were listed as owner decisions. The owner later approved all
  three reclassifications (final section below), and the dataset and all
  dependent artifacts were regenerated.
- **Bootstrap plan precomputed.** `StratifiedResampler` now draws the full
  10,000-resample document-stratified index plan once at construction, and
  `paired_bootstrap_ci` consumes only `plan.indices`. Every metric and all
  three comparisons reuse the same plan, both retrievers in a comparison
  use the same sampled positions, and repeated calls consume no randomness.
  Seed 42, 10,000 resamples, micro/macro formulas, and percentile CIs are
  unchanged.
- **CI values recomputed; point estimates unchanged.** The previous
  implementation advanced the RNG between comparisons, so the corrected
  shared plan changes some interval bounds (11 changed report lines). All
  micro/macro values, subset tables, leave-one-out tables, failure counts,
  regression counts, fingerprints, and the negative primary-subset result
  are unchanged.
- **Tests:** `tests/test_compare_retrievers.py` now has 12 tests, including
  precomputed-plan determinism, a manual recomputation proving both
  retrievers use identical sampled positions, and a spy test proving one
  plan instance serves every metric and comparison. Report determinism, the
  single-disclaimer check, and the audit-note check remain.
- **Verification:** targeted suites 75 passed (12 comparison, 22 validator,
  21 metrics, 15 retrievers, 5 v1 invariants); full suite 87 passed with the
  same 3 pre-existing v1 fixture-collection errors. The report was generated
  twice with identical output. All 14 metric tables keep identical
  micro/macro and delta point estimates; only 9 interval-bound cells, the two
  header lines, and the audit note changed. One interval that previously
  touched zero (recall@3, Soup−frozen) now includes zero at +0.0015; no
  significance is claimed from any interval.
- **Constraints held at that stage:** `data/manual_queries.jsonl` untouched
  (sha256 = query-set fingerprint `116bd4c3…`); corpus fingerprint unchanged
  (`76ab5e88…`); adapter weights, `adapter_config.json`, and `soup_run.json`
  unchanged; no v1 script, data, result, or config changed; retriever
  configurations and metric definitions unchanged; no model inference was
  run. The subsequent owner-approved reclassification is recorded below.

## Owner-approved overlap reclassification (2026-11-01)

- **Owner decisions.** Based on the audit evidence, the owner approved
  reclassifying `manual_002`, `manual_023`, and `manual_043` from `overlap`
  to `primary`. For each record, the training section/chunk IDs were removed
  from the relevant sets, `cross_corpus_overlap` was cleared, the rationale
  was rewritten to the held-out evidence only, and query wording, held-out
  labels, and evidence chunks were preserved. The other 51 records were not
  modified.
- **Final dataset.** 54 unique query IDs: 39 `primary`, 15 `overlap`.
  Query-set fingerprint
  `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3`.
  Corpus fingerprint remains `76ab5e88…`. Validator: 54 checked, 0 errors,
  0 warnings, 1 provisional lexical flag (`manual_010`, known false
  positive).
- **Artifacts regenerated.** All four retrievers were rerun with the
  unchanged models, adapter, corpus, and configurations; the four result
  files and `results/v2/comparison.md` were regenerated. Final micro
  metrics (Hit@1 / Hit@5 / MRR@10): E5-small-v2 0.6852 / 0.8704 / 0.7834;
  MiniLM frozen 0.5741 / 0.8704 / 0.6928; MiniLM + Soup 0.5370 / 0.7963 /
  0.6501; BM25 0.4815 / 0.7222 / 0.5953. The negative result holds:
  Soup−frozen Hit@1 −0.037 [−0.185, +0.111], MRR@10 −0.043
  [−0.148, +0.063], recall@5 −0.111 [−0.204, −0.024]. The subset split is
  39/15; Soup trails frozen on primary and leads on overlap, while BM25 is
  strongest on overlap.
- **Verification.** See the final report for the full evidence: validator,
  test suite, fingerprint equality, report determinism, overlap-label
  integrity, and v1 artifact preservation. Work remains local and unpushed.

## Outstanding dependencies

1. **Publishing authorization.** The P1 fixes and the owner-approved
   reclassification are local working-tree changes; commit, push, and any PR
   description update require explicit owner authorization.
2. `backends-and-ops.md` provenance gap (see above) — cosmetic; owner input
   optional.
