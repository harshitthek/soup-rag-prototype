# Experiment Review — Soup RAG Retrieval Fine-Tuning

Concise review of the Soup embedding fine-tuning experiment in this
repository. Canonical results: `results/comparison.md` (v1 synthetic
benchmark) and `results/v2/comparison.md` (v2 manual benchmark on the
owner-approved query set). Reproduction:
`REPRODUCE.md`. Methodology: `docs/EVALUATION_V2_SPEC.md`.

## Current architecture

1. **Corpus** — 12 Soup CLI Markdown docs (Apache-2.0), vendored with
   sha256 provenance in `data/raw_docs/`; split on ATX headings, sub-split
   to ≤220-token bodies with 28-token overlap; every chunk embeds as
   `"{doc_name}: {heading}\n\n{body}"` (`scripts/prepare_corpus.py`).
2. **Split** — document-level: 8 training docs / 4 held-out docs
   (1,068 chunks: 761 train / 307 test).
3. **Training data** — 1,078 synthetic training queries (deterministic
   templates, `scripts/generate_queries.py`); top-3 hard negatives per query
   with section deduplication, mined with the frozen base model
   (`scripts/mine_hard_negatives.py`) → 3,234 triplets.
4. **Fine-tuning** — Soup `task: embedding`, triplet margin loss (m=0.5),
   LoRA r=16/α=32 on query+value, 3 epochs (2,427 steps), lr 2e-5, seed 42.
   Final adapter: `output_embedding/` (580 KB; base revision pinned in
   `soup_run.json`).
5. **Evaluation v1 (controlled)** — 497 synthetic queries from the held-out
   docs, frozen MiniLM vs the adapter, exact dot-product ranking over all
   1,068 chunks, paired bootstrap uncertainty (exploratory). Reported in
   `results/comparison.md`. Because labels were single-chunk and queries were
   template-generated, v1 numbers describe this controlled setting only.
6. **Evaluation v2 (manual)** — 54 owner-approved queries (drafted by Qoder) with multi-chunk /
   multi-section labels, chunk- and section-level Hit@K / Recall@K / MRR@10,
   four retrievers (frozen MiniLM, Soup adapter, BM25, frozen E5-small-v2),
   doc-stratified paired bootstrap and leave-one-doc-out sensitivity
   (`scripts/retrieval.py`, `scripts/retrievers.py`,
   `scripts/run_retrieval.py`, `scripts/compare_retrievers.py`).

## Key experimental decisions

- **Document-level split** — random chunk splits would leak authorial style
  and shared headings between train and test; the split is frozen.
- **Heading prefix in training and inference** — the model is trained and
  evaluated on the identical passage representation; prefix consistency was
  the single largest measured factor in v1 (see Historical decisions).
- **Triplet margin loss with mined negatives, not InfoNCE** — in-batch
  negatives on a small, topically overlapping corpus risk false negatives;
  triplet loss with section-deduplicated hard negatives avoids that while
  keeping contrastive signal diverse.
- **One adapter, frozen baselines** — the v2 comparison adds BM25 and a
  frozen stronger encoder (E5-small-v2, revision-pinned) rather than more
  tuned variants; BM25 parameters are fixed (no development set exists, and
  tuning against the evaluation labels is prohibited).

## Historical decisions (v1)

Preserved for their durable reasoning; the numbered "bottlenecks" below were
addressed during v1 development and no longer describe open issues.

- **P0 — train/inference prefix discrepancy (fixed).** Early training
  triplets stripped the heading prefix while evaluation embedded it; the
  adapter learned a distribution it was never evaluated on. Fixed by
  prepending the prefix to positives and negatives in `mine_hard_negatives.py`.
- **P1 — repetitive hard negatives (fixed).** Single-negative mining
  re-used boilerplate chunks heavily. Replaced with top-3 section-deduplicated
  negatives (3,234 triplets across 618 distinct negative chunks).
- **P2 — `val_split: 0.1` (fixed).** Internal validation withheld training
  triplets while retrieval quality was already measured on held-out queries;
  set to 0.0.
- **Margin 0.5 → 0.8 (deferred).** On L2-normalized vectors the effective
  cosine-separation threshold is m/2 = 0.25; raising it is plausible but
  unsupported by evidence from this corpus — a higher margin can saturate the
  loss if genuinely similar chunks cannot reach the required gap. Skipped;
  revisit only if loss plateaus with many active triplets.
- **LoRA target expansion, ANCE-style iterative mining (deferred/skipped).**
  Premature for a corpus of this size; the prototype's job is to measure
  whether Soup's native fine-tuning helps, not to maximize the score.
- **InfoNCE (skipped).** False-negative contamination risk with in-batch
  negatives on a small domain corpus; triplet loss with mined negatives
  avoids it.

## Evaluation v2 results (manual benchmark)

54 owner-approved queries (drafted by Qoder, reviewed and frozen by the
owner) over the same 1,068-chunk corpus, with chunk- and section-level
metrics and a paired document-stratified bootstrap (10,000 resamples,
seed 42). Full report: `results/v2/comparison.md`.

| Retriever | Hit@1 | Hit@5 | MRR@10 | Sec Hit@1 | Sec MRR@10 |
|---|:---:|:---:|:---:|:---:|:---:|
| E5-small-v2 | 0.685 | 0.870 | 0.783 | 0.722 | 0.817 |
| MiniLM frozen | 0.593 | 0.870 | 0.702 | 0.648 | 0.735 |
| MiniLM + Soup | 0.556 | 0.815 | 0.669 | 0.593 | 0.701 |
| BM25 | 0.481 | 0.722 | 0.598 | 0.481 | 0.616 |

The adapter does not generalise to natural-language queries: it trails frozen
MiniLM by 3.7 pp Hit@1 and 3.3 pp MRR@10 (intervals include 0), and by
10.7 pp Recall@5 (interval excludes 0). Frozen E5-small-v2 leads every
retriever on every metric.

The subset split is the informative part. On the 36 primary queries, whose
answers exist only in held-out documents, Soup trails frozen MiniLM
(Hit@1 0.528 vs 0.639; MRR@10 0.642 vs 0.724). On the 18 overlap queries,
whose answers also appear in training documents, Soup leads frozen
(Hit@1 0.611 vs 0.500; MRR@10 0.722 vs 0.657) and matches BM25. That pattern
is consistent with the adapter picking up training-document text rather than
a transferable retrieval skill, and the v1 synthetic queries were
near-paraphrases of training-document headings.

Leave-one-document-out keeps the direction: Soup−frozen Hit@1 is ≤ 0 for
every dropped document (range −0.079 to 0.000), and Soup trails E5
throughout. Four held-out documents cannot support population-level claims;
all intervals are exploratory and no p-values are reported.

## Known limitations

- v1's synthetic queries embed their target headings verbatim (measured:
  469/497 queries contain the full heading); v1 results should not be read
  as real-user performance. The v2 manual set tested this: the adapter does
  not beat frozen MiniLM on queries answered only by held-out documents.
- Four held-out documents bound the strength of any conclusion; v2 reports
  uncertainty and leave-one-doc-out sensitivity explicitly and makes no
  population-level claims.
