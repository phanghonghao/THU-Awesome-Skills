---
name: rtx-training-capture
description: >-
  Check the latest training log, verify RTX training results, analyze
  success/failure, record best-iter video, and pull artifacts back to local.
  Use when user mentions "rtx-training-capture", "training results",
  "录制视频", "拉取训练成果", "training log 收尾", "训练完成收尾",
  "capture training", "wrap up training", "训练成果归档".
---

# rtx-training-capture

Wrap up a finished (or failed) RTX training run: read the latest daily log,
verify job state on the server, judge success/failure from the convergence
report, then either record+pull (success) or archive+log (failure).

## Start Here

1. Read `references/rtx_paths.md` for the canonical server paths, conda envs,
   and asset categories.
2. Read `references/success_criteria.md` for the episode-length / reward /
   value-loss thresholds that distinguish success from failure.
3. Read `references/slurm_templates.md` for the recording Slurm template and
   the SCP pull commands.
4. Read `references/canonical_naming.md` for the asset naming rules
   (also in the project's own `CLAUDE.md` at the project root).

## Invocation

- `/rtx-training-capture` — process the latest daily log's open TODOs.
- `/rtx-training-capture --job 386` — process a specific Slurm job.
- `/rtx-training-capture --task T1-Reach` — filter by task name.
- `/rtx-training-capture --dry-run` — only list the planned steps, do not
  execute record/SCP/manifest writes.

## Connection Policy

SSH to the RTX server (`ssh phh@192.168.120.155`) first. If the
connection fails with timeout or connection refused (VPN not up),
auto-launch iNode VPN and retry — do **not** ask the user for
confirmation before launching VPN.

1. Launch iNode VPN:
   ```powershell
   Start-Process 'C:\Program Files (x86)\iNode\iNode Client\iNode Client.exe'
   ```
2. Wait 3 seconds.
3. Retry the SSH command.
4. Keep retrying every 3 seconds, up to 10 attempts total.
5. Only report failure after all retries fail.

This mirrors the `gpu-train` connection policy; keep the two in sync if
the iNode path or retry cadence ever changes.

## Five-Step Workflow

### Step 1 — Read latest training log

The **project root** is the folder Claude Code was launched in (the current
working directory) — NOT a hardcoded path. This skill is project-agnostic:
all `docs/`, `assets/`, `scripts/` paths below are relative to whichever
project you invoke it from.

Glob `docs/Training_Daily_Log/*_Daily_Training_Log.md` under the project
root, sort by name, take the newest. Extract the "## 待办" / TODO section
and list open `[ ]` items.

For each item, identify:
- Slurm Job ID (from the log text)
- Task name (e.g. `T1-Reach-v0`)
- Remote output dir (e.g. `~/output/t1_reach_v6_warmstart_<ts>`)
- Whether a `convergence_report.json` is expected

Present the list to the user and confirm scope before moving on. With
`--job N` or `--task X`, filter to matching items only.

### Step 2 — Remote verification

For each target job, SSH and run:

```bash
ssh phh@192.168.120.155 "
  squeue -u phh | grep -E '(JOBID|<JOB_ID>)' || echo 'not in queue'
  ls -la ~/output/<task>_v*/convergence_report.json 2>/dev/null | tail -1
  ls -la ~/output/<task>_v*/train.log 2>/dev/null | tail -1
"
```

Decision tree:
- `squeue` shows the job still running → report "still running, ETA <X>",
  do not record yet. Skip.
- Job exited and `convergence_report.json` exists → parse it (Step 3).
- Job exited but no convergence_report → fall back to parsing `train.log`
  directly for the last 200 lines and extract `Mean reward`, `Mean episode
  length`, `Mean value loss`.

### Step 3 — Success / failure judgment

Pull the convergence_report.json and inspect these fields:

| Signal                 | Success               | Failure                          |
|------------------------|-----------------------|----------------------------------|
| `latest_metrics.episode_length` | ≥ 500        | < 200 (falls / terminates fast)  |
| reward trend (latest vs peak)   | close OR rising | latest << peak and flat     |
| `latest_metrics.value_loss`     | < 10         | > 50 (failed to converge)        |
| `overfitting_detected`          | inspect `overfitting_reason` — often a false alarm (early spike artifact); only treat as failure if late-stage reward stays depressed |

See `references/success_criteria.md` for worked examples from T1 Stand v4
(success, peak 399@7732, ep_len 1000) vs T1 Reach v4/v5 (failure, ep_len
stuck at 102).

If the result is ambiguous, present the data and ask the user; do not
auto-record.

### Step 4 — Success path: record + pull

1. Identify the canonical checkpoint:
   - Prefer `best_checkpoint_file` from `convergence_report.json`
   - If that exact iter was not saved, take the nearest saved `model_<N>.pt`
     and record the mapping in `run_manifest.json`.

2. Generate the recording Slurm on RTX. Use the template in
   `references/slurm_templates.md`. Key substitutions:
   - `#SBATCH -J` → `<task>_<version>_rec`
   - `--task-id` and `--checkpoint-file`
   - `--output-dir` → `~/output/<task>_<version>_best_recording`

3. `sbatch` the recording job. Wait ~3 minutes for the 1000-step rollout
   to finish (use `squeue -u phh` to track).

4. Verify the output:
   ```bash
   find ~/output/<task>_<version>_best_recording -name "*.mp4"
   ```

5. SCP pull (both model and video) to the local task folder:
   ```
   assets/<category>/<task>/models/model_<N>.pt
   assets/<category>/<task>/videos/<task>_play_video_model_<N>.mp4
   ```
   Use the canonical names from `references/canonical_naming.md`.

6. Update `assets/<category>/<task>/training_records/run_manifest.json`:
   - Set `canonical_run` with version, checkpoint, reward, episode_length,
     selection_policy, selection_note.
   - Move any previous canonical to `retained_auxiliary` with a note.

7. Also pull the convergence_report.json and TensorBoard
   `events.out.tfevents.*` into `training_records/` for future plotting.

8. Regenerate the reward curve via
   `scripts/generate_reward_curves.py` (or its `save_plot()` helper if a
   specific events file must be targeted).

### Step 5 — Failure path: archive + log

1. SCP `convergence_report.json` (if it exists) to
   `assets/<category>/<task>/training_records/convergence_report_<version>.json`.
2. Do NOT record a video.
3. Append a new section to the day's
   `docs/Training_Daily_Log/<date>_Daily_Training_Log.md`:
   - Section header: `### <task> <version> — FAILED`
   - Reward curve summary (start / peak / final)
   - Episode-length trend
   - Value-loss trend
   - Root-cause hypothesis (refer to `references/success_criteria.md`
     patterns: reward-shaping exploit, obs-modality miss, curriculum
     activation timing, warm-start mismatch, etc.)
   - Next-step recommendation (curriculum change, hyperparam change,
     architecture change, gather better demos, etc.)

## Operating Rules

- **Never** delete an existing canonical video/model just because a new run
  finished. Always move the previous canonical to `retained_auxiliary`.
- **Never** treat `_best.mp4`, `_final.mp4`, or raw recorder outputs as
  canonical archive names. Rename to `<task>_play_video_model_<N>.mp4`.
- **Never** select a checkpoint purely by "highest numbered model_*.pt".
  Use the convergence report's `best_checkpoint_file` first.
- **Always** strip CRLF (`sed -i 's/\r$//'`) before sbatch on any Slurm
  script generated locally and uploaded.
- **Always** run the 7-point dry-run from `CLAUDE.md` before submitting a
  *training* job (not needed for recording jobs — they are short and the
  template is pre-verified).
- **Always** record the canonical model + video as a pair; never archive
  one without the other.

## Reference Files

- `references/rtx_paths.md` — RTX server paths, conda envs, asset categories
- `references/success_criteria.md` — success/failure thresholds with examples
- `references/slurm_templates.md` — recording Slurm template, SCP commands
- `references/canonical_naming.md` — model / video / manifest naming rules
