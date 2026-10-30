# Evaluation v2 — Implementation Record

Living log of implementation progress, decisions, test results, and
outstanding dependencies. Canonical methodology: `docs/EVALUATION_V2_SPEC.md`.

## Status

| Phase | State | Notes |
|---|---|---|
| 0 — spec, contracts, branch | done 2026-10-30 | `feat/evaluation-v2` from `origin/main` (`a5d608f`) |
| 1 — vendoring, worksheet, validator | done (Qoder side) | **BLOCKED for Phase 4 only: owner must author + freeze 54 queries** |
| 2 — metrics, classifier, overlap detector | done (core) | `scripts/retrieval.py` + 21 tests; semantic overlap stage deferred to Phase 3 encoder |
| 3 — four retrievers | after Phase 2 | independent of query authoring |
| 4 — four-way run | gated | requires frozen `data/manual_queries.jsonl` |
| 5 — analysis/report | after Phase 4 | |
| 6 — docs + hygiene | after Phase 5 | checkpoint deletion gated on adapter load test |
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
python3 -m pytest tests/test_manual_queries_validation.py -q    # 18 passed
python3 -m pytest tests/test_retrieval_metrics.py -q            # 21 passed
```

The v1 suite (`tests/test_retrieval_pipeline.py`) cannot run yet in this
environment: the default interpreter lacks torch/transformers/peft/numpy
(pytest 9.1.1 and uv 0.11.8 are available). Phase 3 creates
`requirements.txt` and a project venv; running the full suite then becomes a
Phase 3 checkpoint.

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
2. ML environment for Phases 3+ (torch, transformers, peft, numpy, rank_bm25)
   — install into a project venv via `uv` at Phase 3.
3. `backends-and-ops.md` provenance gap (see above) — cosmetic; owner input
   optional.
4. Cluster-bootstrap decision — deferred to Phase 5 on the frozen dataset.
