# Slurm Templates and SCP Commands

## Recording Slurm template

This template is verified working (used for T1 Stand v4 best-iter recording
on 2026-06-13). Copy and substitute the four `<...>` placeholders.

```bash
#!/bin/bash
#SBATCH -J <task>_<version>_rec
#SBATCH -p gpu
#SBATCH --gpus=1
#SBATCH -c 4
#SBATCH -t 00:30:00
#SBATCH -o /home/phh/slurm_logs/<task>_<version>_rec_%j.out
#SBATCH -e /home/phh/slurm_logs/<task>_<version>_rec_%j.err

set -eo pipefail
export PYTHONUNBUFFERED=1
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl

source ~/miniconda3/etc/profile.d/conda.sh
conda activate <conda_env>

CKPT=<remote_checkpoint_path>
OUT=/home/phh/output/<task>_<version>_best_recording

echo "[INFO] Recording started at $(date) job=$SLURM_JOB_ID"
echo "[INFO] Checkpoint: $CKPT"
echo "[INFO] Output dir: $OUT"

ls -la "$CKPT" || { echo "[ERR] Checkpoint missing"; exit 1; }

mkdir -p "$OUT"
cd ~/<project_root>     # e.g. ~/booster_t1_mjlab

python ~/record_headless.py <task_id> \
  --checkpoint-file "$CKPT" \
  --num-envs 1 \
  --video-length 1000 \
  --output-dir "$OUT" \
  --device cuda:0 \
  2>&1 | tee "$OUT/record.log"

echo "[INFO] Recording done at $(date)"
echo "[INFO] === Video files ==="
find "$OUT" -name "*.mp4" -exec ls -la {} \;
```

### Substitution cheat sheet (T1 tasks)

| Placeholder        | Stand v4 example                                                       |
|--------------------|------------------------------------------------------------------------|
| `<task>_<version>` | `t1_stand_v4`                                                          |
| `<conda_env>`      | `unitree_rl_mjlab`                                                     |
| `<remote_checkpoint_path>` | `/home/phh/booster_t1_mjlab/logs/rsl_rl/T1-Stand-PPO/2026-06-13_15-47-54/model_7800.pt` |
| `<project_root>`   | `booster_t1_mjlab`                                                     |
| `<task_id>`        | `T1-Stand-v0`                                                          |

## Common pitfalls

1. **CRLF line endings** — Windows-generated Slurm scripts must be cleaned:
   ```bash
   ssh phh@192.168.120.155 "sed -i 's/\r$//' ~/record_<...>.slurm"
   ```
   Skipping this causes `/bin/bash^M: bad interpreter` errors.

2. **CUDA_VISIBLE_DEVICES** — do NOT set or unset it manually. Slurm
   auto-sets it from `--gres=gpu:1`. The recording script's `--device
   cuda:0` resolves to "first visible GPU" = Slurm's allocation.

3. **MUJOCO_GL** — must be `egl` (or `osmesa` as fallback). Without it,
   headless rendering fails.

4. **Checkpoint missing** — the template's `ls -la "$CKPT"` guard catches
   this. The job exits cleanly rather than running with a stale path.

## SCP pull commands

After the recording job completes (~3 min):

```bash
# 1. Find the output video
ssh phh@192.168.120.155 "find ~/output/<task>_<version>_best_recording -name '*.mp4'"

# 2. Pull both model and video (run from the current project root)
scp phh@192.168.120.155:<remote_ckpt_path> \
    assets/<category>/<task>/models/model_<N>.pt

scp phh@192.168.120.155:~/output/<task>_<version>_best_recording/<video_file>.mp4 \
    assets/<category>/<task>/videos/<task>_play_video_model_<N>.mp4
```

The video file from `record_headless.py` is typically named
`rl-video-step-0.mp4`. Rename on the local side to the canonical
`<task>_play_video_model_<N>.mp4`.

## Pull convergence report and TensorBoard events

```bash
scp phh@192.168.120.155:<remote_run_dir>/convergence_report.json \
    assets/<category>/<task>/training_records/convergence_report_<version>.json

scp phh@192.168.120.155:<remote_run_dir>/events.out.tfevents.* \
    assets/<category>/<task>/training_records/
```

Optionally prefix the events file with `v<version>_` to disambiguate when
multiple versions coexist (e.g.
`events.out.tfevents.v4_2026-06-13_15-47-54`).

## Regenerate reward curve locally

From the **current project root** (the folder Claude Code was launched in):

```bash
# Generic (auto-discovers via run_manifest.json):
.venv_mjlab/Scripts/python.exe scripts/generate_reward_curves.py

# Specific events file (when multiple versions coexist):
.venv_mjlab/Scripts/python.exe -c "
import sys
sys.path.insert(0, 'scripts')
from generate_reward_curves import save_plot
from pathlib import Path
task_dir = Path('assets/<category>/<task>')
event_file = task_dir / 'training_records' / 'events.out.tfevents.v<version>_<ts>'
print(save_plot(task_dir, event_file))
"
```

The generic path uses `sorted(...)[0]` which picks the alphabetically
first events file — that may be a stale v1 file when a newer v4 exists.
Use the specific-events-file form to override.
