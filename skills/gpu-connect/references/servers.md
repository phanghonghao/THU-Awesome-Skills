# GPU server registry

Source of truth for the servers `gpu-connect` targets. All aliases are configured
in `~/.ssh/config` and are passwordless (key auth).

## a100 — ATEC A100 (primary, default)

- **Alias**: `ssh a100`
- **Host**: `220.200.151.154:60322` (public, direct — **no VPN**)
- **User**: `pan-hh` (remote hostname `yc-ai-node7`)
- **Key**: `~/.ssh/id_ras`
- **Storage**:
  - home: `/home/pan-hh` — small files, configs only
  - data: `~/data` → `/data/pan-hh` — datasets, models, logs, experiment outputs
  - Users are isolated; never touch other users' dirs.
- **conda**: shared Miniconda at `/opt/miniconda3`. If `conda` is not on PATH,
  run `source /etc/bash.bashrc`. **Never modify the shared `base` env** — create
  your own (`conda create -n <env> python=3.10`).
- **GPU**: multiple GPUs — always pick a device before launching
  (`CUDA_VISIBLE_DEVICES=<id>`); check `nvidia-smi` first. Long tasks → `tmux`.
  Don't kill others' processes, no casual `sudo`.
- **TensorBoard**: tunnel, never expose to the public net —
  `ssh -L 6006:localhost:6006 a100`, then `tensorboard --logdir <dir> --port 6006`
  on the box; open `http://localhost:6006` locally.
- **Full guide**: `D:\Desktop_Files\ATEC_TsingYun\A100_connect.md`

## autodl — AutoDL RTX 5090

- **Alias**: `ssh autodl`
- **Host**: `connect.bjb2.seetacloud.com:17559` (public — **no VPN**)
- **User**: `phh` (same person as `pan-hh`, same `id_ras` key)
- **Storage**: everything under `/root/autodl-tmp`. Never write to the system disk
  (`/`, `/tmp`, `/usr`, `/opt`, `/root`, `/var/tmp`) — quota limits.
- **GPU**: single RTX 5090 (32 GB, Blackwell), only `cuda:0`.
- **Deeper monitoring** (tail logs, training status, ETA) → use the `autodl-5090`
  skill, not `gpu-connect`.

## spark / dreamzero — Tsinghua RTX (VPN required)

- **Aliases**: `ssh spark`, `ssh dreamzero`
- **Host**: `59.66.25.192` (Tsinghua IP — **iNode VPN required**)
- **User**: `zentek`
- **Keys**: `~/.ssh/id_ed25519_spark` (spark), `~/.ssh/id_rsa_dreamzero` (dreamzero)
- **VPN**: if SSH times out or is refused, launch iNode first — see the `gpu-train`
  skill's Connection Policy. For training / Slurm / orchestrator work, use
  `gpu-train`, not here.

## Notes

- Default server for `/gpu-connect` with no argument is **a100**.
- The same person is `pan-hh` on A100 and `phh` on AutoDL — both use `~/.ssh/id_ras`.
  The default `id_ed25519` key is **not** registered on either; always go through
  the configured alias so the right `id_ras` key is used.
- To add a server: add a `~/.ssh/config` alias, then add an entry here so
  `gpu-connect` knows the host / user / storage / VPN rules.
