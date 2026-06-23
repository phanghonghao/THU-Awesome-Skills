"""Minimal Transformer (Vaswani et al. 2017, 'Attention Is All You Need').

This IS the paper's contribution: a seq2seq model built ONLY from attention
(no recurrence, no convolution). Faithful to the paper's design:

  - sinusoidal positional encoding
  - scaled dot-product multi-head attention
  - encoder-decoder (masked self-attn + cross-attn)
  - position-wise feed-forward, residual + LayerNorm

Trimmed to a tiny config so it runs on pure CPU in seconds. See train.py.
"""
import math
import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Fixed sinusoidal positional encoding (paper eq. 6)."""

    def __init__(self, d_model, max_len=512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x):
        # x: (B, T, d_model)
        return x + self.pe[:, : x.size(1)]


class MultiHeadAttention(nn.Module):
    """Scaled dot-product multi-head attention (paper 3.2.2)."""

    def __init__(self, d_model, n_head):
        super().__init__()
        assert d_model % n_head == 0
        self.n_head = n_head
        self.d_k = d_model // n_head
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

    def forward(self, q, k, v, mask=None):
        B = q.size(0)
        q = self.w_q(q).view(B, -1, self.n_head, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(B, -1, self.n_head, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(B, -1, self.n_head, self.d_k).transpose(1, 2)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))
        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(B, -1, self.n_head * self.d_k)
        return self.w_o(out)


class FeedForward(nn.Module):
    """Position-wise feed-forward (paper 3.3): Linear-ReLU-Linear."""

    def __init__(self, d_model, d_ff):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.ReLU(), nn.Linear(d_ff, d_model)
        )

    def forward(self, x):
        return self.net(x)


class EncoderLayer(nn.Module):
    def __init__(self, d_model, n_head, d_ff, dropout=0.1):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ff = FeedForward(d_model, d_ff)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        x = self.norm1(x + self.drop(self.attn(x, x, x, mask)))
        x = self.norm2(x + self.drop(self.ff(x)))
        return x


class DecoderLayer(nn.Module):
    def __init__(self, d_model, n_head, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, n_head)
        self.cross_attn = MultiHeadAttention(d_model, n_head)
        self.ff = FeedForward(d_model, d_ff)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x, enc_out, tgt_mask=None, src_mask=None):
        x = self.norm1(x + self.drop(self.self_attn(x, x, x, tgt_mask)))
        x = self.norm2(x + self.drop(self.cross_attn(x, enc_out, enc_out, src_mask)))
        x = self.norm3(x + self.drop(self.ff(x)))
        return x


class Transformer(nn.Module):
    """Full encoder-decoder Transformer (paper fig. 1, left+right)."""

    def __init__(self, src_vocab, tgt_vocab, d_model=64, n_head=2, n_layer=2,
                 d_ff=256, dropout=0.1, max_len=128, pad_idx=0):
        super().__init__()
        self.pad_idx = pad_idx
        self.src_emb = nn.Embedding(src_vocab, d_model)
        self.tgt_emb = nn.Embedding(tgt_vocab, d_model)
        self.pos = PositionalEncoding(d_model, max_len)
        self.enc_layers = nn.ModuleList(
            [EncoderLayer(d_model, n_head, d_ff, dropout) for _ in range(n_layer)]
        )
        self.dec_layers = nn.ModuleList(
            [DecoderLayer(d_model, n_head, d_ff, dropout) for _ in range(n_layer)]
        )
        self.norm = nn.LayerNorm(d_model)
        self.out = nn.Linear(d_model, tgt_vocab)

    def encode(self, src):
        # pad mask: (B, 1, 1, T_src) — 0 at pad positions
        mask = (src != self.pad_idx).unsqueeze(1).unsqueeze(1)
        x = self.pos(self.src_emb(src))
        for layer in self.enc_layers:
            x = layer(x, mask)
        return self.norm(x), mask

    def decode(self, tgt, enc_out, src_mask):
        T = tgt.size(1)
        pad_mask = (tgt != self.pad_idx).unsqueeze(1).unsqueeze(1)  # (B,1,1,T)
        causal = torch.tril(torch.ones(T, T, device=tgt.device)).bool()  # (T,T)
        tgt_mask = pad_mask & causal  # (B,1,T,T)
        x = self.pos(self.tgt_emb(tgt))
        for layer in self.dec_layers:
            x = layer(x, enc_out, tgt_mask, src_mask)
        return self.norm(x)

    def forward(self, src, tgt):
        enc_out, src_mask = self.encode(src)
        dec_out = self.decode(tgt, enc_out, src_mask)
        return self.out(dec_out)
