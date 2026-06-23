---
name: unilab-train
description: >-
  Monitor and manage UniLab RL training on local WSL (CPU-only, no CUDA).
  Check training status, tail logs with key metrics, find best checkpoint,
  manage viser / TensorBoard viewers, resume interrupted runs, record Motrix demos.
  Use when user mentions: unilab, UniLab, /unilab-train, WSL training, G1 training,
  Go2 training, PPO training, SAC training, 训练状态, 训练日志, tail log,
  训练监控, best ckpt, resume training, viser, mujoco viewer, tensorboard,
  curriculum, reward tracking, episode length, action std,迁移训练.
---

# UniLab Train

Monitor and manage UniLab RL training jobs on local WSL Ubuntu 24.04 (CPU only).

## Start Here

Read `references/platforms.md` before issuing any command that depends on:
- WSL invocation template
- Log paths (training log + run dir)
- Checkpoint paths (WSL + Windows mirror)
- Resume semantics (`max_iterations` is **additional**, not total)
- Viewer commands (viser / MuJoCo native / TensorBoard)
- Common gotchas (HF_ENDPOINT mandatory, save_interval=50, viser rgba bug, etc.)

Treat `references/platforms.md` as the source of truth for platform-specific paths and commands.

## Operating Rules

- All commands run via `wsl -d Ubuntu -u u20174 -- bash -c "..."` wrapper.
- The wrapper prints a Chinese garbage warning on every invocation — ignore it, never try to "fix" it.
- Always prefix `HF_ENDPOINT=https://hf-mirror.com` for any command that might trigger HF download.
- Prefer compact metric snapshots over raw log dumps. Offer raw dump only if user asks.
- Health assessment: provide a one-line Chinese verdict + concrete next action.
- Never kill training without explicit user confirmation.
- For resume: use `algo.load_run=<path>`, NEVER `resume=true` (UniLab has no such flag).

## Slash-Flag Invocation

User may invoke via `/unilab-train` with optional flags. Interpret the flags as intent:

| Flag | Action |
|---|---|
| (none) or `--status` | Quick health snapshot — is training alive, current iter, ETA, 1-line verdict |
| `--tail` | Detailed tail of latest training log + metric trend analysis |
| `--metrics` | Full metric table extraction (all reward components + losses + curriculum) |
| `--best` | Find best ckpt via tfevents parse, identify nearest saved model_*.pt |
| `--resume <run_dir>` | Resume training from a saved ckpt (remind about max_iterations semantics) |
| `--viser [port]` | Start viser on given port (default 8080); report URL |
| `--mjc` | Start MuJoCo native viewer via WSLg (real-time GLFW window) |
| `--tb` | Start TensorBoard on port 6006 if not already running |
| `--record <demo>` | Record Motrix demo mp4 (play_env_num=1, calculate play_steps from motion length) |

If user passes an unknown flag, treat it as conversational intent and ask for clarification.

## Core Tasks

### Check connectivity

```bash
wsl -d Ubuntu -u u20174 -- bash -c "echo OK && uptime"
```

### Check training status (`--status`)

Detect from process list:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "ps aux | grep -E 'train|play_viser|play_interactive|tensorboard' | grep -v grep"
```

Report:
- training running or not
- PID and elapsed time
- algo (ppo / sac / appo)
- task and sim
- active log file path
- background services (viser / TB) alive?

If nothing is running but log file mtime is recent (<5 min), training may have just finished — check the log tail for "Saving model" or completion message.

If log mtime is >5 min stale while process supposedly running, suspect silent crash or WSL restart — verify with `ps`.

### Tail log (`--tail`)

**Primary use case.** Read active training log and extract structured metrics.

Step 1 — find latest training log:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "ls -t /home/u20174/UniLab/logs/*.log 2>/dev/null | head -3"
```

If user named the run explicitly (e.g. `g1_walk_migrated_resume.log`), use that. Otherwise pick the most recent.

Step 2 — extract last ~50 lines containing key metrics:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "tail -200 /home/u20174/UniLab/logs/<LOG> | grep -E 'Learning iteration|Mean reward|Mean action std|Mean episode|Steps per|Collection time|Learning time|ETA|reward/tracking|reward/alive|reward/feet_phase|reward/penalty|reward/pose|curriculum/|Mean value|Mean surrogate|Mean entropy'"
```

Step 3 — present compact snapshot (NOT raw dump):

```
== Training: <run_name> ==
iter X/Y | elapsed HH:MM:SS | ETA HH:MM:SS
throughput: N steps/s | collection: X.Xs | learning: X.Xs

== Reward ==
Mean reward: CURRENT (trend: was A iter N iters ago → now B, Δ)
  tracking_lin_vel:    X.XX    ← main forward signal
  tracking_ang_vel:    X.XX
  feet_phase:          X.XX
  alive:              XX.XX    ← survival bonus
  penalty_action_rate:-XX.XX   ← should decrease as std drops
  penalty_orientation:-X.XX
  penalty_ang_vel_xy: -X.XX
  pose:               -X.XX

== Policy ==
action_std: X.XX (was 1.0 at start, target 0.2-0.4)
value_loss: X.XX | surrogate: -X.XX | entropy: X.XX | lr: X.XXe-X

== Curriculum ==
penalty_scale: X.XX (range 0.5-1.0)
avg_episode_length: X.X (max = max_episode_steps)
```

Step 4 — one-line Chinese health verdict + next action:

- **健康**: "Reward 持续上涨，action_std 收敛中，按 ETA X 小时完成。无需干预。"
- **警告**: "Episode length 卡在 X，curriculum 未升级。可能需要降噪声或放宽 termination。"
- **危险**: "Reward 不涨反跌 / action_std 卡在 1.0 / learning_time >5s。建议停训调参。"
- **中断**: "训练 log X 分钟没更新，进程已死。WSL 可能重启。需要 resume from model_XXX.pt。"

### Full metrics extraction (`--metrics`)

Same as `--tail` but show full metric table including all sub-rewards, losses, and curriculum state. Useful for comparing runs.

### Find best checkpoint (`--best`)

```bash
wsl -d Ubuntu -u u20174 -- bash -c "cd /home/u20174/UniLab && /home/u20174/.local/uv run --no-sync python << 'EOF'
from tensorboard.backend.event_processing import event_accumulator
ea = event_accumulator.EventAccumulator('<RUN_DIR>', size_guidance={'scalars': 0})
ea.Reload()
events = ea.Scalars('Train/mean_reward')
best = max(events, key=lambda e: e.value)
print(f'Best iter: {best.step}, reward: {best.value:.4f}')
# also print top 5 for context
top5 = sorted(events, key=lambda e: -e.value)[:5]
for e in top5:
    print(f'  iter {e.step}: {e.value:.4f}')
EOF"
```

Then find nearest saved ckpt (multiples of 50):

```bash
wsl -d Ubuntu -u u20174 -- bash -c "ls /home/u20174/UniLab/logs/rsl_rl_ppo/<Task>/<run_dir>/model_*.pt | sort"
```

Pick `model_<nearest_50_below_best>.pt`. Copy to Windows:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "cp /home/u20174/UniLab/logs/.../model_XXXX.pt /mnt/d/Desktop_Files/UniLab/checkpoints/<task>/<sim>/model_XXXX.pt"
```

### Resume training (`--resume <run_dir>`)

```bash
wsl ... train --algo ppo --task <task> --sim <sim> \
  algo.load_run=<RUN_DIR> \
  algo.max_iterations=<N> training.no_play=true \
  > /home/u20174/UniLab/logs/<run_name>_resume.log 2>&1
```

**Critical**: warn user that `max_iterations` is **additional**, not total. If they want total 3000 starting from iter 500, set `max_iterations=2500`.

What gets restored: network weights, optimizer state, normalization stats, action_std, curriculum state, iter counter.
What resets: env RNG (acceptable for PPO).

### viser (`--viser`)

```bash
wsl ... uv run python scripts/play_viser.py \
  task=<task>/mujoco \
  interactive.action_mode=policy \
  algo.load_run=<RUN_DIR> \
  viser.port=<PORT> \
  > /home/u20174/UniLab/logs/viser_<tag>.log 2>&1 &
```

Open `http://localhost:<PORT>` in Windows browser. Ctrl+Shift+R to refresh.

If colors look wrong: viser reads `geom_rgba` directly, not material rgba. Edit XML to add explicit `rgba="..."` on each geom.

### MuJoCo native viewer (`--mjc`)

```bash
wsl ... bash -c "export DISPLAY=:0 && uv run python scripts/play_interactive.py \
  --algo ppo --task <task> --sim mujoco \
  algo.load_run=<RUN_DIR> \
  interactive.action_mode=policy"
```

Opens GLFW window via WSLg. Materials work correctly (no rgba hack). Controls: Space=pause, N=step, +/-=speed, Esc=quit.

If window immediately closes with "Done." in log, DISPLAY may be unset — explicitly `export DISPLAY=:0`.

### TensorBoard (`--tb`)

```bash
wsl ... uv run tensorboard --logdir /home/u20174/UniLab/logs --port 6006 --bind_all \
  > /home/u20174/UniLab/logs/tb.log 2>&1 &
```

Open `http://localhost:6006`. **Restart TB after starting a new training run** — its data server doesn't auto-discover new subdirs.

### Record Motrix demo (`--record`)

```bash
wsl ... eval --algo ppo --task <task> --sim motrix \
  --render-mode record \
  training.play_env_num=1 training.play_steps=<SECONDS × 50> \
  algo.load_run=<RUN_DIR>
```

Output: `src/unilab/assets/checkpoints/<demo>/play_video.mp4`. Copy to Windows:

```bash
wsl ... bash -c "cp .../play_video.mp4 /mnt/d/Desktop_Files/UniLab/videos/<task>/motrix/model_0.mp4"
```

Known motion durations (frames @ 50Hz):
- dance: 870 (17.4s)
- wallflip: 198 (4.0s)
- boxtracking: 725 (14.5s)

## Response Style

Order:
1. Current state (alive? iter X/Y? ETA?)
2. Key metrics (reward + main components)
3. Health verdict (one-line Chinese)
4. Recommended next action

Keep concise unless user asks for full raw logs or full metric tables.

## Common Issues Quick Reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `--load-run must be '-1' or dir name` | CLI flag rejects paths | Use Hydra override `algo.load_run=<path>` |
| `Could not override 'resume'` | UniLab has no resume flag | Just `algo.load_run=<path>` (no resume=true) |
| `HF download RuntimeError: client closed` | hf_hub 1.18.0 bug + GFW | `HF_ENDPOINT=https://hf-mirror.com` prefix |
| `uv sync --extra viser` removes motrix | uv sync matches exactly | `uv sync --extra viser --extra motrix` |
| TB not showing new run | data server caches subdir list | Restart TB process |
| viser color wrong | rgba bug | Add explicit `rgba="..."` to geom XML |
| MuJoCo viewer exits immediately | DISPLAY not propagated | `export DISPLAY=:0` before uv run |
| Motrix mp4 only 1.6s | play_steps too small | `play_steps = seconds × 50` |
| Reward stuck negative | Strict termination + no alive bonus | Tune task yaml: max_tilt, alive, curriculum |
| episode_length stuck low | Termination too strict | Raise max_tilt_deg, lower min_base_height |
| Learning time >5s | CPU thermal throttle | Reduce num_envs or wait for cooldown |

## Project Variants

### G1 walk_flat (PPO)

Focus on:
- Mean reward trend (positive = good)
- tracking_lin_vel (main signal, target >0.8)
- episode_length (target >500 for stable walking)
- penalty_action_rate (should drop below -10 by iter 500)
- curriculum penalty_scale (should ramp 0.5 → 1.0 as episode_length grows)
- action_std (target 0.2-0.4 after 500 iter)

### Go2 joystick_flat (PPO)

Similar but:
- Lower max_episode_seconds (typically 10s = 500 steps)
- Faster convergence (smaller observation space)
- curriculum not always enabled

### G1 motion tracking (Motrix)

Focus on:
- motion reconstruction error
- per-joint tracking accuracy
- play_steps must match motion file length
