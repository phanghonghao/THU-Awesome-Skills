---
name: plot-train-Z1
description: Generate and sync Z1 12DOF training learning curve plots from TensorBoard data on the RTX server, then compile a single-page A4 PDF report with plots + data analysis. Use when user mentions "plot training", "learning curve", "generate plots", "update plots", "学习曲线", "生成图表", "训练曲线", "训练报告", "生成报告".
---

# Plot Train Z1 — Learning Curve Plot Generator + PDF Report

Generate Z1 12DOF locomotion training plots from TensorBoard data on the RTX 6000 server, download locally, and compile a single-page A4 PDF report.

## Platform

| Property | Value |
|----------|-------|
| SSH Host | `<user>@<server_ip>` (VPN required) |
| Conda Env | `isaaclab` |
| Project Root (server) | `~/magiclab_rl_lab` |
| Log Root (server) | `~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity` |
| Plot Script (server) | `~/magiclab_rl_lab/scripts/plot_learning_curves.py` |
| Output Dir (server) | `~/magiclab_rl_lab/plots` |
| Local Plots Dir | `<your_data_path>` |
| Report Script (local) | `<your_data_path>` |
| best_models.json | `<your_data_path>` |
| bestmodel_phase.json | `<your_data_path>` |

## VPN

RTX server requires VPN connection. Use aTrust VPN (shortcut: `C:\Users\Public\Desktop\aTrust.lnk`).
If SSH connection fails, remind user to connect VPN first.

## best_models.json Update (Pre-report)

Before generating any PDF report, **always update `best_models.json`** so the report has full metrics (peak reward, overfitting status, etc.) rather than relying on the SSH fallback.

**Update step** (run before `gen_report_pdf.py`):

```bash
# 1. Run train_monitor on RTX to regenerate best_models.json
ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

# 2. Download updated best_models.json
scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
    "<your_data_path>"
```

This ensures new pipeline runs (p1_coarse, p1_fine, p2_coarse, etc.) are tracked with proper overfitting detection data.

## Local Directory Structure

Plots and reports are organized per-run:

```
plots/
├── phase_p1/
│   ├── 1_reward_trend.png
│   ├── 2_reward_decomposition.png
│   ├── 3_termination.png
│   ├── 4_efficiency.png
│   ├── report_phase_p1.pdf      ← auto-generated A4 PDF
│   ├── report_phase_p1.tex      ← preserved LaTeX source
│   └── report_phase_p1.md       ← Markdown summary
├── s4_full/
│   ├── ...
│   └── report_s4_full.pdf
└── README.md
```

Re-running for the same run replaces old files (no accumulation).

## Commands

The skill supports the following arguments (parsed from the user's invocation):

### Default (no arguments)

Generate all 4 plots on the server + download + compile PDF report.

**Steps:**
1. SSH to RTX server
2. Check if `plot_learning_curves.py` exists at the expected path
3. Run the script on the server:
   ```bash
   ssh <user>@<server_ip> "cd ~/magiclab_rl_lab && source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && python scripts/plot_learning_curves.py --log_root logs/rsl_rl/magiclab_z1_12dof_velocity --output_dir plots"
   ```
4. Download PNG files to temp directory, then organize into per-run folder:
   ```bash
   LOCAL_PLOTS="<your_data_path>"

   mkdir -p /tmp/z1_plots
   scp <user>@<server_ip>:~/magiclab_rl_lab/plots/*.png /tmp/z1_plots/

   ALIAS=$(ls /tmp/z1_plots/*.png 2>/dev/null | head -1 | sed 's/.*_\([a-z0-9_]*\)\.png/\1/' | xargs basename -s .png | sed 's/.*_//')

   mkdir -p "$LOCAL_PLOTS/$ALIAS"
   rm -f "$LOCAL_PLOTS/$ALIAS/"*.png
   mv /tmp/z1_plots/1_reward_trend_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/1_reward_trend.png"
   mv /tmp/z1_plots/2_reward_decomposition_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/2_reward_decomposition.png"
   mv /tmp/z1_plots/3_termination_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/3_termination.png"
   mv /tmp/z1_plots/4_efficiency_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/4_efficiency.png"
   rm -rf /tmp/z1_plots
   ```
5. Clean up old flat-format files (first run only):
   ```bash
   rm -f "$LOCAL_PLOTS/1_reward_comparison.png"
   rm -f "$LOCAL_PLOTS/2_reward_decomposition_"*.png
   rm -f "$LOCAL_PLOTS/3_termination_"*.png
   rm -f "$LOCAL_PLOTS/4_efficiency_"*.png
   ```
6. **Update best_models.json** (before generating report):
   ```bash
   ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

   scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
       "<your_data_path>"
   ```
7. **Generate PDF report** (local):
   ```bash
   cd "<your_data_path>"
   python scripts/gen_report_pdf.py --alias $ALIAS
   ```
8. Open the PDF for the user:
   ```bash
   start "" "$LOCAL_PLOTS/$ALIAS/report_$ALIAS.pdf"
   ```

### `--focus <RUN>`

Specify a focus run for all 4 plots + PDF report.

**Run aliases** (from plot script `RUN_ALIASES`):

*5-phase pipeline runs:*
- `p1_coarse` → `2026-05-06_15-47-12_p1_coarse`
- `p1_fine` → `2026-05-06_17-40-13_p1_fine`
- `p2_coarse` → `2026-05-06_18-49-40_p2_coarse`
- `p2_fine` → `2026-05-06_19-33-51_p2_fine`
- `p3_coarse` → `2026-05-07_03-56-16_p3_coarse`

*Legacy single-stage runs:*
- `s1_flat` → `2026-04-30_04-53-17_s1_flat`
- `s2_gentle` → `2026-05-01_04-50-05_s2_gentle`
- `s3_rough_l2` → `2026-05-01_07-04-35_s3_rough_l2`
- `s4_full` → `2026-05-04_16-56-05_s4_full_terrain`
- `s4_flat_deploy` → `2026-05-05_04-47-06_s4_flat_deploy`
- `s5_explicit_pd` → `2026-05-05_13-57-30_s5_explicit_pd`

*Note:* New pipeline runs are added as they start. Always check `RUN_ALIASES` in the server script for the latest list.

**Steps:**
1. Resolve alias to full run dir name (check `RUN_ALIASES` in the plot script)
2. Run with `--focus_run <dir_name>`:
   ```bash
   ssh <user>@<server_ip> "cd ~/magiclab_rl_lab && source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && python scripts/plot_learning_curves.py --log_root logs/rsl_rl/magiclab_z1_12dof_velocity --output_dir plots --focus_run <FULL_DIR_NAME>"
   ```
3. Download and organize into per-run folder:
   ```bash
   LOCAL_PLOTS="<your_data_path>"
   ALIAS="<the alias, e.g. phase_p1>"

   mkdir -p /tmp/z1_plots
   scp <user>@<server_ip>:~/magiclab_rl_lab/plots/*.png /tmp/z1_plots/

   mkdir -p "$LOCAL_PLOTS/$ALIAS"
   rm -f "$LOCAL_PLOTS/$ALIAS/"*.png
   mv /tmp/z1_plots/1_reward_trend_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/1_reward_trend.png"
   mv /tmp/z1_plots/2_reward_decomposition_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/2_reward_decomposition.png"
   mv /tmp/z1_plots/3_termination_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/3_termination.png"
   mv /tmp/z1_plots/4_efficiency_${ALIAS}.png "$LOCAL_PLOTS/$ALIAS/4_efficiency.png"
   rm -rf /tmp/z1_plots
   ```
4. **Update best_models.json** (before generating report):
   ```bash
   ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

   scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
       "<your_data_path>"
   ```
5. **Generate PDF report** (local):
   ```bash
   cd "<your_data_path>"
   python scripts/gen_report_pdf.py --alias $ALIAS
   ```
6. Open the PDF:
   ```bash
   start "" "$LOCAL_PLOTS/$ALIAS/report_$ALIAS.pdf"
   ```

### `--sync`

Download latest TensorBoard data and regenerate all plots + PDF. Equivalent to default but forces re-read of all event files.

This is the same as the default flow — the script always reads from TensorBoard event files, so re-running naturally syncs.

### `--update-readme`

Only update the local `plots/README.md` without regenerating plots.

**Steps:**
1. Read `<your_data_path>`
2. List existing PNG files in per-run subfolders under `plots/`
3. Update the overview table, key findings, and recommendations sections
4. Ensure image references use `plots/<alias>/` paths

### `--all-runs`

Generate all 4 plots + PDF reports for every run with >5000 data points.

**Steps:**
1. SSH to server, list all run directories
2. For each significant run, run with `--focus_run <dir_name>`
3. For each run, download and organize into `plots/<alias>/` folder
4. **Update best_models.json** (once, before all reports):
   ```bash
   ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

   scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
       "<your_data_path>"
   ```
5. For each run, run `gen_report_pdf.py --alias <alias>` locally
6. This may take several minutes — warn the user

### `--pipeline`

Generate plots + PDF reports for all runs tracked in `bestmodel_phase.json`. This is the recommended way to batch-generate reports for 5-phase pipeline runs.

**Steps:**
1. Read `<your_data_path>` to get all run aliases
2. **Update best_models.json** (once, before all reports):
   ```bash
   ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

   scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
       "<your_data_path>"
   ```
3. For each run in bestmodel_phase.json (that has data), generate plots on server:
   ```bash
   ssh <user>@<server_ip> "cd ~/magiclab_rl_lab && source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && python scripts/plot_learning_curves.py --log_root logs/rsl_rl/magiclab_z1_12dof_velocity --output_dir plots --focus_run <FULL_DIR_NAME>"
   ```
4. Download and organize into per-run folders (same as `--focus` flow)
5. Generate PDF report for each run:
   ```bash
   cd "<your_data_path>"
   python scripts/gen_report_pdf.py --alias <ALIAS>
   ```
6. Open all generated PDFs

**Important:** Server-side `plot_learning_curves.py` uses a smart x-axis formatter that adapts precision:
- Values < 10k iterations → `.1f` precision (e.g. "2.9k, 3.0k, 3.1k")
- Values >= 10k → `.0f` precision (e.g. "12k, 15k, 20k")

### `--pdf-only <RUN>`

Only regenerate the PDF report from existing plot PNGs (skip server plot generation).

**Steps:**
1. Verify all 4 PNGs exist in `plots/<alias>/`
2. **Update best_models.json**:
   ```bash
   ssh <user>@<server_ip> "source ~/miniconda3/etc/profile.d/conda.sh && conda activate isaaclab && cd ~/magiclab_rl_lab && python -u scripts/train_monitor.py --once --terrain gentle 2>/dev/null"

   scp <user>@<server_ip>:~/magiclab_rl_lab/logs/rsl_rl/magiclab_z1_12dof_velocity/best_models.json \
       "<your_data_path>"
   ```
3. Run:
   ```bash
   cd "<your_data_path>"
   python scripts/gen_report_pdf.py --alias <ALIAS>
   ```
4. Open the PDF

## Error Handling

| Error | Action |
|-------|--------|
| SSH connection refused | Remind user to connect aTrust VPN |
| `plot_learning_curves.py` not found | Script may not be uploaded yet; offer to create it from local copy at `<your_data_path>` |
| No TensorBoard events | Run may not have started or crashed; check training log |
| Python import error (tensorboard) | Install: `pip install tensorboard matplotlib` |
| SCP fails | Check VPN, try with `-o StrictHostKeyChecking=no` |
| `gen_report_pdf.py` fails | Check MikTeX is installed, all 4 PNGs exist, best_models.json is valid |
| pdflatex not found | Check MikTeX installation at `C:\MiKTeX\miktex\bin\x64\pdflatex.exe` |

## Output Files

After successful generation, the following files should exist in `plots/<alias>/`:

| File | Description |
|------|-------------|
| `1_reward_trend.png` | Single run reward trend with peak/best annotations + progress bar |
| `2_reward_decomposition.png` | Reward components + curriculum progress |
| `3_termination.png` | Termination reasons + episode length |
| `4_efficiency.png` | Throughput, time, entropy, LR |
| `report_<alias>.pdf` | Single-page A4 PDF with 4 plots + data summary + analysis |
| `report_<alias>.tex` | LaTeX source (preserved for reference) |
| `report_<alias>.md` | Markdown summary with metrics table and analysis |

## References

See `references/plots.md` for detailed plot type descriptions and interpretation guide.
