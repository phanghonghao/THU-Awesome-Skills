"""Generic training-log summarizer (paper-agnostic).

Reads a CSV of per-step metrics, auto-detects the loss column and any
accuracy columns, prints a summary table, draws a curve chart, and emits a
PASS/INCONCLUSIVE verdict.

Verdict rule (configurable):
  PASS if (best accuracy column >= --acc-threshold) OR
        (loss dropped by >= --loss-drop fraction from first to last logged row)

Usage:
    python summarize_eval.py --log train_log.csv --chart curve.png
    python summarize_eval.py --log log.csv --task "seq reversal" --acc-threshold 0.8
"""
import argparse
import csv
import re

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLT = True
except Exception:
    HAS_PLT = False


def pick_columns(headers):
    loss = acc = None
    acc_cols = []
    for h in headers:
        hl = h.lower()
        if loss is None and "loss" in hl:
            loss = h
        if re.search(r"acc(uracy)?", hl):
            acc_cols.append(h)
    acc = acc_cols[0] if acc_cols else None
    return loss, acc, acc_cols


def main():
    ap = argparse.ArgumentParser(description="Summarize a training log CSV.")
    ap.add_argument("--log", default="train_log.csv")
    ap.add_argument("--chart", default="training_curve.png")
    ap.add_argument("--task", default="", help="task name for the report title")
    ap.add_argument("--acc-threshold", type=float, default=0.5)
    ap.add_argument("--loss-drop", type=float, default=0.5,
                    help="PASS if loss drops by at least this fraction")
    args = ap.parse_args()

    with open(args.log, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("no rows in log"); return

    headers = list(rows[0].keys())
    step_col = "step" if "step" in headers else headers[0]
    loss, acc, acc_cols = pick_columns(headers)

    bar = "=" * 56
    title = f" MINIMAL REPRODUCTION SUMMARY  -  {args.task}".rstrip()
    print(bar); print(title); print(bar)
    cols = " | ".join(h for h in [step_col, loss, *(acc_cols)] if h)
    print("  " + cols)
    print("-" * 56)
    for r in rows:
        vals = []
        for h in [step_col, loss, *acc_cols]:
            v = r.get(h, "")
            if h == step_col:
                try:
                    vals.append(f"{int(float(v)):>9}")
                    continue
                except Exception:
                    pass
            try:
                vals.append(f"{float(v):>9.4f}")
            except Exception:
                vals.append(f"{str(v):>9}")
        print("  " + " | ".join(vals))

    # verdict
    passed, reason = False, ""
    if acc:
        best = max(_f(r.get(acc)) for r in rows)
        if best >= args.acc_threshold:
            passed, reason = True, f"best {acc}={best:.1%} >= {args.acc_threshold:.0%}"
    if not passed and loss:
        vals = [r.get(loss) for r in rows]
        f = next((_f(v) for v in vals if _f(v) is not None), None)
        l = next((_f(v) for v in reversed(vals) if _f(v) is not None), None)
        if f is not None and l is not None and f > 0 and (f - l) / f >= args.loss_drop:
            passed = True
            reason = f"loss {f:.3f}->{l:.3f} (dropped {(f-l)/f:.0%})"
    print("-" * 56)
    verdict = "PASS - core claim reproduced" if passed else "INCONCLUSIVE - needs more steps / tuning"
    print(f"  verdict : {verdict}" + (f"  ({reason})" if reason else ""))
    print(bar)

    if HAS_PLT and (loss or acc_cols):
        steps = [_f(r.get(step_col)) or i for i, r in enumerate(rows)]
        n_panels = 1 + (1 if acc_cols else 0)
        fig, ax = plt.subplots(1, n_panels, figsize=(5 * n_panels, 3.5))
        if n_panels == 1:
            ax = [ax]
        i = 0
        if loss:
            y = [_f(r.get(loss)) for r in rows]
            ax[i].plot(steps, y, "o-"); ax[i].set_title("loss"); ax[i].grid(alpha=0.3); i += 1
        for c in acc_cols:
            y = [_f(r.get(c)) for r in rows]
            ax[i].plot(steps, y, "o-", label=c)
        if acc_cols:
            ax[i].set_title("accuracy"); ax[i].legend(); ax[i].grid(alpha=0.3)
        for a in ax:
            a.set_xlabel("step")
        fig.tight_layout()
        fig.savefig(args.chart, dpi=110)
        print(f"  chart -> {args.chart}")
    elif not HAS_PLT:
        print("  (matplotlib unavailable, skipped chart)")


def _f(v):
    try:
        return float(v)
    except Exception:
        return None


if __name__ == "__main__":
    main()
