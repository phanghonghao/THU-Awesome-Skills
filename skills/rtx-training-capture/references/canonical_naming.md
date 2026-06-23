# Canonical Asset Naming

Extracted from the project's own `CLAUDE.md` and `assets/AGENTS.md` (both
relative to the current project root). These rules override convenience;
do not invent new naming schemes.

## Local asset layout

```
assets/
├── Locomotion/            all locomotion task artifacts (RL)
│   └── <task>/
│       ├── models/
│       ├── videos/
│       ├── plots/
│       └── training_records/
│           ├── run_manifest.json
│           ├── convergence_report_<version>.json
│           ├── events.out.tfevents.*
│           └── run_summary.json (optional)
├── Manipulation/          all manipulation task artifacts (RL + VLA/WM)
│   ├── franka_<task>/       RL checkpoints and videos
│   ├── bc_franka_<task>/    BC results
│   ├── act_franka_<task>/   ACT results
│   ├── vla_openpi/          OpenPI VLA results
│   ├── world_model_tdmpc2/  TD-MPC2 world model results
│   ├── world_model_dreamerv3/ DreamerV3 world model results
│   └── robomimic_ph_<task>/ RoboMimic PH community results
├── batch_videos/          convenience batch mirror
└── merge_*.mp4            stitched merge videos
```

## Canonical names

### Models

```
assets/<category>/<task>/models/model_<N>.pt
```

`<N>` is the iteration count of the saved checkpoint, zero-padded only if
the source training run zero-pads it. Always use the raw
`model_<N>.pt` form — do NOT rename to `model_best.pt`,
`model_final.pt`, etc.

### Videos

```
assets/<category>/<task>/videos/<task>_play_video_model_<N>.mp4
```

The `<task>` prefix must match the task folder name exactly. The
`model_<N>` suffix must match the model file used to generate the video.
This pairing is mandatory: a video without its model is not canonical.

### Auxiliary variants

If you need to keep a non-canonical copy (e.g. legacy, raw recorder
output, differently compressed), use explicit suffixes:

- `_legacy`   — older format / superseded
- `_rtx`      — recorded on RTX (as opposed to local replay)
- `_local_usd` — recorded from local USD scene

Examples:
- `mjlab_t1_stand_play_video_model_500_legacy.mp4`
- `mjlab_t1_stand_play_video_model_500_local_usd.mp4`

Do NOT use ad hoc names like `*_best.mp4`, `*_final.mp4`, or
`recorder_output_step0.mp4`. Either delete them or rename to the
canonical form.

## Selection rule

For replay or archival, select the best checkpoint — NOT the
highest-numbered `model_<N>.pt`. Priority:

1. `convergence_report.best_checkpoint_file` (reward-best)
2. Best validated checkpoint
3. Explicitly selected best from logs or curves
4. Fall back to latest checkpoint ONLY when no quality signal exists

When the best iteration was not saved exactly, use the nearest saved
checkpoint to that best iteration and document the mapping in
`run_manifest.json`:

```json
{
  "selection_policy": "nearest_saved_best_iter",
  "best_iter": 7732,
  "selected_checkpoint_iter": 7800,
  "selection_note": "Best iter 7732 not saved; nearest is 7800 (Δ=68)."
}
```

## run_manifest.json structure

The local source of truth for the selected canonical checkpoint. Lives
at `assets/<category>/<task>/training_records/run_manifest.json`.

```json
{
  "framework": "<framework_name>",
  "canonical_run": {
    "version": "<version_tag>",
    "remote_run_dir": "<RTX path to the run dir>",
    "selected_checkpoint": "model_<N>.pt",
    "pulled_at_local": "<ISO timestamp>",
    "local_models": ["model_<N>.pt"],
    "local_videos": ["<task>_play_video_model_<N>.mp4"],
    "best_iter": <int>,
    "best_reward": <float>,
    "selected_checkpoint_iter": <int>,
    "selected_checkpoint_reward": <float>,
    "latest_iter": <int>,
    "latest_reward": <float>,
    "episode_length": <int>,
    "value_loss_final": <float>,
    "selection_policy": "<convergence_report_best_model | nearest_saved_best_iter | ...>",
    "selection_note": "<human-readable explanation, including any anomalies>"
  },
  "retained_auxiliary": [
    {
      "version": "<older_version>",
      "remote_run_dir": "...",
      "selected_checkpoint": "model_<M>.pt",
      "pulled_at_local": "...",
      "local_models": ["..."],
      "local_videos": ["..."],
      "best_iter": <int>,
      "best_reward": <float>,
      "selection_policy": "...",
      "note": "<why this is retained, e.g. 'Superseded by v4' or 'Energy threshold fix prototype'>"
    }
  ],
  "best_reward_tag": "Train/mean_reward"
}
```

When a new canonical run is selected, MOVE the previous canonical_run
block into retained_auxiliary[0]. Do not delete it.

## Asset alignment check

A task folder is "aligned" iff all three hold:

1. The selected checkpoint exists under `models/`.
2. The matching canonical video exists under `videos/`.
3. The pair is consistent with the recorded best-selection evidence in
   `training_records/run_manifest.json`.

When pulling new artifacts, verify alignment at the end. If anything is
missing, document the gap in the daily log rather than silently leaving
the folder half-aligned.
