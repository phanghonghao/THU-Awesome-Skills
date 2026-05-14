# Plot Types Reference

## Plot 1: Reward Comparison

**File:** `1_reward_comparison.png`
**Type:** Multi-line chart
**Data:** `Train/mean_reward` from all runs

### What it shows
- X-axis: Training iteration
- Y-axis: Mean episode reward (smoothed)
- Each line = one training run
- Triangle markers = best model checkpoint

### How to interpret
- **Rising curve**: Policy improving
- **Flat plateau**: Converged
- **Declining after peak**: Overfitting / policy collapse
- **Negative values**: Robot consistently failing (falling, wrong actions)

### Key patterns
- Fast rise + crash (v1, v2, v3): Suggests training instability, need regularization
- Slow steady rise (v4_gentle): Curriculum learning working well
- Always negative (v6 multi-GPU): Configuration issue

---

## Plot 2: Reward Decomposition

**File:** `2_reward_decomposition_<alias>.png`
**Type:** Stacked area + line chart (2 panels)
**Data:** `Episode_Reward/*` tags + `Curriculum/*` tags

### What it shows
- **Top panel**: Individual reward components as colored fills/lines
  - Positive components (green/blue fills): tracking rewards, alive bonus
  - Negative components (red/orange): penalties (action rate, torques)
  - Black line: Total reward
- **Bottom panel**: Curriculum progress
  - Brown line: Terrain difficulty level
  - Teal line: Velocity command level
- Red dashed line: Best model iteration

### How to interpret
- If tracking rewards drop while penalties rise → policy becoming erratic
- If terrain level increases too fast → may cause policy collapse
- Best model should be near the peak of total reward

### Key reward components

| Component | Type | Description |
|-----------|------|-------------|
| tracking_lin_vel | + | Linear velocity tracking accuracy |
| tracking_ang_vel | + | Angular velocity tracking accuracy |
| alive | + | Survival bonus per timestep |
| action_rate | - | Action smoothness penalty |
| torques | - | Joint torque penalty |
| dof_vel | - | Joint velocity penalty |
| dof_acc | - | Joint acceleration penalty |

---

## Plot 3: Termination Reasons

**File:** `3_termination_<alias>.png`
**Type:** Multi-line chart (2 panels)
**Data:** `Episode_Termination/*` + `Train/mean_episode_length`

### What it shows
- **Top panel**: Termination reason ratios (0-1 scale)
  - Green (`time_out`): Episode completed successfully
  - Red (`bad_orientation`): Robot fell / flipped
  - Orange (`base_height`): Base height out of range
- **Bottom panel**: Mean episode length in steps
  - Max = 1000 steps (20s @ 50Hz)

### How to interpret
- **Healthy training**: `time_out` increases, `bad_orientation` decreases
- **Problematic**: `bad_orientation` stays high → robot can't learn to balance
- **Episode length**: Should increase over training; plateau near 1000 is ideal
- If episode length oscillates → curriculum changes causing temporary regression

---

## Plot 4: Training Efficiency

**File:** `4_efficiency_<alias>.png`
**Type:** 2×2 subplots
**Data:** `Perf/*` + `Loss/*` tags

### What it shows
- **Top-left**: Throughput (steps/sec)
  - Raw (light blue) + smoothed (dark blue)
  - Should be roughly constant if GPU utilization is stable
- **Top-right**: Collection vs Learning time (sec/iter)
  - Red: Simulation/data collection time
  - Green: PPO gradient update time
- **Bottom-left**: Policy entropy
  - High → exploring; Low → exploiting
  - Should decrease gradually, not crash to 0
- **Bottom-right**: Learning rate schedule
  - Shows LR adaptation over training

### How to interpret
- **Throughput dips**: GPU contention, I/O bottleneck
- **Collection >> Learning**: Normal for Isaac Lab (simulation-heavy)
- **Entropy collapse**: Policy converged too early, may need higher entropy bonus
- **LR spikes**: Adaptive schedule reacting to large KL divergence

### Typical values (RTX 6000, 4 GPU)

| Config | Throughput | Collection | Learning |
|--------|-----------|------------|----------|
| 4096 envs/GPU | ~176k steps/s | ~1.8s | ~0.4s |
| 32768 envs/GPU | ~524k steps/s | ~4.5s | ~1.5s |
