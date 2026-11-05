"""Deep research audit of BM25 tokenizer expansion, vocabulary growth,
token frequency distribution, OOV query terms, and identifier fragmentation.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from retrievers import tokenize_domain_aware, tokenize_whitespace

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


def audit_tokenizer() -> dict[str, Any]:
    corpus = [
        json.loads(line)
        for line in (DATA_DIR / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    queries = [
        json.loads(line)
        for line in (DATA_DIR / "manual_queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    corpus_texts = [
        f"{c['doc_name']}: {c['heading']}\n\n{c['text']}" for c in corpus
    ]
    query_texts = [q["query"] for q in queries]

    # Tokenize corpus
    c_tokens_ws = [tokenize_whitespace(t) for t in corpus_texts]
    c_tokens_da = [tokenize_domain_aware(t) for t in corpus_texts]

    total_tokens_ws = sum(len(ts) for ts in c_tokens_ws)
    total_tokens_da = sum(len(ts) for ts in c_tokens_da)

    vocab_ws = set(t for ts in c_tokens_ws for t in ts)
    vocab_da = set(t for ts in c_tokens_da for t in ts)

    counts_ws = Counter(t for ts in c_tokens_ws for t in ts)
    counts_da = Counter(t for ts in c_tokens_da for t in ts)

    singletons_ws = sum(1 for c in counts_ws.values() if c == 1)
    singletons_da = sum(1 for c in counts_da.values() if c == 1)

    # Tokenize queries
    q_tokens_ws = [tokenize_whitespace(t) for t in query_texts]
    q_tokens_da = [tokenize_domain_aware(t) for t in query_texts]

    total_q_tokens_ws = sum(len(ts) for ts in q_tokens_ws)
    total_q_tokens_da = sum(len(ts) for ts in q_tokens_da)

    q_vocab_ws = set(t for ts in q_tokens_ws for t in ts)
    q_vocab_da = set(t for ts in q_tokens_da for t in ts)

    # OOV Analysis
    oov_terms_ws = sorted(q_vocab_ws - vocab_ws)
    oov_terms_da = sorted(q_vocab_da - vocab_da)

    # Query level OOV
    q_oov_count_ws = sum(1 for ts in q_tokens_ws if any(t not in vocab_ws for t in ts))
    q_oov_count_da = sum(1 for ts in q_tokens_da if any(t not in vocab_da for t in ts))

    # Token instance OOV
    oov_instances_ws = sum(sum(1 for t in ts if t not in vocab_ws) for ts in q_tokens_ws)
    oov_instances_da = sum(sum(1 for t in ts if t not in vocab_da) for ts in q_tokens_da)

    # Detailed overlap per query
    # Measure: for each query, what fraction of its tokens match the relevant target chunks?
    overlaps_ws = []
    overlaps_da = []
    chunk_map = {c["chunk_id"]: idx for idx, c in enumerate(corpus)}

    for q, q_ws, q_da in zip(queries, q_tokens_ws, q_tokens_da):
        rel_chunks = q["relevant_chunk_ids"]
        # Union of tokens in relevant chunks
        rel_ws_tokens = set()
        for cid in rel_chunks:
            if cid in chunk_map:
                rel_ws_tokens.update(c_tokens_ws[chunk_map[cid]])
        rel_da_tokens = set()
        for cid in rel_chunks:
            if cid in chunk_map:
                rel_da_tokens.update(c_tokens_da[chunk_map[cid]])

        match_ws = len(set(q_ws) & rel_ws_tokens) / max(len(set(q_ws)), 1)
        match_da = len(set(q_da) & rel_da_tokens) / max(len(set(q_da)), 1)
        overlaps_ws.append(match_ws)
        overlaps_da.append(match_da)

    # Identifier fragmentation patterns
    # Count how many tokens contain punctuation in whitespace
    punct_re = re.compile(r"[`'\".,;:?!()\[\]{}]")
    ws_tokens_with_punct = sum(1 for t in counts_ws.keys() if punct_re.search(t))
    da_tokens_with_punct = sum(1 for t in counts_da.keys() if punct_re.search(t))

    # Clean technical tokens in DA
    cli_flags_da = [t for t in vocab_da if t.startswith("-")]
    snake_case_da = [t for t in vocab_da if "_" in t and not t.startswith("-")]
    dotted_da = [t for t in vocab_da if "." in t and not t.startswith("-")]

    return {
        "coverage_diagnostic_definition": {
            "metric_name": "mean_lexical_token_coverage",
            "per_query_formula": "|T(q) ∩ R(q)| / |T(q)|",
            "numerator": "Count of unique query tokens present in the union of ground-truth relevant chunk tokens",
            "denominator": "|T(q)| = total count of unique tokens in query q",
            "mean_formula": "(1 / N) * sum(|T(q) ∩ R(q)| / |T(q)|) across all N=54 queries",
            "distinction_from_recall_at_k": (
                "This is a lexical vocabulary overlap diagnostic measuring query-to-chunk term surface alignment. "
                "It is NOT Recall@K, which measures the fraction of relevant documents/chunks retrieved in the top K."
            ),
        },
        "corpus": {
            "total_tokens_ws": total_tokens_ws,
            "total_tokens_da": total_tokens_da,
            "avg_tokens_per_chunk_ws": round(total_tokens_ws / len(corpus), 2),
            "avg_tokens_per_chunk_da": round(total_tokens_da / len(corpus), 2),
            "vocab_size_ws": len(vocab_ws),
            "vocab_size_da": len(vocab_da),
            "singletons_ws": singletons_ws,
            "singletons_da": singletons_da,
            "singleton_pct_ws": round(singletons_ws / len(vocab_ws) * 100, 2),
            "singleton_pct_da": round(singletons_da / len(vocab_da) * 100, 2),
            "tokens_with_punctuation_ws": ws_tokens_with_punct,
            "tokens_with_punctuation_da": da_tokens_with_punct,
            "cli_flags_da_count": len(cli_flags_da),
            "snake_case_da_count": len(snake_case_da),
            "dotted_da_count": len(dotted_da),
        },
        "queries": {
            "total_tokens_ws": total_q_tokens_ws,
            "total_tokens_da": total_q_tokens_da,
            "vocab_size_ws": len(q_vocab_ws),
            "vocab_size_da": len(q_vocab_da),
            "oov_unique_terms_ws": len(oov_terms_ws),
            "oov_unique_terms_da": len(oov_terms_da),
            "oov_terms_ws_sample": oov_terms_ws[:20],
            "oov_terms_da_sample": oov_terms_da,
            "queries_with_oov_ws": q_oov_count_ws,
            "queries_with_oov_da": q_oov_count_da,
            "oov_instance_pct_ws": round(oov_instances_ws / total_q_tokens_ws * 100, 2),
            "oov_instance_pct_da": round(oov_instances_da / total_q_tokens_da * 100, 2),
            "mean_lexical_token_coverage_ws": round(sum(overlaps_ws) / len(overlaps_ws) * 100, 2),
            "mean_lexical_token_coverage_da": round(sum(overlaps_da) / len(overlaps_da) * 100, 2),
        },
    }


if __name__ == "__main__":
    audit = audit_tokenizer()
    print(json.dumps(audit, indent=2))
