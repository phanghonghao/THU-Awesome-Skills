---
name: merge
description: Merge multiple videos into a single grid video (3x1 vertical, 2x2, 3x2 layouts). Supports custom labels per cell. Use when user mentions "merge videos", "合并视频", "拼视频", "视频对比", "video grid", "视频拼接", "compare videos", "side by side video".
---

# Merge Videos

Merge multiple MP4 videos into a single grid-layout video with optional labels.

## Permanent Script

The merge tool is a permanent CLI script at:
```
<SKILL_ROOT>/merge_videos.py
```

**DO NOT generate temp scripts.** Always call this script directly via `python`.

## Templates

| Template | Layout | Video Count | Description |
|----------|--------|-------------|-------------|
| `2x1` | 2 rows, 1 col | 2 | Vertical stack of 2 videos |
| `3x1` | 3 rows, 1 col | 3 | Vertical (portrait), stacked top to bottom |
| `2x2` | 2 rows, 2 cols | 4 | Square grid, TL TR BL BR |
| `3x2` | 3 rows, 2 cols | 6 | Tall grid, 6 cells |
| `NxM` | Custom | NxM | Any arbitrary grid, auto-parsed |

Auto-detect template when `-t` is omitted:
- 2 videos → `2x1`
- 3 videos → `3x1`
- 4 videos → `2x2`
- 6 videos → `3x2`

## Workflow

1. Find video paths from user arguments (glob directory if needed)
2. Determine template (auto-detect or explicit `-t`)
3. Auto-generate labels from folder/filenames if not provided
4. Run the permanent script directly:
   ```bash
   python "<SKILL_ROOT>/merge_videos.py" <video_paths> -t <template> --labels <labels...> -o <output>
   ```
5. Report output path, frame count, file size
6. **Never create temp scripts or temp files**

## CLI Parameters

```
python merge_videos.py VIDEO [VIDEO ...] [-t TEMPLATE] [--labels LABEL [LABEL ...]]
                       [-o OUTPUT] [--gap N] [--fps N] [--font-size N] [--no-labels]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `videos` | Input video file paths (positional) | Required |
| `-t` / `--template` | Layout: `2x1`, `3x1`, `2x2`, `3x2`, or custom `NxM` | Auto-detect from count |
| `--labels` | Custom label for each cell | Auto from folder/filename |
| `-o` / `--output` | Output file path | `<first_video_dir>/merge_<template>.mp4` |
| `--gap` | Pixel gap between cells | 4 |
| `--fps` | Output frame rate | 30 |
| `--font-size` | Label font size | 20 |
| `--no-labels` | Skip cell labels | Off |

## Example Invocations

**2x2 grid (4 videos in a directory):**
```bash
python "<SKILL_ROOT>/merge_videos.py" \
  "dir/v1.mp4" "dir/v2.mp4" "dir/v3.mp4" "dir/v4.mp4" \
  -t 2x2 --labels "iter 1700" "iter 3000" "iter 5000" "iter 7000"
```

**3x1 vertical (auto-detect from 3 videos):**
```bash
python "<SKILL_ROOT>/merge_videos.py" \
  "dir/v1.mp4" "dir/v2.mp4" "dir/v3.mp4" \
  --labels "IsaacLab" "MuJoCo Humanoid" "MuJoCo Manual"
```

**3x2 grid (6 videos, custom output):**
```bash
python "<SKILL_ROOT>/merge_videos.py" \
  v1.mp4 v2.mp4 v3.mp4 v4.mp4 v5.mp4 v6.mp4 \
  -t 3x2 -o result/comparison.mp4
```

**Custom NxM grid (e.g. 2x3):**
```bash
python "<SKILL_ROOT>/merge_videos.py" \
  v1.mp4 v2.mp4 v3.mp4 v4.mp4 v5.mp4 v6.mp4 \
  -t 2x3
```

## Extending with New Templates

The script already supports arbitrary `NxM` templates via auto-parsing (e.g. `-t 4x3`).
If a genuinely new structure is needed that cannot be expressed as a grid, add it to
`LAYOUTS` dict in `merge_videos.py` with custom layout logic.

## Prerequisites

- Python packages: `pip install av imageio imageio-ffmpeg Pillow numpy`
- All videos should have similar resolution; they will be resized to the smallest common resolution
- Videos are cropped to the shortest duration
