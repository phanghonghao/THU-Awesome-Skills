---
name: start_claude
description: Manage and launch Claude Code instances with different API keys. Use --continue to switch key in-place while preserving conversation history. Supports session recovery from other keys. Use when user mentions "start claude", "launch", "switch key", "换key", "切换key", "continue", "保留会话", "恢复会话", "recover session".
---

# Start Claude - API Key Manager

Manage multiple Claude Code instances with different API keys.

## Two Modes

| Mode | Command | Behavior |
|------|---------|----------|
| **New window** | `/start_claude` | Launch new window with isolated config dir (default) |
| **Continue** | `/start_claude --continue` | Switch key in-place, preserve conversation via `claude --resume` |

---

## Mode 1: New Window (default)

### Step 1: Check API Keys

Run the key checker to see which keys are available:

```bash
python "$HOME/.claude/start_claude.py" --check
```

Parse the output after the `---JSON---` marker to get structured results. Each result has: `name`, `key` (masked), `status` (`ok`/`rate_limited`/`invalid`/`missing`/`error`), `detail`.

### Step 2: Present Choices to User

Based on the check results, use `AskUserQuestion` to present the available profiles to the user. Format like:

- Show each key's name, masked key, and status
- Keys with `status: ok` are recommended
- Keys with `status: rate_limited` still work but may have usage limits
- Skip keys with `status: invalid` or `missing`

Ask the user which profile they want to launch.

### Step 3: Generate Launch Command

Once the user picks a profile, run:

```bash
python "$HOME/.claude/start_claude.py" --launch <profile_name>
```

The output will contain a `---CMD---` marker followed by a **ready-to-run command**.

### Step 4: Show Command to User

Display the command from `---CMD---` to the user in a code block. Tell the user:

1. 在 VSCode 中点击终端面板右上角的 `+` 号新开一个 terminal tab
2. 将命令粘贴到新 terminal 中运行
3. 新窗口的配置完全隔离（独立的 config 目录、API key、配额）

---

## Mode 2: Continue (`--continue`)

Switch key in the **current** config directory while preserving conversation. Auto-detects current session ID — no need to paste anything.

### Step 1: Check keys & auto-detect session

Run these **in parallel**:

```bash
python "$HOME/.claude/start_claude.py" --check
python "$HOME/.claude/start_claude.py" --current-session
```

Parse `--check` output after `---JSON---` for key statuses. Identify the current key (match token in `settings.json`).

Parse `--current-session` output after `---JSON---` to get `session_id`. This is the **current active session** from `.claude.json`, auto-detected from the current config dir and project.

### Step 2: Ask which key to switch to

Use `AskUserQuestion` with **one question only**:

- Show each key with status (current / ok / rate_limited)
- Current key is clearly marked `[当前]`
- Recommend keys with `status: ok`
- Do NOT ask for session ID — it was auto-detected in Step 1

### Step 3: Switch key

Use the **Edit** tool on the current config's `settings.json` to replace:

- `env.ANTHROPIC_AUTH_TOKEN` → new profile's `anthropic_auth_token`
- `env.ANTHROPIC_BASE_URL` → new profile's `anthropic_base_url`
- `model` (top-level) → new profile's `model`

Only edit these three fields — never overwrite the whole file.

### Step 4: Display result

Always show the `claude --resume` command with the auto-detected session ID:

```
Switched to: key2
Token:   9b32...kRkKld

生效方式：Ctrl+C 退出当前会话，然后运行：
  claude --resume <session_id>

对话历史完整保留，只是换了 API key。
```

**Masking rule:** first 4 chars + `...` + last 4 chars of the token.

> **Tip:** If `--current-session` returns empty (no session found), fall back to `claude --resume` without ID — Claude will use the latest session automatically.

---

## Available Profiles

Read from `~/.claude/claude_profiles.json`. Default profiles: `key1`, `key2`, `key3`, `key4`.

## Other Modes

- `--list`: Just list profiles without testing (faster)
- `--sessions`: List recent sessions across all config dirs for current project
- `--sessions --all`: List all sessions across all config dirs and projects
- `--recover <profile>`: Copy latest session data from a profile's config dir to current config dir
- `--recover-id <session_id>`: Recover a specific session by ID (searches all profiles)
- `--init`: Interactive token setup (run from terminal, not from within Claude Code)
- `--setup <name>`: Prepare config dir without launching

## Notes

- **New window mode**: each window uses a separate config directory, settings/history/keys completely isolated
- **Continue mode**: edits the current config directory, can also recover sessions from other config dirs
- **Session recovery**: when a key runs out of quota, start a new session with another key, then use `--continue` to recover the old conversation
- To manage tokens, run `python ~/.claude/start_claude.py --init` from a regular terminal
