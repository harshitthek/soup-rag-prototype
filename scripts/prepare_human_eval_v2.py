"""Build frozen independent human evaluation benchmark v2.

Generates:
- data/human_eval/human_queries_v2.jsonl
- data/human_eval/relevance_annotations_v2.jsonl
- data/human_eval/manifest_v2.json
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
HUMAN_EVAL_DIR = DATA_DIR / "human_eval"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"

BENCHMARK_ITEMS = [
    {
        "id": "soup_human_001",
        "query": "how is energy and CO2 measurements done in soup?",
        "source_file": "data/raw_docs/adapters-and-governance.md",
        "owner_reference": "Energy & CO₂ measurement (--track-energy)",
        "resolved_heading": "Energy & CO₂ measurement (`--track-energy`)",
        "relevant_chunk_ids": [
            "adapters-and-governance::energy-co-measurement-track-energy"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_002",
        "query": "what is strict safetensors mode?",
        "source_file": "data/raw_docs/adapters-and-governance.md",
        "owner_reference": "Strict Safetensors Mode (soup adapters check-safetensors)",
        "resolved_heading": "Strict Safetensors Mode (`soup adapters check-safetensors`)",
        "relevant_chunk_ids": [
            "adapters-and-governance::strict-safetensors-mode-soup-adapters-check-safetensors"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_003",
        "query": "I want to track the experiment is there something in soup that i can use?",
        "source_file": "data/raw_docs/backends-and-ops.md",
        "owner_reference": "Experiment Tracking",
        "resolved_heading": "Experiment Tracking",
        "relevant_chunk_ids": [
            "backends-and-ops::experiment-tracking"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_004",
        "query": "I was training my model but my pc crashed in between is there some way i can resume it?",
        "source_file": "data/raw_docs/adapters-and-governance.md",
        "owner_reference": "Resume Training",
        "resolved_heading": "Resume Training",
        "relevant_chunk_ids": [
            "backends-and-ops::resume-training"
        ],
        "discrepancy_or_notes": "Owner cited adapters-and-governance.md, but the 'Resume Training' section is located at backends-and-ops.md:253 (backends-and-ops::resume-training). In adapters-and-governance.md, pause/resume pertains only to the data flywheel daemon (`soup loop pause / resume`). Mapped to the actual Resume Training section in backends-and-ops.md.",
    },
    {
        "id": "soup_human_005",
        "query": "can i use soup from my coding agent?",
        "source_file": "data/raw_docs/commands.md",
        "owner_reference": "Fine-tune from your coding agent (MCP)",
        "resolved_heading": "Fine-tune from your coding agent (MCP)",
        "relevant_chunk_ids": [
            "commands::fine-tune-from-your-coding-agent-mcp::sub_000",
            "commands::fine-tune-from-your-coding-agent-mcp::sub_001",
            "commands::fine-tune-from-your-coding-agent-mcp::sub_002",
            "commands::fine-tune-from-your-coding-agent-mcp::sub_003",
            "commands::fine-tune-from-your-coding-agent-mcp::sub_004",
            "commands::fine-tune-from-your-coding-agent-mcp::sub_005"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_006",
        "query": "give soup command for  Full traceback on errors.",
        "source_file": "data/raw_docs/commands.md",
        "owner_reference": "All Commands",
        "resolved_heading": "All Commands (entry: soup --verbose <command>)",
        "relevant_chunk_ids": [
            "commands::all-commands::sub_065"
        ],
        "discrepancy_or_notes": "Owner cited broad 'All Commands' section; resolved specifically to sub-chunk sub_065 documenting `soup --verbose <command>  Full traceback on errors`.",
    },
    {
        "id": "soup_human_007",
        "query": "how can i check if model memorized the data & for leak detection and provenance.",
        "source_file": "data/raw_docs/data.md",
        "owner_reference": "Canaries (soup data canary insert|check)",
        "resolved_heading": "Canaries (`soup data canary insert|check`)",
        "relevant_chunk_ids": [
            "data::canaries-soup-data-canary-insert-check",
            "data::1-insert-k-unique-secrets-keep-the-manifest-out-of-your-repo",
            "data::2-train-on-canaried-jsonl-as-usual-then::sub_000",
            "data::2-train-on-canaried-jsonl-as-usual-then::sub_001",
            "data::2-train-on-canaried-jsonl-as-usual-then::sub_002"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_008",
        "query": "which data formats are supported by soup?",
        "source_file": "data/raw_docs/data.md",
        "owner_reference": "Data Formats",
        "resolved_heading": "Data Formats",
        "relevant_chunk_ids": [
            "data::data-formats::sub_000",
            "data::data-formats::sub_001",
            "data::data-formats::sub_002",
            "data::data-formats::sub_003",
            "data::data-formats::sub_004",
            "data::data-formats::sub_005",
            "data::data-formats::sub_006"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_009",
        "query": "how does soup guarentees Proper sequential testing with early-stop?",
        "source_file": "data/raw_docs/evaluation.md",
        "owner_reference": "Sequential A/B Harness (soup ab)",
        "resolved_heading": "Sequential A/B Harness (`soup ab`)",
        "relevant_chunk_ids": [
            "evaluation::sequential-a-b-harness-soup-ab",
            "evaluation::or-with-custom-alpha-beta::sub_000",
            "evaluation::or-with-custom-alpha-beta::sub_001"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_010",
        "query": "how can i know if the model got better or did it break?",
        "source_file": "data/raw_docs/evaluation.md",
        "owner_reference": "Ship Verdict (soup ship)",
        "resolved_heading": "Ship Verdict (`soup ship`)",
        "relevant_chunk_ids": [
            "evaluation::ship-verdict-soup-ship::sub_000",
            "evaluation::ship-verdict-soup-ship::sub_001"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_011",
        "query": "can i create a model card using soup? if yes then how?",
        "source_file": "data/raw_docs/compliance.md",
        "owner_reference": "7. Generate a documented model card",
        "resolved_heading": "7. Generate a documented model card",
        "relevant_chunk_ids": [
            "compliance::7-generate-a-documented-model-card"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_012",
        "query": "how the model card links every file needed for verification?",
        "source_file": "data/raw_docs/compliance.md",
        "owner_reference": "4. Register the run, then emit BOM + attestation",
        "resolved_heading": "4. Register the run, then emit BOM + attestation",
        "relevant_chunk_ids": [
            "compliance::4-register-the-run-then-emit-bom-attestation::sub_000",
            "compliance::4-register-the-run-then-emit-bom-attestation::sub_001"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_013",
        "query": "why should i use unsloth backend instead of simple?",
        "source_file": "data/raw_docs/models.md",
        "owner_reference": "fast: pip install \"soup-cli[fast]\" — Unsloth backend (2-5x faster, lower VRAM)",
        "resolved_heading": "The extras table (entry: fast: unsloth)",
        "relevant_chunk_ids": [
            "models::the-extras-table::sub_001"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_014",
        "query": "diff between onnx and awq? whats there use case?",
        "source_file": "data/raw_docs/models.md",
        "owner_reference": "onnx / tensorrt: ONNX / TensorRT-LLM export and awq / gptq: AWQ / GPTQ quantized export",
        "resolved_heading": "The extras table (entries: onnx / tensorrt and awq / gptq)",
        "relevant_chunk_ids": [
            "models::the-extras-table::sub_004"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_015",
        "query": "why cant i use GaLore with unsloth?",
        "source_file": "data/raw_docs/peft-and-efficiency.md",
        "owner_reference": "GaLore",
        "resolved_heading": "GaLore (Memory-Efficient Full-Parameter Training)",
        "relevant_chunk_ids": [
            "peft-and-efficiency::galore-memory-efficient-full-parameter-training"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_016",
        "query": "tell me the gives and takes of lisa.",
        "source_file": "data/raw_docs/peft-and-efficiency.md",
        "owner_reference": "LISA",
        "resolved_heading": "LISA — Layerwise Importance Sampling (v0.71.34) / What LISA actually costs, measured at 3B and 8B",
        "relevant_chunk_ids": [
            "peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_000",
            "peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_001",
            "peft-and-efficiency::lisa-layerwise-importance-sampling-v0-71-34::sub_002",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_000",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_001",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_002",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_003",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_004",
            "peft-and-efficiency::what-lisa-actually-costs-measured-at-3b-and-8b::sub_005"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_017",
        "query": "why I'm facing error like runtime error when i use training.quantization: bitnet_1.58.",
        "source_file": "data/raw_docs/performance-and-quantization.md",
        "owner_reference": "BitNet",
        "resolved_heading": "BitNet 1.58-Bit Fine-Tuning (BETA, live in v0.71.20)",
        "relevant_chunk_ids": [
            "performance-and-quantization::bitnet-1-58-bit-fine-tuning-beta-live-in-v0-71-20::sub_000",
            "performance-and-quantization::bitnet-1-58-bit-fine-tuning-beta-live-in-v0-71-20::sub_001"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_018",
        "query": "Do i have to manually do pre-quantized bases when i use Quant Menu II + Export Pipeline (v0.53.1)",
        "source_file": "data/raw_docs/performance-and-quantization.md",
        "owner_reference": "Quant Menu II + Export Pipeline (v0.53.1)",
        "resolved_heading": "Quant Menu II + Export Pipeline (v0.53.1)",
        "relevant_chunk_ids": [
            "performance-and-quantization::quant-menu-ii-export-pipeline-v0-53-1"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_019",
        "query": "is there any feature i can use to get advice on eval etc?",
        "source_file": "data/raw_docs/README.md",
        "owner_reference": "Evaluation & probes",
        "resolved_heading": "Soup Documentation (Evaluation & probes link to evaluation.md: soup advise)",
        "relevant_chunk_ids": [
            "README::soup-documentation::sub_002",
            "README::soup-documentation::sub_003",
            "evaluation::pre-flight-decision-soup-advise"
        ],
        "discrepancy_or_notes": "README index entry points to evaluation.md (`soup advise`). Both index entry chunks in README and the target section in evaluation.md are recorded.",
    },
    {
        "id": "soup_human_020",
        "query": "where can i get info about OpenAI-compatible server?",
        "source_file": "data/raw_docs/README.md",
        "owner_reference": "Serving & export (serving-and-export.md)",
        "resolved_heading": "Soup Documentation (Serving & export link to serving-and-export.md: Inference Server)",
        "relevant_chunk_ids": [
            "README::soup-documentation::sub_003",
            "serving-and-export::inference-server"
        ],
        "discrepancy_or_notes": "README index entry points to serving-and-export.md (`Inference Server`). Both index chunk and destination section chunk are recorded.",
    },
    {
        "id": "soup_human_021",
        "query": "why does my training breaked when i used pip install -r ~/.soup/llama.cpp/requirements.txt??",
        "source_file": "data/raw_docs/serving-and-export.md",
        "owner_reference": "Toolchain validated on Windows note",
        "resolved_heading": "Building llama.cpp (required for quantized GGUF)",
        "relevant_chunk_ids": [
            "serving-and-export::building-llama-cpp-required-for-quantized-gguf::sub_002",
            "serving-and-export::building-llama-cpp-required-for-quantized-gguf::sub_003"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_022",
        "query": "can i even turn an OpenAPI 3.x, MCP server manifest, or GraphQL introspection JSON straight into a tool-calling SFT dataset without manual labelling and no scaffolding?",
        "source_file": "data/raw_docs/serving-and-export.md",
        "owner_reference": "Agent Forge",
        "resolved_heading": "Agent Forge",
        "relevant_chunk_ids": [
            "serving-and-export::agent-forge"
        ],
        "discrepancy_or_notes": None,
    },
    {
        "id": "soup_human_023",
        "query": "How do you configure the text-to-speech (TTS) fine-tuning pipeline introduced in version 0.52.0, and what specific data format does its audio dataset require?",
        "source_file": "data/raw_docs/training.md",
        "owner_reference": "TTS fine-tuning pipeline introduced in version 0.52.0",
        "resolved_heading": "TTS Fine-Tuning (`task='tts'`, BETA, live in v0.71.20)",
        "relevant_chunk_ids": [
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_000",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_001",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_002",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_003",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_004",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_005",
            "training::tts-fine-tuning-task-tts-beta-live-in-v0-71-20::sub_006"
        ],
        "discrepancy_or_notes": "v0.52.0 schema stub lifted to live wiring in v0.71.20 under the documented heading.",
    },
    {
        "id": "soup_human_024",
        "query": "What happens to the initialization of the LoRA adapter (lora_A) and classification heads in an unseeded run after update #353, and how does this change the behavior from previous versions?",
        "source_file": "data/raw_docs/training.md",
        "owner_reference": "Seeds & reproducibility (training.seed)",
        "resolved_heading": "Seeds & reproducibility (`training.seed`)",
        "relevant_chunk_ids": [
            "training::seeds-reproducibility-training-seed::sub_000",
            "training::seeds-reproducibility-training-seed::sub_001",
            "training::seeds-reproducibility-training-seed::sub_002",
            "training::seeds-reproducibility-training-seed::sub_003",
            "training::seeds-reproducibility-training-seed::sub_004",
            "training::seeds-reproducibility-training-seed::sub_005",
            "training::seeds-reproducibility-training-seed::sub_006"
        ],
        "discrepancy_or_notes": None,
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_base_section(chunk_id: str) -> str:
    return chunk_id.rsplit("::sub_", 1)[0]


def main() -> None:
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify all chunk IDs against data/corpus.jsonl
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus_chunk_ids = {json.loads(line)["chunk_id"] for line in f}

    corpus_sha256 = sha256_file(CORPUS_PATH)
    print(f"Corpus chunks: {len(corpus_chunk_ids)}, Corpus SHA256: {corpus_sha256}")

    for item in BENCHMARK_ITEMS:
        for cid in item["relevant_chunk_ids"]:
            if cid not in corpus_chunk_ids:
                raise ValueError(f"Chunk ID '{cid}' for {item['id']} not in corpus.jsonl!")

    # 2. Write human_queries_v2.jsonl
    queries_path = HUMAN_EVAL_DIR / "human_queries_v2.jsonl"
    with open(queries_path, "w", encoding="utf-8") as f:
        for item in BENCHMARK_ITEMS:
            record = {
                "query_id": item["id"],
                "query": item["query"],
                "source_file": item["source_file"],
                "owner_reference": item["owner_reference"],
                "authorship_declaration": "Authored and supplied by project owner",
                "ai_assistance_declaration": "Human-authored without AI assistance",
                "dataset_id": "human_eval_v2",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    queries_sha256 = sha256_file(queries_path)
    print(f"Wrote {queries_path} (SHA256: {queries_sha256})")

    # 3. Write relevance_annotations_v2.jsonl
    annotations_path = HUMAN_EVAL_DIR / "relevance_annotations_v2.jsonl"
    with open(annotations_path, "w", encoding="utf-8") as f:
        for item in BENCHMARK_ITEMS:
            # derive unique base section IDs preserving order
            base_sections = list(dict.fromkeys(get_base_section(cid) for cid in item["relevant_chunk_ids"]))
            record = {
                "query_id": item["id"],
                "source_file": item["source_file"],
                "owner_reference": item["owner_reference"],
                "resolved_heading": item["resolved_heading"],
                "relevant_chunk_ids": item["relevant_chunk_ids"],
                "relevant_section_ids": base_sections,
                "annotation_type": "binary",
                "status": "resolved",
                "discrepancy_or_notes": item["discrepancy_or_notes"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    annotations_sha256 = sha256_file(annotations_path)
    print(f"Wrote {annotations_path} (SHA256: {annotations_sha256})")

    # Get current git commit
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    # 4. Write manifest_v2.json
    manifest = {
        "dataset_id": "human_eval_v2",
        "dataset_purpose": "Independent evaluation benchmark authored by project owner without AI assistance to verify retrieval generalization and adapter transfer across full Soup documentation",
        "status": "frozen",
        "frozen": True,
        "query_count": len(BENCHMARK_ITEMS),
        "authorship_declaration": "Authored and supplied directly by project owner",
        "ai_assistance_declaration": "Project owner confirmed 24 queries were human-authored without AI assistance; no LLM rewrites or paraphrases",
        "creation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "freeze_timestamp": datetime.now(timezone.utc).isoformat(),
        "repository_commit": git_commit,
        "corpus_fingerprint": corpus_sha256,
        "corpus_manifest_reference": "data/corpus.jsonl",
        "chunking_configuration": "Canonical indexed markdown chunking, header-aware sub-chunking, 1,068 chunks",
        "queries_sha256": queries_sha256,
        "annotations_sha256": annotations_sha256,
        "query_ids": [item["id"] for item in BENCHMARK_ITEMS],
        "queries": [
            {
                "id": item["id"],
                "query": item["query"],
                "source_file": item["source_file"],
                "owner_reference": item["owner_reference"],
                "resolved_heading": item["resolved_heading"],
                "relevant_chunk_ids": item["relevant_chunk_ids"],
                "relevant_section_ids": list(dict.fromkeys(get_base_section(cid) for cid in item["relevant_chunk_ids"])),
            }
            for item in BENCHMARK_ITEMS
        ],
        "retrieval_system_configurations": {
            "improved_bm25": "Domain-aware BM25 with token-split, camelCase/snake_case/kebab-case splitting, CLI preservation, punctuation filtering",
            "frozen_e5_small": "intfloat/e5-small-v2 (frozen weights, query: prefix for queries, passage: prefix for documents)",
            "fine_tuned_e5_small_lr2e5": "intfloat/e5-small-v2 with PEFT LoRA adapter (r=16, alpha=32, target=[q_proj, v_proj]), trained with lr=2e-5, 3 epochs, 1857 steps on 2475 triplets",
            "hybrid_rrf": "Reciprocal Rank Fusion with k=60 combining Improved BM25 and Frozen E5-small",
            "frozen_minilm": "sentence-transformers/all-MiniLM-L6-v2 (frozen weights)",
            "adapter_exp_c_matched_balanced": "all-MiniLM-L6-v2 adapter trained on Exp C balanced triplets"
        },
        "evaluation_metrics": [
            "Hit@1", "Recall@3", "Recall@5", "MRR@10", "Sec-Hit@1", "Sec-MRR@10"
        ],
        "bootstrap_configuration": {
            "method": "paired document-stratified bootstrap",
            "seed": 42,
            "resamples": 10000,
            "confidence_interval": 0.95
        }
    }

    manifest_path = HUMAN_EVAL_DIR / "manifest_v2.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Wrote frozen manifest to {manifest_path}")


if __name__ == "__main__":
    main()
