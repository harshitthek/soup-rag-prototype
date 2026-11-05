"""Retriever implementations for Evaluation v2.

``DenseRetriever``: frozen or LoRA-adapted BERT-family encoders with
attention-masked mean pooling and L2 normalization (MiniLM and E5 share this
math; tokenization, revision pinning, truncation length, and input prefixes
are per-model configuration).

``BM25Retriever``: BM25Okapi over the same passage text the dense retrievers
embed, with lowercase whitespace tokenization. Parameters k1/b are fixed;
tuning is prohibited (no development set exists).

Heavy dependencies (torch/transformers/peft, rank_bm25) are imported lazily
inside the classes so that metric-only workflows stay stdlib.
"""

from __future__ import annotations

import re
from typing import Any, Sequence

MINILM_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MINILM_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"  # pinned in soup_run.json
E5_MODEL_ID = "intfloat/e5-small-v2"
E5_REVISION = "ffb93f3bd4047442299a41ebb6fa998a38507c52"

RETRIEVER_SPECS: dict[str, dict[str, Any]] = {
    "mini_lm_frozen": {
        "model": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": None,
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    "mini_lm_soup": {
        "model": MINILM_MODEL_ID,
        "revision": MINILM_REVISION,
        "adapter_dir": "output_embedding",
        "max_length": 256,
        "query_prefix": "",
        "passage_prefix": "",
    },
    "bm25": {
        "model": "bm25-okapi",
        "k1": 1.5,
        "b": 0.75,
        "tokenizer": "domain_aware",
        "query_prefix": "",
        "passage_prefix": "",
    },
    "bm25_legacy": {
        "model": "bm25-okapi",
        "k1": 1.5,
        "b": 0.75,
        "tokenizer": "whitespace",
        "query_prefix": "",
        "passage_prefix": "",
    },
    "e5_small": {
        "model": E5_MODEL_ID,
        "revision": E5_REVISION,
        "adapter_dir": None,
        "max_length": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    "e5_small_ft": {
        "model": E5_MODEL_ID,
        "revision": E5_REVISION,
        "adapter_dir": "output/adapter_e5_exp_b",
        "max_length": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    "e5_small_ft_lr2e5": {
        "model": E5_MODEL_ID,
        "revision": E5_REVISION,
        "adapter_dir": "output/adapter_e5_exp_b_lr2e5",
        "max_length": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    "e5_small_ft_lr2e4": {
        "model": E5_MODEL_ID,
        "revision": E5_REVISION,
        "adapter_dir": "output/adapter_e5_exp_b_lr2e4",
        "max_length": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
}


def build_passage_text(chunk: dict[str, Any]) -> str:
    """Passage representation: heading prefix + body, matching v1 evaluation."""
    prefix = chunk.get("heading_prefix") or chunk.get("doc_name") or ""
    return f"{prefix}\n\n{chunk['text']}"


def _mean_pool(last_hidden, attention_mask):
    mask = attention_mask.unsqueeze(-1).float()
    summed = (last_hidden * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp(min=1e-12)
    return summed / denom


def _l2_normalize(vectors):
    import numpy as np

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return vectors / norms


class DenseRetriever:
    """BERT-family encoder with optional PEFT adapter.

    Pooling is attention-masked mean pooling (matching v1 ``encoder.py`` and
    E5's official ``1_Pooling`` config, which specifies mean tokens). Other
    pooling modes are rejected explicitly rather than silently misused.
    """

    def __init__(
        self,
        retriever_id: str,
        model_id: str,
        revision: str | None = None,
        adapter_dir: str | None = None,
        max_length: int = 256,
        pooling: str = "mean",
        query_prefix: str = "",
        passage_prefix: str = "",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        if pooling != "mean":
            raise ValueError(
                f"pooling={pooling!r} unsupported; only attention-masked mean pooling is implemented"
            )
        self.retriever_id = retriever_id
        self.model_id = model_id
        self.revision = revision
        self.adapter_dir = adapter_dir
        self.max_length = max_length
        self.pooling = pooling
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix
        self.device = device
        self.batch_size = batch_size
        self._loaded = False

    def config(self) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "revision": self.revision,
            "adapter_dir": self.adapter_dir,
            "max_length": self.max_length,
            "pooling": self.pooling,
            "query_prefix": self.query_prefix,
            "passage_prefix": self.passage_prefix,
            "device": self.device,
        }

    def _load(self) -> None:
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id, revision=self.revision
        )
        base_model = AutoModel.from_pretrained(self.model_id, revision=self.revision)
        if self.adapter_dir:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(base_model, self.adapter_dir)
        else:
            self.model = base_model
        self.model.to(self.device)
        self.model.eval()
        self._loaded = True

    def encode(self, texts: Sequence[str]) -> Any:
        import numpy as np
        import torch

        if not self._loaded:
            self._load()

        all_vectors: list[Any] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                outputs = self.model(**encoded)
            pooled = _mean_pool(outputs.last_hidden_state, encoded["attention_mask"])
            all_vectors.append(pooled.cpu().numpy().astype(np.float32))
        return _l2_normalize(np.concatenate(all_vectors, axis=0))

    def encode_queries(self, queries: Sequence[str]) -> Any:
        return self.encode([self.query_prefix + q for q in queries])

    def encode_corpus(self, chunks: Sequence[dict[str, Any]]) -> Any:
        return self.encode(
            [self.passage_prefix + build_passage_text(c) for c in chunks]
        )


VERSION_RE = re.compile(r"^v?\d+(?:\.\d+)+$")
STRIP_PUNCT = "\"'`()[]{}<>,;?!~*#%^&|=+"


def tokenize_whitespace(text: str) -> list[str]:
    """Legacy lowercase whitespace tokenizer for BM25."""
    return text.lower().split()


def tokenize_domain_aware(text: str) -> list[str]:
    """Deterministic, lightweight domain-aware technical tokenizer.

    Handles:
    - Case normalization (lowercase).
    - Preserves full CLI flags (e.g., ``--gradient-accumulation-steps``) alongside sub-words.
    - Preserves underscore and dotted identifiers (e.g., ``torch.nn.Linear``, ``lora.r``).
    - Preserves package names and slash identifiers (e.g., ``sentence-transformers``, ``intfloat/e5-small-v2``).
    - Preserves version strings (e.g., ``v0.77.1``, ``3.12.13``) without splitting into single digits.
    - Preserves file paths and file extensions.
    - Strips noisy punctuation (quotes, backticks, brackets, Markdown headers) while preserving internal delimiters.
    """
    text = text.lower()
    raw_tokens = text.split()
    tokens: list[str] = []

    for raw in raw_tokens:
        t = raw.strip(STRIP_PUNCT)
        # Strip trailing punctuation like colons, commas, dots, slashes
        while t and t[-1] in ".:,/":
            if t.endswith(".") and not VERSION_RE.match(t):
                t = t[:-1]
            elif t.endswith(":") or t.endswith(",") or t.endswith("/"):
                t = t[:-1]
            else:
                break

        if not t or not any(c.isalnum() for c in t):
            continue

        # Check for flag assignment e.g. --margin=0.5
        if t.startswith("--") and "=" in t:
            flag_part, val_part = t.split("=", 1)
            candidate_tokens = [flag_part, val_part]
        else:
            candidate_tokens = [t]

        for cand in candidate_tokens:
            cand = cand.strip(STRIP_PUNCT)
            if not cand or not any(c.isalnum() for c in cand):
                continue

            # Version number check e.g. v0.77.1 or 3.12.13
            if VERSION_RE.match(cand):
                tokens.append(cand)
                if cand.startswith("v") and cand[1:]:
                    tokens.append(cand[1:])
                continue

            # CLI flag check e.g. --gradient-accumulation-steps
            if cand.startswith("--"):
                clean_flag = cand.rstrip(".,;:")
                tokens.append(clean_flag)
                parts = clean_flag[2:].split("-")
                for p in parts:
                    if len(p) > 1 and any(c.isalnum() for c in p):
                        tokens.append(p)
                continue

            # Path with slashes e.g. output/adapter_model.safetensors
            if "/" in cand:
                tokens.append(cand)
                segments = cand.split("/")
                for seg in segments:
                    if seg and any(c.isalnum() for c in seg) and seg != cand:
                        tokens.append(seg)
                        if any(s in seg for s in ("_", "-", ".")):
                            for sp in re.split(r"[_.-]", seg):
                                if sp and any(c.isalnum() for c in sp) and sp != seg:
                                    tokens.append(sp)
                continue

            # Compound identifiers with underscores, hyphens, or dots
            has_compound = any(sep in cand for sep in ("_", "-", "."))
            if has_compound:
                tokens.append(cand)
                sub_parts = re.split(r"[_.-]", cand)
                for sp in sub_parts:
                    if sp and any(c.isalnum() for c in sp) and sp != cand:
                        tokens.append(sp)
            else:
                tokens.append(cand)

    return tokens


class BM25Retriever:
    """BM25Okapi over prefixed passages with selectable tokenizer."""

    def __init__(
        self,
        retriever_id: str = "bm25",
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: str = "domain_aware",
    ):
        self.retriever_id = retriever_id
        self.k1 = k1
        self.b = b
        self.tokenizer_name = tokenizer
        if tokenizer == "whitespace":
            self._tokenize_func = tokenize_whitespace
        elif tokenizer == "domain_aware":
            self._tokenize_func = tokenize_domain_aware
        else:
            raise ValueError(
                f"unknown tokenizer '{tokenizer}'; choose 'domain_aware' or 'whitespace'"
            )
        self._index = None

    def config(self) -> dict[str, Any]:
        return {
            "model": "bm25-okapi",
            "k1": self.k1,
            "b": self.b,
            "tokenizer": self.tokenizer_name,
            "passage": "heading_prefix + body",
            "tuning": "none (fixed defaults; tuning prohibited)",
        }

    def _tokenize(self, text: str) -> list[str]:
        return self._tokenize_func(text)

    def fit(self, chunks: Sequence[dict[str, Any]]) -> None:
        from rank_bm25 import BM25Okapi

        corpus = [build_passage_text(c) for c in chunks]
        self._index = BM25Okapi(
            [self._tokenize(t) for t in corpus],
            k1=self.k1,
            b=self.b,
        )

    def score(self, query: str) -> list[float]:
        if self._index is None:
            raise RuntimeError("fit() must be called before score()")
        return [float(s) for s in self._index.get_scores(self._tokenize(query))]


def build_retriever(retriever_id: str, repo_root: Any = None) -> Any:
    """Instantiate a retriever from RETRIEVER_SPECS by id."""
    from pathlib import Path

    if retriever_id not in RETRIEVER_SPECS:
        raise ValueError(
            f"unknown retriever '{retriever_id}'; choose from {sorted(RETRIEVER_SPECS)}"
        )
    spec = RETRIEVER_SPECS[retriever_id]
    if retriever_id in ("bm25", "bm25_legacy"):
        return BM25Retriever(
            retriever_id,
            k1=spec["k1"],
            b=spec["b"],
            tokenizer=spec.get("tokenizer", "domain_aware"),
        )
    adapter_dir = spec.get("adapter_dir")
    if adapter_dir and repo_root is not None:
        adapter_dir = str(Path(repo_root) / adapter_dir)
    return DenseRetriever(
        retriever_id=retriever_id,
        model_id=spec["model"],
        revision=spec.get("revision"),
        adapter_dir=adapter_dir,
        max_length=spec["max_length"],
        query_prefix=spec["query_prefix"],
        passage_prefix=spec["passage_prefix"],
    )


def retrieve_ranked(
    retriever: Any,
    chunks: Sequence[dict[str, Any]],
    queries: Sequence[str],
    top_k: int = 10,
) -> list[list[dict[str, Any]]]:
    """Ranked results per query through one shared ranking path.

    Returns a list (per query) of ranked entries ``{rank, chunk_id, score}``
    produced by ``retrieval.rank_corpus``, so every retriever is evaluated by
    the same metric implementation.
    """
    if not queries:
        return []

    try:
        from retrieval import rank_corpus
    except ImportError:
        from scripts.retrieval import rank_corpus

    chunk_ids = [c["chunk_id"] for c in chunks]
    if isinstance(retriever, BM25Retriever):
        retriever.fit(chunks)
        return [
            rank_corpus(retriever.score(q), chunk_ids, top_k=top_k) for q in queries
        ]
    query_vecs = retriever.encode_queries(queries)
    corpus_vecs = retriever.encode_corpus(chunks)
    return [
        rank_corpus(corpus_vecs @ query_vecs[i], chunk_ids, top_k=top_k)
        for i in range(len(queries))
    ]
