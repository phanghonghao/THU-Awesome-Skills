---
name: sys-health
description: >-
  One-shot read-only health snapshot for THIS machine (AMD Ryzen 7 8745HS
  laptop, CPU-only RL training in WSL2). Probes CPU load, memory, swap, disk
  usage, SSD write activity from checkpoints, active training-process
  detection, and the Windows host (CPU/disk/GPU). Tells you whether a UniLab
  run is hammering the box and what is wearing out (heat, SSD writes, C: drive
  space). Use when the user asks about 本机情况, 系统状态, 系统体检, 机器性能,
  训练对电脑的影响, 电脑吃得消吗, 散热, CPU温度, 内存占用, 磁盘空间, SSD损耗,
  占用多少, check the system, host status, how is the machine doing, is training
  stressing the PC.
---

# sys-health

One-shot system health snapshot for this UniLab dev laptop. RL training here is
**CPU-only and runs inside WSL2**. A long run stresses three things, in order
of risk for a laptop:

1. **Heat** — sustained 100%-on-all-cores cooks a mobile CPU.
2. **SSD write endurance** — every `model_*.pt` checkpoint and tfevents line is
   a write; small `save_interval` × many iters = real wear.
3. **C: drive space** — the WSL2 ext4 filesystem is a `.vhdx` that lives on C:;
   if C: fills, the vhdx can't grow and training crashes mid-run.

This skill measures all three in one command (heat needs one-time setup, below).

## How to invoke

```bash
wsl -d Ubuntu -u u20174 -- bash -c \
  "tr -d '\r' < /mnt/c/Users/20174/.claude/skills/sys-health/check_sys.sh | bash" 2>/dev/null
```

- `tr -d '\r'` makes the script immune to CRLF a Windows editor may introduce.
- `2>/dev/null` mutes the WSL localhost-proxy Chinese-garbage warning.
- The script is **read-only and idempotent** — safe to run anytime, including
  mid-training.

After it prints, give the user a **one-paragraph health verdict + the single
most important action** (see Interpretation). Do not just dump the raw output.

## Sections & how to read them

| Section | Healthy | Watch / Act |
|---|---|---|
| Load (1/5/15 min) | below 16 sustained | 15-min load pinned near/over 16 = box fully committed; nothing else runs well |
| MEMORY & SWAP | Swap `0B` used, available > 2GB | Swap in use = training spilling to SSD (slow + wear). Low available RAM → reduce `algo.num_envs` |
| DISK USAGE | Use% < 80% | > 85% → clean up; this ext4 is the WSL vhdx |
| TOP CPU PROCESSES | see what's running | a `python` at ~`cores×100%` for a long ELAPSED = a UniLab run is active (note the run path under TRAINING WRITE ACTIVITY) |
| TRAINING WRITE ACTIVITY | few files in last 10 min | every listed file = an SSD write; checkpoint `size × save_interval × iters` = cumulative wear |
| NVMe SMART | Data Units Written low, temp < 65°C | only works after `sudo apt install nvme-cli` (see Gaps) |
| WINDOWS MEMORY | plenty free | tight free + large Used → check what's hogging RAM |
| WINDOWS PHYSICAL DISKS | `Status: OK` | — |
| WINDOWS VOLUMES | C: Free > 60GB | C: < 40GB risky — vhdx + pagefile live here and grow with training data |
| WINDOWS CPU TEMP | < 85°C (laptop) | needs LibreHardwareMonitor; without it, temp is the one signal this skill can't see |

## Known gaps (and the one-time fixes)

- **CPU temperature** is invisible by default. WSL2's virtual kernel does not
  expose host CPU temp, and stock Windows WMI hides it. This is the #1 laptop
  risk signal, so enable it once:
  1. Install **LibreHardwareMonitor** (free), launch it, enable its **WMI**
     provider (and ideally run at startup).
  2. Re-run this skill — the WINDOWS CPU TEMP section auto-detects it via the
     `root/LibreHardwareMonitor` namespace. No script edit needed.
- **SSD wear numbers** (bytes written, % life left) need `nvme-cli` + sudo.
  Until then the script reports *proxies*: checkpoint count/size and recent
  write activity. For real numbers:
  `sudo apt install nvme-cli`, then re-run.

## Verdict guidance tuned to THIS box

- **It's a laptop** (8745HS mobile APU, no discrete GPU). Heat is the real risk
  under long CPU-only runs. Until LibreHardwareMonitor is on, recommend:
  elevate the laptop, keep vents clear, run in a cool room, and consider not
  pegging all 16 threads 100% (smaller `num_envs`).
- RAM ~14GB in WSL / ~28GB on host — memory is not the bottleneck; do **not**
  let training swap.
- The Samsung 1TB NVMe is roomy but an OEM low-power part with modest write
  endurance — checkpoint spam (very small `save_interval`) is the main wear
  source. Move old checkpoints off the SSD (see `checkpoints/` convention in
  the project CLAUDE.md).
- If C: drops under ~40GB free, move/clean **before** starting a long run,
  not after it crashes.

## Files

- `check_sys.sh` — the probe script (read-only, idempotent, safe anytime).
  Edit the probe list here if new hardware is added or a section misbehaves.
