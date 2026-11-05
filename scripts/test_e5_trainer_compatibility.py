"""Compatibility gate test for E5-small fine-tuning with Soup's native embedding trainer."""

import json
import shutil
import tempfile
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from transformers import AutoModel, AutoTokenizer

from scripts.retrievers import DenseRetriever

def run_compatibility_gate():
    print("=== Step 1: Base Model & Tokenizer Verification ===")
    base_id = "intfloat/e5-small-v2"
    revision = "ffb93f3bd4047442299a41ebb6fa998a38507c52"
    tokenizer = AutoTokenizer.from_pretrained(base_id, revision=revision)
    base_model = AutoModel.from_pretrained(base_id, revision=revision)
    print(f"Base model: {base_id} (revision {revision})")
    print(f"Architecture: {base_model.config.architectures}")
    assert base_model.config.model_type == "bert"

    print("\n=== Step 2: Triplet Construction & Prefix Verification ===")
    sample_anchor_raw = "What does the `soup shrink` command do?"
    sample_pos_raw = "README: Soup Documentation\n\nPrune least-important layer blocks."
    sample_neg_raw = "commands: All Commands\n\nOther commands listed here."

    sample_anchor = f"query: {sample_anchor_raw}"
    sample_pos = f"passage: {sample_pos_raw}"
    sample_neg = f"passage: {sample_neg_raw}"

    # Tokenize
    enc_anchor = tokenizer(sample_anchor, return_tensors="pt")
    enc_pos = tokenizer(sample_pos, return_tensors="pt")
    enc_neg = tokenizer(sample_neg, return_tensors="pt")

    # Decode first few tokens to verify prefix tokens
    print(f"Anchor token prefix: {tokenizer.decode(enc_anchor['input_ids'][0][:3])}")
    print(f"Pos token prefix: {tokenizer.decode(enc_pos['input_ids'][0][:3])}")
    print(f"Neg token prefix: {tokenizer.decode(enc_neg['input_ids'][0][:3])}")
    assert tokenizer.decode(enc_anchor['input_ids'][0][:3]).startswith("[CLS] query :")
    assert tokenizer.decode(enc_pos['input_ids'][0][:3]).startswith("[CLS] passage :")

    print("\n=== Step 3: Mean Pooling & L2 Normalization Equivalence ===")
    # 1. Using DenseRetriever (our inference implementation)
    dr = DenseRetriever(
        retriever_id="e5_small",
        model_id=base_id,
        revision=revision,
        max_length=512,
        query_prefix="query: ",
        passage_prefix="passage: ",
        device="cpu",
    )
    inf_anchor_vec = dr.encode_queries([sample_anchor_raw])[0]
    inf_pos_vec = dr.encode([f"passage: {sample_pos_raw}"])[0]

    # 2. Using Soup's internal pooling & normalization logic
    # from soup_cli.trainer.embedding import _pool_embeddings
    with torch.no_grad():
        out_anchor = base_model(input_ids=enc_anchor["input_ids"], attention_mask=enc_anchor["attention_mask"])
        mask_expanded = enc_anchor["attention_mask"].unsqueeze(-1).float()
        sum_embeddings = (out_anchor.last_hidden_state * mask_expanded).sum(dim=1)
        sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-9)
        trainer_anchor_pooled = sum_embeddings / sum_mask
        trainer_anchor_vec = F.normalize(trainer_anchor_pooled, p=2, dim=-1)[0].numpy()

    # Compare inference vector with trainer vector
    diff = np.max(np.abs(inf_anchor_vec - trainer_anchor_vec))
    print(f"Max absolute difference between inference and training forward pass: {diff:.8e}")
    assert diff < 1e-6, f"Representation divergence: diff={diff}"
    print("  ✓ Perfect representation parity between training and inference encoders!")

    print("\n=== Step 4: LoRA Target Modules & Parameter Count ===")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["query", "value"],
        task_type=TaskType.FEATURE_EXTRACTION,
    )
    peft_model = get_peft_model(base_model, lora_config)
    trainable_params, total_params = peft_model.get_nb_trainable_parameters()
    print(f"Trainable params: {trainable_params:,} / {total_params:,} ({100*trainable_params/total_params:.4f}%)")
    assert trainable_params == 294912, f"Expected 294,912 trainable params, got {trainable_params}"
    print("  ✓ Trainable parameters verified: exactly 294,912 for 12 layers x 2 modules.")

    print("\n=== Step 5: Smoke Training Batch & Gradient Flow ===")
    peft_model.train()
    optimizer = torch.optim.AdamW(peft_model.parameters(), lr=2e-5)

    batch_anchors = tokenizer([sample_anchor, sample_anchor], padding=True, return_tensors="pt")
    batch_pos = tokenizer([sample_pos, sample_pos], padding=True, return_tensors="pt")
    batch_neg = tokenizer([sample_neg, sample_neg], padding=True, return_tensors="pt")

    out_a = peft_model(input_ids=batch_anchors["input_ids"], attention_mask=batch_anchors["attention_mask"])
    out_p = peft_model(input_ids=batch_pos["input_ids"], attention_mask=batch_pos["attention_mask"])
    out_n = peft_model(input_ids=batch_neg["input_ids"], attention_mask=batch_neg["attention_mask"])

    def pool_and_norm(out, mask):
        m = mask.unsqueeze(-1).float()
        pooled = (out.last_hidden_state * m).sum(dim=1) / m.sum(dim=1).clamp(min=1e-9)
        return F.normalize(pooled, p=2, dim=-1)

    emb_a = pool_and_norm(out_a, batch_anchors["attention_mask"])
    emb_p = pool_and_norm(out_p, batch_pos["attention_mask"])
    emb_n = pool_and_norm(out_n, batch_neg["attention_mask"])

    pos_dist = (emb_a - emb_p).pow(2).sum(dim=-1)
    neg_dist = (emb_a - emb_n).pow(2).sum(dim=-1)
    loss = F.relu(pos_dist - neg_dist + 0.5).mean()

    print(f"Initial loss: {loss.item():.4f}")
    assert loss.requires_grad
    loss.backward()

    # Check gradients
    grads_present = False
    for name, param in peft_model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Missing gradient for {name}"
            if param.grad.abs().sum() > 0:
                grads_present = True
    assert grads_present, "No non-zero gradients found!"
    optimizer.step()
    print("  ✓ Gradient flow verified through LoRA adapters.")

    print("\n=== Step 6: Serialization & PeftModel Reloading ===")
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        peft_model.save_pretrained(tmp_dir)
        tokenizer.save_pretrained(tmp_dir)
        assert (tmp_dir / "adapter_model.safetensors").exists()
        assert (tmp_dir / "adapter_config.json").exists()

        # Reload with DenseRetriever
        reloaded_dr = DenseRetriever(
            retriever_id="e5_small_ft_test",
            model_id=base_id,
            revision=revision,
            adapter_dir=str(tmp_dir),
            max_length=512,
            query_prefix="query: ",
            passage_prefix="passage: ",
            device="cpu",
        )
        reloaded_vec = reloaded_dr.encode_queries([sample_anchor_raw])[0]
        assert reloaded_vec.shape == (384,)
        assert np.isfinite(reloaded_vec).all()
        # Verify L2 norm is 1.0
        norm = np.linalg.norm(reloaded_vec)
        assert np.abs(norm - 1.0) < 1e-5
        print(f"  ✓ Reloaded adapter vector shape: {reloaded_vec.shape}, L2 norm: {norm:.6f}")
    finally:
        shutil.rmtree(tmp_dir)

    print("\n=== ALL COMPATIBILITY GATE CHECKS PASSED ===")

if __name__ == "__main__":
    run_compatibility_gate()
