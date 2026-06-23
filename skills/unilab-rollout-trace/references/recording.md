# Recording reference — `record_offpolicy_rollout.py`

Source of truth for the recorder's flags, output schemas, command injection,
and stability thresholds. The recorder lives at
`UniLab/scripts/record_offpolicy_rollout.py` and runs **in WSL** (needs the
UniLab env + mujoco).

## Hard limits (do not try to exceed)

| Dim | Value | Code anchor |
|---|---|---|
| sim | **MuJoCo only** | `_env_factory` hardcodes `sim_backend="mujoco"` |
| algo | **sac / flashsac only** | `create_sac_playback_session` + `build_offpolicy_env_cfg_override` |
| task | **any registered task** | `--task` is a free arg, `g1_walk_flat` is only the default |

PPO checkpoints → no recorder; use the viser / MuJoCo-native viewer from `unilab-train`.
Motrix targets → no headless trace; use `eval --render-mode record` for an mp4.

## CLI flags

```
--algo {sac,flashsac}        default sac
--task <name>                default g1_walk_flat
--sim mujoco                 (effectively fixed)
--steps N                    default 1000   (1 step = ctrl_dt s; G1 ctrl_dt=0.02 → 20 s)
--num-envs N                 default 1      (CPU: keep 1)
--output PATH                npz path; sibling .summary.csv + .metadata.json auto-written
--no-disable-autoreset       keep env autoreset ON (default: recorder disables it)
--summary-env IDX            env index for the CSV (default 0)
[overrides...]               Hydra overrides, e.g. algo.load_run=<path>, +env.commands...
```

Always pass the checkpoint as a Hydra override (not a CLI flag):
`algo.load_run=/mnt/d/.../model_N.pt`.

## Output schemas

### `*.summary.csv` — the plotting input (FIXED columns)

```
step, reward, terminated, truncated,
base_x, base_y, base_z,
vx, vy, vz,
cmd_vx, cmd_vy, cmd_vyaw,
action_l2, dof_vel_l2
```

This is the only file the plotter (`scripts/plot_rollout_trace.py`) needs.
One row per step, for `--summary-env` (default env 0).

### `*.npz` — full per-step tensors (all envs)

| Key | Shape | Notes |
|---|---|---|
| `reward` | (steps, num_envs) | per-step reward |
| `terminated`, `truncated` | (steps, num_envs) | bool |
| `dof_pos`, `dof_vel` | (steps, num_envs, n_dof) | actuated joints |
| `actions` | (steps, num_envs, n_dof) | from `info["current_actions"]` |
| `commands` | (steps, num_envs, 3) | vx, vy, vyaw — **zeros if env has no `info["commands"]`** |
| `gait_phase` | (steps, num_envs, 2) | **zeros for non-gaited tasks** |
| `base_pos`, `base_quat` | (steps, num_envs, 3/4) | |
| `linvel` | (steps, num_envs, 3) | local-frame |
| `gyro` | (steps, num_envs, 3) | |
| `reward_terms` | (steps, num_envs, K) | one column per reward scale key |
| `joint_names`, `actuator_names`, `reward_log_keys`, `default_angles` | 1-D | metadata arrays |

### `*.metadata.json` — run context

`algo, task, sim, checkpoint_path, steps, num_envs, ctrl_dt, sim_dt,
action_scale, autoreset_disabled, joint_names, actuator_names,
reward_log_keys, default_angles, obs_groups_spec`

The plotter reads `ctrl_dt` and `task` from here (fallback 0.02 s / parent dir).

## Command injection

The recorder has **no `--command` flag**. Commands come from the env's command
manager (`env.cfg.commands`). The SAC `g1_walk_flat` yaml has an `env:` section
but no `commands:` block, so command keys are **new** → prefix with `+`.

Mechanism (verified, `src/unilab/envs/locomotion/common/commands.py` +
`g1/joystick.py:_sample_commands`):

```python
commands = uniform(vel_limit[0], vel_limit[1])      # [vx, vy, vyaw]
if rel_standing_envs > 0:                            # fraction of envs → zero cmd
    commands[standing_mask] = 0.0
```

| Goal | Hydra override |
|---|---|
| **Zero command** (strictest stability test) | `+env.commands.rel_standing_envs=1.0` |
| **Fixed forward** (e.g. 1 m/s, no turn) | `+env.commands.vel_limit=[[1.0,0.0,0.0],[1.0,0.0,0.0]]` |
| **Custom vx,vy,yaw** | set `vel_limit` `[min]=[max]` so the sample is deterministic |
| **Default random** (training distribution) | (no override) — samples from `[[-0.6,-0.4,-0.8],[1.0,0.4,0.8]]` |

`vel_limit` layout: `[[vx_min, vy_min, vyaw_min], [vx_max, vy_max, vyaw_max]]`.
For a deterministic fixed command, set each component's min == max.

Example — fixed forward 0.5 m/s:

```bash
... record_offpolicy_rollout.py --algo sac --task g1_walk_flat --sim mujoco \
    --steps 1000 --output .../rollout_trace_fwd_cmd.npz \
    algo.load_run=/mnt/d/.../model_1000.pt interactive.action_mode=policy \
    +env.commands.vel_limit=[[0.5,0.0,0.0],[0.5,0.0,0.0]]
```

> Other tasks may use a different command manager (e.g. manipulation tasks have
> no velocity command). For those, `cmd_*` columns will be zeros and that's
> expected — the base-height / effort / reward panels are still meaningful.

## Stability thresholds

| Signal | Where | Stable | Unstable |
|---|---|---|---|
| `first_terminated_step` | recorder stdout + CSV `terminated` | `None` (survived full run) | a step index |
| fall time | `first_terminated_step × ctrl_dt` | — | seconds (G1: <2 s = bad) |
| `min_base_z` (plotter) | CSV `base_z` | stays near target (~0.75 m for G1) | drops toward 0 |
| `min_base_z` vs `min_base_height` | task yaml (G1 = 0.3) | above | below → env would terminate |
| `mean_reward` (plotter) | CSV `reward` | positive / near tracking target | strongly negative |

### `min_base_z` caveat (autoreset disabled)

The recorder **disables autoreset** by default (so the trace is one continuous
rollout, not many resets). Consequence: after the robot falls it **keeps
crawling**, so `min_base_z` over the full run can be much lower than the height
*at the moment of fall*. E.g. the `sac_v1_iter1000` zero-cmd trace: terminated
at step 58 (1.16 s) where base_z ≈ 0.27 m, but `min_base_z` over 1000 steps is
0.12 m. The **fall time** is the primary stability signal; `min_base_z` is a
secondary check. Use `--no-disable-autoreset` only if you want reset-on-fall
behavior (the trace then contains multiple short episodes).

## Stability verdict recipe

```
if first_terminated_step is None and min_base_z > min_base_height:
    → 稳定 (survived, upright)
elif first_terminated_step is None but min_base_z < min_base_height:
    → 临界 (didn't formally terminate but sagging — borderline)
else:
    fall_s = first_terminated_step * ctrl_dt
    → 不稳定 (fell at {fall_s:.2f}s, base_z → {min_base_z:.2f}m)
```

## Advanced: reward-term decomposition from the npz

When the policy is unstable, dig into *why* via `reward_terms` (per-step,
one column per reward scale). `reward_log_keys` (in metadata + npz) gives the
column order, e.g. `['reward/tracking_lin_vel', 'reward/penalty_action_rate',
'reward/alive', …]`.

```bash
wsl -d Ubuntu -u u20174 -- bash -c "cd /home/u20174/UniLab && \
/home/u20174/.local/uv run --no-sync python - <<'EOF'
import numpy as np, json
d = np.load('/mnt/d/.../rollout_trace_zero_cmd.npz', allow_pickle=True)
keys = [str(k) for k in d['reward_log_keys']]
rt = d['reward_terms'][:, 0]          # env 0
print('per-term mean (env0):')
for k, v in zip(keys, rt.mean(axis=0)):
    print(f'  {k:36s} {v:+.4f}')
EOF"
```

The most negative term before the fall is the culprit (e.g.
`penalty_orientation` spiking = the robot is tilting; `penalty_action_rate`
spiking = twitching; `tracking_*` collapsing = not following command).

## Gotchas

- **`+` prefix required** for `env.commands.*` (no `commands:` in the SAC yaml).
  Bare `env.commands.rel_standing_envs=1.0` → "Key 'commands' is not in struct".
- **`commands` / `gait_phase` are zero** for tasks without a velocity command
  manager / gait — that's expected, not a bug.
- **Plotting runs on Windows python**, not WSL (WSL env lacks matplotlib). The
  CSV is on `D:\` so Windows reads it directly.
- **`max_iterations` / `resume` semantics do not apply** here — the recorder
  does playback, not training. Only `algo.load_run=<path>` matters.
- **CPU only** (this machine has no CUDA); `--num-envs 1` is fastest per-step.
- The WSL wrapper prints a Chinese garbage localhost-proxy warning every call —
  ignore it.
