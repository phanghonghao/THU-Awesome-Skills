"""Synthetic seq2seq task: sequence reversal.

Replaces the paper's WMT translation task, which needs a multi-GB download
plus spacy + torchtext (the latter is deprecated and won't install on
Python 3.14). Zero download, instant, CPU-friendly.

The model must learn — via attention alone — to emit the input digits in
reverse order. That is a non-trivial positional mapping (output position i
must attend to input position N-i), so it actually exercises the
self/cross attention mechanisms instead of being solvable by an identity.
"""
import torch

# Special tokens (indices must stay below the digit range).
PAD, SOS, EOS = 0, 1, 2
NUM_SPECIAL = 3


def make_batch(batch_size, seq_len, vocab_digits, device="cpu"):
    """One batch of (src, tgt_in, tgt_out) for the reversal task.

    src      = [d0 d1 ... dN EOS]
    tgt_in   = [SOS dN ... d1]            (teacher forcing input)
    tgt_out  = [dN ... d1 d0 EOS]         (targets to predict)
    """
    digit_low = NUM_SPECIAL
    digit_high = digit_low + vocab_digits
    seq = torch.randint(digit_low, digit_high, (batch_size, seq_len))
    src = torch.cat([seq, torch.full((batch_size, 1), EOS, dtype=torch.long)], dim=1)

    rev = torch.flip(seq, dims=[1])
    tgt_full = torch.cat(
        [
            torch.full((batch_size, 1), SOS, dtype=torch.long),
            rev,
            torch.full((batch_size, 1), EOS, dtype=torch.long),
        ],
        dim=1,
    )
    tgt_in = tgt_full[:, :-1]
    tgt_out = tgt_full[:, 1:]
    return src.to(device), tgt_in.to(device), tgt_out.to(device)
