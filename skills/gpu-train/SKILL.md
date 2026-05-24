---
name: gpu-train
description: >-
  Monitor and manage remote RL training on the RTX PRO 6000 server over SSH.
  Check training status, tail logs, inspect GPU usage, find idle GPUs, show my
  CUDA usage, review Slurm jobs and bypass violations, analyze failures, record
  simulation videos, and manage multi-phase automation pipelines. Use when the
  user mentions training status, GPU usage, my CUDA, logs, overfitting, best
  model, pipeline, phase training, Slurm, queue, bypass, ARM101, ACT monitor,
  鑷姩鍖杙ipeline, 杩滅▼璁粌, 璁粌鐘舵€? GPU鍗犵敤, 鎴戠殑CUDA, 杩囨嫙鍚? 鏈€浣虫ā鍨?
  璁粌鍒嗘瀽, 澶辫触鍒嗘瀽, 鍙傛暟璋冧紭, 鎺掗槦, 杩濊妫€娴? 璋佸湪鐢℅PU.
---

# GPU Train

Monitor and manage RL training jobs on the remote RTX server.

## Start Here

Read `references/platforms.md` before issuing commands that depend on:
- SSH host
- conda environment
- project root
- log paths
- checkpoint paths
- video recording commands

Treat `references/platforms.md` as the source of truth for platform-specific paths and commands.

Supplementary HTML references:
- `D:\Desktop_Files\GPU-Train\RTX6000\docs\RTX_Server_Guide.html` for VPN, SSH, Slurm, and RTX-side workflow details.
- `D:\Desktop_Files\GPU-Train\RTX6000\docs\GPU_Train_Command_Reference.html` for supported `/gpu-train` command patterns and orchestrator entry points.
- `D:\Desktop_Files\GPU-Train\RTX6000\Magicbot_Z1\docs\guides\Z1_Orchestrator_Guide.html` for Z1 pipeline state, resume, adopt, and recovery behavior.
- `D:\Desktop_Files\GPU-Train\RTX6000\Magicbot_Z1\docs\guides\gpu_train_sim_pipeline_light.html` for the current remote-record, local-fetch simulation video pipeline.

Execution mapping for current orchestrator flows:
- `/gpu-train --orchestrator --start` -> fresh full pipeline via `bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh`
- `/gpu-train --orchestrator --start --from <sub_phase>` -> fresh start from a specific sub-phase via `bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh --from <sub_phase>`
- `/gpu-train --orchestrator --resume` -> state resume via `bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh --resume`
- Prefer the Slurm wrapper above over direct `nohup python ... phase_orchestrator.py` unless the user explicitly asks for a manual direct launch or Slurm is unavailable.
- Before any orchestrator resume, verify `~/magiclab_rl_lab/orchestrator_state.json` exists on `rtx`.
- If the user gives both `--resume` and a phase hint such as `p3_fine`, prefer state resume when the state file exists; if no state exists, say so explicitly and treat the phase hint as a fresh `--start --from <sub_phase>` request.

## Connection Policy

When connecting to the `rtx` server and SSH fails with timeout or connection refused:

1. Launch iNode VPN:
   ```powershell
   Start-Process 'C:\Program Files (x86)\iNode\iNode Client\iNode Client.exe'
   ```
2. Wait 3 seconds.
3. Retry the SSH command.
4. Keep retrying every 3 seconds, up to 10 attempts total.
5. Only report failure after all retries fail.

Do not ask the user for confirmation before launching iNode for this recovery flow.

## Operating Rules

- Prefer short SSH one-liners and summarize the results clearly.
- For training status, show whether the process is alive and where the active log is.
- For log tails, show the last 30 lines unless the user asks for a different window.
- For GPU checks, include utilization, memory use, and which GPUs are actually free.
- For Slurm checks, distinguish normal Slurm usage from bypassed direct GPU usage.
- Do not kill training, orchestrators, or remote jobs without explicit user confirmation.
- When the user asks for analysis, provide a conclusion, the evidence, and a concrete next action.

## Core Tasks

### Check connectivity

Use an SSH echo test first. If it fails, apply the VPN retry policy.

### Check training status

Detect whether training is running from remote process lists. Use the platform-specific process pattern from `references/platforms.md`.

Report:
- running or not running
- project type if clear
- PID when available
- active run name if available

### Tail logs

Read the active training log and summarize:
- current iteration or step
- speed
- elapsed time
- ETA if visible
- key metrics such as reward or loss
- one-line health assessment in Chinese

Prefer a compact snapshot instead of a long raw dump unless the user explicitly asks for raw logs.

For `Magicbot_Z1` tails:
- Before reading remote logs, run `powershell -ExecutionPolicy Bypass -File D:\Desktop_Files\GPU-Train\RTX6000\sync_magicbot_z1_tracking.ps1`.
- This must refresh `~/magiclab_rl_lab/docs/tracking/bestmodel_phase.json` on RTX and pull it back to `D:\Desktop_Files\GPU-Train\RTX6000\Magicbot_Z1\docs\tracking\bestmodel_phase.json` locally.
- If the remote tracking JSON is unexpectedly empty while the local file is populated, do not overwrite the local file; report the sync failure instead.

### Check GPU usage

Use `nvidia-smi` on the remote host and report:
- per-GPU utilization
- used and total memory
- active compute processes when relevant

### Find idle GPUs

Treat a GPU as idle only when both are true:
- utilization is below 10%
- memory usage is below 5% of total or below 5 GB

Recommend a specific `cuda:<id>` device when idle GPUs are found.

### Show my CUDA usage

Show only GPU compute processes belonging to the configured remote user from `references/platforms.md`.

### Review Slurm state

For Slurm-related requests:
- inspect queue and running jobs
- identify GPU processes not attached to Slurm jobs
- summarize bypass violations clearly
- report affected GPU, PID, user, and command if available

## Project Variants

Handle these common project families separately when the user is specific:

### Z1 locomotion

Focus on:
- reward
- episode length
- tracking metrics
- terrain curriculum
- termination ratios
- best checkpoint and exported policy when relevant

### ARM101 / ACT

Focus on:
- current step
- current loss
- best loss
- GPU device
- training speed
- convergence trend

## Pipeline / Orchestrator Work

For multi-phase pipeline requests:

1. Check whether the orchestrator is already running.
2. Read its state file if present.
3. Report current phase, run directory, best model, rollback count, and recent progress.
4. On stop requests, show exactly what would be stopped and wait for explicit confirmation.
5. On resume requests, verify the saved state exists before launching.
6. For `/gpu-train --orchestrator --resume`, use the Slurm wrapper `bash D:/Desktop_Files/GPU-Train/RTX6000/rtx_submit_orchestrator_train.sh --resume` by default.
7. For `/gpu-train --orchestrator --start` with no phase, start the full pipeline from the beginning; do not silently default to `p3_fine`.

## Video and Artifact Handling

When the user asks for simulation videos or model artifacts:

1. Find the run directory and checkpoint.
2. Use the platform-specific recording commands from `references/platforms.md`.
3. Download requested outputs to the local project location the user is already using.
4. Report the local paths and whether the operation succeeded.

## Response Style

Prefer this order in responses:
1. Current state
2. Key metrics
3. Health assessment
4. Recommended next action

Keep outputs concise unless the user asks for full raw logs.
