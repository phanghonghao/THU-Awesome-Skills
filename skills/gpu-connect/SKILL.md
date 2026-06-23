---
name: gpu-connect
description: >-
  Connect to a GPU server over SSH and report a one-shot read-only status
  snapshot — connectivity, identity, GPU utilization/memory/temp, disk, RAM,
  CPU load, conda envs. Default target is the A100 (`ssh a100`, user pan-hh,
  host yc-ai-node7); pass any configured alias (`autodl`, `spark`, `dreamzero`)
  or a raw command to run remotely. Use when the user mentions 连接服务器,
  连服务器, 登录GPU, ssh a100, 连上A100, gpu-connect, 看看GPU, nvidia-smi,
  机器状态, GPU状态, 显存.
---

# GPU Connect

Connect to a GPU server over SSH and report a one-shot read-only status snapshot.
A lightweight, general-purpose entry point — complementary to the heavier
`gpu-train` (RTX PRO 6000 + Slurm + orchestrator) and `autodl-5090` (AutoDL
monitor) skills. `gpu-connect` is just: pick a server, connect, show the machine
+ GPU state. It is deliberately smaller and mostly read-only.

## Invocation

`/gpu-connect [server] [-- cmd ...]` or `/gpu-connect [server] [flags]`.

| Arg | Meaning |
|-----|---------|
| *(none)* | connect default server `a100` and run the status snapshot |
| `a100` / `autodl` / `spark` / `dreamzero` | connect that configured alias |
| `--status` | (default) the full status snapshot |
| `--gpu` | GPU-only snapshot (just `nvidia-smi`) |
| `-- cmd …` | run an arbitrary command on the server and return output |
| `--shell` | print the exact `! ssh <alias>` line for the user to open an interactive shell |

Parsing: if the first token is a known alias, treat it as the server and default
to `a100` otherwise. Flag tokens (`--status` / `--gpu` / `--shell`) are stripped
from the command; anything after `--` is a raw remote command.

## Start Here

Read `references/servers.md` before issuing commands. It is the source of truth for:
- the SSH alias and host for each server
- the remote user and data directories
- whether a VPN is required
- conda location and storage rules

## Connection Policy

Run commands as `ssh <alias> '<remote command>'` (one-liners). All aliases are
passwordless and already configured in `~/.ssh/config`.

If SSH times out or is refused:
1. Retry up to 5 times, ~3 s apart.
2. For VPN-dependent hosts (`spark`, `dreamzero` — `59.66.25.192`, a Tsinghua IP),
   the connection needs iNode VPN; if so, point the user to the `gpu-train` skill's
   VPN launch policy instead of retrying forever.
3. `a100` and `autodl` are public/direct — no VPN. A failure usually means the box
   is down or restarting; a later retry typically succeeds.
4. Only report failure after all retries fail.

Interactive shells: Claude cannot hold an interactive SSH session through the Bash
tool. For an interactive login, print and instruct the user to run it with the `!`
prefix (e.g. `! ssh a100`). The `--shell` flag is exactly this.

## Operating Rules

- Default to **read-only** one-liners. Summarize, never dump raw output unless asked.
- Never kill a process or write/delete remote files without explicit confirmation.
- Respect each server's storage rules (see `references/servers.md`): on A100 write
  big files to `~/data`; on AutoDL to `/root/autodl-tmp`.
- For GPU checks, report util %, mem used/total, temp, and call out which GPUs are
  actually free (util < 10% **and** mem < 5% of total).
- On A100: before launching any GPU task, pick a device (`CUDA_VISIBLE_DEVICES`)
  and check `nvidia-smi` first. Never modify the shared `base` conda env.

## Core Task: status snapshot (default / `--status`)

One read-only round-trip (works across servers; tolerates missing `~/data`):

```bash
ssh <alias> '
  echo "=== HOST ===";  whoami; hostname; uptime;
  echo "=== GPU ===";   nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader;
  echo "=== DISK ===";  df -h ~ 2>/dev/null; df -h ~/data 2>/dev/null;
  echo "=== MEM ===";   free -h;
  echo "=== LOAD ===";  cat /proc/loadavg; echo "cores: $(nproc)";
  echo "=== CONDA ==="; { command -v conda >/dev/null 2>&1 && conda env list; } || { source /opt/miniconda3/etc/profile.d/conda.sh 2>/dev/null && conda env list; } || { source /etc/bash.bashrc 2>/dev/null && conda env list; } || echo "(conda 未找到)";
'
```

Report, in this order:
1. **Connectivity** — connected? alias + host + remote user (one line).
2. **GPU** — per-GPU util, mem used/total, temp; which GPUs are free.
3. **Disk / RAM / CPU** — home + data dir usage (A100), RAM available, loadavg vs cores.
4. **conda envs** — list available envs (A100: shared `/opt/miniconda3`).
5. **One-line verdict in Chinese** — 机器是否可用、有没有空闲 GPU、要不要等。

## Core Task: `--gpu`

GPU-only:
```bash
ssh <alias> 'nvidia-smi'
```
Summarize utilization, memory, temperature, and free GPUs.

## Core Task: run a custom command — `-- cmd …`

Run the given command remotely and return its output:
```bash
ssh <alias> '<cmd>'
```
Prefix with `cd ~/data && ` for data-dir work on A100 when appropriate.

## Core Task: interactive shell — `--shell`

Print the command for the user to open an interactive session themselves:
```
! ssh <alias>
```
(Claude can't hold interactive shells via the Bash tool — the user must run it.)

## Response Style

1. Current state (connected? healthy?)
2. Key metrics (GPU, disk, RAM)
3. One-line Chinese health verdict
4. Recommended next action only if something needs attention

Keep it concise. No raw dumps unless explicitly asked.
