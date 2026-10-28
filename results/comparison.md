# Retrieval Quality: Before vs After Embedding Fine-Tuning

**Baseline:** Frozen `sentence-transformers/all-MiniLM-L6-v2`  
**Candidate:** Fine-tuned (adapter: `../output_embedding`)  
**Corpus:** 1068 chunks from 12 docs  
**Queries:** 497 held-out test queries  

## Aggregate Metrics

| Metric | Baseline | Candidate | Delta | 95% CI | p-value | Significant |
|--------|----------|-----------|-------|--------|---------|-------------|
| recall@1 | 0.5453 | 0.6700 | +0.1247 | [+0.0926, +0.1590] | 0.0000 | Yes |
| recall@3 | 0.7606 | 0.8551 | +0.0946 | [+0.0684, +0.1227] | 0.0000 | Yes |
| recall@5 | 0.8209 | 0.9034 | +0.0825 | [+0.0584, +0.1066] | 0.0000 | Yes |
| mrr@10 | 0.6615 | 0.7706 | +0.1090 | [+0.0878, +0.1317] | 0.0000 | Yes |

> Bootstrap: 10000 resamples, seed=42, paired query-level. With n=497 queries from 4 docs, treat these intervals as exploratory.

## Per-Document Breakdown

| Document | Queries | B Recall@1 | C Recall@1 | B MRR@10 | C MRR@10 |
|----------|---------|------------|------------|----------|----------|
| adapters-and-governance | 188 | 0.5851 | 0.7287 | 0.6921 | 0.8084 |
| compliance | 26 | 0.5385 | 0.6923 | 0.6859 | 0.8196 |
| evaluation | 193 | 0.5959 | 0.6995 | 0.7101 | 0.7951 |
| peft-and-efficiency | 90 | 0.3556 | 0.4778 | 0.4864 | 0.6247 |

## Retrieval Regressions (16 queries)

| Query | Baseline Rank | Candidate Rank | B Top-1 | C Top-1 |
|-------|---------------|----------------|---------|---------|
| What does  soup attest emit  do in the context of adapters, ... | 9 | >10 | `adapters-and-governance::provenance-attestations-soup-attest-emit::sub_001` | `adapters-and-governance::provenance-attestations-soup-attest-emit::sub_001` |
| What does 

 do in the context of 2. attach it to the bom:?... | 9 | >10 | `adapters-and-governance::2-attach-it-to-the-bom::sub_000` | `adapters-and-governance::2-attach-it-to-the-bom::sub_000` |
| What does  soup adapters { merge, pr, bisect }  do in the co... | 10 | >10 | `adapters-and-governance::adapters-registry-governance::sub_000` | `adapters-and-governance::adapters-registry-governance::sub_000` |
| What does  mini _ arithmetic  do in the context of offline: ... | 2 | 5 | `evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_001` | `evaluation::offline-decide-from-pre-computed-scores-persist-the-verdict-json::sub_001` |
| How do you configure list all snapshotted branches in Soup?... | 4 | 5 | `backends-and-ops::standalone-sweep-config` | `adapters-and-governance::branches-node-under-the-entry-in-soup-history` |
| How do you use namespace pinning (anti-ai-jacking) in Soup C... | 1 | 2 | `adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_000` | `adapters-and-governance::namespace-pinning-anti-ai-jacking::sub_001` |
| How do you configure 4. register the run, then emit bom + at... | 1 | 2 | `compliance::4-register-the-run-then-emit-bom-attestation::sub_000` | `compliance::4-register-the-run-then-emit-bom-attestation::sub_001` |
| How do you configure evaluation, diagnostics & probes in Sou... | 1 | 2 | `evaluation::evaluation-diagnostics-probes::sub_003` | `evaluation::evaluation-diagnostics-probes::sub_000` |
| What does , off-diagonal).

 do in the context of 6. sae aut... | 3 | 4 | `evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_003` | `evaluation::6-sae-auto-download-capture-pipeline-v0-71-8::sub_003` |
| What is show prior verdicts (newest first), with per-choice ... | 1 | 2 | `evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_001` | `evaluation::show-prior-verdicts-newest-first-with-per-choice-counts::sub_000` |

