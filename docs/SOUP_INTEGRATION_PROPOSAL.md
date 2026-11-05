# Soup Integration Proposal: Documentation Retrieval & RAG Support

**Document Version:** 1.0  
**Target Maintainer:** Alpamys (@MakazhanAlpamys)  
**Status:** Proposal for Maintainer Discussion (Unapproved proposal awaiting maintainer review; no upstream changes applied)
**Scope:** Minimal, decoupled documentation retrieval component for Soup CLI  

---

## 1. Executive Summary

This proposal defines a minimal, configuration-driven documentation retrieval integration for Soup. Based on the empirical findings from the Soup RAG prototype benchmark:
1. **Domain-Aware BM25** provides lexical matching for exact keywords, CLI flags (`--gradient-accumulation-steps`), configuration keys (`loraplus_lr_ratio`), and file paths without neural inference latency (107 ms index build, 2.37 ms query time measured on Apple Silicon).
2. **Dense Retrieval (E5-small)** provides semantic retrieval on natural developer questions.
3. **Reciprocal Rank Fusion (RRF, $k=60$)** unifies lexical and dense rankings, achieving the highest observed MRR@10 (**0.7254**) on the 24-query benchmark and improving top-3 recall over Frozen E5 (+0.0361, 95% bootstrap CI `[+0.0069, +0.0653]`), though the paired 95% bootstrap CI for the MRR@10 difference against Frozen E5 includes zero (`[-0.0687, +0.0996]`).

The objective is to establish a small, maintainable boundary that exposes fast, relevant documentation search to Soup users (`soup docs search <query>`) and feeds context to downstream LLM generation commands (`soup advise`, `soup init`, or chat assistants) without introducing heavy external databases, services, or multi-tenant complexity.

---

## 2. Non-Goals (What Retrieval Does NOT Own)

To keep Soup lean and Unix-philosophy aligned:
- **No LLM Generation:** The retriever only finds and ranks relevant document chunks. Prompt generation and synthesis remain with the existing caller.
- **No External Databases:** No ChromaDB, Pinecone, Milvus, Qdrant, or Postgres/pgvector dependencies.
- **No Microservices or Daemons:** Self-contained file-based storage using compressed numpy embeddings and an in-memory BM25 inverted index.
- **No Complex Frameworks:** Zero LangChain, LlamaIndex, or Haystack dependencies. Pure PyTorch, Hugging Face `transformers`, and standard library.

---

## 3. Minimal Component Architecture & Responsibilities

```
┌────────────────────────────────────────────────────────┐
│                      Soup CLI                          │
│   (e.g., `soup docs search`, `soup advise`, `chat`)    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            DocumentationRetriever Interface            │
│   - build_index(documents, config)                     │
│   - search(query, top_k=5)                             │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Domain-Aware BM25      │  │     Dense Retriever      │
│   (Regex Tokenizer)      │  │ (intfloat/e5-small-v2)   │
└──────────────┬───────────┘  └───────────┬──────────────┘
               │                          │
               └───────────┬──────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Reciprocal Rank Fusion (RRF)               │
│               RRF score = 1 / (60 + r)                 │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                Standard Ranked Results                 │
│    List[Dict[chunk_id, text, score, rank, heading]]    │
└────────────────────────────────────────────────────────┘
```

### Proposed Component Responsibilities:

#### A. Document Ingestion & Indexing
- Ingests Markdown (`.md`) and plain text (`.txt`) documentation files.
- Applies deterministic, heading-aware hierarchy chunking (`#`, `##`, `###`), preserving document name, section path, and line bounds.
- Computes and caches:
  - Lexical inverted index for BM25 (tokenized with domain-aware regex preserving flags and identifiers).
  - Pre-computed dense embeddings ($384$-dimensional float32 vectors) saved in `.soup/cache/docs_embeddings.npy`.
- Stores SHA256 corpus fingerprints and config hashes in `.soup/cache/docs_manifest.json` for automatic cache invalidation upon document modification.

#### B. Query Retrieval
- Accepts a natural language query string `query: str` and `top_k: int = 5`.
- Executes the configured pipeline:
  - `strategy: "bm25"`: Pure lexical scoring (sub-millisecond latency).
  - `strategy: "e5"`: Dense vector dot-product search against cached corpus embeddings.
  - `strategy: "hybrid"`: Concurrent BM25 + E5 execution fused via Reciprocal Rank Fusion ($k=60$).
- Returns a standardized list of ranked dictionaries.

---

## 4. Minimal Code Interface Specification

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    rank: int
    source_path: str
    heading: str
    token_count: int

class DocumentationRetriever:
    """Minimal decoupled documentation retriever for Soup."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.strategy = self.config.get("strategy", "hybrid")
        self.cache_dir = Path(self.config.get("cache_dir", ".soup/cache/docs"))
        self._bm25_index = None
        self._corpus_chunks: list[dict[str, Any]] = []
        self._embeddings = None

    def build_index(self, docs_dir: Path | str, force_rebuild: bool = False) -> None:
        """Parse documents, build BM25 index, compute/cache E5 dense embeddings."""
        ...

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Execute query search and return top-k ranked chunks."""
        ...
```

### Output Schema:
Each item returned by `search()` is a dictionary matching:
```python
{
    "chunk_id": "commands::soup-shrink::sub_001",
    "text": "soup shrink prunes least-important layer blocks with perplexity verification...",
    "score": 0.0328,
    "rank": 1,
    "source_path": "docs/commands.md",
    "heading": "Command Reference > soup shrink",
    "token_count": 142
}
```

---

## 5. Architectural Integration Details for Soup

### 5.1 Where Code Belongs in the Upstream Repo
- **Core Engine:** `src/soup_cli/retrieval/retriever.py` (contains `DocumentationRetriever`, `BM25`, and `RRF` fusion).
- **Tokenizer:** `src/soup_cli/retrieval/tokenizer.py` (contains `tokenize_domain_aware`).
- **CLI Command:** `src/soup_cli/commands/docs.py` (registers `soup docs search <query>` and `soup docs index <dir>`).

### 5.2 Where Index Persistence Belongs
- Index and cached embeddings reside in the project's local cache directory:
  ```text
  .soup/cache/docs/
  ├── manifest.json            # Corpus fingerprint, timestamp, model ID, config hash
  ├── chunks.jsonl             # Extracted chunk texts and heading metadata
  ├── bm25_index.pkl           # Lightweight pickled Okapi BM25 state (~200 KB)
  └── embeddings_e5.npy        # Float32 memory-mapped embedding matrix (~1.6 MB for 1k chunks)
  ```
- Fast loading via `numpy.load(..., mmap_mode="r")` is proposed to ensure search startup takes $<50$ ms when cached. (Note: These are design targets; in prototype benchmarks on Apple Silicon, cold start took ~36 seconds when indexing and loading the model into memory, while steady-state warm retrieval was 12.76 ms).

### 5.3 Cache Invalidation
Upon calling `build_index()` or invoking search:
1. The retriever computes the aggregate SHA256 of all input `.md` files.
2. If the hash matches `manifest.json`, the pre-computed index is loaded directly.
3. If documents were edited, added, or deleted, the index is automatically rebuilt incrementally.

### 5.4 Handling Model Dependencies & Optional Extras
To prevent bloating the base `soup-cli` installation:
- BM25 requires only `rank-bm25` (pure Python, 50 KB).
- Dense search (`e5_small` or adapters) uses existing `transformers` and `torch` already required by Soup training.
- If PyTorch is unavailable or `--lexical-only` is passed, the retriever cleanly falls back to Domain-Aware BM25 with a clear console notification:
  ```text
  [dim]Running fast lexical search (BM25 domain-aware)...[/]
  ```

### 5.5 How Downstream Soup Commands Can Reuse It
1. **`soup docs search "<query>"`:** Interactive developer documentation lookups in the terminal with rich Markdown highlighting.
2. **`soup advise`:** Feeds top-3 documentation sections as grounded context when advising users on hyperparameters or quantization choices.
3. **`soup chat` / Agent Forge:** Provides plug-and-play local retrieval tool for developer assistance.

### 5.6 Testability & Mocking
Because `DocumentationRetriever` accepts raw strings and yields simple dataclasses, unit tests in Soup's test suite can mock retrieval without loading Hugging Face weights:
```python
def test_retriever_mock(monkeypatch):
    retriever = DocumentationRetriever({"strategy": "bm25"})
    # Fits small in-memory test fixture without downloading any Hugging Face weights
    retriever.fit_in_memory([
        {"chunk_id": "c1", "heading": "Test", "text": "soup shrink prune"}
    ])
    results = retriever.search("shrink")
    assert results[0].chunk_id == "c1"
```

---

## 6. Minimal Configuration Example (`soup.yaml` extension)

```yaml
# Optional retrieval configuration block in soup.yaml
retrieval:
  strategy: hybrid          # Options: hybrid | bm25 | e5
  rrf_k: 60                 # Fixed reciprocal rank smoothing constant
  docs_dir: docs/           # Documentation root directory
  cache_dir: .soup/cache/docs
  dense_model: intfloat/e5-small-v2
  top_k: 5
```

---

## 7. Open Decisions for Alpamys

This integration proposal remains unapproved and requires maintainer discussion before any upstream PR is opened. Before proceeding, the maintainer should decide:
1. **CLI Command Naming:** Do you prefer `soup docs search "<query>"` or a top-level `soup search "<query>"`?
2. **Default Strategy:** Should the default be `hybrid` (highest observed MRR@10 on the 24-query benchmark, requires model load) or `bm25` (zero startup delay, strictly lexical)?
3. **Packaging:** Should `rank-bm25` be added to base dependencies in `pyproject.toml` (~50 KB pure Python) or gated under an optional extra (e.g. `pip install soup-cli[docs]`)?
