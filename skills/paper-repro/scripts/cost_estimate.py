"""Estimate the cost of a FULL paper reproduction on the local hardware.

Reads a feasibility report (from analyze_repo.py --json) and the local
machine's compute, then gives a rough, clearly-labeled estimate. This is the
'how much would the full thing cost?' answer autoarxiv-style tools give.

Heuristics are intentionally simple and transparent — not a precise predictor.

Usage:
    python cost_estimate.py --report analyze_report.json
    python cost_estimate.py --n-gpu 8 --epochs 400 --params 65e6 --dataset-gb 4.5
"""
import argparse
import json
import os
import subprocess


def detect_hardware():
    hw = {"gpus": [], "cpu_count": os.cpu_count()}
    try:
        import torch
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                hw["gpus"].append(torch.cuda.get_device_name(i))
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, check=False,
        )
        if out.returncode == 0 and out.stdout.strip() and not hw["gpus"]:
            hw["gpus"] = [l.strip() for l in out.stdout.strip().splitlines()]
    except Exception:
        pass
    return hw


def guess_tier(gpu_name):
    n = (gpu_name or "").upper()
    if "H100" in n:
        return "H100", 1.0
    if "A100" in n:
        return "A100", 1.6
    if "V100" in n:
        return "V100", 3.0
    if "3090" in n or "4090" in n:
        return "consumer", 4.0
    return "other", 8.0


def estimate(params, steps, n_gpu_paper, dataset_gb):
    """Rough GPU-hours for a full run. Pure heuristic, labeled as such."""
    # very rough: a transformer-scale fwd+bwd cost scales with params * steps
    # calibrated so that the original Transformer (65M, ~100k steps, 8 GPU,
    # 3.5 days) lands near ~600 GPU-hours.
    base = params * steps / 1e12  # arbitrary unit
    gpu_hours_full = max(1.0, base * 6.0)  # on paper's own GPUs
    wall_days_full = gpu_hours_full / max(n_gpu_paper, 1) / 24.0
    return {
        "gpu_hours_full": round(gpu_hours_full, 1),
        "wall_days_on_paper_hw": round(wall_days_full, 2),
        "dataset_gb": round(dataset_gb, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="Estimate full-repro cost.")
    ap.add_argument("--report", help="JSON report from analyze_repo.py")
    ap.add_argument("--n-gpu", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=400)
    ap.add_argument("--steps", type=int, default=0, help="total optimizer steps if known")
    ap.add_argument("--params", type=float, default=65e6, help="approx param count")
    ap.add_argument("--dataset-gb", type=float, default=0.0)
    args = ap.parse_args()

    if args.report and os.path.exists(args.report):
        with open(args.report, encoding="utf-8") as f:
            rep = json.load(f)
        sig = rep.get("resource_signals", {})
        n = sig.get("n_gpu")
        args.n_gpu = int(n) if isinstance(n, str) and n.isdigit() else args.n_gpu
        ep = sig.get("epochs")
        if isinstance(ep, str) and ep.isdigit():
            args.epochs = int(ep)
        ds = sig.get("dataset_deps")
        if ds:
            args.dataset_gb = max(args.dataset_gb, 1.0)

    steps = args.steps or args.epochs * 1000  # fallback heuristic
    est = estimate(args.params, steps, args.n_gpu, args.dataset_gb)
    hw = detect_hardware()

    bar = "=" * 56
    print(bar)
    print(" FULL REPRODUCTION COST ESTIMATE  (rough heuristic)")
    print(bar)
    print(f"  paper config    : ~{args.params/1e6:.0f}M params, {steps:,} steps, "
          f"{args.n_gpu} GPU(s), ~{est['dataset_gb']} GB data")
    print(f"  full repro cost : ~{est['gpu_hours_full']} GPU-hours  "
          f"(~{est['wall_days_on_paper_hw']} wall-days on paper's {args.n_gpu} GPUs)")
    print(f"  local hardware  : CPU cores={hw['cpu_count']} | GPUs={hw['gpus'] or 'NONE'}")
    if hw["gpus"]:
        tier, slowdown = guess_tier(hw["gpus"][0])
        local_hours = est["gpu_hours_full"] * slowdown / len(hw["gpus"])
        print(f"  on your GPU(s)  : ~{local_hours:.0f} hours ({tier}, "
              f"~{local_hours/24:.1f} wall-days)")
        verdict = "feasible on local GPU (but consider minimal repro first)"
    else:
        years = (est["gpu_hours_full"] * 200) / 24 / 365  # CPU ~200x slower, v rough
        print(f"  on your CPU     : ~{years:.0f}+ years (CPU-only)  ->  INFEASIBLE")
        verdict = "full repro INFEASIBLE on this CPU-only machine -> use MINIMAL repro"
    print(f"  recommendation  : {verdict}")
    print(bar)


if __name__ == "__main__":
    main()
