# Platform: `wsl` (UniLab local CPU training)

## Environment

| Property | Value |
|----------|-------|
| WSL Distro | `Ubuntu-24.04` (`Ubuntu`) |
| User | `u20174` |
| Project Root (WSL) | `/home/u20174/UniLab` |
| Windows Mirror | `D:\Desktop_Files\UniLab\` |
| Compute | **CPU only** (no CUDA, no usable GPU) |
| uv binary | `/home/u20174/.local/uv` |
| HF Mirror | `HF_ENDPOINT=https://hf-mirror.com` (REQUIRED for any HF download) |

## Connection Check

WSL is always local — no SSH. Verify alive:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "echo OK && uptime"
```

The `wsl ... -- bash -c "..."` wrapper **prints a Chinese garbage warning on every invocation** (`wsl: 检测到 localhost 代理配置...`). Ignore it.

## Command Prefix Template

Every UniLab command inside WSL:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "export HOME=/home/u20174 && cd /home/u20174/UniLab && HF_ENDPOINT=https://hf-mirror.com /home/u20174/.local/uv run --no-sync <CMD>"
```

For long-running training, append log redirection:

```bash
... > /home/u20174/UniLab/logs/<run_name>.log 2>&1
```

## Process Detection

```bash
wsl -d Ubuntu -u u20174 -- bash -c "ps aux | grep -E 'train|play_viser|play_interactive|tensorboard' | grep -v grep"
```

## Train Command

```bash
# PPO (default for most tasks)
train --algo ppo --task <task> --sim <mujoco|motrix> \
  algo.num_envs=N algo.max_iterations=M training.no_play=true

# SAC (offpolicy, GPU recommended but CPU works for smoke)
train --algo sac --task <task> --sim <mujoco|motrix> \
  training.num_gpus=0 training.use_amp=false \
  algo.algo_params.use_compile=false
```

**Gotcha**: `--task` and `--sim` are separate flags. Do NOT write `--task g1_walk_flat/mujoco` (will fail with "the following arguments are required: --sim").

## Resume Mechanism

```bash
train --algo ppo --task <task> --sim <sim> \
  algo.load_run=/home/u20174/UniLab/logs/rsl_rl_ppo/<Task>/<run_dir> \
  algo.max_iterations=<N> training.no_play=true
```

**Critical semantics**: `max_iterations` is **ADDITIONAL**, not total. Resuming from iter 500 with `max_iterations=3000` → final iter is 3500, not 3000. To hit total 3000, set `max_iterations=2500`.

There is **no `resume=true` flag** in UniLab — `algo.load_run=<path>` alone restores:
- Network weights (actor + critic)
- Optimizer state (Adam moments)
- Empirical normalization stats
- Policy action_std
- Curriculum penalty_scale
- Iter counter

Env RNG state resets (acceptable for PPO; matters more for SAC).

## Key Paths

| Artifact | WSL Path | Windows Mirror |
|---|---|---|
| Train log (stdout) | `/home/u20174/UniLab/logs/<run_name>.log` | — |
| Run dir (ckpts + tfevents) | `/home/u20174/UniLab/logs/rsl_rl_ppo/<Task>/<YYYY-MM-DD_HH-MM-SS>_<sim>/` | — |
| SAC run dir | `/home/u20174/UniLab/logs/fast_sac/<Task>/<...>_<sim>/` | — |
| Final ckpts | — | `D:\Desktop_Files\UniLab\checkpoints\{task}\{sim}\model_*.pt` |
| Final videos | — | `D:\Desktop_Files\UniLab\videos\{task}\{sim}\*.mp4` |
| Robot XML (e.g. G1) | `/home/u20174/UniLab/src/unilab/assets/robots/g1/g1.xml` | — |
| Task YAML | `/home/u20174/UniLab/conf/ppo/task/<task>/<sim>.yaml` | — |

## save_interval

`conf/ppo/config.yaml:12` → `save_interval: 50` (changed from upstream 100).
Every 50 iter saves a ckpt → finer-grained best-ckpt selection for short runs.

## Best Checkpoint Selection

After training finishes (or when picking ckpt to deploy):

1. Read `run_summary.json` if present → `best_mean_reward`
2. Otherwise parse tfevents `Train/mean_reward`:

```bash
wsl -d Ubuntu -u u20174 -- bash -c "cd /home/u20174/UniLab && /home/u20174/.local/uv run --no-sync python << 'EOF'
from tensorboard.backend.event_processing import event_accumulator
ea = event_accumulator.EventAccumulator('<RUN_DIR>', size_guidance={'scalars': 0})
ea.Reload()
events = ea.Scalars('Train/mean_reward')
best = max(events, key=lambda e: e.value)
print(f'Best iter: {best.step}, reward: {best.value:.4f}')
EOF"
```

3. Pick the saved ckpt (model_*.pt at multiples of 50) closest to best iter.

## Common Metrics (PPO G1 example)

```
Train/mean_reward              ← total reward (weighted sum)
Train/mean_episode_length      ← survival steps (max = max_episode_steps)
reward/tracking_lin_vel        ← main forward velocity tracking
reward/tracking_ang_vel        ← turning tracking
reward/feet_phase              ← gait phase reward
reward/alive                   ← survival bonus (if configured)
reward/penalty_action_rate     ← action smoothness penalty
reward/penalty_orientation     ← body uprightness penalty
reward/penalty_ang_vel_xy      ← roll/pitch penalty
reward/pose                    ← joint pose deviation
curriculum/penalty_scale       ← adaptive curriculum (0.5=start, 1.0=full)
curriculum/average_episode_length
Loss/value, Loss/surrogate, Loss/entropy, Loss/learning_rate
```

## Health Heuristics

| Signal | Healthy | Concern |
|---|---|---|
| Mean reward trend | Monotonic increase over 50+ iter | Stuck or oscillating |
| action_std | Decreasing from 1.0 → 0.2-0.4 over 500 iter | Stuck at 1.0 (no learning) |
| episode_length | Increasing toward max_episode_steps | Stuck low (<100) |
| penalty_action_rate | Decreasing as std drops | Stuck high (>50 at iter 200+) |
| Learning time | <2s/iter | >5s/iter (CPU thermal throttle) |
| Steps/s | >2000 (256 envs) | <1000 (CPU contention) |
| curriculum penalty_scale | Ramps up as episode_length grows | Stuck at min_scale |

## Viewer Commands

### viser (browser 3D, MuJoCo only)

```bash
wsl ... uv run python scripts/play_viser.py \
  task=g1_walk_flat/mujoco \
  interactive.action_mode=policy \
  algo.load_run=<RUN_DIR> \
  viser.port=8080
```

Open `http://localhost:8080` in Windows browser. Ctrl+Shift+R to hard-refresh.

**viser rgba bug**: viser reads `model.geom_rgba[i]` directly. MuJoCo materials set via `<material name="X">` do NOT propagate to `geom_rgba` at compile time. To make color changes visible, **also set explicit `rgba="..."` on each geom** in the XML.

### MuJoCo native viewer (GLFW via WSLg)

```bash
wsl ... bash -c "export DISPLAY=:0 && uv run python scripts/play_interactive.py \
  --algo ppo --task g1_walk_flat --sim mujoco \
  algo.load_run=<RUN_DIR> \
  interactive.action_mode=policy"
```

Opens a GLFW window on Windows desktop via WSLg. MuJoCo native renderer respects materials correctly (no rgba hack needed).

Controls: Space=pause, N=step, +/-=speed, Esc=quit.

### TensorBoard

```bash
wsl ... uv run tensorboard --logdir /home/u20174/UniLab/logs --port 6006 --bind_all
```

Open `http://localhost:6006`. **Restart TB if a new run subdir was created after TB startup** — TB's data server doesn't auto-discover new subdirs.

## Motrix Demo Recording

```bash
eval --algo ppo --task <task> --sim motrix \
  --render-mode record \
  training.play_env_num=1 training.play_steps=<N> \
  algo.load_run=<RUN_DIR>
```

- `play_steps = desired_seconds × 50` (Motrix runs at 50Hz)
- `play_env_num=1` is mandatory on CPU (8 envs = 8× slower)
- Output: `src/unilab/assets/checkpoints/<demo>/play_video.mp4`
- Copy to Windows: `videos/{task}/motrix/model_0.mp4`

**demo CLI** (`src/unilab/demo.py`) has NO `--render-mode` flag — use `eval` directly.

## WSL Restart Recovery

WSL sometimes restarts (Windows update, memory pressure). All background processes die. Recovery:

1. `wsl ... ps aux | grep python` to confirm what's still alive
2. Resume training from latest ckpt: `algo.load_run=<RUN_DIR>` (no `resume=true`)
3. Restart viser / TB if needed
4. Check log mtimes to detect silent interruptions

## Gotchas (verified)

- `--load-run` CLI flag rejects paths (only dir names or `-1`). Use Hydra override `algo.load_run=<path>` instead.
- `uv sync --extra X` removes any extra not specified. Always run `uv sync --extra viser --extra motrix` together.
- viser can't replay Motrix-trained demos — those need Motrix mp4 path.
- WSL2 localhost auto-forwards to Windows — browser/viser/TB at `http://localhost:<port>` works from Windows.
- Motrix Bevy renderer on CPU: ~1-2 sec/frame via WARP software fallback.
- `conf/ppo/task/<task>/<sim>.yaml` is per-backend tuning; `base.yaml` is shared contract.
- Penalty-named rewards (`penalty_action_rate`, `penalty_orientation`, etc.) map to same functions as non-prefixed (`action_rate`, `orientation`) — only naming differs.

## Demo → Task Mapping

| demo | task | sim |
|---|---|---|
| dance | g1_motion_tracking | motrix |
| wallflip | g1_wall_flip_tracking | motrix |
| boxtracking | g1_box_tracking | motrix |
| locomani | go2_arm_manip_loco | mujoco |

## Ports

- 6006: TensorBoard
- 8080: viser (G1 typically)
- 8081: viser (Go2 typically)
