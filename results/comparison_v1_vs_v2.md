# Retrieval Quality: Before vs After Embedding Fine-Tuning

**Baseline:** Frozen `sentence-transformers/all-MiniLM-L6-v2`  
**Candidate:** Fine-tuned (adapter: `output_embedding_v2`)  
**Corpus:** 1068 chunks from 12 docs  
**Queries:** 497 held-out test queries  

## Aggregate Metrics

| Metric | Baseline | Candidate | Delta | 95% CI | p-value | Significant |
|--------|----------|-----------|-------|--------|---------|-------------|
| recall@1 | 0.6700 | 0.7565 | +0.0865 | [+0.0483, +0.1247] | 0.0000 | Yes |
| recall@3 | 0.8551 | 0.9336 | +0.0785 | [+0.0483, +0.1087] | 0.0000 | Yes |
| recall@5 | 0.9034 | 0.9718 | +0.0684 | [+0.0423, +0.0946] | 0.0000 | Yes |
| mrr@10 | 0.7706 | 0.8477 | +0.0772 | [+0.0518, +0.1029] | 0.0000 | Yes |

> Bootstrap: 10000 resamples, seed=42, paired query-level. With n=497 queries from 4 docs, treat these intervals as exploratory.

## Per-Document Breakdown

| Document | Queries | B Recall@1 | C Recall@1 | B MRR@10 | C MRR@10 |
|----------|---------|------------|------------|----------|----------|
| adapters-and-governance | 188 | 0.7287 | 0.7766 | 0.8084 | 0.8677 |
| compliance | 26 | 0.6923 | 0.8462 | 0.8196 | 0.9231 |
| evaluation | 193 | 0.6995 | 0.7720 | 0.7951 | 0.8542 |
| peft-and-efficiency | 90 | 0.4778 | 0.6556 | 0.6247 | 0.7701 |

## Retrieval Regressions (47 queries)

| Query | Baseline Rank | Candidate Rank | B Top-1 | C Top-1 |
|-------|---------------|----------------|---------|---------|
| How do you use noise floor (v0.73.2) in Soup CLI?... | 2 | 7 | `evaluation::noise-floor-v0-73-2::sub_005` | `evaluation::noise-floor-v0-73-2::sub_005` |
| How do you configure multipack — ffd bin-packing sampler in ... | 1 | 6 | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_000` | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_006` |
| What does BatchSamplerShard do in the context of multipack —... | 2 | 6 | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_002` | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_006` |
| What does soup advise do in the context of evaluation, diagn... | 1 | 4 | `evaluation::evaluation-diagnostics-probes::sub_000` | `evaluation::evaluation-diagnostics-probes::sub_004` |
| How do you configure lora quality — pissa, relora, per-patte... | 1 | 4 | `peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_000` | `peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_001` |
| What does  soup airgap - bundle  do in the context of adapte... | 1 | 3 | `adapters-and-governance::adapters-registry-governance::sub_004` | `adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_001` |
| What does Conv1D do in the context of diff what the model sa... | 3 | 5 | `adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000` | `adapters-and-governance::diff-what-the-model-says-before-vs-after-the-edit-live-generation::sub_000` |
| What does $CWD do in the context of list all snapshotted bra... | 1 | 3 | `adapters-and-governance::list-all-snapshotted-branches::sub_001` | `adapters-and-governance::list-all-snapshotted-branches::sub_002` |
| What is evaluation, diagnostics & probes and how does it wor... | 2 | 4 | `evaluation::evaluation-diagnostics-probes::sub_004` | `evaluation::evaluation-diagnostics-probes::sub_004` |
| What does FileNotFoundError do in the context of eval-gated ... | 1 | 3 | `evaluation::eval-gated-training::sub_002` | `evaluation::eval-gated-training::sub_001` |

