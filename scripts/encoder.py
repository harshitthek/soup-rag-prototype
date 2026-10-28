"""Shared encoder for baseline and candidate retrieval.

One code path, two modes:
  - Frozen base MiniLM (no adapter)
  - Base MiniLM + SOUP-trained LoRA adapter

Both use identical tokenization (256 max), attention-masked mean pooling,
and L2 normalization. Cosine similarity = dot product on the output.
"""

from __future__ import annotations

import numpy as np
import torch
from pathlib import Path
from typing import Optional

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_SEQ_LENGTH = 256  # Model was trained with this max


def _mean_pool(
    last_hidden: torch.Tensor, attention_mask: torch.Tensor
) -> torch.Tensor:
    """Attention-masked mean pooling over the token axis."""
    mask_expanded = attention_mask.unsqueeze(-1).float()
    sum_hidden = (last_hidden * mask_expanded).sum(dim=1)
    sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-12)
    return sum_hidden / sum_mask


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalization (matches SOUP's embed.py)."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return vectors / norms


class SharedEncoder:
    """Encode texts with frozen MiniLM or fine-tuned MiniLM + LoRA adapter."""

    def __init__(
        self,
        model_dir: str | Path = MODEL_ID,
        adapter_dir: Optional[str | Path] = None,
        device: str = "cpu",
        batch_size: int = 32,
    ):
        from transformers import AutoTokenizer, AutoModel

        self.device = device
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

        base_model = AutoModel.from_pretrained(model_dir)

        if adapter_dir is not None:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(base_model, str(adapter_dir))
            self.has_adapter = True
        else:
            self.model = base_model
            self.has_adapter = False

        self.model.to(device)
        self.model.eval()

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts to L2-normalized float32 vectors.

        Returns shape ``(len(texts), hidden_dim)``.
        """
        all_vectors: list[np.ndarray] = []

        for start in range(0, len(texts), self.batch_size):
            batch_texts = texts[start : start + self.batch_size]

            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=MAX_SEQ_LENGTH,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**encoded)

            pooled = _mean_pool(outputs.last_hidden_state, encoded["attention_mask"])
            batch_vecs = pooled.cpu().numpy().astype(np.float32)
            all_vectors.append(batch_vecs)

        vectors = np.concatenate(all_vectors, axis=0)
        return _l2_normalize(vectors)

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text. Returns shape ``(hidden_dim,)``."""
        return self.encode([text])[0]
