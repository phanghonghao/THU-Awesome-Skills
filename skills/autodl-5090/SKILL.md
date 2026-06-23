---
name: autodl-5090
description: >-
  Lightweight, read-only monitor for RL training on the AutoDL RTX 5090 box over
  SSH. Two jobs selected by flags: `--tail` to follow the live training logs
  (G1 AMP, Z1 AMP, Z1 Isaac Lab) and snapshot iteration / speed / ETA / metrics,
  and `--status` for a one-shot CPU+load / RAM / disk-quota / GPU snapshot of the
  single RTX 5090. Canonical call: `/autodl-5090 --tail --status` (both at once).
  Use when the user mentions autodl, 5090, --tail, --status, tail logs, 看看训练,
  训练日志, 训练进度, iteration, ETA, steps/s, CPU占用, 显存, GPU状态, 磁盘配额,
  机器忙不忙, G1 AMP, Z1 AMP, MJLAB.
---

# AutoDL 5090

Lightweight, read-only monitor for RL training on the shared AutoDL RTX 5090 box.
Two read-only jobs, picked by flags.

This is deliberately smaller than `gpu-train` (which targets the 8-GPU RTX PRO 6000
with Isaac Sim + Slurm + orchestrator + video pipeline). The AutoDL box has a
**single RTX 5090 (32 GB, Blackwell)**, no Slurm, no orchestrator, no VPN — just
`ssh autodl` and read-only inspection.

## Invocation

Call as `/autodl-5090 <flags>`. Flags select which job(s) to run:

| Flag | Action |
|------|--------|
| `--tail` | follow the live training log(s) and summarize progress |
| `--status` | one-shot CPU / RAM / disk / GPU snapshot |
| *(no flag)* | run **both** `--tail` and `--status` |
| `--tail z1` / `--tail g1` / `--tail isaac` | tail one project only |

Combine freely — `/autodl-5090 --tail --status` is the default full snapshot.

## Start Here

Read `references/platforms.md` before issuing commands. It is the source of truth for:

- the `ssh autodl` alias and host
- the single-GPU layout (only `cuda:0`)
- per-project log paths and run directories
- the process-detection pattern
- AutoDL disk / quota rules

## Connection

`ssh autodl` is passwordless → `connect.bjb2.seetacloud.com:17559` (user `phh`).
**No VPN needed** (unlike `gpu-train`'s RTX server).

If SSH times out or is refused:
1. Retry up to 5 times, ~3 s apart.
2. The AutoDL container may be restarting; a later retry usually succeeds.
3. Only report failure after all retries fail.

## Operating Rules

- Default to **read-only** one-liners over SSH. Summarize, don't dump.
- For `--tail`, show a compact per-training snapshot (not the raw log) unless the user asks for raw lines.
- For `--status`, show overall box state **and** call out my own training procs separately.
- Never kill a training process or write/delete remote files without explicit user confirmation.
- Respect AutoDL quotas: never write/checkpoint to the system disk (`/`, `/tmp`, `/usr`, `/opt`, `/root`, `/var/tmp`). Everything lives under `/root/autodl-tmp`.

## Core Task: `--tail` — follow the logs / training status

Auto-detect the running training(s), tail the matching log, summarize.

**Detect what's running:**
```bash
ssh autodl 'ps -eo pid,etime,cmd | grep "train.py" | grep -v grep'
```

**Tail the matching log** (project → log map in `references/platforms.md`). Default window 30 lines:
```bash
ssh autodl 'tail -30 <LOG_PATH>'
```

Per training, report:
- **PID + elapsed** (from `ps`)
- **project / task** — `Z1-AMP-Flat`, `Unitree-G1-AMP-Flat`, `Magiclab-Z1-12dof-Velocity`…
- **total timesteps** and **iteration time**
- **ETA** (when printed)
- **key metrics** — for AMP runs: `slip_velocity_mean` and termination ratios (`bad_orientation`, `bad_base_height`, `time_out`); for Isaac Lab Z1: reward + tracking + episode length
- **one-line health note in Chinese**, e.g. `Z1 稳定推进，ETA 4h，无异常终止`

With `--tail z1` / `--tail g1` / `--tail isaac`, tail only that project. Bare `--tail` tails every detected training.

## Core Task: `--status` — host + GPU snapshot

Single read-only round-trip:
```bash
ssh autodl '
  echo "=== GPU ==="; nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader;
  echo "=== CPU ==="; cat /proc/loadavg; echo "cores: $(nproc)";
  echo "=== MEM ==="; free -h;
  echo "=== DISK (/root/autodl-tmp) ==="; df -h /root/autodl-tmp;
  echo "=== MY TRAINING PROCS ==="; ps -eo pid,etime,pcpu,pmem,cmd | grep train.py | grep -v grep;
'
```

Report:
- **GPU**: the single 5090's util %, mem used/total (32 GB), temp. All my trainings share `cuda:0`, so concurrent runs divide throughput.
- **CPU**: 1/5/15-min loadavg vs `nproc` (shared box — load may include other users).
- **RAM**: used / available.
- **Disk**: `/root/autodl-tmp` use %; flag if `~/projects` grows toward the 100 GB/user quota.
- **My procs**: which of my trainings are actually consuming CPU/GPU.

End with a one-line verdict: box healthy? anything near a limit? should envs scale up or down?

## Response Style

For both commands, lead with:
1. Current state (running? healthy?)
2. Key metrics
3. One-line health / limit verdict
4. Recommended next action (only if something needs attention)

Keep it concise. No raw dumps unless explicitly asked.

## Project Families

| Family | Task | Train log | Stack |
|--------|------|-----------|-------|
| Z1 AMP | `Z1-AMP-Flat` | `~/projects/Z1_AMP_MJLAB_train_*.log` | MJLAB (MuJoCo) + AMP |
| G1 AMP | `Unitree-G1-AMP-Flat` | `~/projects/AMP_mjlab_train_*.log` | MJLAB + AMP |
| Z1 Isaac Lab | `Magiclab-Z1-12dof-Velocity` | nohup log under `~/`, runs under `~/projects/magiclab_rl_lab/` | Isaac Lab + rsl-rl |

Exact run-directory paths and the full log map live in `references/platforms.md`.
