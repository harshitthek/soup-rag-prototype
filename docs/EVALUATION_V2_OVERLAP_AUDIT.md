# Evaluation v2 — Overlap Query Audit

Audit date: 2026-10-31. Owner decisions: approved and applied 2026-11-01.
Auditor: Qoder (AI), at the owner's request. This is not independent human
annotation; the original verdicts below were proposals that the project owner
accepted or rejected.

**Final status:** all 18 original overlap candidates were audited, 15 are
confirmed overlap queries, and 3 were reclassified as `primary` with explicit
owner approval. Zero overlap decisions remain unresolved. The final dataset
contains 39 primary and 15 overlap queries (54 total), query-set fingerprint
`971e1570…`.

## Scope and method

The dataset at audit time (`data/manual_queries.jsonl`, 54 records, original
query-set fingerprint `116bd4c3…`) labeled 18 queries as `overlap`, meaning an
equivalent answer was believed to exist in a training-document chunk. This
audit re-checks every one of those 18 labels against the actual chunk text in
`data/corpus.jsonl`.

For each query the audit inspected:

1. the exact frozen query wording;
2. the held-out source document;
3. the held-out evidence chunk(s) and the relevant section/chunk annotations;
4. every chunk ID listed in `cross_corpus_overlap.train_chunk_ids`;
5. the full text of each referenced training chunk.

A label is accepted only when the referenced training passage contains
information capable of answering substantially the same question. Shared
terminology, a shared command name, or a heading is not sufficient. Some
sections in the corpus are stored as a single chunk whose ID has no
`::sub_` suffix; those IDs are valid chunk IDs.

No query wording or annotation was changed by this audit itself. The original
verdicts were proposals; the owner later approved the three reclassifications
recorded below, and those changes were applied in a separate, explicitly
authorized step. Every other label is unchanged.

## Verdict summary

| Query ID | Query | Held-out evidence | Training evidence | Answer-bearing justification | Audit verdict |
|---|---|---|---|---|---|
| manual_002 | How do I bisect training checkpoints when an eval regresses? | adapters-and-governance · `adapters-and-governance::4-bisect-a-training-history-to-find-the-step-that-broke-an-eval` | commands · `commands::all-commands::sub_054` | Training chunk names `--eval-command` and "binary search over training history", but it is a fragment: it omits the command name (`soup adapters bisect`), the checkpoint-step arguments, and the invocation shown in the held-out chunk. A reader cannot reconstruct the procedure from it. | Questionable → reclassified to primary (owner-approved) |
| manual_004 | what does soup loop automate | adapters-and-governance · `adapters-and-governance::data-flywheel-soup-loop` | commands · `commands::all-commands::sub_020` | Training chunk documents `soup loop init/status/watch` and the pre-wired stages "harvest → train → gate → deploy daemon". The held-out description is finer (production traces, preference pairs, DPO, rollback), but the training passage states what the loop automates. | Confirmed overlap |
| manual_005 | does soup roll back a canary automatically if the eval regresses | adapters-and-governance · `adapters-and-governance::promote-a-canary-at-5-traffic-with-auto-rollback-on-major-verdict` | commands · `commands::all-commands::sub_021` | Training chunk: `soup loop canary <adapter> --traffic 5% promote canary + auto-rollback on major`. This answers the yes/no question and gives the command. | Confirmed overlap |
| manual_007 | compare model answers before and after a knowledge edit | adapters-and-governance · `adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000` | commands · `commands::all-commands::sub_042` | Training chunk: `soup edit diff <before-run> <after-run> --probes p.jsonl [--before-model <m> --after-model <m>] knowledge-injection diff (live before/after generation when both models given)`. Same command, same purpose. | Confirmed overlap |
| manual_008 | build a control vector from positive and negative prompts | adapters-and-governance · `adapters-and-governance::train-a-steering-vector-from-contrastive-positive-negative-prompt-pairs` | commands · `commands::all-commands::sub_043` | Training chunk: `soup steer train --base <m> --method caa|iti|repe --name <id> --pairs <jsonl> fit a caa/iti/repe activation-steering vector from {positive, negative} pairs`. Same procedure and inputs. | Confirmed overlap |
| manual_010 | soup registry diff output | adapters-and-governance · `adapters-and-governance::side-by-side-config-diff-eval-delta-between-two-entries` | commands · `commands::all-commands::sub_022` | Training chunk: `soup registry diff <a> <b> side-by-side config + eval delta`. This is the answer to what the output contains. | Confirmed overlap |
| manual_017 | which soup init templates exist for regulated industries | compliance · `compliance::1-start-from-a-compliance-template` | README · `README::soup-documentation::sub_003` | Training README lists "hipaa / soc2 / eu-ai-act / sr-11-7 `init` templates". The question asks which templates exist; all four names are present, though the training passage gives no per-template descriptions. | Confirmed overlap |
| manual_018 | clean emails and phone numbers out of my training data | compliance · `compliance::2-clean-the-data-before-training` | commands · `commands::all-commands::sub_019` | Training chunk: `soup data pii ... flag rows containing email / phone / ssn / credit-card`. Same command and PII categories; both held-out and training describe flagging, not deletion. | Confirmed overlap |
| manual_020 | what ends up in the generated model card | compliance · `compliance::7-generate-a-documented-model-card` | commands · `commands::all-commands::sub_027` | Training chunk: `soup card <registry-id> -o modelcard.md hf model card from a registry entry: training config, evals, hashes, lineage, artifacts`. Lists the main contents; omits the base model, BOM, and attestation that the held-out section adds. | Confirmed overlap |
| manual_021 | publish a model to huggingface with my own model card | compliance · `compliance::or-when-uploading-to-the-hub-override-the-auto-generated-card` | commands · `commands::all-commands::sub_027` | Training chunk: `soup push --model ./out --repo you/m --card <registry-id> upload that registry-driven card as the readme (hf only)`. Same command and card override. | Confirmed overlap |
| manual_023 | which expectation checks can go in expectations.yaml | compliance · `compliance::writes-github-workflows-soup-gate-yml::sub_000` | data · `data::expectations-suite-great-expectations-for-chat-data` | Training chunk shows the YAML and three supported names (`expect_no_pii`, `expect_token_length_between`, `expect_no_refusal_pattern`). The held-out chunk lists a fourth, `expect_chosen_preferred_over_rejected_by_judge`. The training passage gives an incomplete set for a "which checks" question. | Questionable → reclassified to primary (owner-approved) |
| manual_031 | what does exit code 3 from soup drift-alarm mean | evaluation · `evaluation::drift-alarm-soup-drift-alarm` | commands · `commands::all-commands::sub_046` | Training chunk: `soup drift-alarm --reference <jsonl> --live <jsonl> --threshold 0.2 Rolling-KL drift alarm (exit 3 on drift)`. States the exit-code meaning directly. | Confirmed overlap |
| manual_034 | noise floor flag effect on ship verdict | evaluation · `evaluation::noise-floor-v0-73-2::sub_000` | commands · `commands::all-commands::sub_027` | Training chunk: `--noise-floor n re-run base model n times; per-axis floor = max-min spread; gate at max(threshold, floor); leg-1 measured in every task-mode`. Matches the held-out description of the flag's effect. | Confirmed overlap |
| manual_035 | how do I make a ship verdict replayable in CI | evaluation · `evaluation::closing-the-evidence-loop-v0-71-39::sub_001` | commands · `commands::all-commands::sub_026` | Training chunk: `--emit-evidence ev.json Re-serialise the scores as replayable --evidence input (output-is-input, #312)`, plus `--config soup.yaml` gate defaults and `--push` PR comment. Same replayability mechanism. | Confirmed overlap |
| manual_039 | run a short LoRA probe on several base models before choosing one | evaluation · `evaluation::tunability-probe-soup-tunability` | commands · `commands::all-commands::sub_047` | Training chunk: `soup tunability --list` catalogue, `soup tunability --dataset <jsonl> [--candidates ...] probe candidate bases + pareto frontier report`, `--live ... live per-candidate lora probe`. Same procedure and purpose. | Confirmed overlap |
| manual_042 | preview which decoder layers soup shrink will drop | peft-and-efficiency · `peft-and-efficiency::see-the-importance-table-chosen-block-without-writing-anything` | commands · `commands::all-commands::sub_030` | Training chunk: `--drop-layers N ... soup shrink` and `--tolerance 0.10 --plan-only ... print importance table only`. Confirms the plan-only preview and the layer-drop operation, but does not itself enumerate the chosen layers; the layer list comes from the importance table. | Confirmed overlap |
| manual_043 | how does longlora shifted sparse attention work | peft-and-efficiency · `peft-and-efficiency::longlora-forward-override` | training · `training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000`, `::sub_001` | Training chunks only set `use_longlora: true` with the comment "shifted-sparse attention on the Q/K projections for long-context tuning", plus schema/gating constraints. They do not explain the S² mechanism (which heads shift, by how much, or the forward override). The held-out chunk explains the mechanism. | Not equivalent → reclassified to primary (owner-approved) |
| manual_046 | Can I add fresh layers to a Llama model and only train those? | peft-and-efficiency · `peft-and-efficiency::soup-yaml-llama-pro-continued-training-on-a-llama-3-1-base::sub_000` | training · `training::architecture-knobs-mixture-of-depths-llama-pro-longlora::sub_000`, `::sub_001` | Training chunks show `expand_layers: 4` and `freeze_trainable_layers: 4` with the comment "append zero-initialised identity decoder blocks and train only the new ones", plus attach/gating details. Same configuration and same purpose. | Confirmed overlap |

## Detailed notes

### manual_002

Held-out evidence is the working example:

```
soup adapters bisect \
  ckpt-step-100 ckpt-step-200 ckpt-step-400 ckpt-step-800 \
  --eval-command "soup eval custom --model {ckpt} --tasks eval.jsonl" \
  -o bisect.json
```

The referenced training chunk is a fragment of the generated All Commands
table. It begins mid-entry at `--eval-command` and says "binary search over
training history". It does not name `soup adapters bisect`, does not show the
checkpoint-step arguments, and does not show how to run the search. It shares
the concept and the flag name but cannot answer "how do I bisect checkpoints"
on its own. The provenance of the shared command makes partial overlap
plausible, but the classification is not proven by this chunk.

### manual_004

The training chunk is the `soup loop` command-table entry. It names the loop
subcommands and states the pre-wired stages as "harvest → train → gate →
deploy daemon". The held-out chunk describes the same flywheel in more detail
(production traces → preference pairs → Eval-Gated DPO → canary deploy →
rollback). The training passage answers the question at a coarser grain; the
additional detail does not change what the loop automates.

### manual_023

The training chunk is an executable example:

```
expectations:
  - {name: expect_no_pii}
  - {name: expect_token_length_between, args: {min_tokens: 16, max_tokens: 4096}}
  - {name: expect_no_refusal_pattern}
```

The held-out chunk lists all four supported names, including
`expect_chosen_preferred_over_rejected_by_judge`. A reader using only the
training passage would miss one supported check, so the passage is
answer-bearing but incomplete for a set-membership question.

### manual_043

The training passage contains the switch and a one-line gloss:

```
# LongLoRA S²: shifted-sparse attention on the Q/K projections for long-context tuning.
use_longlora: true
```

The held-out chunk explains the mechanism: a `LongLoRAForwardOverride` context
monkey-patches attention forwards, half the heads are rolled by
`group_size // 2` along the sequence dimension, the Mixtral shell is handled,
restoration is idempotent, and FlashAttention v3 is rejected. The training
passage documents how to enable the feature and when it is rejected, not how
the shifted-sparse attention works. Under the audit rule, a config mention is
not an answer to a "how does it work" question.

### manual_042

The training chunk documents both halves of the operation:

```
--drop-layers N --heal h.jsonl --heal-steps 200 --device cpu  Drop N layers + distill-heal ...
--tolerance 0.10 --plan-only [--attach-to-registry <id>]  Ppl-regression tolerance / print importance table only / registry attach
```

The exact layer identities come from the importance table that `--plan-only`
prints, so the training passage supports the preview mechanism even though it
does not enumerate a specific layer list.

## Final counts

| Final classification | Count | Query IDs |
|---|:---:|---|
| Confirmed overlap | 15 | manual_004, manual_005, manual_007, manual_008, manual_010, manual_017, manual_018, manual_020, manual_021, manual_031, manual_034, manual_035, manual_039, manual_042, manual_046 |
| Reclassified as primary (owner-approved) | 3 | manual_002, manual_023, manual_043 |
| Unresolved overlap decisions | 0 | — |

The three reclassifications cover both original questionable verdicts
(manual_002, manual_023) and the one unsupported verdict (manual_043).

## Owner decisions (resolved 2026-11-01)

The project owner reviewed the audit evidence and approved all three
reclassifications. The decisions and applied dataset changes are:

| Query ID | Original verdict | Owner decision | Why the classification changed |
|---|---|---|---|
| manual_002 | Questionable | Reclassify as primary | The training passage describes a binary search and the `--eval-command` flag but does not provide enough command and invocation detail to answer the question. |
| manual_023 | Questionable | Reclassify as primary | The training passage contains only 3 of the 4 supported expectation checks, so it does not provide the complete answer. |
| manual_043 | Not equivalent | Reclassify as primary | The training passages describe LongLoRA configuration and gating but do not explain the S² shifted sparse attention mechanism. |

For each of the three records, the applied change was:

- `subset` set to `primary`;
- the training-document section IDs removed from `relevant_section_ids`;
- the training chunk IDs removed from `relevant_chunk_ids`;
- `cross_corpus_overlap` set to `null`;
- the rationale rewritten to describe only the held-out evidence.

Query wording, held-out relevant sections and chunks, and all existing
evidence chunk IDs were preserved. The other 51 records were not modified.

## Final dataset state

- 54 unique query IDs: 39 `primary`, 15 `overlap`.
- Query-set fingerprint: `971e157083c31e5e55131a35597dc492d20996a02c7a491543e02d7cbef362b3`.
- Validator: 54 checked, 0 errors, 0 warnings, 1 provisional lexical flag
  (`manual_010`, a known short-chunk false positive on a confirmed overlap
  query).
- All four result files, the comparison report, and the narrative documents
  were regenerated from this dataset. No overlap decision remains unresolved.
