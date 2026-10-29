# Retrieval Quality: Before vs After Embedding Fine-Tuning

**Baseline:** Frozen `sentence-transformers/all-MiniLM-L6-v2`  
**Candidate:** Fine-tuned (adapter: `output_embedding`)  
**Corpus:** 1068 chunks from 12 docs  
**Queries:** 497 synthetic test queries (template-generated from held-out docs)  

## Aggregate Metrics

| Metric | Baseline | Candidate | Delta | 95% Bootstrap CI |
|--------|----------|-----------|-------|------------------|
| recall@1 | 0.5453 | 0.7565 | +0.2113 | [+0.1650, +0.2555] |
| recall@3 | 0.7606 | 0.9336 | +0.1730 | [+0.1368, +0.2113] |
| recall@5 | 0.8209 | 0.9718 | +0.1509 | [+0.1167, +0.1851] |
| mrr@10 | 0.6615 | 0.8477 | +0.1862 | [+0.1534, +0.2195] |

> Bootstrap: 10000 resamples, seed=42, paired query-level percentile interval. With n=497 queries from 4 held-out docs, treat these intervals as exploratory uncertainty estimates on the paired difference.

## Per-Document Breakdown

| Document | Queries | B Recall@1 | C Recall@1 | B MRR@10 | C MRR@10 |
|----------|---------|------------|------------|----------|----------|
| adapters-and-governance | 188 | 0.5851 | 0.7766 | 0.6921 | 0.8677 |
| compliance | 26 | 0.5385 | 0.8462 | 0.6859 | 0.9231 |
| evaluation | 193 | 0.5959 | 0.7720 | 0.7101 | 0.8542 |
| peft-and-efficiency | 90 | 0.3556 | 0.6556 | 0.4864 | 0.7701 |

## Retrieval Regressions (39 queries)

| Query | Baseline Rank | Candidate Rank | B Top-1 | C Top-1 |
|-------|---------------|----------------|---------|---------|
| What does  mini _ arithmetic  do in the context of offline: ... | 2 | 7 | `evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_001` | `evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_003` |
| How do you configure multipack — ffd bin-packing sampler in ... | 1 | 6 | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_000` | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_006` |
| How do you use noise floor (v0.73.2) in Soup CLI?... | 4 | 7 | `training::install-audio-support` | `evaluation::noise-floor-v0-73-2::sub_005` |
| What does BatchSamplerShard do in the context of multipack —... | 3 | 6 | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_002` | `peft-and-efficiency::multipack-ffd-bin-packing-sampler::sub_006` |
| How do you configure lora quality — pissa, relora, per-patte... | 1 | 4 | `peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_000` | `peft-and-efficiency::lora-quality-pissa-relora-per-pattern-rank-surgical-patches::sub_001` |
| What does  soup airgap - bundle  do in the context of adapte... | 1 | 3 | `adapters-and-governance::adapters-registry-governance::sub_004` | `adapters-and-governance::airgap-bundle-soup-airgap-bundle::sub_001` |
| What is evaluation, diagnostics & probes and how does it wor... | 2 | 4 | `evaluation::evaluation-diagnostics-probes::sub_003` | `evaluation::evaluation-diagnostics-probes::sub_004` |
| How do you configure evaluation, diagnostics & probes in Sou... | 1 | 3 | `evaluation::evaluation-diagnostics-probes::sub_003` | `evaluation::evaluation-diagnostics-probes::sub_004` |
| What does FileNotFoundError do in the context of eval-gated ... | 1 | 3 | `evaluation::eval-gated-training::sub_002` | `evaluation::eval-gated-training::sub_001` |
| What does --diagnose-gate do in the context of attach the re... | 1 | 3 | `evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_003` | `evaluation::attach-the-report-to-a-model-registry-entry-as-a-first-class-artifact::sub_002` |

