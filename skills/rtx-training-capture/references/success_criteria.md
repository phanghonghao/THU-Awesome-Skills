# Success / Failure Criteria

Use these thresholds to judge a training run after it exits. They are
empirical, derived from observed T1 / K1 / Franka runs on this server.

## Primary signals

### `episode_length` (mean across last 100 iters)

| Range          | Verdict                                                   |
|----------------|-----------------------------------------------------------|
| ≥ 500          | **Success** — robot maintains at least half the episode   |
| 200 – 500      | **Partial** — needs more iters OR is unstable; investigate |
| < 200          | **Failure** — terminates/falls quickly                    |

For 1000-step episodes (typical mjlab T1), 1000 = full 20s standing.
102 = ~2s, the classic "robot falls immediately" signature.

### Reward trend

Compare `latest_metrics.reward` against `peak_reward`:

| Ratio (latest/peak) | Verdict                                  |
|---------------------|------------------------------------------|
| ≥ 0.85              | **Success** (or near-converged)          |
| 0.5 – 0.85          | Investigate — may need more iters        |
| < 0.5               | **Failure** OR premature termination     |

Also check if reward is still rising at the end of training. If yes and
`max_iterations` was hit, the run is incomplete — consider extending.

### `value_loss` (last reported)

| Range   | Verdict                                |
|---------|----------------------------------------|
| < 1     | Excellent (well-converged critic)      |
| 1 – 10  | Healthy                                |
| 10 – 50 | Convergence struggling                 |
| > 50    | **Failure** — critic diverged          |

### `overfitting_detected` flag

Treat with caution. The convergence_monitor.py flags overfitting when
reward drops 20%+ from a local peak. This is OFTEN a false alarm:

- T1 Stand v4 hit reward 375@iter 355 (early spike), dropped to 297@529,
  then recovered and peaked at 399@7732. The monitor flagged overfitting
  at iter 529, but the run was actually still progressing.
- Inspect `overfitting_reason` to see whether the peak was an early
  outlier. If `latest_metrics.reward` is back near or above the cited peak,
  ignore the flag.

## Common failure signatures

### 1. Episode length stuck at 102 (~2s)

Robot falls immediately. Common causes:
- Energy threshold too low (early termination) — fix: raise
  `Curriculum/energy_threshold` from 5000 → 50000 (T1 Stand v3b fix).
- Reward shaping exploits (robot learns to "die" to avoid penalty) —
  fix: rebalance reward terms.
- No warm-start for tasks that require balance (e.g. Reach without
  Stand pretraining) — fix: warm-start from a converged Stand policy.

Example: T1 Reach v4/v5 stuck at ep_len 102. Fixed in v6 via warm-start
from T1 Stand v4 model_7800.pt — ep_len jumped to 851 at iter 173.

### 2. Reward rises then collapses

- Instability from too-high learning rate
- Action std collapsed (deterministic policy gets stuck)
- Curriculum activated too aggressively

### 3. Value loss diverging

- Obs dim mismatch between actor and critic (check
  `actor.mlp.0.weight.shape[1]` vs `critic.mlp.0.weight.shape[1]`)
- Reward scale too large
- Gamma / GAE lambda misconfigured

### 4. Low-dim-only BC outputs mean action

Specific to imitation learning (P0 RoboMimic). The BC MLP collapses to
outputting the dataset mean regardless of observation. Root cause: lack
of image observations. Fix: retrain with image obs (84x84).

### 5. Grasp / contact never happens

Specific to manipulation. Common causes:
- Demo gripper sign reversed
- Action normalization missing (gripper bimodal -1/+1 drowned by position deltas)
- Obs key wrong (`cubeA_pos` vs `cube_pos`)

## Worked examples

### Success: T1 Stand v4 (2026-06-13_15-47-54)

- `peak_reward`: 399.137 @ iter 7732
- `best_model_reward`: 397.318 @ iter 7800
- `latest_metrics.reward`: 395.357 (iter 7999) → ratio 0.99 ✅
- `latest_metrics.episode_length`: 1000 ✅
- `latest_metrics.value_loss`: 0.005 ✅
- `overfitting_detected`: true (FALSE ALARM — early iter-355 spike artifact)

Verdict: **Success. Pulled model_7800.pt + matching video. Showcase updated.**

### Failure: T1 Reach v4/v5

- ep_len stuck at 102 across all 15000 iters
- reward -70 to -10 range, never recovered
- value_loss > 50 throughout

Verdict: **Failure. Archived convergence report. Recommended v6 warm-start
from Stand v4.**

### Failure: P0 RoboMimic PH (low-dim only)

- 2000 epochs trained, action variance <0.01 across radically different states
- 87% dead neurons (125-132/1024 non-zero post-ReLU)
- Eval success rate: 0%

Verdict: **Failure. Root cause = missing image obs. Retrained with image
obs (job 340).**

## When in doubt

If signals are ambiguous, present the convergence_report.json fields and
the last 200 lines of train.log to the user and ask for a decision. Do
NOT auto-record a video for an ambiguous run.
