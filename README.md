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

## Primary Benchmark: Independent Human Evaluation (`human_eval_v2`)

The primary benchmark evaluates retrieval systems on **24 authentic queries** authored by the project owner without AI assistance, evaluated across all 12 Soup documentation files (1,068 canonical chunks in `data/corpus.jsonl`).

| System | Architecture / Mode | Hit@1 | Recall@3 | Recall@5 | MRR@10 | Sec-Hit@1 | Sec-MRR@10 | Warm Latency | Cold Start |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hybrid RRF** | Improved BM25 + Frozen E5 ($k=60$) | **0.6250** | **0.4923** | **0.5551** | **0.7254** | **0.6250** | **0.7292** | 11.75 ms | 30.4 s |
| **Frozen E5-small** | `intfloat/e5-small-v2` (frozen, 384d) | **0.6250** | 0.4562 | **0.5690** | 0.7101 | **0.6250** | 0.7240 | 9.41 ms | 30.3 s |
| **C-matched-bal** | MiniLM + Exp C balanced LoRA | 0.5833 | 0.5103 | 0.5196 | 0.7004 | 0.5833 | 0.7073 | 6.06 ms | 14.4 s |
| **Improved BM25** | Domain-aware regex ($k_1=1.5, b=0.75$) | **0.6250** | 0.4929 | 0.5150 | 0.6921 | **0.6250** | 0.6921 | **2.31 ms** | **0.11 s** |
| **Frozen MiniLM** | `all-MiniLM-L6-v2` (frozen, 256d) | 0.5417 | 0.4929 | 0.5497 | 0.6587 | 0.5417 | 0.6622 | 5.26 ms | 13.6 s |
| **Fine-Tuned E5** | E5-small + LoRA (matched lr=2e-5) | 0.5417 | **0.5177** | 0.5591 | 0.6413 | 0.5417 | 0.6448 | 11.14 ms | 28.4 s |

*Steady-state warm latency measured per query on Apple Silicon with preloaded corpus embeddings.*

For full bootstrap uncertainty intervals, ablation analyses, and comparison with the historical 54-query AI-assisted benchmark, see [`RESULTS.md`](RESULTS.md).

---

## Key Experimental Takeaways

1. **Hybrid Retrieval Delivers Highest Overall Effectiveness:** Reciprocal Rank Fusion ($k=60$) combining domain-aware BM25 and frozen E5-small achieves the top MRR@10 (**0.7254**), Sec-MRR@10 (**0.7292**), and a statistically positive improvement on Recall@3 (+0.0361, 95% CI `[+0.0069, +0.0653]`).
2. **Fine-Tuning E5 Induces Negative Transfer on Human Queries:** Parameter-efficient fine-tuning on synthetic domain triplets degraded E5-small retrieval on authentic developer queries (MRR@10 dropped from **0.7101 to 0.6413**; Hit@1 dropped from **0.6250 to 0.5417**). Off-the-shelf frozen E5-small remains strictly superior.
3. **Lexical BM25 is Highly Competitive on Real Developer Queries:** Human queries rely heavily on exact technical identifiers, flags, and error tokens (`--track-energy`, `check-safetensors`, `bitnet_1.58`, `onebitllms`, `LISA`). Improved BM25 matches dense Hit@1 (**0.6250**) at **2.31 ms** query latency and **0.11 s** cold start.
4. **Synthetic Benchmarks Overstate Adapter Gains:** Synthetic queries favor dense models trained on similar distributions while penalizing lexical search. Independent, unassisted human queries are essential to detect negative transfer and accurately evaluate retrieval utility.

---

## Quickstart & Reproduction

### Installation

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Reproduce Independent Human Benchmark (v2)

Execute the 6-system evaluation on the frozen 24 human queries:

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
