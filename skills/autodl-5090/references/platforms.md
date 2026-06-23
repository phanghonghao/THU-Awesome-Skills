# Platform: AutoDL RTX 5090

Source of truth for SSH, hardware, disk/quota, projects, logs, and process detection.

## Connection

| Property | Value |
|----------|-------|
| SSH alias | `autodl` (passwordless, agent-authed) |
| Host | `connect.bjb2.seetacloud.com:17559` |
| User | `phh` |
| Container hostname | `autodl-container-56194fa31d-630ca0b9` |
| VPN | None — direct SSH |

`ssh autodl 'hostname'` should print `autodl-container-...`. Use this as a connectivity probe.

## Hardware

| Property | Value |
|----------|-------|
| GPU | 1× NVIDIA RTX 5090 (Blackwell sm_120), 32 GB |
| Usable device | `cuda:0` — **the only one** |
| RAM | ~754 GB (shared box) |
| CPU cores | ~208 (shared box) |

Single GPU ⇒ all concurrent trainings share `cuda:0` and divide throughput. Do not assign
`cuda:1` and above — they don't exist on this box.

## Disk & Quota (IMPORTANT)

- Everything lives under **`/root/autodl-tmp`**. `~` and `~/projects` resolve to
  `/root/autodl-tmp/users/phh/home` and `.../home/projects`.
- **Never** write big files to the system disk: `/`, `/tmp`, `/usr`, `/opt`, `/root`,
  `/var/tmp`. No checkpoints / logs / datasets / conda envs there.
- **Quota**: 100 GB/user (soft warning ~290 GB; >100 GB is a serious alert).
- Don't install system packages yourself — ask the admin (`louis`).
- Don't run the official Claude / Claude Code proxy on the server.

Checks:
```bash
df -h /root/autodl-tmp        # volume free space
du -sh ~/projects             # your footprint toward the 100 GB quota
```

## Projects, Runs & Logs

| Project | Task arg | Run directory | Train log |
|---------|----------|---------------|-----------|
| Z1 AMP (MJLAB) | `Z1-AMP-Flat` | `~/projects/Z1_AMP_MJLAB/logs/rsl_rl/z1_amp_unified/<run-name>/` | `~/projects/Z1_AMP_MJLAB_train_128.log` |
| G1 AMP (MJLAB) | `Unitree-G1-AMP-Flat` | `~/projects/AMP_mjlab/logs/rsl_rl/g1_amp_locomotion/<ts>/` | `~/projects/AMP_mjlab_train_256.log` |
| Z1 Isaac Lab | `Magiclab-Z1-12dof-Velocity` | `~/projects/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/<ts>/` | nohup log under `~/` (e.g. `~/smoke_train.log`, `~/full_pipeline3.log`) |

Logs are launched as `nohup python scripts/train.py ... > <LOG> 2>&1 &`, so the redirect
is **not** visible in `ps`. Map by task name, or take the newest `*_train*.log` in `~/projects`:

```bash
ssh autodl 'ls -t ~/projects/*_train*.log | head'
```

## Process Detection

```bash
ssh autodl 'ps -eo pid,etime,pcpu,pmem,cmd | grep "train.py" | grep -v grep'
```

Two arg styles are in use on this box — match either:
- **MJLAB / argparse**: `python scripts/train.py --task Z1-AMP-Flat --device cuda:0 --num-envs 128 --max-iterations 20000 --experiment-name z1_amp_unified --run-name concurrent_128`
- **Hydra**: `python scripts/train.py Unitree-G1-AMP-Flat --env.scene.num-envs=256`

## Log Format (rsl-rl)

Both MJLAB runs print rsl-rl iteration blocks. Pull these fields:
- `Total timesteps:` — cumulative environment steps
- `Iteration time:` — seconds per iteration
- `Total time:` / `Time elapsed:` — wall clock so far
- `ETA:` — estimated time remaining

AMP-specific lines worth surfacing:
- `Metrics/slip_velocity_mean`
- `Episode_Termination/time_out`, `bad_orientation`, `bad_base_height`
- `Diagnostics/amp_sanitized_envs`, `amp_policy_samples_dropped`, `amp_invalid_minibatches`, `style_reward_sanitized_envs`

Isaac Lab Z1 additionally prints reward breakdowns and tracking-error metrics.

## conda env (Isaac Lab runs only)

`/root/autodl-tmp/users/phh/home/envs/conda/isaaclab_232`

- Activate by **full path**: `conda activate /root/autodl-tmp/users/phh/home/envs/conda/isaaclab_232`
  (bare `conda activate isaaclab_232` fails — `EnvironmentNameNotFound`).
- Stack: torch 2.7.0+cu128 (arch incl. `sm_120`), Isaac Sim 5.1.0, Isaac Lab 2.3.2, rsl-rl-lib 3.1.2.
- MJLAB (AMP) runs may use a different env; check the launch script if a metric-related import fails.

## Common Issues

| Symptom | Fix |
|---------|-----|
| SSH timeout / refused | AutoDL container likely restarting — retry a few times |
| `no kernel image available` (Isaac Lab) | torch must be cu128 with `sm_120` in `torch.cuda.get_arch_list()` (5090/Blackwell) |
| `conda activate isaaclab_232` fails | activate by full path instead |
| `import isaaclab` ModuleNotFoundError | core pkg skipped during install; see the project setup memo |
| Disk / quota warning | move old checkpoints off `/root/autodl-tmp`; never write to system disk |
| High termination ratios (AMP) | not a platform bug — surface to the user as a training-health signal, not an error |
