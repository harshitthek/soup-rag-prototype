# Soup RAG Prototype: Technical Documentation Retrieval

Soup RAG Prototype is a configuration-driven retrieval experimentation framework built around [Soup CLI](https://github.com/MakazhanAlpamys/Soup) technical documentation. It investigates whether parameter-efficient fine-tuning (LoRA), off-the-shelf dense encoders, or hybrid lexical-dense retrieval (Reciprocal Rank Fusion) best solve the retrieval challenges of command-line tools—specifically high lexical overlap, nested flag syntax, and boilerplate distractors.

> [!IMPORTANT]
> **Prototype Status:** This repository is an experimental research prototype evaluating retrieval quality and embedding adaptation strategies on technical Markdown documentation. It is **not** a production-ready feature or an upstream Soup CLI command.

---

## Architecture

The candidate hybrid pipeline combines domain-aware lexical tokenization with a frozen dense encoder using Reciprocal Rank Fusion (RRF):

```
                            ┌─────────────────────────────────────────────────────┐
                            │                    User Query                       │
                            └──────────────────────────┬──────────────────────────┘
                                                       │
                             ┌─────────────────────────┴────────────────────────┐
                             │                                                  │
                             ▼                                                  ▼
                ┌──────────────────────────┐                      ┌──────────────────────────┐
                │ Domain-Aware Tokenizer   │                      │ Prefix Formulation       │
                │ Regex flags/paths/idents │                      │ Prepend "query: "        │
                └────────────┬─────────────┘                      └─────────────┬────────────┘
                             │                                                  │
                             ▼                                                  ▼
                ┌──────────────────────────┐                      ┌──────────────────────────┐
                │ BM25 Okapi Scoring       │                      │ Frozen E5-small-v2       │
                │ k1=1.5, b=0.75           │                      │ Mean Pool + L2 Normalize │
                └────────────┬─────────────┘                      └─────────────┬────────────┘
                             │                                                  │
                             └─────────────────────────┬────────────────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ Reciprocal Rank Fusion    │
                                         │ RRF (k=60, equal weights) │
                                         └─────────────┬─────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │ Top-K Retrieved Passages  │
                                         └───────────────────────────┘
```

---

## Primary Benchmark: Independent Owner-Authored Evaluation (`human_eval_v2`)

The primary benchmark evaluates retrieval systems on **24 queries** authored directly by the project owner without AI assistance, with owner-supplied target sections mechanically mapped to canonical chunk IDs across all 12 files (1,068 chunks) of the Soup documentation corpus (`data/corpus.jsonl`). No independent third-party relevance annotation was conducted, and the benchmark does not represent production telemetry or a sampled developer population.

| System | Architecture / Mode | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Warm Latency | Cold Start |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hybrid RRF** | Improved BM25 + Frozen E5 ($k=60$) | **0.6250** | 0.4923 | 0.5551 | **0.7254** | **0.6250** | **0.7292** | 12.76 ms | 36.0 s |
| **Frozen E5-small** | `intfloat/e5-small-v2` (frozen, 384d) | **0.6250** | 0.4562 | **0.5690** | 0.7101 | **0.6250** | 0.7240 | 10.38 ms | 35.9 s |
| **C-matched-bal** | MiniLM + Exp C balanced LoRA | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 | 6.67 ms | 17.0 s |
| **Improved BM25** | Domain-aware regex ($k_1=1.5, b=0.75$) | **0.6250** | 0.4929 | 0.5150 | 0.6921 | **0.6250** | 0.6921 | **2.37 ms** | **0.11 s** |
| **Frozen MiniLM** | `all-MiniLM-L6-v2` (frozen, 256d) | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 | 6.23 ms | 16.0 s |
| **Fine-Tuned E5** | E5-small + LoRA (matched lr=2e-5) | 0.5417 | **0.5177** | 0.5591 | 0.6413 | 0.5417 | 0.6448 | 11.44 ms | 36.4 s |
| **Original BM25** | Whitespace baseline (`text.lower().split()`, supplemental baseline) | 0.2917 | 0.3153 | 0.3688 | 0.4140 | 0.2917 | 0.4200 | **2.12 ms** | **0.03 s** |

*Steady-state warm latency measured per query on Apple Silicon with preloaded corpus embeddings.*

For full bootstrap uncertainty intervals, ablation analyses, and comparison with the historical 54-query AI-assisted benchmark, see [`RESULTS.md`](RESULTS.md).

---

## Key Experimental Takeaways

1. **Hybrid Retrieval Delivers Highest Observed MRR and Improves Recall@3 over Frozen E5:** Reciprocal Rank Fusion ($k=60$) combining domain-aware BM25 and frozen E5-small achieves the highest observed MRR@10 (**0.7254**) and Sec-MRR@10 (**0.7292**). While Fine-Tuned E5 achieved higher Recall@3 (0.5177) and Improved BM25 reached 0.4929, Hybrid RRF (0.4923) improves Recall@3 specifically over Frozen E5 (0.4562); the paired 95% bootstrap confidence interval excludes zero (+0.0361, 95% bootstrap CI `[+0.0069, +0.0653]`). The paired 95% bootstrap confidence interval for the MRR@10 difference includes zero (`[-0.0687, +0.0996]`).
2. **Fine-Tuning E5 Observed Lower Ranking Point Estimates:** Parameter-efficient fine-tuning on synthetic domain triplets observed lower ranking performance (MRR@10 dropped from **0.7101 to 0.6413**; Hit@1 dropped from **0.6250 to 0.5417**), while Recall@3 was slightly higher (**0.5177** vs **0.4562**). The paired 95% bootstrap confidence interval includes zero for every evaluated metric. Directionally, frozen E5-small remains the more reliable out-of-the-box choice.
3. **Domain-Aware BM25 Substantially Outperforms Whitespace Baseline:** Moving from whitespace tokenization to domain-aware parsing increased MRR@10 from **0.4140 to 0.6921** (+0.2781, 95% bootstrap CI `[+0.1685, +0.3912]`) and Hit@1 from **0.2917 to 0.6250** (+0.3333, 95% bootstrap CI `[+0.2083, +0.4583]`), matching Frozen E5 Hit@1 at sub-2.5 ms latency. Paired 95% bootstrap confidence intervals strictly exclude zero across all metrics.
4. **Benchmark Scope and Design Distinctions:** Both benchmarks evaluated candidate retrieval over the complete 1,068-chunk canonical corpus. Differences reflect benchmark design, query formulation style, query set size (54 vs 24), and relevance target distribution (restricted to 4 held-out documents vs spanning all 12 corpus documents), rather than query authorship alone. Independent evaluation on owner-authored queries provides an essential empirical check against overfitting to automated query distributions.

---

## Quickstart & Reproduction

### Installation

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Reproduce Independent Human Benchmark (v2)

Execute the 7-system evaluation on the frozen 24 human queries:

```bash
python scripts/evaluate_human_eval_v2.py
```

Outputs are written to `results/human_eval_v2/` and `results/HUMAN_EVAL_V2_REPORT.md`.

### Run Verification Test Suite

```bash
pytest tests/ -v
```

---

## Documentation Links

- **[`RESULTS.md`](RESULTS.md)**: Authoritative empirical findings, bootstrap confidence intervals, latency breakdowns, and research answers.
- **[`docs/RESEARCH_INTEGRITY.md`](docs/RESEARCH_INTEGRITY.md)**: Provenance disclosures, unassisted human author verification, withdrawal of 12-query draft, and benchmark separation.
- **[`docs/SOUP_INTEGRATION_PROPOSAL.md`](docs/SOUP_INTEGRATION_PROPOSAL.md)**: Non-invasive proposal for integrating hybrid retrieval and domain-aware tokenization into Soup CLI (`soup docs search`).
- **[`data/human_eval/manifest_v2.json`](data/human_eval/manifest_v2.json)**: Frozen benchmark manifest with dataset hashes and system configurations.
