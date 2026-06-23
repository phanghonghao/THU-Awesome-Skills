---
name: start_codex
description: >-
  Manage and launch Codex (codex CLI) instances with different API keys / profiles.
  Supports launch (isolated CODEX_HOME, new session), --continue (codex resume --last
  inside an isolated profile home), and --check (test each key's availability). All
  modes use ~/.codex/start_codex.py and an isolated per-profile CODEX_HOME, so the
  root ~/.codex (auth.json / config.toml / current bf1 default) is never touched.
  Use when the user mentions "start codex", "launch codex", "switch codex key",
  "codex resume", "换 codex key", "切 codex", "codex continue", "atec key",
  "codex atec", "start_codex", "用 atec 跑 codex".
---

# Start Codex - API Key / Profile Manager

Manage multiple Codex profiles and launch `codex` with the chosen key. Each profile
lives in its own isolated `CODEX_HOME` (`~/.codex/profiles/<name>`), so config,
history and keys are fully isolated — **the root `~/.codex` is never modified**.

Mirrors `/start_claude`, but adapted to Codex: the launcher is
`~/.codex/start_codex.py`, isolation is via `CODEX_HOME` (not `CLAUDE_CONFIG_DIR`),
and "continue" maps to `codex resume --last` (Codex auto-picks the last session in
that home — no session ID needed).

## Invocation

`/start_codex [profile] [--continue] [--check]`

| Arg / Flag | Meaning |
|------------|---------|
| *(none)* | launch mode: pick a profile, print a ready-to-run command (new session) |
| `<profile>` | launch that profile directly (e.g. `/start_codex atec`) |
| `--continue` | resume mode: print a `codex resume --last` command for the chosen profile |
| `--check` | test every profile's key, report ok / rate_limited / invalid / error |

Parsing: a single non-flag token that matches a profile name is the target
profile; `--continue` and `--check` select the mode. If both are given, `--check`
wins (verify first, then the user can launch).

---

## Mode 1: Launch (default) — isolated new session

### Step 1: List profiles (fast)

```bash
python "$HOME/.codex/start_codex.py" --list
```

Output is one line per enabled profile:
`<name>  <masked key>  home=<CODEX_HOME>[ active]`
The `active` marker shows which key matches the root `~/.codex/auth.json` (the
default Codex uses when no `CODEX_HOME` is set). **Launching any profile does NOT
change which is "active" — it just starts an isolated Codex with that key.**

### Step 2: Ask the user which profile to launch

Use `AskUserQuestion` (one question). Show each enabled profile with its masked
key and note any non-default `base_url` (only `atec` has one — `https://atec.chat`;
the rest use the global `https://codex.0u0o.com`). Recommend the profile the user
named on the command line if they gave one.

### Step 3: Ensure the profile home exists

The launch command points `CODEX_HOME` at `~/.codex/profiles/<name>`. If that
directory is missing (no `config.toml` / `auth.json` inside), set it up first:

```bash
python "$HOME/.codex/start_codex.py" --setup <name>
```

`--setup` copies the global `config.toml` into the home, overrides `base_url` from
the profile, links `rules`/`skills`, and writes `auth.json` with the profile key.
Currently `bf1`, `RTX6000`, `bf2`, `atec` are already set up — skip unless `--list`
shows a missing home.

### Step 4: Generate the launch command

```bash
python "$HOME/.codex/start_codex.py" --launch <name>
```

Parse the line **after** the `---CMD---` marker — it is a ready-to-run
**PowerShell** one-liner of the form:
`$env:CODEX_HOME="..."; $env:OPENAI_API_KEY="..."; Set-Location -LiteralPath "..."; codex`

### Step 5: Show the command to the user

Display the `---CMD---` command in a code block and tell the user:
1. 在 VSCode 中点击终端面板右上角的 `+` 号新开一个 terminal tab（确保是 PowerShell）
2. 将命令粘贴进去运行
3. 该窗口完全隔离：独立的 CODEX_HOME / config / 历史 / key，不影响根 `~/.codex`

---

## Mode 2: Continue (`--continue`) — resume last session in an isolated home

Same as launch, but the command ends in `codex resume --last` instead of `codex`.

### Step 1–3

Same as Mode 1 (`--list` → `AskUserQuestion` → `--setup` if home missing).

### Step 4: Generate the resume command

```bash
python "$HOME/.codex/start_codex.py" --resume <name>
```

The `---CMD---` line is the same PowerShell prefix but ends with `codex resume --last`.

### Step 5: Show the command + explain semantics

Display the command and note the **important difference from `/start_claude --continue`**:
- `/start_claude --continue` edits the *current* config dir to swap the key, then
  resumes the *current* session.
- `/start_codex --continue` does **not** touch the current Codex. It opens the
  chosen profile's isolated `CODEX_HOME` and runs `codex resume --last` there —
  i.e. it resumes **that profile home's** most recent session (history is
  per-home), with that profile's key + base_url. This keeps the root `~/.codex`
  untouched by design.

Tell the user:
```
Resume: <name>  (key: <masked>)
在新的 PowerShell tab 中运行上面的命令，会以 <name> 的隔离 home 恢复该 home 的最近一次会话。
当前根 codex 不受影响。
```

---

## Mode 3: Check (`--check`) — test key availability

```bash
python "$HOME/.codex/start_codex.py" --check
```

This is slow (each profile spawns a real `codex exec` probe, up to ~45 s each).
Parse the JSON after the `---JSON---` marker — an array of
`{name, key(masked), status, detail}`. Report each profile:

| status | meaning |
|--------|---------|
| `ok` | key works — recommend |
| `rate_limited` | works but quota/limited — usable |
| `invalid` | 401 / unauthorized — skip |
| `missing` | no token set — skip |
| `error` | timeout / other — note the detail |

If the user then wants to launch, continue from Mode 1 Step 2 (offer the `ok`
profiles via `AskUserQuestion`).

> If `atec` reports a model error (e.g. "model not found"), the relay
> `https://atec.chat` may not serve the configured `model = "gpt-5.4"`. Edit
> `~/.codex/profiles/atec/config.toml`'s top-level `model` to one the relay
> supports, then re-check. (This only affects the atec home, not the root.)

---

## Available Profiles

Read from `~/.codex/codex_profiles.json`. Current profiles:

| name | base_url | note |
|------|----------|------|
| `bf1` | `https://codex.0u0o.com` (global default) | root-active default |
| `RTX6000` | `https://codex.0u0o.com` | |
| `bf2` | `https://codex.0u0o.com` | |
| `atec` | `https://atec.chat` | ATEC relay — own base_url |

## How base_url & isolation work (do not bypass)

- Each profile's `base_url` lives in **its own profile home's `config.toml`**
  (`~/.codex/profiles/<name>/config.toml`, inside `[model_providers.codex]`).
  `--setup` copies the global config and overrides that single `base_url` line.
- `--launch` / `--resume` set `$env:CODEX_HOME` to the profile home, so Codex
  reads that home's `config.toml` (correct base_url) **and** that home's
  `auth.json` (correct key). key ↔ base_url always match. ✓
- **Do NOT use `--activate`** from this skill. `--activate` rewrites the *root*
  `~/.codex/auth.json` key but does **not** change the root `config.toml`
  `base_url` — so activating `atec` at the root would pair the atec key with the
  `codex.0u0o.com` base_url and fail. The whole point of this skill is to avoid
  that by using isolated homes. (If you ever do need the root on atec, you must
  edit both root `auth.json` **and** root `config.toml` `base_url` together.)

## Notes

- Launch/resume output is **PowerShell** (uses `$env:...`). The user must run it
  in a PowerShell terminal (VSCode default terminal on Windows is fine).
- Each profile window is fully isolated: its own config, sessions, history, key.
- To add/change tokens, run `python ~/.codex/start_codex.py --init` from a regular
  terminal (interactive `getpass`, not from inside Claude Code).
- The desktop shortcut `C:\Users\20174\Desktop\start_codex.bat` just runs
  `python %USERPROFILE%\.codex\start_codex.py` interactively — equivalent to this
  skill's no-arg launch flow but in a plain terminal.
