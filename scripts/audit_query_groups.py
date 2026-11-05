"""Audit exact query IDs in parameter, CLI, and configuration queries,
correcting the grouping to separate strict parameter/CLI lookups from procedural how-to questions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retrieval import compute_metrics

REPO_ROOT = Path(__file__).resolve().parents[1]
HYBRID_DIR = REPO_ROOT / "results" / "hybrid"


def audit_query_groups() -> dict[str, Any]:
    per_query = json.loads((HYBRID_DIR / "per_query_results.json").read_text(encoding="utf-8"))

    # 1. Strict Parameter, Configuration & CLI Detail queries (16 queries)
    # Origin: query_type in ("command_detail", "config_behavior")
    strict_param_cli_ids = [
        "manual_009",  # grace codebook size limit
        "manual_010",  # soup registry diff output
        "manual_011",  # dare merge seed determinism
        "manual_017",  # which soup init templates exist for regulated industries
        "manual_023",  # which expectation checks can go in expectations.yaml
        "manual_029",  # eval_gate block settings in soup.yaml
        "manual_034",  # noise floor flag effect on ship verdict
        "manual_036",  # score BLEU and ROUGE on custom eval outputs
        "manual_038",  # custom eval jsonl fields for exact and regex scoring
        "manual_041",  # soup eval irt-subset size and item model options
        "manual_042",  # preview which decoder layers soup shrink will drop
        "manual_045",  # set up yarn for 4x context extension
        "manual_047",  # different learning rates for q_proj and v_proj
        "manual_049",  # loraplus_lr_ratio effect on B matrix lr
        "manual_051",  # neftune_alpha range for chat fine tuning
        "manual_053",  # stop training when loss spikes repeatedly
    ]

    # 2. Procedural How-To queries (13 queries)
    # Origin: query_type == "how_to"
    how_to_ids = [
        "manual_002",  # How do I bisect training checkpoints when an eval regresses?
        "manual_003",  # how do I see which training rows influenced an adapter
        "manual_005",  # does soup roll back a canary automatically if the eval regresses
        "manual_007",  # compare model answers before and after a knowledge edit
        "manual_008",  # build a control vector from positive and negative prompts
        "manual_015",  # what goes into a soup airgap bundle and how big can it get
        "manual_018",  # clean emails and phone numbers out of my training data
        "manual_021",  # publish a model to huggingface with my own model card
        "manual_026",  # generate an eval suite from my training data
        "manual_028",  # block a git push when eval accuracy regresses
        "manual_035",  # how do I make a ship verdict replayable in CI
        "manual_039",  # run a short LoRA probe on several base models before choosing one
        "manual_046",  # Can I add fresh layers to a Llama model and only train those?
    ]

    # 3. Conceptual, Troubleshooting & Relationship queries (25 queries)
    other_ids = [
        pq["query_id"]
        for pq in per_query
        if pq["query_id"] not in strict_param_cli_ids and pq["query_id"] not in how_to_ids
    ]

    all_groups = {
        "strict_parameter_cli": {
            "name": "Strict Parameter, Configuration & CLI Details",
            "query_ids": strict_param_cli_ids,
            "description": "Specific named CLI options, subcommands, schema fields, and hyperparameter flags.",
        },
        "procedural_how_to": {
            "name": "Procedural How-To Workflows",
            "query_ids": how_to_ids,
            "description": "Multi-step workflows and procedures (e.g. data cleaning, publishing, canary rollback).",
        },
        "conceptual_and_other": {
            "name": "Conceptual, Troubleshooting & Architecture",
            "query_ids": other_ids,
            "description": "Mechanism definitions, architecture trade-offs, and error troubleshooting.",
        },
    }

    out_metrics: dict[str, Any] = {}
    for gkey, gdata in all_groups.items():
        qids = gdata["query_ids"]
        out_metrics[gkey] = {
            "name": gdata["name"],
            "count": len(qids),
            "query_ids": qids,
            "description": gdata["description"],
            "systems": {},
        }
        for sys_id in ["bm25_legacy", "bm25_improved", "e5_small", "hybrid_rrf"]:
            subset = [
                {
                    "query_id": pq["query_id"],
                    "query": pq["query"],
                    "subset": pq["subset"],
                    "source_document": pq["source_document"],
                    "relevant_chunk_ids": pq["relevant_chunk_ids"],
                    "relevant_section_ids": pq["relevant_section_ids"],
                    "ranked": pq["systems"][sys_id]["ranked_top10"],
                }
                for pq in per_query
                if pq["query_id"] in qids
            ]
            m = compute_metrics(subset)["metrics"]
            out_metrics[gkey]["systems"][sys_id] = {
                "hit@1": round(m["hit@1"], 4),
                "recall@3": round(m["recall@3"], 4),
                "recall@5": round(m["recall@5"], 4),
                "mrr@10": round(m["mrr@10"], 4),
                "sec_hit@1": round(m["sec_hit@1"], 4),
                "sec_mrr@10": round(m["sec_mrr@10"], 4),
            }

    return out_metrics


if __name__ == "__main__":
    res = audit_query_groups()
    print(json.dumps(res, indent=2))
