# Evaluation v2 — Manual Query Coverage Worksheet

**Authorship note (amended 2026-10-31).** The project owner originally required
every query to be hand-written by the owner and barred tooling from drafting.
On 2026-10-31 the owner explicitly instructed Qoder to draft all 54 queries.
The entries below are Qoder-drafted and owner-reviewed before freeze; every
wording, annotation, and validator rule still applies. The amendment is also
recorded in `docs/EVALUATION_V2_SPEC.md` §4 and the progress log.

Read the source text in `data/raw_docs/<document>.md` before writing a query.

## How to fill this in

1. Pick a section row below and read its chunks (open `data/raw_docs/` or the `data/corpus.jsonl` chunk IDs listed per section).

2. Write your question in the slots at the end of each document block: one query per slot, in your own natural wording.

3. For each query fill: `query` (exact wording), `query_type` (one of: conceptual, how_to, troubleshooting, config_behavior, relationship, command_detail), `relevant_section_ids` and `relevant_chunk_ids` (every section/chunk that genuinely contains the answer — siblings only when each independently carries answer-bearing text), `evidence_chunk_ids` (subset of relevant_chunk_ids that most directly supports the label), and `rationale` (why these labels).

4. `subset`: `primary` unless the validator flags an equivalent answer in a training document, in which case you may move the query to `overlap` and add train-chunk IDs to the labels and `cross_corpus_overlap`.

## Query writing rules

- No copied heading phrases: do not reproduce 4+ consecutive words from any heading of the source document.

- No mechanical templates ("How do you configure X in Soup?"-style).

- Legitimate command, flag, and concept names (e.g. `soup adapters merge`, `--track-energy`, PiSSA) are allowed — banning all technical terms is not the goal.

- The question must be answerable from the held-out documentation.

- The question must read like something a developer would actually type into a search box.

- At least 6 queries overall must target multi-chunk sections (sections marked `[multi]`).

- Excluded degenerate sections (table artifacts): `evaluation::1-0`, `evaluation::0-5`.


## Allocation targets

| Document | Chunks | Sections | Target queries |
|---|---|---|---|
| adapters-and-governance | 106 | 79 | 16 |
| compliance | 16 | 13 | 8 |
| evaluation | 120 | 82 | 17 |
| peft-and-efficiency | 65 | 33 | 13 |


## adapters-and-governance.md — 106 chunks, 79 sections, target 16 queries

### Sections and chunk IDs

| section_id | heading | level | chunks |
|---|---|---|---|
| `adapters-and-governance::1-train-and-persist-the-measured-energy-needs-pip-install-soup-cli-carbon` | 1. Train and persist the measured energy (needs `pip install soup-cli[carbon]`): | 1 | adapters-and-governance::1-train-and-persist-the-measured-energy-needs-pip-install-soup-cli-carbon |
| `adapters-and-governance::2-attach-it-to-the-bom` | 2. Attach it to the BOM: | 1 [multi] | adapters-and-governance::2-attach-it-to-the-bom::sub_000, adapters-and-governance::2-attach-it-to-the-bom::sub_001 |
| `adapters-and-governance::2-render-the-merge-as-a-github-pr-for-review-eval-deltas-sample-diffs` | 2. Render the merge as a GitHub PR for review (eval deltas + sample diffs). | 1 | adapters-and-governance::2-render-the-merge-as-a-github-pr-for-review-eval-deltas-sample-diffs |
| `adapters-and-governance::3-lock-a-reproducible-run-state-closure-sha-base-dataset-env` | 3. Lock a reproducible run state. Closure = sha(base + dataset + env). | 1 | adapters-and-governance::3-lock-a-reproducible-run-state-closure-sha-base-dataset-env |
| `adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval` | 4. Bisect a training history to find the step that broke an eval. | 1 | adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval |
| `adapters-and-governance::activation-steering-soup-steer` | Activation Steering (`soup steer`) | 2 | adapters-and-governance::activation-steering-soup-steer |
| `adapters-and-governance::adapter-backdoor-scanner-soup-adapters-scan` | Adapter Backdoor Scanner (`soup adapters scan`) | 2 | adapters-and-governance::adapter-backdoor-scanner-soup-adapters-scan |
| `adapters-and-governance::adapter-lifecycle-soup-adapters-merge-pr-bisect-soup-lock` | Adapter Lifecycle (`soup adapters {merge,pr,bisect}`, `soup lock`) | 2 | adapters-and-governance::adapter-lifecycle-soup-adapters-merge-pr-bisect-soup-lock |
| `adapters-and-governance::adapter-management-git-for-lora` | Adapter Management (git for LoRA) | 2 | adapters-and-governance::adapter-management-git-for-lora |
| `adapters-and-governance::adapter-sign-verify-soup-adapters-sign-verify` | Adapter Sign + Verify (`soup adapters sign` / `verify`) | 2 | adapters-and-governance::adapter-sign-verify-soup-adapters-sign-verify |
| `adapters-and-governance::adapters-registry-governance` | Adapters, Registry & Governance | 1 [multi] | adapters-and-governance::adapters-registry-governance::sub_000, adapters-and-governance::adapters-registry-governance::sub_001, adapters-and-governance::adapters-registry-governance::sub_002, adapters-and-governance::adapters-registry-governance::sub_003, adapters-and-governance::adapters-registry-governance::sub_004, adapters-and-governance::adapters-registry-governance::sub_005 |
| `adapters-and-governance::airgap-bundle-soup-airgap-bundle` | Airgap Bundle (`soup airgap-bundle`) | 2 [multi] | adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_000, adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_001 |
| `adapters-and-governance::apply-at-decode-time-via-soup-serve` | Apply at decode time via soup serve | 1 | adapters-and-governance::apply-at-decode-time-via-soup-serve |
| `adapters-and-governance::attaching-energy-co-energy` | Attaching energy + CO₂ (`--energy`) | 3 | adapters-and-governance::attaching-energy-co-energy |
| `adapters-and-governance::audit-log-soup-audit-log` | Audit Log (`soup audit-log`) | 2 [multi] | adapters-and-governance::audit-log-soup-audit-log::sub_000, adapters-and-governance::audit-log-soup-audit-log::sub_001 |
| `adapters-and-governance::background-subprocess-writes-pid-no-shell` | Background subprocess (writes PID, no shell) | 1 | adapters-and-governance::background-subprocess-writes-pid-no-shell |
| `adapters-and-governance::bill-of-materials-soup-bom-emit` | Bill of Materials (`soup bom emit`) | 2 | adapters-and-governance::bill-of-materials-soup-bom-emit |
| `adapters-and-governance::branches-node-under-the-entry-in-soup-history` | `branches` node under the entry in `soup history`. | 1 | adapters-and-governance::branches-node-under-the-entry-in-soup-history |
| `adapters-and-governance::covariance-preconditioned-rome-genuine-c-1-k-update-from-a-stats-corpus` | Covariance-preconditioned ROME (genuine C^-1 k* update) from a stats corpus. | 1 | adapters-and-governance::covariance-preconditioned-rome-genuine-c-1-k-update-from-a-stats-corpus |
| `adapters-and-governance::dare-merge-deterministic-via-seed` | DARE merge (deterministic via --seed) | 1 | adapters-and-governance::dare-merge-deterministic-via-seed |
| `adapters-and-governance::data-flywheel-soup-loop` | Data Flywheel (`soup loop`) | 2 | adapters-and-governance::data-flywheel-soup-loop |
| `adapters-and-governance::delete-cascades-to-artifacts-lineage-links` | Delete (cascades to artifacts + lineage links) | 1 | adapters-and-governance::delete-cascades-to-artifacts-lineage-links |
| `adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation` | Diff what the model says before vs after the edit (live generation). | 1 [multi] | adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000, adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_001, adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_002, adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_003, adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_004 |
| `adapters-and-governance::embed-in-toto-attestations-into-the-manifest-v3-cans-repeatable` | Embed in-toto attestations into the manifest (v3 cans; repeatable) | 1 | adapters-and-governance::embed-in-toto-attestations-into-the-manifest-v3-cans-repeatable |
| `adapters-and-governance::energy-co-measurement-track-energy` | Energy & CO₂ measurement (`--track-energy`) | 3 | adapters-and-governance::energy-co-measurement-track-energy |
| `adapters-and-governance::eu-ai-act-annex-xi-xii-auto-doc-soup-train-annex-xi` | EU AI Act Annex XI/XII Auto-Doc (`soup train --annex-xi`) | 2 [multi] | adapters-and-governance::eu-ai-act-annex-xi-xii-auto-doc-soup-train-annex-xi::sub_000, adapters-and-governance::eu-ai-act-annex-xi-xii-auto-doc-soup-train-annex-xi::sub_001 |
| `adapters-and-governance::eval-and-the-best-blend-is-written-to-output` | --eval, and the best blend is written to --output. | 1 | adapters-and-governance::eval-and-the-best-blend-is-written-to-output |
| `adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution` | Exits 3 on BROKEN_AT — pipe into `soup adapters blame` for attribution. | 1 [multi] | adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution::sub_000, adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution::sub_001 |
| `adapters-and-governance::fork-with-modifications-dotted-path-overrides-and-re-pack` | Fork with modifications (dotted-path overrides) and re-pack | 1 | adapters-and-governance::fork-with-modifications-dotted-path-overrides-and-re-pack |
| `adapters-and-governance::full-text-search-across-name-base-model-task-notes` | Full-text search across name / base model / task / notes | 1 | adapters-and-governance::full-text-search-across-name-base-model-task-notes |
| `adapters-and-governance::generate-a-keypair-sign-in-one-shot` | generate a keypair + sign in one shot | 1 | adapters-and-governance::generate-a-keypair-sign-in-one-shot |
| `adapters-and-governance::genuine-authentication-require-the-signer-s-key-match-a-trusted-one` | genuine authentication: require the signer's key match a trusted one | 1 | adapters-and-governance::genuine-authentication-require-the-signer-s-key-match-a-trusted-one |
| `adapters-and-governance::gh-token-uses-gh-api-under-the-hood-no-secret-leaks-to-the-child` | / GH_TOKEN; uses `gh api` under the hood (no secret leaks to the child). | 1 | adapters-and-governance::gh-token-uses-gh-api-under-the-hood-no-secret-leaks-to-the-child |
| `adapters-and-governance::grace-codebook-lifelong-knowledge-edits` | GRACE Codebook — Lifelong Knowledge Edits | 2 | adapters-and-governance::grace-codebook-lifelong-knowledge-edits |
| `adapters-and-governance::inspect-counters-status` | Inspect counters + status | 1 | adapters-and-governance::inspect-counters-status |
| `adapters-and-governance::into-one-adapter-arxiv-2212-04089-names-map-to-dirs-via-adapter-name-path` | into one adapter (arXiv:2212.04089). Names map to dirs via --adapter name=path. | 1 | adapters-and-governance::into-one-adapter-arxiv-2212-04089-names-map-to-dirs-via-adapter-name-path |
| `adapters-and-governance::knowledge-editing-soup-edit-set-rome-memit-alphaedit` | Knowledge Editing (`soup edit set`, ROME / MEMIT / AlphaEdit) | 2 | adapters-and-governance::knowledge-editing-soup-edit-set-rome-memit-alphaedit |
| `adapters-and-governance::leave-one-out-ablation-plan-against-a-4-hour-wall-clock-budget` | Leave-one-out ablation plan against a 4-hour wall-clock budget | 1 | adapters-and-governance::leave-one-out-ablation-plan-against-a-4-hour-wall-clock-budget |
| `adapters-and-governance::license-conflict-matrix-at-merge` | License-Conflict Matrix at Merge | 2 [multi] | adapters-and-governance::license-conflict-matrix-at-merge::sub_000, adapters-and-governance::license-conflict-matrix-at-merge::sub_001, adapters-and-governance::license-conflict-matrix-at-merge::sub_002 |
| `adapters-and-governance::list-all-snapshotted-branches` | List all snapshotted branches | 1 [multi] | adapters-and-governance::list-all-snapshotted-branches::sub_000, adapters-and-governance::list-all-snapshotted-branches::sub_001, adapters-and-governance::list-all-snapshotted-branches::sub_002, adapters-and-governance::list-all-snapshotted-branches::sub_003, adapters-and-governance::list-all-snapshotted-branches::sub_004, adapters-and-governance::list-all-snapshotted-branches::sub_005 |
| `adapters-and-governance::list-entries-filter-by-name-tag-base-model-task` | List entries (filter by name, tag, base model, task) | 1 | adapters-and-governance::list-entries-filter-by-name-tag-base-model-task |
| `adapters-and-governance::list-locally-stored-steering-vectors` | List locally-stored steering vectors | 1 [multi] | adapters-and-governance::list-locally-stored-steering-vectors::sub_000, adapters-and-governance::list-locally-stored-steering-vectors::sub_001 |
| `adapters-and-governance::live-edit-optimises-a-residual-applies-a-rank-1-weight-update-then-saves` | Live edit: optimises a residual + applies a rank-1 weight update, then saves. | 1 | adapters-and-governance::live-edit-optimises-a-residual-applies-a-rank-1-weight-update-then-saves |
| `adapters-and-governance::machine-readable-json-for-ci` | Machine-readable JSON for CI | 1 | adapters-and-governance::machine-readable-json-for-ci |
| `adapters-and-governance::model-registry-lineage` | Model Registry & Lineage | 2 | adapters-and-governance::model-registry-lineage |
| `adapters-and-governance::namespace-pinning-anti-ai-jacking` | Namespace Pinning (Anti-AI-Jacking) | 2 [multi] | adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_000, adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_001 |
| `adapters-and-governance::on-a-major-regression-a-pre-scored-canary-suite-needs-no-model-load` | on a MAJOR regression. A pre-scored canary suite needs no model load. | 1 | adapters-and-governance::on-a-major-regression-a-pre-scored-canary-suite-needs-no-model-load |
| `adapters-and-governance::one-time-setup` | One-time setup | 1 | adapters-and-governance::one-time-setup |
| `adapters-and-governance::or-derive-a-fresh-snapshot-s-config-base-straight-from-a-registry-entry-v0-71-4` | Or derive a fresh snapshot's config + base straight from a Registry entry (v0.71.4) | 1 | adapters-and-governance::or-derive-a-fresh-snapshot-s-config-base-straight-from-a-registry-entry-v0-71-4 |
| `adapters-and-governance::or-sign-with-an-existing-key-or-set-soup-signing-key` | or sign with an existing key (or set SOUP_SIGNING_KEY) | 1 | adapters-and-governance::or-sign-with-an-existing-key-or-set-soup-signing-key |
| `adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups` | Or via soup.yaml when training a model with GRACE-aware lookups | 1 [multi] | adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups::sub_000, adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups::sub_001 |
| `adapters-and-governance::pack-a-registry-entry-into-a-can` | Pack a registry entry into a .can | 1 | adapters-and-governance::pack-a-registry-entry-into-a-can |
| `adapters-and-governance::pause-resume-the-daemon-between-iterations-atomic-state-flip` | Pause/resume the daemon between iterations (atomic state flip) | 1 | adapters-and-governance::pause-resume-the-daemon-between-iterations-atomic-state-flip |
| `adapters-and-governance::per-layer-w-frobenius-diff-effective-rank-drift-top-k-changed-projections` | Per-layer ΔW Frobenius diff + effective-rank drift + top-K changed projections | 1 | adapters-and-governance::per-layer-w-frobenius-diff-effective-rank-drift-top-k-changed-projections |
| `adapters-and-governance::plan-only-mode-validates-the-request-prints-the-resolved-editplan-exits-0` | Plan-only mode validates the request + prints the resolved EditPlan + exits 0. | 1 | adapters-and-governance::plan-only-mode-validates-the-request-prints-the-resolved-editplan-exits-0 |
| `adapters-and-governance::preview-the-manifest-without-extracting` | Preview the manifest without extracting | 1 | adapters-and-governance::preview-the-manifest-without-extracting |
| `adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict` | Promote a canary at 5% traffic with auto-rollback on MAJOR verdict | 1 | adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict |
| `adapters-and-governance::promote-an-entry-add-a-tag-e-g-prod` | Promote an entry (add a tag, e.g. "prod") | 1 | adapters-and-governance::promote-an-entry-add-a-tag-e-g-prod |
| `adapters-and-governance::provenance-attestations-soup-attest-emit` | Provenance Attestations (`soup attest emit`) | 2 [multi] | adapters-and-governance::provenance-attestations-soup-attest-emit::sub_000, adapters-and-governance::provenance-attestations-soup-attest-emit::sub_001, adapters-and-governance::provenance-attestations-soup-attest-emit::sub_002 |
| `adapters-and-governance::publish-a-can-to-hf-hub-as-a-dataset` | Publish a .can to HF Hub as a dataset | 1 [multi] | adapters-and-governance::publish-a-can-to-hf-hub-as-a-dataset::sub_000, adapters-and-governance::publish-a-can-to-hf-hub-as-a-dataset::sub_001 |
| `adapters-and-governance::register-a-completed-run` | Register a completed run | 1 | adapters-and-governance::register-a-completed-run |
| `adapters-and-governance::registry-lineage-via-pack-cans` | Registry lineage via --pack-cans. | 1 | adapters-and-governance::registry-lineage-via-pack-cans |
| `adapters-and-governance::replay-any-recorded-iteration` | Replay any recorded iteration | 1 | adapters-and-governance::replay-any-recorded-iteration |
| `adapters-and-governance::reproducibility-receipt-soup-train-repro-receipt` | Reproducibility Receipt (`soup train --repro-receipt`) | 2 | adapters-and-governance::reproducibility-receipt-soup-train-repro-receipt |
| `adapters-and-governance::restore-the-snapshot-s-config-refuses-if-source-sha-drifted` | Restore the snapshot's config (refuses if source SHA drifted) | 1 | adapters-and-governance::restore-the-snapshot-s-config-refuses-if-source-sha-drifted |
| `adapters-and-governance::run-a-can-end-to-end-extract-train-optional-deploy` | Run a .can end-to-end: extract → train (→ optional deploy) | 1 | adapters-and-governance::run-a-can-end-to-end-extract-train-optional-deploy |
| `adapters-and-governance::run-the-daemon-foreground` | Run the daemon (foreground) | 1 | adapters-and-governance::run-the-daemon-foreground |
| `adapters-and-governance::self-consistency-verify-embedded-public-key` | self-consistency verify (embedded public key) | 1 | adapters-and-governance::self-consistency-verify-embedded-public-key |
| `adapters-and-governance::show-full-details-config-eval-baseline-artifacts-ancestors` | Show full details: config, eval baseline, artifacts, ancestors | 1 | adapters-and-governance::show-full-details-config-eval-baseline-artifacts-ancestors |
| `adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries` | Side-by-side config diff + eval delta between two entries | 1 | adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries |
| `adapters-and-governance::snapshot-a-training-environment-as-a-comparable-branch` | Snapshot a training environment as a comparable branch | 1 | adapters-and-governance::snapshot-a-training-environment-as-a-comparable-branch |
| `adapters-and-governance::soup-cans-shareable-recipes` | Soup Cans (Shareable Recipes) | 2 | adapters-and-governance::soup-cans-shareable-recipes |
| `adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors` | Strict Safetensors Mode (`soup adapters check-safetensors`) | 2 | adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors |
| `adapters-and-governance::teammates-re-check-the-lock-exit-3-on-drift` | Teammates re-check the lock; exit 3 on drift. | 1 | adapters-and-governance::teammates-re-check-the-lock-exit-3-on-drift |
| `adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs` | Train a steering vector from contrastive (positive, negative) prompt pairs | 1 | adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs |
| `adapters-and-governance::unpack-a-recorded-iteration-s-soup-can-for-what-if-analysis-v0-71-4` | Unpack a recorded iteration's Soup Can for what-if analysis (v0.71.4) | 1 | adapters-and-governance::unpack-a-recorded-iteration-s-soup-can-for-what-if-analysis-v0-71-4 |
| `adapters-and-governance::verify-schema-config-parseability` | Verify schema + config parseability | 1 | adapters-and-governance::verify-schema-config-parseability |
| `adapters-and-governance::weighted-merge-with-linear-ties-dare-svd-strategies` | Weighted merge with linear / ties / dare / svd strategies | 1 | adapters-and-governance::weighted-merge-with-linear-ties-dare-svd-strategies |
| `adapters-and-governance::writes-bom-cdx-json-bom-spdx-json` | writes bom.cdx.json + bom.spdx.json | 1 | adapters-and-governance::writes-bom-cdx-json-bom-spdx-json |

### Query slots (fill in below — do not edit the section table)

### adapters-and-governance slot 1

```
query_id:            manual_001
query:               why does soup lock check exit with code 3
query_type:          troubleshooting
relevant_section_ids:
  - adapters-and-governance::3-lock-a-reproducible-run-state-closure-sha-base-dataset-env
  - adapters-and-governance::teammates-re-check-the-lock-exit-3-on-drift
  - adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution
relevant_chunk_ids:
  - adapters-and-governance::3-lock-a-reproducible-run-state-closure-sha-base-dataset-env
  - adapters-and-governance::teammates-re-check-the-lock-exit-3-on-drift
  - adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution::sub_000
evidence_chunk_ids:
  - adapters-and-governance::exits-3-on-broken-at-pipe-into-soup-adapters-blame-for-attribution::sub_000
  - adapters-and-governance::teammates-re-check-the-lock-exit-3-on-drift
rationale:           The lock chunks define the closure as base + dataset + env and show the check command; sub_000 lists the five compared fields that trigger exit 3 and marks soup_version/created_at advisory.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 2

```
query_id:            manual_002
query:               How do I bisect training checkpoints when an eval regresses?
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval
  - commands::all-commands::sub_054
evidence_chunk_ids:
  - adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval
rationale:           The bisect chunk shows the checkpoint list, the per-checkpoint eval command template, and the output file. Cross-corpus: the training command table documents the same bisect command and its binary-search purpose.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_054"], "note": "the training command table documents the same bisect command and its binary-search purpose"}
```

### adapters-and-governance slot 3

```
query_id:            manual_003
query:               how do I see which training rows influenced an adapter
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::leave-one-out-ablation-plan-against-a-4-hour-wall-clock-budget
  - adapters-and-governance::list-all-snapshotted-branches
relevant_chunk_ids:
  - adapters-and-governance::leave-one-out-ablation-plan-against-a-4-hour-wall-clock-budget
  - adapters-and-governance::list-all-snapshotted-branches::sub_002
evidence_chunk_ids:
  - adapters-and-governance::leave-one-out-ablation-plan-against-a-4-hour-wall-clock-budget
rationale:           The blame chunk passes the dataset and layer; sub_002 documents the live DataInf runner, the --top-k count, and the synthetic-probe fallback.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 4

```
query_id:            manual_004
query:               what does soup loop automate
query_type:          conceptual
relevant_section_ids:
  - adapters-and-governance::data-flywheel-soup-loop
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::data-flywheel-soup-loop
  - commands::all-commands::sub_020
evidence_chunk_ids:
  - adapters-and-governance::data-flywheel-soup-loop
rationale:           The section describes the traces to preference pairs to eval-gated DPO to canary and rollback pipeline and the components it connects. Cross-corpus: the training command table names the loop stages (harvest, train, gate, deploy) and pre-wired mode.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_020"], "note": "the training command table names the loop stages (harvest, train, gate, deploy) and pre-wired mode"}
```

### adapters-and-governance slot 5

```
query_id:            manual_005
query:               does soup roll back a canary automatically if the eval regresses
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict
  - adapters-and-governance::replay-any-recorded-iteration
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict
  - adapters-and-governance::replay-any-recorded-iteration
  - commands::all-commands::sub_021
evidence_chunk_ids:
  - adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict
rationale:           The canary command enables autoroll on regression; the loop-state chunk explains the sticky deterministic router. Cross-corpus: the training command table states that loop canary promotes and auto-rolls-back on a major verdict.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_021"], "note": "the training command table states that loop canary promotes and auto-rolls-back on a major verdict"}
```

### adapters-and-governance slot 6

```
query_id:            manual_006
query:               ROME vs MEMIT vs AlphaEdit differences
query_type:          conceptual
relevant_section_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation
relevant_chunk_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_002
evidence_chunk_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_002
rationale:           sub_002 defines each method: ROME edits one layer, MEMIT spreads the residual over a band, AlphaEdit projects the update orthogonally.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 7

```
query_id:            manual_007
query:               compare model answers before and after a knowledge edit
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000
  - commands::all-commands::sub_042
evidence_chunk_ids:
  - adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000
rationale:           sub_000 shows the edit-diff command with before/after models and probe prompts. Cross-corpus: the training command table shows the same edit-diff command with probes and before/after models.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_042"], "note": "the training command table shows the same edit-diff command with probes and before/after models"}
```

### adapters-and-governance slot 8

```
query_id:            manual_008
query:               build a control vector from positive and negative prompts
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs
  - adapters-and-governance::list-locally-stored-steering-vectors
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs
  - adapters-and-governance::list-locally-stored-steering-vectors::sub_001
  - commands::all-commands::sub_043
evidence_chunk_ids:
  - adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs
rationale:           The train command takes contrastive pairs; sub_001 covers the live fit, persisted vector files, and the per-method pair minimums. Cross-corpus: the training command table shows steer train with --method caa|iti|repe and positive/negative pairs.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_043"], "note": "the training command table shows steer train with --method caa|iti|repe and positive/negative pairs"}
```

### adapters-and-governance slot 9

```
query_id:            manual_009
query:               grace codebook size limit
query_type:          config_behavior
relevant_section_ids:
  - adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups
relevant_chunk_ids:
  - adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups::sub_000
evidence_chunk_ids:
  - adapters-and-governance::or-via-soup-yaml-when-training-a-model-with-grace-aware-lookups::sub_000
rationale:           The YAML chunk sets grace_codebook_size with a 100k maximum and the residual-stream width.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 10

```
query_id:            manual_010
query:               soup registry diff output
query_type:          command_detail
relevant_section_ids:
  - adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries
  - commands::all-commands
relevant_chunk_ids:
  - adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries
  - commands::all-commands::sub_022
evidence_chunk_ids:
  - adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries
rationale:           The registry-diff command compares two entries; the section heading states the side-by-side config diff and eval delta output. Cross-corpus: the training command table describes registry diff as side-by-side config plus eval delta.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_022"], "note": "the training command table describes registry diff as side-by-side config plus eval delta"}
```

### adapters-and-governance slot 11

```
query_id:            manual_011
query:               dare merge seed determinism
query_type:          command_detail
relevant_section_ids:
  - adapters-and-governance::dare-merge-deterministic-via-seed
relevant_chunk_ids:
  - adapters-and-governance::dare-merge-deterministic-via-seed
evidence_chunk_ids:
  - adapters-and-governance::dare-merge-deterministic-via-seed
rationale:           The DARE example passes --density and --seed, and the section marks the merge deterministic through the seed.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 12

```
query_id:            manual_012
query:               how do signed attestations get embedded in a soup can
query_type:          relationship
relevant_section_ids:
  - adapters-and-governance::embed-in-toto-attestations-into-the-manifest-v3-cans-repeatable
  - adapters-and-governance::provenance-attestations-soup-attest-emit
relevant_chunk_ids:
  - adapters-and-governance::embed-in-toto-attestations-into-the-manifest-v3-cans-repeatable
  - adapters-and-governance::provenance-attestations-soup-attest-emit::sub_000
evidence_chunk_ids:
  - adapters-and-governance::embed-in-toto-attestations-into-the-manifest-v3-cans-repeatable
  - adapters-and-governance::provenance-attestations-soup-attest-emit::sub_000
rationale:           The can-pack example passes an attestation file with --attest; sub_000 shows the in-toto/SLSA statement that attest emit produces.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 13

```
query_id:            manual_013
query:               can I merge adapters whose licenses conflict
query_type:          conceptual
relevant_section_ids:
  - adapters-and-governance::license-conflict-matrix-at-merge
relevant_chunk_ids:
  - adapters-and-governance::license-conflict-matrix-at-merge::sub_000
  - adapters-and-governance::license-conflict-matrix-at-merge::sub_001
evidence_chunk_ids:
  - adapters-and-governance::license-conflict-matrix-at-merge::sub_000
rationale:           sub_000 defines the 33-license compatibility table and a refusal example; sub_001 covers auto-detection and the audit-logged override.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 14

```
query_id:            manual_014
query:               what stops a hijacked huggingface repo from being pulled
query_type:          conceptual
relevant_section_ids:
  - adapters-and-governance::namespace-pinning-anti-ai-jacking
relevant_chunk_ids:
  - adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_000
  - adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_001
evidence_chunk_ids:
  - adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_000
rationale:           sub_000 describes the trust-on-first-use author pin; sub_001 covers the re-created-repo attack and download-time enforcement.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 15

```
query_id:            manual_015
query:               what goes into a soup airgap bundle and how big can it get
query_type:          how_to
relevant_section_ids:
  - adapters-and-governance::airgap-bundle-soup-airgap-bundle
relevant_chunk_ids:
  - adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_000
  - adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_001
evidence_chunk_ids:
  - adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_000
rationale:           sub_000 lists the bundle contents and manifest; sub_001 gives the 100 GiB cap, deterministic labeling, and safe extraction.
subset:              primary
cross_corpus_overlap: null
```

### adapters-and-governance slot 16

```
query_id:            manual_016
query:               Soup refuses to load a .bin adapter, what formats are allowed?
query_type:          troubleshooting
relevant_section_ids:
  - adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors
relevant_chunk_ids:
  - adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors
evidence_chunk_ids:
  - adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors
rationale:           The section lists the eight refused pickle extensions, the conversion recipe, and the strict-mode exit code.
subset:              primary
cross_corpus_overlap: null
```


## compliance.md — 16 chunks, 13 sections, target 8 queries

### Sections and chunk IDs

| section_id | heading | level | chunks |
|---|---|---|---|
| `compliance::1-start-from-a-compliance-template` | 1. Start from a compliance template | 2 | compliance::1-start-from-a-compliance-template |
| `compliance::2-clean-the-data-before-training` | 2. Clean the data before training | 2 | compliance::2-clean-the-data-before-training |
| `compliance::3-train-with-a-reproducibility-receipt-annex-xi-energy-for-the-eu` | 3. Train with a reproducibility receipt (+ Annex XI / energy for the EU) | 2 | compliance::3-train-with-a-reproducibility-receipt-annex-xi-energy-for-the-eu |
| `compliance::4-register-the-run-then-emit-bom-attestation` | 4. Register the run, then emit BOM + attestation | 2 [multi] | compliance::4-register-the-run-then-emit-bom-attestation::sub_000, compliance::4-register-the-run-then-emit-bom-attestation::sub_001 |
| `compliance::5-sign-scan-and-verify-the-artifact` | 5. Sign, scan, and verify the artifact | 2 | compliance::5-sign-scan-and-verify-the-artifact |
| `compliance::6-air-gap-transfer-optional` | 6. Air-gap transfer (optional) | 2 | compliance::6-air-gap-transfer-optional |
| `compliance::7-generate-a-documented-model-card` | 7. Generate a documented model card | 2 | compliance::7-generate-a-documented-model-card |
| `compliance::8-gate-future-changes-in-ci` | 8. Gate future changes in CI | 2 | compliance::8-gate-future-changes-in-ci |
| `compliance::compliance-governance-quickstart` | Compliance & governance quickstart | 1 [multi] | compliance::compliance-governance-quickstart::sub_000, compliance::compliance-governance-quickstart::sub_001 |
| `compliance::eu-ai-act-auto-generate-the-annex-xi-xii-documentation-measure-energy` | EU AI Act: auto-generate the Annex XI/XII documentation + measure energy | 1 | compliance::eu-ai-act-auto-generate-the-annex-xi-xii-documentation-measure-energy |
| `compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card` | or, when uploading to the Hub, override the auto-generated card: | 1 | compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card |
| `compliance::sr-11-7-soc-2-hipaa-capture-seeds-kernels-gpu-os` | SR 11-7 / SOC 2 / HIPAA: capture seeds, kernels, GPU, OS | 1 | compliance::sr-11-7-soc-2-hipaa-capture-seeds-kernels-gpu-os |
| `compliance::writes-github-workflows-soup-gate-yml` | writes .github/workflows/soup-gate.yml | 1 [multi] | compliance::writes-github-workflows-soup-gate-yml::sub_000, compliance::writes-github-workflows-soup-gate-yml::sub_001 |

### Query slots (fill in below — do not edit the section table)

### compliance slot 1

```
query_id:            manual_017
query:               which soup init templates exist for regulated industries
query_type:          command_detail
relevant_section_ids:
  - compliance::1-start-from-a-compliance-template
  - README::soup-documentation
relevant_chunk_ids:
  - compliance::1-start-from-a-compliance-template
  - README::soup-documentation::sub_003
evidence_chunk_ids:
  - compliance::1-start-from-a-compliance-template
rationale:           The template chunk lists the four regime templates and explains that their header comments carry the compliance commands. Cross-corpus: the training README lists the four init templates for regulated regimes.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["README::soup-documentation::sub_003"], "note": "the training README lists the four init templates for regulated regimes"}
```

### compliance slot 2

```
query_id:            manual_018
query:               clean emails and phone numbers out of my training data
query_type:          how_to
relevant_section_ids:
  - compliance::2-clean-the-data-before-training
  - commands::all-commands
relevant_chunk_ids:
  - compliance::2-clean-the-data-before-training
  - commands::all-commands::sub_019
evidence_chunk_ids:
  - compliance::2-clean-the-data-before-training
rationale:           The data chunk shows soup data pii for emails, phones, SSNs and MRNs, plus decontaminate for benchmark overlap. Cross-corpus: the training command table documents data pii flagging email, phone, SSN, and credit-card rows.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_019"], "note": "the training command table documents data pii flagging email, phone, SSN, and credit-card rows"}
```

### compliance slot 3

```
query_id:            manual_019
query:               bom --attach-to-registry wrote the files but exited non-zero
query_type:          troubleshooting
relevant_section_ids:
  - compliance::4-register-the-run-then-emit-bom-attestation
relevant_chunk_ids:
  - compliance::4-register-the-run-then-emit-bom-attestation::sub_000
  - compliance::4-register-the-run-then-emit-bom-attestation::sub_001
evidence_chunk_ids:
  - compliance::4-register-the-run-then-emit-bom-attestation::sub_001
rationale:           sub_001 states that --attach-to-registry needs --output and that lookup or attachment failure exits non-zero while the emitted files stay on disk.
subset:              primary
cross_corpus_overlap: null
```

### compliance slot 4

```
query_id:            manual_020
query:               what ends up in the generated model card
query_type:          conceptual
relevant_section_ids:
  - compliance::7-generate-a-documented-model-card
  - commands::all-commands
relevant_chunk_ids:
  - compliance::7-generate-a-documented-model-card
  - commands::all-commands::sub_027
evidence_chunk_ids:
  - compliance::7-generate-a-documented-model-card
rationale:           The section enumerates base model, training config, eval scorecard, hashes, lineage, and attached artifacts. Cross-corpus: the training command table lists the card contents: config, evals, hashes, lineage, artifacts.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_027"], "note": "the training command table lists the card contents: config, evals, hashes, lineage, artifacts"}
```

### compliance slot 5

```
query_id:            manual_021
query:               publish a model to huggingface with my own model card
query_type:          how_to
relevant_section_ids:
  - compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card
  - commands::all-commands
relevant_chunk_ids:
  - compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card
  - commands::all-commands::sub_027
evidence_chunk_ids:
  - compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card
rationale:           The chunk shows soup push --card with a registry reference as the Hub card override. Cross-corpus: the training command table shows push --card uploading the registry-driven card.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_027"], "note": "the training command table shows push --card uploading the registry-driven card"}
```

### compliance slot 6

```
query_id:            manual_022
query:               generated ci workflow steps
query_type:          relationship
relevant_section_ids:
  - compliance::8-gate-future-changes-in-ci
  - compliance::writes-github-workflows-soup-gate-yml
relevant_chunk_ids:
  - compliance::8-gate-future-changes-in-ci
  - compliance::writes-github-workflows-soup-gate-yml::sub_000
evidence_chunk_ids:
  - compliance::writes-github-workflows-soup-gate-yml::sub_000
rationale:           The gate section generates the workflow; sub_000 lists the validate, expect, ship sequence and the exit-2 block.
subset:              primary
cross_corpus_overlap: null
```

### compliance slot 7

```
query_id:            manual_023
query:               which expectation checks can go in expectations.yaml
query_type:          config_behavior
relevant_section_ids:
  - compliance::writes-github-workflows-soup-gate-yml
  - data::expectations-suite-great-expectations-for-chat-data
relevant_chunk_ids:
  - compliance::writes-github-workflows-soup-gate-yml::sub_000
  - data::expectations-suite-great-expectations-for-chat-data
evidence_chunk_ids:
  - compliance::writes-github-workflows-soup-gate-yml::sub_000
rationale:           sub_000 shows the minimal expectations YAML and the four supported check names. Cross-corpus: the training data guide shows the expectations YAML and its supported check names.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["data::expectations-suite-great-expectations-for-chat-data"], "note": "the training data guide shows the expectations YAML and its supported check names"}
```

### compliance slot 8

```
query_id:            manual_024
query:               what steps does soup's compliance workflow cover
query_type:          conceptual
relevant_section_ids:
  - compliance::compliance-governance-quickstart
relevant_chunk_ids:
  - compliance::compliance-governance-quickstart::sub_000
  - compliance::compliance-governance-quickstart::sub_001
evidence_chunk_ids:
  - compliance::compliance-governance-quickstart::sub_001
rationale:           sub_000 introduces the end-to-end flow; sub_001 lists the commands for templates, provenance, integrity, audit, air gap, publish, and CI.
subset:              primary
cross_corpus_overlap: null
```


## evaluation.md — 120 chunks, 82 sections, target 17 queries

### Sections and chunk IDs

| section_id | heading | level | chunks |
|---|---|---|---|
| `evaluation::0-5` **[EXCLUDED]** | 0.5 | 1 | evaluation::0-5 |
| `evaluation::1-0` **[EXCLUDED]** | 1.0 | 1 | evaluation::1-0 |
| `evaluation::1-draft-a-goal-conditioned-suite-from-your-training-data` | 1. Draft a goal-conditioned suite from your training data. | 1 | evaluation::1-draft-a-goal-conditioned-suite-from-your-training-data |
| `evaluation::1-sparse-autoencoder-feature-diff-which-sae-features-moved-during-ft` | 1. Sparse-Autoencoder feature diff: which SAE features moved during FT? | 1 | evaluation::1-sparse-autoencoder-feature-diff-which-sae-features-moved-during-ft |
| `evaluation::2-discover-held-out-canaries-memorization-probes` | 2. Discover held-out canaries + memorization probes. | 1 | evaluation::2-discover-held-out-canaries-memorization-probes |
| `evaluation::2-live-influence-function-blame-which-50-training-rows-pulled-toward-this-output` | 2. Live influence-function blame: which 50 training rows pulled toward this output? | 1 | evaluation::2-live-influence-function-blame-which-50-training-rows-pulled-toward-this-output |
| `evaluation::20833-33-none-when-wall-clock-0-no-fabrication` | 20833.33  — None when wall_clock <= 0 (no fabrication) | 1 | evaluation::20833-33-none-when-wall-clock-0-no-fabrication |
| `evaluation::3-freeze-the-design-as-a-checksummed-eval-suite-artifact` | 3. Freeze the design as a checksummed eval_suite artifact. | 1 | evaluation::3-freeze-the-design-as-a-checksummed-eval-suite-artifact |
| `evaluation::3-sleeper-agent-defection-probe-per-token-defection-rate-via-calibrated-linear-probe` | 3. Sleeper-agent defection probe: per-token defection rate via calibrated linear probe | 1 | evaluation::3-sleeper-agent-defection-probe-per-token-defection-rate-via-calibrated-linear-probe |
| `evaluation::3b-honesty-misuse-probes-v0-71-8-same-shape-5-20-verdict-bands` | 3b. Honesty + misuse probes (v0.71.8) — same shape, 5% / 20% verdict bands | 1 | evaluation::3b-honesty-misuse-probes-v0-71-8-same-shape-5-20-verdict-bands |
| `evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy` | 4. Heuristic gap analysis vs the task taxonomy. | 1 [multi] | evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy::sub_000, evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy::sub_001 |
| `evaluation::4-pairwise-adapter-interference-matrix-which-pairs-can-t-be-deployed-together` | 4. Pairwise adapter interference matrix: which pairs can't be deployed together? | 1 | evaluation::4-pairwise-adapter-interference-matrix-which-pairs-can-t-be-deployed-together |
| `evaluation::5-probe-pack-list-assemble-calibrated-probes-per-base-sleeper-truth-harm-per-base` | 5. Probe pack: list/assemble calibrated probes per base (sleeper + truth + harm per base) | 1 | evaluation::5-probe-pack-list-assemble-calibrated-probes-per-base-sleeper-truth-harm-per-base |
| `evaluation::6-sae-auto-download-capture-pipeline-v0-71-8` | 6. SAE auto-download + capture pipeline (v0.71.8) | 1 [multi] | evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_000, evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_001, evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_002, evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_003 |
| `evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact` | Attach the report to a Model Registry entry as a first-class artifact | 1 [multi] | evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_000, evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_001, evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_002, evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_003 |
| `evaluation::auto-eval-after-training-configure-in-soup-yaml` | Auto-eval after training (configure in soup.yaml) | 1 | evaluation::auto-eval-after-training-configure-in-soup-yaml |
| `evaluation::auto-eval-config-soup-yaml` | Auto-Eval Config (soup.yaml) | 3 | evaluation::auto-eval-config-soup-yaml |
| `evaluation::base-vs-tuned-per-prompt-swap-debiased-base-0-5-coin-flip-won-winrate-0-5` | base vs tuned per prompt (swap-debiased); base = 0.5 coin-flip, won <=> winrate > 0.5 | 1 | evaluation::base-vs-tuned-per-prompt-swap-debiased-base-0-5-coin-flip-won-winrate-0-5 |
| `evaluation::baseline-logits-quantized-logits-list-list-float-aligned-per-prompt` | baseline_logits / quantized_logits: list[list[float]] aligned per-prompt | 1 | evaluation::baseline-logits-quantized-logits-list-list-float-aligned-per-prompt |
| `evaluation::both-sides-may-be-registry-refs` | Both sides may be registry refs | 1 | evaluation::both-sides-may-be-registry-refs |
| `evaluation::closing-the-evidence-loop-v0-71-39` | Closing the evidence loop (v0.71.39) | 3 [multi] | evaluation::closing-the-evidence-loop-v0-71-39::sub_000, evaluation::closing-the-evidence-loop-v0-71-39::sub_001, evaluation::closing-the-evidence-loop-v0-71-39::sub_002, evaluation::closing-the-evidence-loop-v0-71-39::sub_003, evaluation::closing-the-evidence-loop-v0-71-39::sub_004 |
| `evaluation::compare-a-pre-quant-model-with-its-post-quant-version` | Compare a pre-quant model with its post-quant version | 1 | evaluation::compare-a-pre-quant-model-with-its-post-quant-version |
| `evaluation::compare-eval-results-between-two-training-runs` | Compare eval results between two training runs | 1 | evaluation::compare-eval-results-between-two-training-runs |
| `evaluation::compute-scores-from-a-pre-built-evidence-json` | Compute scores from a pre-built evidence JSON | 1 | evaluation::compute-scores-from-a-pre-built-evidence-json |
| `evaluation::custom-eval-format` | Custom Eval Format | 3 | evaluation::custom-eval-format |
| `evaluation::custom-eval-tasks-from-jsonl` | Custom eval tasks from JSONL | 1 | evaluation::custom-eval-tasks-from-jsonl |
| `evaluation::diagnose-post-training-report-card` | Diagnose (Post-Training Report Card) | 2 | evaluation::diagnose-post-training-report-card |
| `evaluation::drift-alarm-soup-drift-alarm` | Drift Alarm (`soup drift-alarm`) | 2 | evaluation::drift-alarm-soup-drift-alarm |
| `evaluation::dry-run-a-sweep-across-a-subset` | Dry-run a sweep across a subset | 1 | evaluation::dry-run-a-sweep-across-a-subset |
| `evaluation::eval-depth-soup-eval-behavior-capability-checklist-irt-subset` | Eval Depth (`soup eval behavior / capability / checklist / irt-subset`) | 2 | evaluation::eval-depth-soup-eval-behavior-capability-checklist-irt-subset |
| `evaluation::eval-design-pipeline-soup-eval-design-discover-lock-coverage` | Eval Design Pipeline (`soup eval design / discover / lock / coverage`) | 2 | evaluation::eval-design-pipeline-soup-eval-design-discover-lock-coverage |
| `evaluation::eval-gated-training` | Eval-Gated Training | 2 [multi] | evaluation::eval-gated-training::sub_000, evaluation::eval-gated-training::sub_001, evaluation::eval-gated-training::sub_002 |
| `evaluation::evaluation-diagnostics-probes` | Evaluation, Diagnostics & Probes | 1 [multi] | evaluation::evaluation-diagnostics-probes::sub_000, evaluation::evaluation-diagnostics-probes::sub_001, evaluation::evaluation-diagnostics-probes::sub_002, evaluation::evaluation-diagnostics-probes::sub_003, evaluation::evaluation-diagnostics-probes::sub_004 |
| `evaluation::gate-pr-ci-refuse-evidence-that-doesn-t-match-the-committed-config-comment-the-verdict` | Gate (PR CI): refuse evidence that doesn't match the committed config, comment the verdict | 1 [multi] | evaluation::gate-pr-ci-refuse-evidence-that-doesn-t-match-the-committed-config-comment-the-verdict::sub_000, evaluation::gate-pr-ci-refuse-evidence-that-doesn-t-match-the-committed-config-comment-the-verdict::sub_001, evaluation::gate-pr-ci-refuse-evidence-that-doesn-t-match-the-committed-config-comment-the-verdict::sub_002 |
| `evaluation::generic-dispatch-by-canonical-name` | generic dispatch by canonical name | 1 | evaluation::generic-dispatch-by-canonical-name |
| `evaluation::harmful-prompts-ship-redacted-pull-real-sets-from-upstream-papers` | Harmful prompts ship REDACTED — pull real sets from upstream papers. | 1 | evaluation::harmful-prompts-ship-redacted-pull-real-sets-from-upstream-papers |
| `evaluation::headline-ux-one-line-gives-you-a-verdict` | Headline UX — one line gives you a verdict. | 1 | evaluation::headline-ux-one-line-gives-you-a-verdict |
| `evaluation::human-a-b-evaluation-with-elo-ratings` | Human A/B evaluation with Elo ratings | 1 | evaluation::human-a-b-evaluation-with-elo-ratings |
| `evaluation::install-eval-dependencies` | Install eval dependencies | 1 | evaluation::install-eval-dependencies |
| `evaluation::leg-1-via-llm-as-a-judge-instead-of-an-accuracy-metric` | Leg-1 via LLM-as-a-judge instead of an accuracy metric | 1 | evaluation::leg-1-via-llm-as-a-judge-instead-of-an-accuracy-metric |
| `evaluation::leg-2-via-lm-eval-benchmarks-base-scores-supplied-by-baseline` | Leg-2 via lm-eval benchmarks, base scores supplied by --baseline | 1 | evaluation::leg-2-via-lm-eval-benchmarks-base-scores-supplied-by-baseline |
| `evaluation::list-the-built-in-catalogue` | List the built-in catalogue | 1 | evaluation::list-the-built-in-catalogue |
| `evaluation::live-base-vs-a-lora-adapter-metric-leg-default-mini-benchmarks` | Live: base vs a LoRA adapter, metric leg + default mini benchmarks | 1 | evaluation::live-base-vs-a-lora-adapter-metric-leg-default-mini-benchmarks |
| `evaluation::live-v0-71-7-generate-pre-post-responses-on-the-bundled-battery-score-the-diff` | LIVE (v0.71.7): generate pre/post responses on the bundled battery + score the diff | 1 | evaluation::live-v0-71-7-generate-pre-post-responses-on-the-bundled-battery-score-the-diff |
| `evaluation::live-v0-71-7-invoke-lm-eval-harness-per-task-against-a-real-model` | LIVE (v0.71.7): invoke lm-eval-harness per task against a real model | 1 | evaluation::live-v0-71-7-invoke-lm-eval-harness-per-task-against-a-real-model |
| `evaluation::live-v0-71-7-load-the-model-and-run-all-six-probes-for-real` | LIVE (v0.71.7): load the model and run all six probes for real | 1 | evaluation::live-v0-71-7-load-the-model-and-run-all-six-probes-for-real |
| `evaluation::llm-as-a-judge-score-model-outputs-using-gpt-4o-ollama-etc` | LLM-as-a-judge (score model outputs using GPT-4o, Ollama, etc.) | 1 | evaluation::llm-as-a-judge-score-model-outputs-using-gpt-4o-ollama-etc |
| `evaluation::local-leaderboard-across-all-evaluated-models` | Local leaderboard across all evaluated models | 1 | evaluation::local-leaderboard-across-all-evaluated-models |
| `evaluation::lora-probe-and-base-model-proximity-held-out-logit-agreement-implies-probe` | LoRA probe, and base-model proximity (held-out logit agreement). Implies --probe. | 1 | evaluation::lora-probe-and-base-model-proximity-held-out-logit-agreement-implies-probe |
| `evaluation::model-arena-elo-tournament` | Model Arena (Elo Tournament) | 2 | evaluation::model-arena-elo-tournament |
| `evaluation::model-evaluation` | Model Evaluation | 2 | evaluation::model-evaluation |
| `evaluation::neutral-report-no-model-load-runs-as-a-sanity-check` | Neutral report (no model load — runs as a sanity check) | 1 | evaluation::neutral-report-no-model-load-runs-as-a-sanity-check |
| `evaluation::nlg-evaluation-metrics-bleu-rouge` | NLG Evaluation Metrics (BLEU + ROUGE) | 2 | evaluation::nlg-evaluation-metrics-bleu-rouge |
| `evaluation::noise-floor-v0-73-2` | Noise Floor (v0.73.2) | 3 [multi] | evaluation::noise-floor-v0-73-2::sub_000, evaluation::noise-floor-v0-73-2::sub_001, evaluation::noise-floor-v0-73-2::sub_002, evaluation::noise-floor-v0-73-2::sub_003, evaluation::noise-floor-v0-73-2::sub_004, evaluation::noise-floor-v0-73-2::sub_005, evaluation::noise-floor-v0-73-2::sub_006 |
| `evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json` | Offline: decide from pre-computed scores, persist the verdict JSON | 1 [multi] | evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_000, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_001, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_002, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_003, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_004, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_005, evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_006 |
| `evaluation::ok-0-012` | OK 0.012 | 1 | evaluation::ok-0-012 |
| `evaluation::optional-roi-probe-offline-heuristic-zero-few-shot-rag-lora-estimate` | Optional ROI probe (offline heuristic: zero/few-shot + RAG + LoRA estimate). | 1 | evaluation::optional-roi-probe-offline-heuristic-zero-few-shot-rag-lora-estimate |
| `evaluation::optional-webhook-on-drift-detected` | Optional webhook on drift detected | 1 | evaluation::optional-webhook-on-drift-detected |
| `evaluation::or-with-custom-alpha-beta` | Or with custom alpha / beta | 1 [multi] | evaluation::or-with-custom-alpha-beta::sub_000, evaluation::or-with-custom-alpha-beta::sub_001 |
| `evaluation::pick-top-info-30-of-items-5-10x-eval-bill-cut-without-losing-power` | Pick top-info 30% of items (5-10x eval-bill cut without losing power) | 1 | evaluation::pick-top-info-30-of-items-5-10x-eval-bill-cut-without-losing-power |
| `evaluation::post-train-x-rays-soup-probe-soup-adapters-blame-live` | Post-train X-rays (`soup probe`, `soup adapters blame --live`) | 2 | evaluation::post-train-x-rays-soup-probe-soup-adapters-blame-live |
| `evaluation::pre-flight-decision-soup-advise` | Pre-flight Decision (`soup advise`) | 2 | evaluation::pre-flight-decision-soup-advise |
| `evaluation::pre-push-regression-gate-soup-eval-gate-install` | Pre-Push Regression Gate (`soup eval gate-install`) | 2 [multi] | evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_000, evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_001, evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_002 |
| `evaluation::print-the-rubric-evidence-trail-of-the-last-verdict` | Print the rubric / evidence trail of the last verdict. | 1 | evaluation::print-the-rubric-evidence-trail-of-the-last-verdict |
| `evaluation::producer-train-job-compute-or-stamp-scores-bound-to-the-committed-recipe` | Producer (train job): compute or stamp scores, bound to the committed recipe | 1 | evaluation::producer-train-job-compute-or-stamp-scores-bound-to-the-committed-recipe |
| `evaluation::quant-calibration-kl-divergence` | Quant Calibration (KL Divergence) | 2 | evaluation::quant-calibration-kl-divergence |
| `evaluation::quant-lobotomy-checker` | Quant-Lobotomy Checker | 3 | evaluation::quant-lobotomy-checker |
| `evaluation::record-this-verdict-to-soup-advise-history-jsonl-for-later-compare` | Record this verdict to ~/.soup/advise_history.jsonl for later compare. | 1 | evaluation::record-this-verdict-to-soup-advise-history-jsonl-for-later-compare |
| `evaluation::render-as-json-for-ci-integration` | Render as JSON for CI integration | 1 | evaluation::render-as-json-for-ci-integration |
| `evaluation::richer-item-models-2pl-learns-per-item-discrimination-3pl-adds-a-guessing-floor` | Richer item models: 2PL learns per-item discrimination, 3PL adds a guessing floor | 1 | evaluation::richer-item-models-2pl-learns-per-item-discrimination-3pl-adds-a-guessing-floor |
| `evaluation::run-the-full-sweep-write-a-json-report` | Run the full sweep + write a JSON report | 1 | evaluation::run-the-full-sweep-write-a-json-report |
| `evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped` | Run your judge on a calibration set with positions swapped. | 1 [multi] | evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped::sub_000, evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped::sub_001 |
| `evaluation::score-over-refusal-regression-on-xstest-operator-supplies-evidence-json` | Score over-refusal regression on XSTest (operator supplies evidence JSON) | 1 | evaluation::score-over-refusal-regression-on-xstest-operator-supplies-evidence-json |
| `evaluation::sequential-a-b-harness-soup-ab` | Sequential A/B Harness (`soup ab`) | 2 | evaluation::sequential-a-b-harness-soup-ab |
| `evaluation::ship-verdict-soup-ship` | Ship Verdict (`soup ship`) | 2 [multi] | evaluation::ship-verdict-soup-ship::sub_000, evaluation::ship-verdict-soup-ship::sub_001 |
| `evaluation::show-prior-verdicts-newest-first-with-per-choice-counts` | Show prior verdicts (newest first), with per-choice counts. | 1 [multi] | evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_000, evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_001, evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_002 |
| `evaluation::so-the-golden-doc-n-ids-line-up-with-what-the-model-saw-at-train-time-v0-71-17` | so the golden [doc-N] ids line up with what the model saw at train time (v0.71.17) | 1 | evaluation::so-the-golden-doc-n-ids-line-up-with-what-the-model-saw-at-train-time-v0-71-17 |
| `evaluation::standard-benchmarks-wraps-lm-evaluation-harness` | Standard benchmarks (wraps lm-evaluation-harness) | 1 | evaluation::standard-benchmarks-wraps-lm-evaluation-harness |
| `evaluation::tests-yaml` | tests.yaml | 1 | evaluation::tests-yaml |
| `evaluation::tunability-probe-soup-tunability` | Tunability Probe (`soup tunability`) | 2 | evaluation::tunability-probe-soup-tunability |
| `evaluation::twitter-shareable-svg-badge-embeddable-in-a-model-card` | Twitter-shareable SVG badge embeddable in a model card | 1 | evaluation::twitter-shareable-svg-badge-embeddable-in-a-model-card |
| `evaluation::v0-71-8-auto-measure-the-matrix-live-instead-of-supplying-losses-json` | v0.71.8: auto-measure the matrix live instead of supplying losses.json | 1 | evaluation::v0-71-8-auto-measure-the-matrix-live-instead-of-supplying-losses-json |

### Query slots (fill in below — do not edit the section table)

### evaluation slot 1

```
query_id:            manual_025
query:               Should I fine-tune with DPO or SFT for my dataset?
query_type:          conceptual
relevant_section_ids:
  - evaluation::show-prior-verdicts-newest-first-with-per-choice-counts
relevant_chunk_ids:
  - evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_000
evidence_chunk_ids:
  - evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_000
rationale:           The rubric chunk maps paired chosen/rejected rows to DPO and routes the other cases to GRPO, prompt engineering, RAG, or SFT.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 2

```
query_id:            manual_026
query:               generate an eval suite from my training data
query_type:          how_to
relevant_section_ids:
  - evaluation::1-draft-a-goal-conditioned-suite-from-your-training-data
relevant_chunk_ids:
  - evaluation::1-draft-a-goal-conditioned-suite-from-your-training-data
evidence_chunk_ids:
  - evaluation::1-draft-a-goal-conditioned-suite-from-your-training-data
rationale:           The design command builds a goal-conditioned suite from the training JSONL and writes evals/design.json.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 3

```
query_id:            manual_027
query:               do two eval designs with the same content hash the same
query_type:          conceptual
relevant_section_ids:
  - evaluation::3-freeze-the-design-as-a-checksummed-eval-suite-artifact
  - evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy
relevant_chunk_ids:
  - evaluation::3-freeze-the-design-as-a-checksummed-eval-suite-artifact
  - evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy::sub_001
evidence_chunk_ids:
  - evaluation::4-heuristic-gap-analysis-vs-the-task-taxonomy::sub_001
rationale:           sub_001 explains canonical sorted-key JSON, the SHA-256 over on-disk bytes, and that semantic matches hash identically.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 4

```
query_id:            manual_028
query:               block a git push when eval accuracy regresses
query_type:          how_to
relevant_section_ids:
  - evaluation::pre-push-regression-gate-soup-eval-gate-install
relevant_chunk_ids:
  - evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_000
  - evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_001
evidence_chunk_ids:
  - evaluation::pre-push-regression-gate-soup-eval-gate-install::sub_000
rationale:           sub_000 installs the pre-push hook; sub_001 lists the four watched metrics and the paired-bootstrap decision bound.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 5

```
query_id:            manual_029
query:               eval_gate block settings in soup.yaml
query_type:          config_behavior
relevant_section_ids:
  - evaluation::eval-gated-training
relevant_chunk_ids:
  - evaluation::eval-gated-training::sub_000
  - evaluation::eval-gated-training::sub_001
evidence_chunk_ids:
  - evaluation::eval-gated-training::sub_000
rationale:           sub_000 shows the eval_gate YAML block and its keys; sub_001 shows the CLI override and post-hoc gate run.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 6

```
query_id:            manual_030
query:               how does soup ab decide when to stop collecting samples
query_type:          conceptual
relevant_section_ids:
  - evaluation::sequential-a-b-harness-soup-ab
  - evaluation::or-with-custom-alpha-beta
relevant_chunk_ids:
  - evaluation::sequential-a-b-harness-soup-ab
  - evaluation::or-with-custom-alpha-beta::sub_000
evidence_chunk_ids:
  - evaluation::sequential-a-b-harness-soup-ab
rationale:           The harness chunk describes the SPRT and its three decisions; sub_000 shows the input rows and the decision values.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 7

```
query_id:            manual_031
query:               what does exit code 3 from soup drift-alarm mean
query_type:          troubleshooting
relevant_section_ids:
  - evaluation::drift-alarm-soup-drift-alarm
  - evaluation::optional-webhook-on-drift-detected
  - commands::all-commands
relevant_chunk_ids:
  - evaluation::drift-alarm-soup-drift-alarm
  - evaluation::optional-webhook-on-drift-detected
  - commands::all-commands::sub_046
evidence_chunk_ids:
  - evaluation::drift-alarm-soup-drift-alarm
rationale:           The drift section sets the KL threshold and exit 3 on drift; the webhook chunk repeats the cron-friendly exit. Cross-corpus: the training command table states that drift-alarm exits 3 on drift.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_046"], "note": "the training command table states that drift-alarm exits 3 on drift"}
```

### evaluation slot 8

```
query_id:            manual_032
query:               soup diagnose failure modes
query_type:          conceptual
relevant_section_ids:
  - evaluation::diagnose-post-training-report-card
  - evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact
relevant_chunk_ids:
  - evaluation::diagnose-post-training-report-card
  - evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_001
  - evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_002
  - evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_003
evidence_chunk_ids:
  - evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_001
rationale:           The intro states seven failure modes and the verdict taxonomy; the table chunks list all modes, and sub_003 gives verdict bands and exit 2.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 9

```
query_id:            manual_033
query:               Task accuracy went up but MMLU dropped, should I ship?
query_type:          relationship
relevant_section_ids:
  - evaluation::ship-verdict-soup-ship
relevant_chunk_ids:
  - evaluation::ship-verdict-soup-ship::sub_000
  - evaluation::ship-verdict-soup-ship::sub_001
evidence_chunk_ids:
  - evaluation::ship-verdict-soup-ship::sub_000
  - evaluation::ship-verdict-soup-ship::sub_001
rationale:           sub_000 defines the task-win leg and the forgetting leg; sub_001 says any single regressed benchmark yields DON'T SHIP.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 10

```
query_id:            manual_034
query:               noise floor flag effect on ship verdict
query_type:          config_behavior
relevant_section_ids:
  - evaluation::noise-floor-v0-73-2
  - commands::all-commands
relevant_chunk_ids:
  - evaluation::noise-floor-v0-73-2::sub_000
  - evaluation::noise-floor-v0-73-2::sub_001
  - evaluation::noise-floor-v0-73-2::sub_004
  - commands::all-commands::sub_027
evidence_chunk_ids:
  - evaluation::noise-floor-v0-73-2::sub_000
rationale:           sub_000 motivates the measured GPU spread; sub_001 shows the flag and max(threshold, floor) gating; sub_004 covers cost and the --evidence rejection. Cross-corpus: the training command table documents the noise-floor repeat and max(threshold, floor) gating.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_027"], "note": "the training command table documents the noise-floor repeat and max(threshold, floor) gating"}
```

### evaluation slot 11

```
query_id:            manual_035
query:               how do I make a ship verdict replayable in CI
query_type:          how_to
relevant_section_ids:
  - evaluation::closing-the-evidence-loop-v0-71-39
  - evaluation::producer-train-job-compute-or-stamp-scores-bound-to-the-committed-recipe
  - commands::all-commands
relevant_chunk_ids:
  - evaluation::closing-the-evidence-loop-v0-71-39::sub_001
  - evaluation::closing-the-evidence-loop-v0-71-39::sub_003
  - evaluation::producer-train-job-compute-or-stamp-scores-bound-to-the-committed-recipe
  - commands::all-commands::sub_026
evidence_chunk_ids:
  - evaluation::closing-the-evidence-loop-v0-71-39::sub_001
rationale:           sub_001 defines --emit-evidence as replayable input; sub_003 documents the config gate exit 3; the producer chunk shows the command. Cross-corpus: the training command table documents emit-evidence, the config provenance gate, and the PR push.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_026"], "note": "the training command table documents emit-evidence, the config provenance gate, and the PR push"}
```

### evaluation slot 12

```
query_id:            manual_036
query:               score BLEU and ROUGE on custom eval outputs
query_type:          command_detail
relevant_section_ids:
  - evaluation::nlg-evaluation-metrics-bleu-rouge
relevant_chunk_ids:
  - evaluation::nlg-evaluation-metrics-bleu-rouge
evidence_chunk_ids:
  - evaluation::nlg-evaluation-metrics-bleu-rouge
rationale:           The section lists the BLEU/ROUGE helpers and the generic dispatch function for custom eval.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 13

```
query_id:            manual_037
query:               My quantized model lost 8% accuracy, is that too much?
query_type:          troubleshooting
relevant_section_ids:
  - evaluation::quant-lobotomy-checker
  - evaluation::render-as-json-for-ci-integration
relevant_chunk_ids:
  - evaluation::quant-lobotomy-checker
  - evaluation::render-as-json-for-ci-integration
evidence_chunk_ids:
  - evaluation::render-as-json-for-ci-integration
rationale:           The checker section introduces the before/after task comparison; the CI chunk carries the per-task 2% and 10% thresholds.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 14

```
query_id:            manual_038
query:               custom eval jsonl fields for exact and regex scoring
query_type:          config_behavior
relevant_section_ids:
  - evaluation::custom-eval-format
relevant_chunk_ids:
  - evaluation::custom-eval-format
evidence_chunk_ids:
  - evaluation::custom-eval-format
rationale:           The format chunk shows prompt, expected, category, and scoring rows for exact, regex, and contains.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 15

```
query_id:            manual_039
query:               run a short LoRA probe on several base models before choosing one
query_type:          how_to
relevant_section_ids:
  - evaluation::tunability-probe-soup-tunability
  - evaluation::run-the-full-sweep-write-a-json-report
  - commands::all-commands
relevant_chunk_ids:
  - evaluation::tunability-probe-soup-tunability
  - evaluation::run-the-full-sweep-write-a-json-report
  - commands::all-commands::sub_047
evidence_chunk_ids:
  - evaluation::tunability-probe-soup-tunability
rationale:           The probe section covers the candidate catalogue and plan/live modes; the sweep chunk gives the JSON report and Pareto frontier. Cross-corpus: the training command table shows the tunability probe and its Pareto report.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_047"], "note": "the training command table shows the tunability probe and its Pareto report"}
```

### evaluation slot 16

```
query_id:            manual_040
query:               position_bias in judge calibration
query_type:          conceptual
relevant_section_ids:
  - evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped
relevant_chunk_ids:
  - evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped::sub_000
  - evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped::sub_001
evidence_chunk_ids:
  - evaluation::run-your-judge-on-a-calibration-set-with-positions-swapped::sub_000
rationale:           sub_000 defines position_bias, agreement, and the calibrated flag; sub_001 covers persistence and load-time validation.
subset:              primary
cross_corpus_overlap: null
```

### evaluation slot 17

```
query_id:            manual_041
query:               soup eval irt-subset size and item model options
query_type:          command_detail
relevant_section_ids:
  - evaluation::pick-top-info-30-of-items-5-10x-eval-bill-cut-without-losing-power
  - evaluation::richer-item-models-2pl-learns-per-item-discrimination-3pl-adds-a-guessing-floor
relevant_chunk_ids:
  - evaluation::pick-top-info-30-of-items-5-10x-eval-bill-cut-without-losing-power
  - evaluation::richer-item-models-2pl-learns-per-item-discrimination-3pl-adds-a-guessing-floor
evidence_chunk_ids:
  - evaluation::richer-item-models-2pl-learns-per-item-discrimination-3pl-adds-a-guessing-floor
rationale:           The first chunk shows --size; the second documents --model 1pl/2pl/3pl, Fisher-information ranking, and the size cuts.
subset:              primary
cross_corpus_overlap: null
```


## peft-and-efficiency.md — 65 chunks, 33 sections, target 13 queries

### Sections and chunk IDs

| section_id | heading | level | chunks |
|---|---|---|---|
| `peft-and-efficiency::auto-mixed-precision` | Auto Mixed-Precision | 3 | peft-and-efficiency::auto-mixed-precision |
| `peft-and-efficiency::auto-warmup-schedule` | Auto Warmup Schedule | 3 | peft-and-efficiency::auto-warmup-schedule |
| `peft-and-efficiency::convergence-detector` | Convergence Detector | 3 | peft-and-efficiency::convergence-detector |
| `peft-and-efficiency::curriculum-learning` | Curriculum Learning | 2 | peft-and-efficiency::curriculum-learning |
| `peft-and-efficiency::dense-model-get-a-ship-don-t-ship-perplexity-verdict` | dense model) + get a SHIP/DON'T-SHIP perplexity verdict: | 1 [multi] | peft-and-efficiency::dense-model-get-a-ship-don-t-ship-perplexity-verdict::sub_000, peft-and-efficiency::dense-model-get-a-ship-don-t-ship-perplexity-verdict::sub_001, peft-and-efficiency::dense-model-get-a-ship-don-t-ship-perplexity-verdict::sub_002, peft-and-efficiency::dense-model-get-a-ship-don-t-ship-perplexity-verdict::sub_003 |
| `peft-and-efficiency::depth-pruning-distill-heal-soup-shrink` | Depth Pruning + Distill-Heal (`soup shrink`) | 2 [multi] | peft-and-efficiency::depth-pruning-distill-heal-soup-shrink::sub_000, peft-and-efficiency::depth-pruning-distill-heal-soup-shrink::sub_001 |
| `peft-and-efficiency::dora-weight-decomposed-lora` | DoRA (Weight-Decomposed LoRA) | 2 | peft-and-efficiency::dora-weight-decomposed-lora |
| `peft-and-efficiency::freeze-training` | Freeze Training | 2 | peft-and-efficiency::freeze-training |
| `peft-and-efficiency::galore-memory-efficient-full-parameter-training` | GaLore (Memory-Efficient Full-Parameter Training) | 2 | peft-and-efficiency::galore-memory-efficient-full-parameter-training |
| `peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34` | LISA — Layerwise Importance Sampling (v0.71.34) | 2 [multi] | peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_000, peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_001, peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_002 |
| `peft-and-efficiency::llama-3-1-with-ntk-aware-scaling-out-to-128k` | Llama 3.1 with NTK-aware scaling out to 128k | 1 | peft-and-efficiency::llama-3-1-with-ntk-aware-scaling-out-to-128k |
| `peft-and-efficiency::llama-pro-block-expansion` | LLaMA Pro Block Expansion | 2 | peft-and-efficiency::llama-pro-block-expansion |
| `peft-and-efficiency::long-context-yarn-llama-3-1-ntk-longlora` | Long Context — YaRN, Llama 3.1 NTK, LongLoRA | 2 | peft-and-efficiency::long-context-yarn-llama-3-1-ntk-longlora |
| `peft-and-efficiency::longlora-forward-override` | LongLoRA Forward Override | 2 | peft-and-efficiency::longlora-forward-override |
| `peft-and-efficiency::lora-differentiated-learning-rates` | LoRA+ (Differentiated Learning Rates) | 2 | peft-and-efficiency::lora-differentiated-learning-rates |
| `peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches` | LoRA Quality — PiSSA, ReLoRA, Per-Pattern Rank, Surgical Patches | 2 [multi] | peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_000, peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_001, peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_002, peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_003 |
| `peft-and-efficiency::loss-spike-auto-recovery` | Loss Spike Auto-Recovery | 3 | peft-and-efficiency::loss-spike-auto-recovery |
| `peft-and-efficiency::loss-watchdog` | Loss Watchdog | 2 | peft-and-efficiency::loss-watchdog |
| `peft-and-efficiency::lr-range-finder` | LR Range Finder | 3 | peft-and-efficiency::lr-range-finder |
| `peft-and-efficiency::multipack-ffd-bin-packing-sampler` | Multipack — FFD Bin-Packing Sampler | 2 [multi] | peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_000, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_001, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_002, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_003, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_004, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_005, peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_006 |
| `peft-and-efficiency::neftune-noisy-embeddings-fine-tuning` | NEFTune (Noisy Embeddings Fine-Tuning) | 2 | peft-and-efficiency::neftune-noisy-embeddings-fine-tuning |
| `peft-and-efficiency::optimizer-peft-zoo` | Optimizer & PEFT Zoo | 2 [multi] | peft-and-efficiency::optimizer-peft-zoo::sub_000, peft-and-efficiency::optimizer-peft-zoo::sub_001, peft-and-efficiency::optimizer-peft-zoo::sub_002 |
| `peft-and-efficiency::peft-long-context-training-efficiency` | PEFT, Long Context & Training Efficiency | 1 [multi] | peft-and-efficiency::peft-long-context-training-efficiency::sub_000, peft-and-efficiency::peft-long-context-training-efficiency::sub_001, peft-and-efficiency::peft-long-context-training-efficiency::sub_002, peft-and-efficiency::peft-long-context-training-efficiency::sub_003, peft-and-efficiency::peft-long-context-training-efficiency::sub_004 |
| `peft-and-efficiency::rslora-rank-stabilized-scaling` | rsLoRA (Rank-Stabilized Scaling) | 2 | peft-and-efficiency::rslora-rank-stabilized-scaling |
| `peft-and-efficiency::sample-packing` | Sample Packing | 2 | peft-and-efficiency::sample-packing |
| `peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything` | See the importance table + chosen block without writing anything: | 1 | peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything |
| `peft-and-efficiency::soup-yaml` | soup.yaml | 1 [multi] | peft-and-efficiency::soup-yaml::sub_000, peft-and-efficiency::soup-yaml::sub_001, peft-and-efficiency::soup-yaml::sub_002, peft-and-efficiency::soup-yaml::sub_003 |
| `peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base` | soup.yaml — LLaMA Pro continued-training on a Llama-3.1 base | 1 [multi] | peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_000, peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_001, peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_002 |
| `peft-and-efficiency::training-intelligence-forgetting-checkpoint-quality` | Training Intelligence (Forgetting + Checkpoint Quality) | 2 [multi] | peft-and-efficiency::training-intelligence-forgetting-checkpoint-quality::sub_000, peft-and-efficiency::training-intelligence-forgetting-checkpoint-quality::sub_001 |
| `peft-and-efficiency::training-stability-auto-tuning` | Training Stability & Auto-Tuning | 2 | peft-and-efficiency::training-stability-auto-tuning |
| `peft-and-efficiency::vera-olora-smaller-footprint-peft` | VeRA & OLoRA (Smaller-Footprint PEFT) | 2 | peft-and-efficiency::vera-olora-smaller-footprint-peft |
| `peft-and-efficiency::vram-pressure-advisory` | VRAM Pressure Advisory | 3 | peft-and-efficiency::vram-pressure-advisory |
| `peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b` | What LISA actually costs, measured at 3B and 8B | 3 [multi] | peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_000, peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_001, peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_002, peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_003, peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_004, peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_005 |

### Query slots (fill in below — do not edit the section table)

### peft-and-efficiency slot 1

```
query_id:            manual_042
query:               preview which decoder layers soup shrink will drop
query_type:          command_detail
relevant_section_ids:
  - peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything
  - peft-and-efficiency::depth-pruning-distill-heal-soup-shrink
  - commands::all-commands
relevant_chunk_ids:
  - peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything
  - peft-and-efficiency::depth-pruning-distill-heal-soup-shrink::sub_001
  - commands::all-commands::sub_030
evidence_chunk_ids:
  - peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything
rationale:           The plan-only chunk previews the table and chosen block; sub_001 explains the angular-distance ranking and protected first and last layers. Cross-corpus: the training command table shows shrink with --plan-only and the healing flags.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["commands::all-commands::sub_030"], "note": "the training command table shows shrink with --plan-only and the healing flags"}
```

### peft-and-efficiency slot 2

```
query_id:            manual_043
query:               how does longlora shifted sparse attention work
query_type:          conceptual
relevant_section_ids:
  - peft-and-efficiency::longlora-forward-override
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora
relevant_chunk_ids:
  - peft-and-efficiency::longlora-forward-override
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_001
evidence_chunk_ids:
  - peft-and-efficiency::longlora-forward-override
rationale:           The section explains the S-squared half-head shift, the architecture allowlist, and the FlashAttention v3 rejection. Cross-corpus: the training guide documents use_longlora and the shifted-sparse attention gate.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000", "training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_001"], "note": "the training guide documents use_longlora and the shifted-sparse attention gate"}
```

### peft-and-efficiency slot 3

```
query_id:            manual_044
query:               difference between multipack and packing
query_type:          relationship
relevant_section_ids:
  - peft-and-efficiency::multipack-ffd-bin-packing-sampler
relevant_chunk_ids:
  - peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_000
  - peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_001
evidence_chunk_ids:
  - peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_000
rationale:           sub_000 separates FFD sample selection from attention-mask construction and notes mutual exclusion; sub_001 lists the architecture allowlist.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 4

```
query_id:            manual_045
query:               set up yarn for 4x context extension
query_type:          config_behavior
relevant_section_ids:
  - peft-and-efficiency::soup-yaml
relevant_chunk_ids:
  - peft-and-efficiency::soup-yaml::sub_000
  - peft-and-efficiency::soup-yaml::sub_001
evidence_chunk_ids:
  - peft-and-efficiency::soup-yaml::sub_000
rationale:           sub_000 holds the YaRN YAML; sub_001 gives the 4-8x guidance and which tunables the schema accepts.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 5

```
query_id:            manual_046
query:               Can I add fresh layers to a Llama model and only train those?
query_type:          how_to
relevant_section_ids:
  - peft-and-efficiency::llama-pro-block-expansion
  - peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora
relevant_chunk_ids:
  - peft-and-efficiency::llama-pro-block-expansion
  - peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_000
  - peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_001
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000
  - training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_001
evidence_chunk_ids:
  - peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_000
rationale:           The block-expansion section explains the zero-init append; the YAML chunks set expand_layers and freeze_trainable_layers and describe trainer start. Cross-corpus: the training guide documents expand_layers and freeze_trainable_layers for block expansion.
subset:              overlap
cross_corpus_overlap: {"train_chunk_ids": ["training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000", "training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_001"], "note": "the training guide documents expand_layers and freeze_trainable_layers for block expansion"}
```

### peft-and-efficiency slot 6

```
query_id:            manual_047
query:               different learning rates for q_proj and v_proj
query_type:          config_behavior
relevant_section_ids:
  - peft-and-efficiency::optimizer-peft-zoo
relevant_chunk_ids:
  - peft-and-efficiency::optimizer-peft-zoo::sub_000
evidence_chunk_ids:
  - peft-and-efficiency::optimizer-peft-zoo::sub_000
rationale:           sub_000 shows lr_groups with per-module patterns and the first-match-wins rule.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 7

```
query_id:            manual_048
query:               does pissa init speed up lora convergence
query_type:          conceptual
relevant_section_ids:
  - peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches
relevant_chunk_ids:
  - peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_000
  - peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_001
evidence_chunk_ids:
  - peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_001
rationale:           sub_001 says PiSSA initializes from the base SVD for faster early convergence at the cost of an extra SVD pass.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 8

```
query_id:            manual_049
query:               loraplus_lr_ratio effect on B matrix lr
query_type:          config_behavior
relevant_section_ids:
  - peft-and-efficiency::lora-differentiated-learning-rates
relevant_chunk_ids:
  - peft-and-efficiency::lora-differentiated-learning-rates
evidence_chunk_ids:
  - peft-and-efficiency::lora-differentiated-learning-rates
rationale:           The section defines lr_B as lr times the ratio and shows a 16.0 example.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 9

```
query_id:            manual_050
query:               can dora and vera be enabled together
query_type:          troubleshooting
relevant_section_ids:
  - peft-and-efficiency::vera-olora-smaller-footprint-peft
relevant_chunk_ids:
  - peft-and-efficiency::vera-olora-smaller-footprint-peft
evidence_chunk_ids:
  - peft-and-efficiency::vera-olora-smaller-footprint-peft
rationale:           The section states use_dora, use_vera, and use_olora are mutually exclusive and validated at config load.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 10

```
query_id:            manual_051
query:               neftune_alpha range for chat fine tuning
query_type:          config_behavior
relevant_section_ids:
  - peft-and-efficiency::neftune-noisy-embeddings-fine-tuning
relevant_chunk_ids:
  - peft-and-efficiency::neftune-noisy-embeddings-fine-tuning
evidence_chunk_ids:
  - peft-and-efficiency::neftune-noisy-embeddings-fine-tuning
rationale:           The section gives the 0-50 alpha range, the 5-15 typical band, and the supported tasks.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 11

```
query_id:            manual_052
query:               does lisa actually use less memory than lora
query_type:          conceptual
relevant_section_ids:
  - peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b
relevant_chunk_ids:
  - peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_000
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_001
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_002
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_003
evidence_chunk_ids:
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_001
  - peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_002
rationale:           The intro flags that the memory claim does not hold; the tables show LISA at 52.14 GB vs LoRA at 34.56 GB on 8B and 19.37 vs 15.93 on 3B, and sub_003 explains the embedding and head overhead.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 12

```
query_id:            manual_053
query:               stop training when loss spikes repeatedly
query_type:          config_behavior
relevant_section_ids:
  - peft-and-efficiency::loss-watchdog
relevant_chunk_ids:
  - peft-and-efficiency::loss-watchdog
evidence_chunk_ids:
  - peft-and-efficiency::loss-watchdog
rationale:           The watchdog config enables a loss threshold plus a consecutive-step patience.
subset:              primary
cross_corpus_overlap: null
```

### peft-and-efficiency slot 13

```
query_id:            manual_054
query:               Can GaLore run with quantized weights?
query_type:          troubleshooting
relevant_section_ids:
  - peft-and-efficiency::galore-memory-efficient-full-parameter-training
relevant_chunk_ids:
  - peft-and-efficiency::galore-memory-efficient-full-parameter-training
evidence_chunk_ids:
  - peft-and-efficiency::galore-memory-efficient-full-parameter-training
rationale:           The GaLore section requires quantization: none and the transformers backend.
subset:              primary
cross_corpus_overlap: null
```
