---
name: unilab-rollout-trace
description: >-
  Record a headless numeric rollout trace from a UniLab OFF-POLICY policy
  (SAC / FlashSAC) on MuJoCo, then plot it into a 4-panel stability figure
  (base height/fall, velocity tracking, effort, reward) and give a one-line
  verdict. Works for ANY task — not just g1_walk_flat. Use when user mentions:
  unilab rollout, rollout trace, record rollout, headless rollout, SAC playback,
  policy stability, policy 是否稳定, 倒下, 跌倒, 站不站得住, 画 rollout,
  rollout 画图, 画曲线, 稳定性分析, trace CSV, record_offpolicy_rollout,
  /unilab-rollout-trace, checkpoint 验证, off-policy 验证, compare checkpoints.
---

# UniLab Rollout Trace

Record a **headless numeric rollout** from a UniLab off-policy checkpoint,
plot it into a stability figure, and judge whether the policy is stable.
**General-purpose**: any task, as long as it's **SAC/FlashSAC on MuJoCo**.

## What it does

Given a checkpoint + task, produce three artifacts next to the checkpoint:

| Artifact | Content |
|---|---|
| `rollout_trace_<tag>.npz` | Full per-step tensors (dof_pos/vel, actions, commands, base_pos/quat, linvel, gyro, reward, reward_terms, gait_phase) |
| `rollout_trace_<tag>.summary.csv` | Compact CSV (fixed schema) — the plotting input |
| `rollout_trace_<tag>.metadata.json` | ctrl_dt, task, checkpoint_path, joint_names, reward_log_keys |
| `rollout_trace_<tag>.plot.png` | 4-panel stability figure (base height, vel tracking, effort, reward) |

Then a one-line Chinese verdict: 稳定 / 不稳定 (fell at Xs).

## Hard constraints (read first)

The recorder `UniLab/scripts/record_offpolicy_rollout.py` has these **fixed**
limits — verify the target matches before promising anything:

| Dimension | Limit | Why |
|---|---|---|
| **sim** | **MuJoCo only** | `sim_backend="mujoco"` is hardcoded + uses `mujoco.MjModel` |
| **algo** | **SAC or FlashSAC only** | uses `create_sac_playback_session`. **PPO checkpoints CANNOT use this tool.** |
| **task** | **any registered task** | `--task` is a free arg; `g1_walk_flat` is only the default |

For PPO checkpoints, use the viser / MuJoCo-native viewer path from
`unilab-train` instead — there is no numeric-trace recorder for PPO.

## Where each step runs

| Step | Where | Why |
|---|---|---|
| Record (rollout) | **WSL** | needs UniLab env + mujoco |
| Plot (CSV → PNG) | **Windows python** | has matplotlib 3.10 + numpy; CSV is already on `D:\` |

The recorder only emits CSV/npz — plotting is done by this skill's own script
`scripts/plot_rollout_trace.py` (numpy + matplotlib, no pandas).

## Read first

`references/recording.md` — before running anything that depends on:
- The recorder's exact flags / return values
- CSV vs npz schema and which columns exist for non-locomotion tasks
- How to inject a specific command (zero / forward / random)
- Stability thresholds (first-terminated step, base_z vs min_base_height)
- Advanced: npz reward-term decomposition
- Gotchas (commands/gait_phase fallback to zeros for non-locomotion tasks)

Treat `references/recording.md` as the source of truth for recorder specifics.

## Slash-flag invocation

| Flag | Action |
|---|---|
| (none) or `--record` | Record a trace for a checkpoint, copy to Windows, plot, verdict |
| `--plot-only <csv...>` | Skip recording — just plot existing CSV(s) |
| `--compare <csv...>` | Overlay multiple CSVs in one figure (compare ckpts / cmds / tasks) |
| `--cmd zero\|fwd\|<vx,vy,yaw>` | Command to inject during recording (default `zero`) |

If the user gives a bare checkpoint path or task name, treat it as `--record`.

## Full workflow (`--record`, default)

Inputs to resolve from the user's message:
- `TASK` — e.g. `g1_walk_flat` (the **task name**, not a path)
- `CKPT` — absolute path to a `model_*.pt` (WSL path if recording, or derive)
- `CMD` — `zero` (default) | `fwd` (~1 m/s forward) | explicit `vx,vy,yaw`

### Step 1 — Record in WSL

Output goes **next to the checkpoint** so Windows plotting finds it directly.
Pick a `<TAG>` for the command type (`zero_cmd`, `fwd_cmd`, `cmd_1_0_0`, …).

```bash
wsl -d Ubuntu -u u20174 -- bash -c "export HOME=/home/u20174 && cd /home/u20174/UniLab && \
HF_ENDPOINT=https://hf-mirror.com /home/u20174/.local/uv run --no-sync \
  python scripts/record_offpolicy_rollout.py \
    --algo sac --task <TASK> --sim mujoco \
    --steps <STEPS> --num-envs 1 \
    --output /mnt/d/Desktop_Files/UniLab/checkpoints/<TASK>/mujoco/<RUN>/rollout_trace_<TAG>.npz \
    algo.load_run=/mnt/d/Desktop_Files/UniLab/checkpoints/<TASK>/mujoco/<RUN>/model_<N>.pt \
    interactive.action_mode=policy \
    <COMMAND_OVERRIDE>"
```

- `<STEPS>`: 1000 is a good default for stability. `1 step ≈ ctrl_dt s`
  (G1 = 0.02 s → 1000 steps = 20 s).
- `--num-envs 1` on CPU (more envs = slower, no benefit for a trace).
- **Command injection**: the env reads commands internally; for a custom
  command use a Hydra/env override appropriate to the task, e.g.
  `+env.command_ranges_x='[0.0,0.0]'` for zero, or
  `+env.command_ranges_x='[1.0,1.0]'` for fixed 1 m/s. If unsure, see
  `references/recording.md` — when in doubt, record zero-command (the
  strictest stability test).

The recorder prints `summary_env=0 first_terminated_step=<N or None>`.

### Step 2 — Plot on Windows python

The CSV is already on `D:\` (next to the checkpoint). Run the skill's plotter:

```bash
python "C:/Users/20174/.claude/skills/unilab-rollout-trace/scripts/plot_rollout_trace.py" \
  "D:/Desktop_Files/UniLab/checkpoints/<TASK>/mujoco/<RUN>/rollout_trace_<TAG>.summary.csv" \
  --min-base-height 0.3
```

- `--min-base-height` is optional but recommended for bipeds (draws the fall
  threshold on the base-height panel). Get the value from the task yaml
  (`min_base_height`) or env cfg; common: G1 = 0.3.
- Auto-opens the PNG unless `--no-show`.
- Prints a compact summary table (steps, duration_s, fall time, min_z,
  mean/cum reward, effort).

### Step 3 — Verdict

From the printed summary table:

| Signal | Stable | Unstable |
|---|---|---|
| `fall@` | `—` (survived full run) | a time (terminated) |
| `min_z` vs `min_base_height` | stays above | drops below |
| `mean_r` | positive / near command target | strongly negative |

One-line Chinese verdict + next action, e.g.:
- **稳定**: "零命令下站满 20s 未倒,base_z 稳在 0.72m,无需干预。"
- **不稳定**: "零命令下 1.16s 倒下,base_z 跌到 0.12m < 0.3 阈值。该 ckpt 未收敛,建议换更晚的 ckpt 或继续训练。"

## Compare runs (`--compare`)

```bash
python ".../plot_rollout_trace.py" \
  "D:/.../rollout_trace_zero_cmd.summary.csv" \
  "D:/.../rollout_trace_fwd_cmd.summary.csv" \
  --labels zero_cmd fwd_cmd \
  --min-base-height 0.3 \
  --out "D:/.../comparison.png"
```

Overlays all CSVs on every panel (one color per run). Great for:
- zero vs forward command (does it still stand when commanded to move?)
- different checkpoints (model_500 vs model_1000 — is training improving stability?)
- before/after a sim2sim or config change

## Plot-only (`--plot-only`)

If a CSV already exists (recorder already ran), skip Step 1:

```bash
python ".../plot_rollout_trace.py" "D:/.../<csv>" --min-base-height 0.3
```

## Response style

Order:
1. What was recorded (task / ckpt / command / steps)
2. The summary table (from the plotter stdout)
3. One-line Chinese verdict
4. Recommended next action (continue train / change ckpt / tune termination)

Keep concise. Offer the npz reward-term breakdown (`references/recording.md`)
only if the user wants to dig into *why* it's unstable.

## Common issues

| Symptom | Cause | Fix |
|---|---|---|
| `Key 'X' is not in struct` | new Hydra/env key | prefix with `+env.X=...` |
| `--load-run must be '-1' or dir name` | recorder Hydra override vs CLI | recorder already uses `algo.load_run=<path>` override — keep it |
| PPO checkpoint | recorder is SAC/FlashSAC-only | use viser / MuJoCo viewer from `unilab-train` |
| Motrix target | recorder is MuJoCo-only | no headless trace for Motrix; use `eval --render-mode record` mp4 |
| `cmd_vx/yaw` columns all zero | non-locomotion task (no `info["commands"]`) | expected — those panels just show zeros |
| `ModuleNotFoundError: matplotlib` | plotting in WSL instead of Windows | run plotter on **Windows python** (it has matplotlib) |
| PNG won't open | non-Windows or `--no-show` set | open `D:/.../*.plot.png` manually |

## Reference files

- `references/recording.md` — recorder flags, CSV/npz schema, command injection,
  stability thresholds, npz reward-term decomposition, gotchas.
- `scripts/plot_rollout_trace.py` — the plotter (numpy + matplotlib).
