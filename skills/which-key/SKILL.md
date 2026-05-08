---
name: which-key
description: Check which API key the current Claude Code session is using. Use when user asks "which key", "哪个key", "当前key", "what key am I using".
---

# Which Key

Quickly check which API key the current session is using. Read-only, no Bash needed.

## Workflow

1. Read `~/.claude/settings.json` and extract `env.ANTHROPIC_AUTH_TOKEN`
2. Read `~/.claude/claude_profiles.json` and extract the `profiles` array
3. Compare the current token against each profile's `anthropic_auth_token`
4. Display:

**Match found:**
```
Current session: key3
Token:   6a4f...K1Wk
Base URL: https://open.bigmodel.cn/api/anthropic
Model:   glm-5.1
```

**No match:**
```
Current token (masked): abcd...xyz0
Not found in known profiles.
```

## Masking rule

Show first 4 chars + `...` + last 4 chars of the token.

## Notes

- Read-only — only uses the `Read` tool on two JSON files
- To **switch** key (preserving conversation), use `/start_claude --continue` instead
