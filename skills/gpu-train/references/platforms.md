# Platform Configurations

## Platform: `rtx`

| Property | Value |
|----------|-------|
| SSH Host | `phh@192.168.120.155` (VPN required) |
| Address | `192.168.120.155` |
| User | `phh` |
| Architecture | x86_64 |
| GPU | 8x NVIDIA RTX 6000D (85 GB each) |
| Conda Env | `isaaclab` |
| Conda Activation | `source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab` |
| Isaac Lab Root | `~/IsaacLab` |
| Project Root | `~/magiclab_rl_lab` |
| VPN | iNode VPN (`C:\Program Files (x86)\iNode\iNode Client\iNode Client.exe`) |
| Display | Headless offscreen (`--headless` alone, no Xvfb needed) |
| Video Recording | Use `--video --headless` directly (no Xvfb, no display needed) |

### Hard Constraints For Resume / Re-submit

- Never launch Isaac Sim multi-GPU training with `CUDA_VISIBLE_DEVICES` set.
- Reason: Omniverse Kit `carb.cudainterop` treats `CUDA_VISIBLE_DEVICES` as a hard incompatibility and may mark GPUs as `bad state`, causing all GPUs to be skipped.
- For any Slurm-based resume or re-submit, explicitly `unset CUDA_VISIBLE_DEVICES` before `torchrun`.
- Multi-GPU allocation must be continuous from `cuda:0`.
- `torchrun` cannot skip an in-between GPU. If one GPU in the middle is occupied, do not use a fragmented set such as `0,1,2,3,5`; instead choose a continuous prefix such as `0-3` or `0-5` depending on actual availability.
- Validate continuity from the Slurm-assigned `CUDA_VISIBLE_DEVICES` **before** unsetting it.
- Do **not** require `torch.cuda.device_count()` to equal `NUM_GPUS` after unsetting. On this server, unsetting the mask can expose all 8 GPUs again, which is acceptable as long as the original Slurm allocation was the exact prefix `0..NUM_GPUS-1`.
- Before headless launch, verify EGL vendor config exists:
  `~/miniconda3/envs/isaaclab/share/glvnd/egl_vendor.d/10_nvidia.json`
- If the EGL vendor file is missing, fail fast and fix the environment before retrying.
- Every concurrent `torchrun` must use a unique `--master_port`.
- When re-submitting, either choose a known-free port manually or probe for a free local port before launch.

### GPU Allocation

| GPU | Status | Notes |
|-----|--------|-------|
| cuda:0 | Z1 Locomotion | Configured env, rsl-rl 3.0.1 |
| cuda:4 | Free | |
| cuda:6 | Free | |
| Others | Other users | Check before use |

### Process Detection

```bash
ssh phh@192.168.120.155 'ps aux | grep train.py | grep -v grep'
```

### Log Access

```bash
# Active training log (from nohup)
ssh phh@192.168.120.155 "tail -30 /tmp/z1_train_v1.log"

# Detect log path from process args
ssh phh@192.168.120.155 "ps aux | grep train.py | grep -v grep | grep -oP '> \K[^ ]+\.log'"
```

### Checkpoint Paths

| Project | Path |
|---------|------|
| Z1 Locomotion | `~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/<run_dir>/` |

### Video Recording Command

**Isaac Sim (headless offscreen, recommended):**

Two modes available:
```bash
# Mode 1: --checkpoint (OnPolicyRunner, loads raw .pt directly, no JIT export needed)
ssh phh@192.168.120.155 "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/rsl_rl/play_z1_video.py --checkpoint <CHECKPOINT> --video --video_length 1000 --headless --num_envs 1 --disable_fabric --device cuda:0 --camera_distance 2.5 --camera_height 1.2"

# Mode 2: --policy (JIT, no rsl-rl dependency)
ssh phh@192.168.120.155 "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/rsl_rl/play_z1_video.py --policy <RUN>/exported/policy.pt --video --video_length 1000 --headless --num_envs 1 --disable_fabric --device cuda:0 --camera_distance 2.5 --camera_height 1.2"
```

Camera defaults (verified robot-visible): `--camera_distance 2.5`, `--camera_height 1.2`
- `--device cuda:0` is REQUIRED; using other GPUs causes Kit renderer to hang
- `--disable_fabric` is REQUIRED to avoid PhysX Fabric crash
- `--video_length 1000` gives ~20s at 50fps

**MuJoCo (EGL offscreen, no X Server needed):**
```bash
ssh phh@192.168.120.155 "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u sim2sim/mujoco_manual.py --mjcf ~/magicbot-z1_description/mjcf/MAGICBOTZ1.xml --policy <RUN>/exported/policy.pt --deploy_cfg <RUN>/params/deploy.yaml --record /tmp/<NAME>_mujoco.mp4 --num_steps 1000 --vel_x 0.5"
```

**One-click recording (both Isaac Sim + MuJoCo):**
```bash
bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_record_video.sh <RUN_DIR> <CHECKPOINT> [VIDEO_LENGTH] [VEL_X] [DURATION]
```

### Video Download

```bash
# Isaac Sim video
scp phh@192.168.120.155:<checkpoint_dir>/videos/play/rl-video-step-0.mp4 "<LOCAL_PATH>"

# MuJoCo video
scp phh@192.168.120.155:/tmp/<NAME>_mujoco.mp4 "<LOCAL_PATH>"
```

Local save: `D:\Desktop_Files\Magicbot_Z1\videos/`

### Training Launch

```bash
ssh phh@192.168.120.155 "cd ~/magiclab_rl_lab && source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && nohup python -u scripts/rsl_rl/train.py --task Magiclab-Z1-12dof-Velocity --run_name <NAME> --headless --max_iterations <N> --num_envs <N> --device cuda:<ID> > /tmp/<LOG_NAME>.log 2>&1 & echo PID=\$!"
```

### Orchestrator Launch / Resume

Preferred Slurm wrapper:
```bash
# Fresh full pipeline
bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh

# Fresh start from a sub-phase
bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh --from p3_fine

# Resume from saved state
bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh --resume
```

Direct manual launch on the server:
```bash
ssh phh@192.168.120.155 "cd ~/magiclab_rl_lab && source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && nohup python -u scripts/automation/phase_orchestrator.py --plan training_plans/z1_5phase_plan.yaml --num-gpus 4 --poll-interval 120 > /tmp/z1_5phase_pipeline.log 2>&1 & echo PID=\$!"
```

Resume preflight:
- Verify state file exists: `ssh phh@192.168.120.155 'test -f ~/magiclab_rl_lab/orchestrator_state.json && echo EXISTS || echo MISSING'`
- If state is missing, do not call resume; use a fresh `--from <sub_phase>` launch instead.
- For Slurm resume/re-submit, ensure the wrapper clears `CUDA_VISIBLE_DEVICES`, checks the EGL vendor file, and uses a unique `MASTER_PORT`.

Orchestrator state and logs:
- State file: `~/magiclab_rl_lab/orchestrator_state.json`
- Slurm stdout: `~/magiclab_rl_lab/logs/slurm-z1_orch-<JOBID>.out`
- Slurm stderr: `~/magiclab_rl_lab/logs/slurm-z1_orch-<JOBID>.err`
- Persistent orchestrator log: `~/magiclab_rl_lab/logs/phase_orchestrator.log`
- Manual nohup log: `/tmp/z1_5phase_pipeline.log`

### Key Training Config Files (on server)

| File | Path |
|------|------|
| Robot config | `source/magiclab_rl_lab/magiclab_rl_lab/assets/robots/magiclab.py` |
| Env config | `source/magiclab_rl_lab/magiclab_rl_lab/tasks/locomotion/robots/z1/12dof/velocity_env_cfg.py` |
| Agent config | `source/magiclab_rl_lab/magiclab_rl_lab/tasks/locomotion/agents/rsl_rl_ppo_cfg.py` |
| Train script | `scripts/rsl_rl/train.py` |

### Common Issues

| Symptom | Fix |
|---------|-----|
| SSH timeout | Connect iNode VPN first |
| `isaacsim.asset` not found | Extension auto-downloads on first run |
| `KeyError: 'actor'` | rsl-rl version mismatch, install `rsl-rl-lib==3.0.1` |
| iray permission error | `rm -rf ~/.local/share/ov/data/exts/v2/omni.iray.libs-*` |
| Wrong URDF path | Check `MAGICLAB_ROS_DIR` in `magiclab.py` |
| Isaac Sim video all black | Renderer needs warmup — use updated `play_z1_video.py` (20-step warmup built-in) |
| Isaac Sim robot not visible | Camera stuck at origin — use updated `play_z1_video.py` (camera tracking built-in) |
| MuJoCo robot falls | Use `mujoco_sim2sim.py` (has all sim2sim fixes) |

### Connection Details

See `D:\Desktop_Files\GPU-Train\RTX6000\docs\RTX_Server_Guide.html` for full VPN and SSH setup, and `D:\Desktop_Files\GPU-Train\RTX6000\Magicbot_Z1\docs\guides\Z1_Orchestrator_Guide.html` for Z1-specific orchestrator recovery and resume flows.
