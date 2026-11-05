"""Unit tests for domain-aware BM25 tokenizer."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from retrievers import tokenize_domain_aware, tokenize_whitespace, BM25Retriever  # noqa: E402


class TestBM25Tokenizer:
    def test_cli_flags_double_hyphens(self):
        tokens = tokenize_domain_aware("--gradient-accumulation-steps")
        assert tokens == ["--gradient-accumulation-steps", "gradient", "accumulation", "steps"]

        tokens_short = tokenize_domain_aware("--top-k")
        assert tokens_short == ["--top-k", "top"]

        # Flag with equals
        tokens_val = tokenize_domain_aware("--margin=0.5")
        assert tokens_val == ["--margin", "margin", "0.5"]

    def test_hyphenated_compound_identifiers(self):
        tokens = tokenize_domain_aware("sentence-transformers")
        assert tokens == ["sentence-transformers", "sentence", "transformers"]

        tokens_multi = tokenize_domain_aware("peft-and-efficiency")
        assert tokens_multi == ["peft-and-efficiency", "peft", "and", "efficiency"]

    def test_underscore_separated_identifiers(self):
        tokens = tokenize_domain_aware("gradient_accumulation_steps")
        assert tokens == ["gradient_accumulation_steps", "gradient", "accumulation", "steps"]

        tokens_short = tokenize_domain_aware("learning_rate")
        assert tokens_short == ["learning_rate", "learning", "rate"]

    def test_dotted_module_and_class_identifiers(self):
        tokens_cls = tokenize_domain_aware("torch.nn.Linear")
        assert tokens_cls == ["torch.nn.linear", "torch", "nn", "linear"]

        tokens_mod = tokenize_domain_aware("torch.cuda")
        assert tokens_mod == ["torch.cuda", "torch", "cuda"]

        tokens_trainer = tokenize_domain_aware("transformers.Trainer")
        assert tokens_trainer == ["transformers.trainer", "transformers", "trainer"]

    def test_package_names(self):
        tokens1 = tokenize_domain_aware("bitsandbytes")
        assert tokens1 == ["bitsandbytes"]

        tokens2 = tokenize_domain_aware("peft")
        assert tokens2 == ["peft"]

    def test_cli_commands(self):
        tokens1 = tokenize_domain_aware("soup train")
        assert tokens1 == ["soup", "train"]

        tokens2 = tokenize_domain_aware("soup ship")
        assert tokens2 == ["soup", "ship"]

        tokens3 = tokenize_domain_aware("soup init")
        assert tokens3 == ["soup", "init"]

    def test_version_numbers(self):
        tokens_v = tokenize_domain_aware("v0.77.1")
        assert tokens_v == ["v0.77.1", "0.77.1"]
        # Numeric tokens should not be fragmented into noisy isolated single digits
        assert "0" not in tokens_v
        assert "77" not in tokens_v
        assert "1" not in tokens_v

        tokens_num = tokenize_domain_aware("0.77.1")
        assert tokens_num == ["0.77.1"]

        tokens_py = tokenize_domain_aware("Python 3.12.13")
        assert tokens_py == ["python", "3.12.13"]

    def test_paths_and_file_extensions(self):
        tokens_path = tokenize_domain_aware("output/adapter_model.safetensors")
        assert "output/adapter_model.safetensors" in tokens_path
        assert "output" in tokens_path
        assert "adapter_model.safetensors" in tokens_path
        assert "adapter" in tokens_path
        assert "model" in tokens_path
        assert "safetensors" in tokens_path

        tokens_file = tokenize_domain_aware("config.yaml")
        assert tokens_file == ["config.yaml", "config", "yaml"]

    def test_case_normalization(self):
        tokens1 = tokenize_domain_aware("LoRA")
        tokens2 = tokenize_domain_aware("lora")
        assert tokens1 == tokens2 == ["lora"]

        tokens3 = tokenize_domain_aware("SOUP TRAIN --LORA-ALPHA=32")
        assert "--lora-alpha" in tokens3
        assert "lora" in tokens3
        assert "alpha" in tokens3
        assert "32" in tokens3

    def test_punctuation_and_empty_strings(self):
        assert tokenize_domain_aware("") == []
        assert tokenize_domain_aware("   ") == []
        assert tokenize_domain_aware("---") == []
        assert tokenize_domain_aware("...") == []
        assert tokenize_domain_aware("###") == []
        assert tokenize_domain_aware("???") == []
        assert tokenize_domain_aware("`--flag`") == ["--flag", "flag"]
        assert tokenize_domain_aware('"soup ship"') == ["soup", "ship"]

    def test_consistent_query_and_document_tokenization(self):
        doc_text = "Run `soup train --gradient-accumulation-steps=4` with torch.nn.Linear."
        query_text = "How to configure --gradient-accumulation-steps in soup train?"

        doc_tokens = tokenize_domain_aware(doc_text)
        query_tokens = tokenize_domain_aware(query_text)

        # Both contain full flag token and subcomponents
        assert "--gradient-accumulation-steps" in doc_tokens
        assert "--gradient-accumulation-steps" in query_tokens
        assert "soup" in doc_tokens and "soup" in query_tokens
        assert "train" in doc_tokens and "train" in query_tokens
        assert "gradient" in doc_tokens and "gradient" in query_tokens

    def test_legacy_whitespace_preserved(self):
        text = "soup train --flag"
        assert tokenize_whitespace(text) == ["soup", "train", "--flag"]

    def test_retriever_tokenizer_selection(self):
        r_domain = BM25Retriever("bm25", tokenizer="domain_aware")
        assert r_domain.tokenizer_name == "domain_aware"
        assert r_domain.config()["tokenizer"] == "domain_aware"

        r_legacy = BM25Retriever("bm25_legacy", tokenizer="whitespace")
        assert r_legacy.tokenizer_name == "whitespace"
        assert r_legacy.config()["tokenizer"] == "whitespace"

        with pytest.raises(ValueError, match="unknown tokenizer"):
            BM25Retriever(tokenizer="invalid_tok")
