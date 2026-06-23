# RTX Paths Quick Reference

## Server access

- SSH: `ssh phh@192.168.120.155`
- VPN required: iNode client at
  `C:\Program Files (x86)\iNode\iNode Client\iNode Client.exe`
- BMC: `https://192.168.120.154/`
- Slurm node: `pro6000d`, partition `gpu`

## Conda environments (under `~/miniconda3/envs/`)

Always activate with:
```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate <env>
```

| Env                  | Use                                       |
|----------------------|-------------------------------------------|
| `isaaclab`           | Isaac Lab training (RL track)             |
| `unitree_rl_mjlab`   | MuJoCo Lab training (RL track, T1/K1/G1)  |
| `act`, `diffusion_policy`, `tdmpc2`, `dreamerv3`, `openpi`, `octo`, `robomimic_il`, `lerobot` | VLA/WM track |

## Project roots on RTX

| Remote path                       | Contents                                            |
|-----------------------------------|-----------------------------------------------------|
| `~/IsaacLab/`                     | Isaac Lab source + logs                             |
| `~/unitree_rl_mjlab/`             | MuJoCo Lab upstream mirror + scripts                |
| `~/booster_t1_mjlab/`             | T1 (Booster humanoid) task package + train wrappers |
| `~/UniLab/`                       | UniLab source + logs                                |
| `~/vla_wm/`                       | VLA/WM track (separate from RL)                     |
| `~/output/`                       | Per-job output dirs (`<task>_<version>_<ts>/`)      |
| `~/slurm_logs/`                   | `<jobname>_<jobid>.out` and `.err`                  |

## Log layouts

### mjlab / booster_t1_mjlab

```
~/booster_t1_mjlab/logs/rsl_rl/<experiment_name>/<YYYY-MM-DD_HH-MM-SS>[_<run_name>]/
├── model_<iter>.pt                 # checkpoints every save_interval
├── events.out.tfevents.*           # TensorBoard scalars
├── params/env.yaml, agent.yaml     # config dumps
└── convergence_report.json         # written by ~/convergence_monitor.py (if used)
```

Experiment names: `T1-Stand-PPO`, `T1-Reach-PPO`, `T1-Getup-PPO`.

### Isaac Lab

```
~/IsaacLab/logs/rsl_rl/<task>/<YYYY-MM-DD_HH-MM-SS>/
├── model_<iter>.pt
├── events.out.tfevents.*
└── params/
```

### VLA/WM

```
~/vla_wm/outputs/<method>/<task>/
```

## Per-job output dirs

Slurm scripts conventionally write to `~/output/<task>_<version>_<timestamp>/`:

- `train.log` (piped via `tee`)
- `convergence_report.json` (if convergence_monitor.py was attached)
- `monitor.log` (if convergence_monitor.py ran in background)
- For recording jobs: `rl-video-step-0.mp4` or similar

## Local repo layout

- Root: the **current project root** — the folder Claude Code was launched
  in (CWD). This skill is project-agnostic; all paths below are relative to
  whichever project you invoke it from.
- Daily logs: `docs/Training_Daily_Log/`
- Assets: `assets/<category>/<task>/{models,videos,plots,training_records}/`
- Categories: `Locomotion/`, `Manipulation/`
- Plot tool: `scripts/generate_reward_curves.py`
- Warm-start trainer: `scripts/rtx_deploy/train_warmstart.py`

## Recording script

- Path: `~/record_headless.py` (booster_t1_mjlab-specific, wraps mjlab play)
- Usage: `python ~/record_headless.py <task_id> --checkpoint-file <path> --num-envs 1 --video-length 1000 --output-dir <dir> --device cuda:0`
- Output file name pattern: `rl-video-step-0.mp4` (must be renamed to
  `<task>_play_video_model_<N>.mp4` after SCP — see canonical_naming.md).

## Convergence monitor

- Path: `~/convergence_monitor.py`
- Attach to a running job via:
  ```bash
  python ~/convergence_monitor.py --realtime --run_dir <RUN_DIR> --preset <name> --report_path <OUT>/convergence_report.json
  ```
- Presets: `t1_stand`, `t1_reach`, etc. — selects which TensorBoard tags
  to track and what `behavioral_summary` to compute.

## SCP conventions

Local → remote:
```bash
scp <local_path> phh@192.168.120.155:<remote_path>
```

Remote → local (use forward slashes, quote paths with spaces):
```bash
scp phh@192.168.120.155:<remote_path> <local_path>
```

After uploading any Slurm script or Python file generated on Windows:
```bash
ssh phh@192.168.120.155 "sed -i 's/\r$//' <path>"
```
