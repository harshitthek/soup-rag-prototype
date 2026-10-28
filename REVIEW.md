# RAG Prototype v2 — Review Assessment

Independent evaluation of the external architectural review against the actual codebase.

---

## Verdict: 1 confirmed bug, 2 useful tuning levers, 3 items to skip

The review identifies six "bottlenecks." After verifying each claim against the actual code and Soup's trainer implementation, here is what holds up and what does not.

---

## Confirmed Bug (Fix Immediately)

### Bottleneck 1: Train–Inference Heading Prefix Discrepancy

**Verdict: Real bug. Must fix.**

The review correctly identified a distribution mismatch between training and inference:

| Stage | What the model sees |
|---|---|
| Hard negative mining | `"{heading_prefix}\n\n{text}"` (line 44 of `mine_hard_negatives.py`) |
| Evaluation (baseline & candidate) | `"{heading_prefix}\n\n{text}"` (line 49 of `evaluate_retrieval.py`) |
| **Training triplets (positive/negative)** | **`"{text}"` only** (lines 77, 99 of `mine_hard_negatives.py`) |

The miner used prefixed text to compute similarity scores, then **stripped the prefix** when writing the actual triplet fields. The LoRA adapter spent 729 steps learning representations of raw body text, then was evaluated on prefixed text it never trained on.

This is a genuine data preparation bug. The fix is mechanical: prepend `heading_prefix` to both positive and negative fields when writing triplets.

> [!IMPORTANT]
> This single fix is likely responsible for a large share of the achievable improvement. The review's ablation showed the heading prefix accounts for over 50% of total retrieval signal (Recall@1 jumps from 0.2193 to 0.5453 just from adding the prefix). Teaching the adapter to work *with* this prefix rather than ignoring it is the highest-value change.

---

## Useful Tuning Levers (Worth Implementing)

### Bottleneck 2: Repetitive Hard Negatives

**Verdict: Real observation. Worth fixing.**

Verified against the actual data: 406 unique negatives across 1,078 triplets. The single most repeated negative ("Global flag on the root `soup` command...") appears 25 times. Mining top-3 negatives per query with section-deduplication would produce ~3,234 triplets with more diverse contrastive signal.

The concern is real: training against the same boilerplate chunk 25 times teaches the model to distinguish "documentation content" from "CLI help text" rather than discriminating between competing technical sections.

### Bottleneck 5: `val_split: 0.1` Discards Training Data

**Verdict: Valid point. Easy fix.**

With `val_split: 0.1`, Soup's trainer withholds 107 of the 1,078 triplets for internal validation loss tracking. Since retrieval quality is already evaluated separately on the 497 held-out queries, this internal validation split is redundant. Setting `val_split: 0.0` recovers all 1,078 triplets (or ~3,234 after multi-negative mining) for training.

---

## Skip or Defer

### Bottleneck 3: Margin Calibration ($m = 0.5 \to 0.8$)

**Verdict: Math is correct but the prescription is speculative.**

The derivation is mechanically sound: on L2-normalized vectors, `pos_dist - neg_dist + m` becomes `2(cos(a,n) - cos(a,p)) + m`, so the effective cosine separation threshold is $m/2 = 0.25$. Raising $m$ to 0.8 would push this to 0.40.

However, the claim that 0.25 "truncates optimization prematurely" is unsupported by evidence from this specific corpus. A higher margin also risks the opposite problem: if genuinely similar chunks cannot achieve a 0.40 cosine gap, the loss stays saturated and gradients become noisy. Without running an ablation, this is a guess dressed up in math.

**Decision:** Skip for now. After fixing the prefix bug and adding multi-negative mining, revisit only if the training loss plateaus above zero with a high fraction of active triplets.

### Bottleneck 4: Restricted LoRA Target Modules

**Verdict: Reasonable suggestion but premature optimization.**

The current adapter targets `query` and `value` (PEFT's default `auto` for BERT-family). Expanding to `key` and `dense` would increase trainable params from 147K to ~420K. On a 22.86M parameter model, going from 0.65% to 1.8% trainable is safe from a capacity perspective.

However, on a 1,078-triplet (or even 3,234-triplet) dataset, wider adapters risk overfitting to the training queries rather than learning generalizable representations. The prefix fix and multi-negative mining should be evaluated first. If there is still headroom, then expanding targets makes sense.

**Decision:** Defer. Try after v2 results are in.

### Bottleneck 6: Two-Stage Iterative Mining (ANCE)

**Verdict: Correct in principle but unnecessary complexity for this prototype.**

ANCE-style iterative hard negative mining is a real technique used in production retrieval systems. But on a 1,068-chunk corpus with 1,078 queries, the diminishing returns are steep. The prototype's job is to demonstrate whether Soup's embedding fine-tuning improves retrieval — not to squeeze out the last percentage point.

**Decision:** Skip entirely. If Alpamys wants to see whether iterative mining matters, that is a separate experiment.

### Lever 4: Switch to InfoNCE

**Verdict: The review contradicts itself.**

The original plan deliberately chose triplet loss over InfoNCE after the red-team critique identified false negative contamination risk with in-batch negatives. With batch size 16, any in-batch negative that happens to answer the anchor query becomes a false negative, corrupting the gradient. On a small domain-specific corpus with overlapping topics, this risk is concrete.

The review proposes InfoNCE without addressing this. Skip.

---

## Projected Impact Table

The review's projected metrics table (claiming Recall@1 up to 0.7650) has no empirical basis — those are fabricated projections, not measurements. Ignore the table entirely.

What is defensible:
- **Prefix fix alone** should produce a meaningful improvement because the adapter will finally train on the same input distribution it is evaluated on.
- **Multi-negative mining** should help because the adapter will see diverse distractors instead of the same boilerplate.
- **val_split: 0.0** recovers training data at zero cost.

The actual magnitude is unknown until measured.

---

## Recommended v2 Changes

| Priority | Change | File(s) | Risk |
|---|---|---|---|
| **P0** | Prepend `heading_prefix` to positive and negative in triplets | `mine_hard_negatives.py` L77, L99 | Zero — fixes a bug |
| **P1** | Mine top-3 negatives per query with section deduplication | `mine_hard_negatives.py` L86-L106 | Zero — more data, same format |
| **P2** | Set `val_split: 0.0` | `config/embedding.yaml` L8 | Zero — recovers training data |
| **Defer** | Expand LoRA target modules, raise margin, ANCE | — | Evaluate after P0–P2 |
| **Skip** | InfoNCE switch | — | False negative risk on small corpus |

---

## What NOT to Do

1. Do not fabricate projected metric tables. Run the experiment and measure.
2. Do not change the evaluation protocol, corpus, queries, or split.
3. Do not increase complexity (ANCE, InfoNCE) before measuring the effect of the bug fix alone.
4. Do not retrain on this machine right now — CPU training took 28 minutes for 729 steps; with 3x triplets it will take ~84 minutes.
