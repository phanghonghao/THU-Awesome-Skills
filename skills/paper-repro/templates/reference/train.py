"""Minimal-reproduction training loop for 'Attention Is All You Need'.

Runs on PURE CPU. Validates the paper's central claim: a model built only
from attention (no RNN/CNN) can learn a seq2seq mapping.

Includes the paper's actual training tricks so the minimal run is faithful:
  - Noam learning-rate warmup schedule (paper 5.3)
  - label smoothing (paper 5.4, eps=0.1)
"""
import argparse
import csv
import time

import torch
import torch.nn.functional as F

from model import Transformer
from data import make_batch, PAD, NUM_SPECIAL


def label_smoothing_loss(logits, target, smoothing=0.1, ignore_index=PAD):
    """Cross-entropy with label smoothing (paper 5.4)."""
    logp = F.log_softmax(logits, dim=-1)                      # (B,T,V)
    nll = -logp.gather(2, target.unsqueeze(-1)).squeeze(-1)   # (B,T)
    smooth = -logp.mean(dim=-1)                               # uniform part
    mask = (target != ignore_index).float()
    loss = ((1 - smoothing) * nll + smoothing * smooth) * mask
    return loss.sum() / mask.sum()


@torch.no_grad()
def evaluate(model, vocab_digits, seq_len, device, batches=20, batch_size=64):
    model.eval()
    correct_tokens, total_tokens, exact, total_seq = 0, 0, 0, 0
    for _ in range(batches):
        src, tgt_in, tgt_out = make_batch(batch_size, seq_len, vocab_digits, device)
        pred = model(src, tgt_in).argmax(-1)
        mask = tgt_out != PAD
        correct_tokens += ((pred == tgt_out) & mask).sum().item()
        total_tokens += mask.sum().item()
        exact += (((pred == tgt_out) | ~mask).all(dim=1)).sum().item()
        total_seq += batch_size
    model.train()
    return correct_tokens / max(total_tokens, 1), exact / max(total_seq, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=600)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seq_len", type=int, default=8)
    p.add_argument("--vocab_digits", type=int, default=10)
    p.add_argument("--d_model", type=int, default=64)
    p.add_argument("--n_head", type=int, default=2)
    p.add_argument("--n_layer", type=int, default=2)
    p.add_argument("--d_ff", type=int, default=256)
    p.add_argument("--warmup", type=int, default=100)
    p.add_argument("--eval_every", type=int, default=50)
    p.add_argument("--log", type=str, default="train_log.csv")
    args = p.parse_args()

    device = "cpu"
    V = NUM_SPECIAL + args.vocab_digits
    model = Transformer(
        V, V, args.d_model, args.n_head, args.n_layer, args.d_ff,
        max_len=128, pad_idx=PAD,
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[config] vocab={V} d_model={args.d_model} heads={args.n_head} "
          f"layers={args.n_layer} d_ff={args.d_ff} steps={args.steps} device={device}")
    print(f"[config] params={n_params:,}")

    opt = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(0.9, 0.98), eps=1e-9)
    rows, t0 = [], time.time()
    for step in range(1, args.steps + 1):
        # Noam schedule (paper eq. 3.6 in 5.3)
        lr = args.d_model ** -0.5 * min(step ** -0.5, step * args.warmup ** -1.5)
        for g in opt.param_groups:
            g["lr"] = lr
        src, tgt_in, tgt_out = make_batch(args.batch_size, args.seq_len, args.vocab_digits, device)
        logits = model(src, tgt_in)
        loss = label_smoothing_loss(logits, tgt_out)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step == 1 or step % args.eval_every == 0:
            tok_acc, seq_acc = evaluate(model, args.vocab_digits, args.seq_len, device)
            el = time.time() - t0
            print(f"step {step:4d} | loss {loss.item():.4f} | tok_acc {tok_acc:.3f} "
                  f"| seq_acc {seq_acc:.3f} | lr {lr:.2e} | {el:.1f}s")
            rows.append((step, loss.item(), tok_acc, seq_acc, lr, el))

    tok_acc, seq_acc = evaluate(model, args.vocab_digits, args.seq_len, device, batches=50)
    print(f"[FINAL] token_acc={tok_acc:.3f} seq_acc={seq_acc:.3f} ({time.time()-t0:.1f}s)")
    rows.append((args.steps, float("nan"), tok_acc, seq_acc, float("nan"), time.time() - t0))

    with open(args.log, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step", "loss", "token_acc", "seq_acc", "lr", "elapsed_s"])
        w.writerows(rows)
    print(f"[done] log -> {args.log}")


if __name__ == "__main__":
    main()
