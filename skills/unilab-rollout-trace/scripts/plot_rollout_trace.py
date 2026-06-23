"""Plot a UniLab off-policy rollout trace summary CSV.

Reads one or more ``*.summary.csv`` files produced by
``UniLab/scripts/record_offpolicy_rollout.py`` and renders a 4-panel figure:

  1. Base height + fall marker (+ optional min_base_height threshold)
  2. Velocity tracking  (vx/vy  vs  cmd_vx/cmd_vy)
  3. Effort / smoothness (action_l2, dof_vel_l2)
  4. Reward + termination markers

Multiple CSVs are overlaid with a shared legend (compare checkpoints / tasks /
command sets). The time axis is in seconds, using ``ctrl_dt`` from each CSV's
sibling ``.metadata.json`` (fallback 0.02 s = 50 Hz).

Dependencies: numpy + matplotlib only (no pandas). Runs on Windows python.

Example:
    python plot_rollout_trace.py \\
        D:/.../rollout_trace_zero_cmd.summary.csv \\
        D:/.../rollout_trace_fwd_cmd.summary.csv \\
        --labels zero_cmd fwd_cmd \\
        --min-base-height 0.3 \\
        --out D:/.../comparison.png
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless-safe; we open the file ourselves afterwards
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Fixed schema written by record_offpolicy_rollout.py::_write_summary_csv
EXPECTED_COLS = (
    "step", "reward", "terminated", "truncated",
    "base_x", "base_y", "base_z",
    "vx", "vy", "vz",
    "cmd_vx", "cmd_vy", "cmd_vyaw",
    "action_l2", "dof_vel_l2",
)


def _read_csv(path: Path) -> dict[str, np.ndarray]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty CSV (no header)")
        cols: dict[str, list[float]] = {name: [] for name in reader.fieldnames}
        for row in reader:
            for name, raw in row.items():
                cols[name].append(raw)
    out: dict[str, np.ndarray] = {}
    for name, values in cols.items():
        if name in ("terminated", "truncated"):
            out[name] = np.array(
                [str(v).strip().lower() in ("true", "1", "yes") for v in values],
                dtype=bool,
            )
        else:
            out[name] = np.array([float(v) for v in values], dtype=float)
    return out


def _load_metadata(csv_path: Path) -> dict[str, Any]:
    """Sibling metadata.json (recorder writes both next to the .npz)."""
    meta_path = Path(str(csv_path).replace(".summary.csv", ".metadata.json"))
    if not meta_path.exists():
        # also try stem-based sibling
        meta_path = csv_path.with_name(csv_path.name.replace(".summary.csv", ".metadata.json"))
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _label_for(csv_path: Path, override: str | None) -> str:
    if override:
        return override
    return csv_path.name.replace(".summary.csv", "")


def _summarise(label: str, data: dict[str, np.ndarray], ctrl_dt: float) -> dict[str, Any]:
    steps = data["step"]
    n = len(steps)
    term = data.get("terminated", np.zeros(n, dtype=bool))
    first_term = int(np.argmax(term)) if term.any() else None
    fall_s = first_term * ctrl_dt if first_term is not None else None
    reward = data.get("reward", np.zeros(n))
    base_z = data.get("base_z", np.full(n, np.nan))
    return {
        "label": label,
        "n_steps": n,
        "duration_s": (n - 1) * ctrl_dt,
        "first_term_step": first_term,
        "fall_time_s": fall_s,
        "survived": first_term is None,
        "min_base_z": float(np.nanmin(base_z)),
        "final_base_z": float(base_z[-1]) if n else float("nan"),
        "mean_reward": float(np.nanmean(reward)),
        "cum_reward": float(np.nansum(reward)),
        "mean_action_l2": float(np.nanmean(data.get("action_l2", np.zeros(n)))),
        "mean_dof_vel_l2": float(np.nanmean(data.get("dof_vel_l2", np.zeros(n)))),
        "cmd": (
            float(data["cmd_vx"][-1]) if "cmd_vx" in data and n else 0.0,
            float(data["cmd_vy"][-1]) if "cmd_vy" in data and n else 0.0,
            float(data["cmd_vyaw"][-1]) if "cmd_vyaw" in data and n else 0.0,
        ),
    }


def _plot(traces: list[dict[str, Any]], out: Path, min_base_height: float | None,
          title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.5), constrained_layout=True)
    ax_h, ax_v = axes[0]
    ax_e, ax_r = axes[1]
    ax_e2 = ax_e.twinx()  # right axis for dof_vel_l2 (shared across traces)
    palette = plt.get_cmap("tab10")

    for i, tr in enumerate(traces):
        data = tr["data"]
        t = data["step"] * tr["ctrl_dt"]
        c = palette(i % 10)
        lbl = tr["label"]
        term = data.get("terminated", np.zeros(len(t), dtype=bool))

        # 1. base height
        ax_h.plot(t, data.get("base_z", np.full(len(t), np.nan)),
                  color=c, lw=1.4, label=lbl)
        if term.any():
            ft = int(np.argmax(term))
            ax_h.axvline(t[ft], color=c, ls="--", lw=1.0, alpha=0.7)

        # 2. velocity tracking (forward + lateral; command as dashed)
        ax_v.plot(t, data.get("vx", np.zeros(len(t))), color=c, lw=1.4,
                  label=f"{lbl} vx")
        ax_v.plot(t, data.get("cmd_vx", np.zeros(len(t))), color=c, lw=1.1,
                  ls="--", alpha=0.7)
        # lateral as faint same-hue
        ax_v.plot(t, data.get("vy", np.zeros(len(t))), color=c, lw=1.0, alpha=0.35)

        # 3. effort (action_l2 left, dof_vel_l2 right)
        ax_e.plot(t, data.get("action_l2", np.zeros(len(t))),
                  color=c, lw=1.3, label=f"{lbl} action_l2")
        ax_e2.plot(t, data.get("dof_vel_l2", np.zeros(len(t))),
                   color=c, lw=1.0, alpha=0.5)

        # 4. reward + termination markers
        ax_r.plot(t, data.get("reward", np.zeros(len(t))),
                  color=c, lw=1.3, label=lbl)
        if term.any():
            ax_r.scatter(t[term], data.get("reward", np.zeros(len(t)))[term],
                         color=c, marker="x", s=30, zorder=5)

    # axis cosmetics
    for ax in (ax_h, ax_v, ax_e, ax_r):
        ax.set_xlabel("time (s)")
        ax.grid(True, alpha=0.3)

    ax_h.set_title("Base height (z)  —  dashed = first termination")
    ax_h.set_ylabel("base_z (m)")
    if min_base_height is not None:
        ax_h.axhline(min_base_height, color="red", ls=":", lw=1.2,
                     label=f"min_base_height={min_base_height}")
    ax_h.legend(fontsize=8, loc="best")

    ax_v.set_title("Velocity tracking  (solid=vx, dashed=cmd_vx, faint=vy)")
    ax_v.set_ylabel("velocity (m/s)")
    ax_v.axhline(0, color="grey", lw=0.6)
    ax_v.legend(fontsize=8, loc="best")

    ax_e.set_title("Effort / smoothness  (left=action_l2, right=dof_vel_l2)")
    ax_e.set_ylabel("action_l2")
    ax_e2.set_ylabel("dof_vel_l2")
    ax_e.legend(fontsize=8, loc="upper left")

    ax_r.set_title("Reward  —  ✕ = terminated step")
    ax_r.set_ylabel("reward (per step)")
    ax_r.axhline(0, color="grey", lw=0.6)
    ax_r.legend(fontsize=8, loc="best")

    fig.suptitle(title, fontsize=13, fontweight="bold")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)


def _open(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")
    except Exception as exc:  # noqa: BLE001
        print(f"[plot] could not auto-open {path}: {exc}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Plot UniLab off-policy rollout trace CSV(s).")
    p.add_argument("csv", nargs="+", type=Path, help="One or more *.summary.csv files")
    p.add_argument("--labels", nargs="*", default=None,
                   help="Display labels (one per CSV). Default = CSV stem.")
    p.add_argument("--min-base-height", type=float, default=None,
                   help="Draw a threshold line on the base-height panel (e.g. 0.3).")
    p.add_argument("--out", type=Path, default=None, help="Output PNG path.")
    p.add_argument("--no-show", action="store_true", help="Do not auto-open the PNG.")
    args = p.parse_args(argv)

    if args.labels and len(args.labels) != len(args.csv):
        raise SystemExit(f"--labels needs {len(args.csv)} entries, got {len(args.labels)}")

    traces: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    task_name = None
    for i, csv_path in enumerate(args.csv):
        if not csv_path.exists():
            raise SystemExit(f"CSV not found: {csv_path}")
        data = _read_csv(csv_path)
        missing = [c for c in EXPECTED_COLS if c not in data]
        if missing:
            print(f"[plot] WARN {csv_path.name}: missing columns {missing}", file=sys.stderr)
        meta = _load_metadata(csv_path)
        ctrl_dt = float(meta.get("ctrl_dt", 0.02))
        if task_name is None:
            task_name = meta.get("task") or csv_path.parent.name
        label = _label_for(csv_path, args.labels[i] if args.labels else None)
        traces.append({"data": data, "ctrl_dt": ctrl_dt, "label": label})
        summaries.append(_summarise(label, data, ctrl_dt))

    if args.out is None:
        if len(args.csv) == 1:
            args.out = args.csv[0].with_name(args.csv[0].name.replace(".summary.csv", ".plot.png"))
        else:
            args.out = args.csv[0].parent / f"comparison_{len(args.csv)}.plot.png"

    title = f"Rollout trace — {task_name}" + (
        f"  ({len(traces)} runs)" if len(traces) > 1 else "")
    _plot(traces, args.out, args.min_base_height, title)

    # stdout summary table
    print(f"[plot] wrote {args.out}")
    hdr = f"{'label':<22}{'steps':>7}{'dur_s':>8}{'fall@':>9}{'min_z':>8}{'mean_r':>9}{'cum_r':>10}{'act_l2':>9}{'dofvel':>9}"
    print(hdr)
    print("-" * len(hdr))
    for s in summaries:
        fall = f"{s['fall_time_s']:.2f}s" if s["fall_time_s"] is not None else "—"
        print(
            f"{s['label']:<22}{s['n_steps']:>7}{s['duration_s']:>8.1f}{fall:>9}"
            f"{s['min_base_z']:>8.3f}{s['mean_reward']:>9.3f}{s['cum_reward']:>10.2f}"
            f"{s['mean_action_l2']:>9.2f}{s['mean_dof_vel_l2']:>9.2f}"
        )

    if not args.no_show:
        _open(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
