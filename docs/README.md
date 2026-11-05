# Soup RAG Prototype — Technical Documentation Index

Welcome to the technical documentation for the `soup-rag-prototype`. This directory contains detailed specifications, progress records, coverage worksheets, pre-training audits, and architectural reviews.

> [!TIP]
> **Quick Summary:** For high-level project goals, pipeline architecture, and headline Phase 3 results, see the repository [Root README](../README.md). For step-by-step reproduction and verification commands, see [`REPRODUCE.md`](../REPRODUCE.md).

---

## 1. Documentation Map & Directory Layout

```
docs/
├── README.md                          # This documentation index & executive summaries
├── RESEARCH_INTEGRITY.md              # AI disclosure, claim corrections, & human eval protocol
├── REVIEW.md                          # Architectural review & key experimental decisions
├── EVALUATION_V2_SPEC.md              # Canonical specification for the 54-query manual benchmark
├── EVALUATION_V2_OVERLAP_AUDIT.md     # Audit of the 18 candidate overlap queries (15 confirmed, 3 primary)
├── evaluation/
│   └── EVALUATION_V2_COVERAGE.md      # Detailed manual query authoring worksheet & chunk allocations
├── progress/
│   └── EVALUATION_V2_PROGRESS.md      # Implementation record and commit diary for Evaluation v2 milestone
├── phase0/
│   ├── PHASE_0_AUDIT.md               # Pre-training corpus audit & leak-free split validation
│   ├── PHASE_0_RECOMMENDATION.md      # Architectural recommendations for training split & candidate data
│   └── PHASE_0_CORPUS_INVENTORY.csv   # Catalog of 23 candidate expansion documents
└── reports/
    └── PHASE_1_DELIVERY_REPORT.md     # Historical Phase 1 delivery report (synthetic benchmark)
```

---

## 2. Summary of Key Documentation Areas

### 2.1 Evaluation Benchmark & Query Coverage

The evaluation benchmark evaluates dense and lexical retrieval over **54 owner-approved natural language queries** targeting technical developer workflows across the four held-out evaluation documents.

| Document Name | File Chunks | Sections | Target Queries | Primary Queries | Overlap Queries |
|---|:---:|:---:|:---:|:---:|:---:|
| `adapters-and-governance.md` | 106 | 79 | 16 | 10 | 6 |
| `compliance.md` | 16 | 13 | 8 | 5 | 3 |
| `evaluation.md` | 120 | 82 | 17 | 13 | 4 |
| `peft-and-efficiency.md` | 65 | 33 | 13 | 11 | 2 |
| **Total Benchmark** | **307** | **207** | **54** | **39** | **15** |

- **Specification:** [`EVALUATION_V2_SPEC.md`](EVALUATION_V2_SPEC.md) establishes the methodology, metrics (Hit@K, Recall@K, MRR@10, Section Hit@K), and bootstrap evaluation rules.
- **Overlap Audit:** [`EVALUATION_V2_OVERLAP_AUDIT.md`](EVALUATION_V2_OVERLAP_AUDIT.md) documents the audit of 18 candidate overlap queries against training documents (15 confirmed as overlap, 3 reclassified as primary with owner approval).
- **Full Coverage Worksheet:** [`evaluation/EVALUATION_V2_COVERAGE.md`](evaluation/EVALUATION_V2_COVERAGE.md) contains the complete per-section chunk mappings, query authoring rules, and detailed relevance slot definitions.

---

### 2.2 Implementation Progress & Milestone Tracking

Project execution evolved across multiple structured phases:

| Phase | Focus Area | Status | Key Artifacts |
|:---|:---|:---:|:---|
| **Phase 0** | Corpus Audit & Separation | Complete | [`phase0/PHASE_0_AUDIT.md`](phase0/PHASE_0_AUDIT.md), [`phase0/PHASE_0_RECOMMENDATION.md`](phase0/PHASE_0_RECOMMENDATION.md) |
| **Phase 1.0–1.4** | Benchmark Authoring & Setup | Complete | [`EVALUATION_V2_SPEC.md`](EVALUATION_V2_SPEC.md), [`progress/EVALUATION_V2_PROGRESS.md`](progress/EVALUATION_V2_PROGRESS.md) |
| **Phase 1.5–1.10** | Diverse Training Data & Locks | Complete | `results/PHASE_1_5_QUERY_QUALITY_REPORT.md`, `results/PHASE_1_10_FINAL_EXPERIMENT_LOCK.md` |
| **Phase 2.0–2.1** | Adapter Retraining Matrix | Complete | `results/PHASE_2_TRAINING_EXECUTION_REPORT.md`, `results/PHASE_2_1_ARTIFACT_VERIFICATION_REPORT.md` |
| **Phase 3.0–3.1** | 9-Retriever Benchmark & Audit | Complete | `results/PHASE_3_BENCHMARK_EVALUATION_REPORT.md`, `results/PHASE_3_1_INTEGRITY_AUDIT.md` |

- **Detailed Progress Diary:** [`progress/EVALUATION_V2_PROGRESS.md`](progress/EVALUATION_V2_PROGRESS.md) preserves the historical day-by-day implementation notes, review resolutions, and rehearsal logs for the initial Evaluation v2 milestone.

---

### 2.3 Pre-Training Audits & Candidate Documents (Phase 0)

Before adapter fine-tuning was initiated, Phase 0 audited the 12 core documentation files and 23 expansion candidates:
- **Corpus Audit:** [`phase0/PHASE_0_AUDIT.md`](phase0/PHASE_0_AUDIT.md) verified the 8/4 document-level split, ensuring that test documents (`adapters-and-governance`, `compliance`, `evaluation`, `peft-and-efficiency`) share no headings or content with training documents.
- **Recommendations:** [`phase0/PHASE_0_RECOMMENDATION.md`](phase0/PHASE_0_RECOMMENDATION.md) specified guidelines for candidate document inclusion and data governance.
- **Corpus Inventory:** [`phase0/PHASE_0_CORPUS_INVENTORY.csv`](phase0/PHASE_0_CORPUS_INVENTORY.csv) catalogs all 23 candidate expansion documents.

---

### 2.4 Research Integrity, Reviews & Architecture

- **Research Integrity Protocol:** [`RESEARCH_INTEGRITY.md`](RESEARCH_INTEGRITY.md) provides full AI assistance disclosures, dataset provenance, corrected experimental claims, and the protocol for the independent human-authored query evaluation check.
- **Architecture Review:** [`REVIEW.md`](REVIEW.md) details durable design choices: document-level separation, consistent heading prefixing (`"{doc_name}: {heading}\n\n{body}"`), triplet margin loss with section-deduplicated negatives, matched-budget training matrices, and key findings.
- **Historical Delivery Report:** [`reports/PHASE_1_DELIVERY_REPORT.md`](reports/PHASE_1_DELIVERY_REPORT.md) preserves the Phase 1 delivery report evaluated on 497 synthetic queries.

---

## 3. Authoritative Experimental Results

For verified benchmark scores, bootstrap confidence intervals, and research findings:
- **Authoritative Experimental Results:** [`../RESULTS.md`](../RESULTS.md)
- **Independent Human Benchmark Report (v2):** [`../results/HUMAN_EVAL_V2_REPORT.md`](../results/HUMAN_EVAL_V2_REPORT.md)
- **Research Integrity, Provenance & Disclosures:** [`RESEARCH_INTEGRITY.md`](RESEARCH_INTEGRITY.md)
- **Upstream Soup Integration Proposal:** [`SOUP_INTEGRATION_PROPOSAL.md`](SOUP_INTEGRATION_PROPOSAL.md)

> [!NOTE]
> Detailed historical interim phase reports (Phase 1 through Phase 3) and large raw JSON evaluation logs are fully preserved on git branch `archive/research-history`.
