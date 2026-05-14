---
name: sync-claude-skill
description: Synchronize Codex user skills from C:\Users\20174\.codex\skills into the Claude Code skills folder discovered from the local Claude environment. Use when the user wants to sync, update, replace, or copy one or all Codex custom skills back into Claude. Supports full sync and single-skill sync. Excludes Codex built-in .system and accepts both skill.md and SKILL.md.
---

# Sync Claude Skill

Synchronize user-created Codex skills into Claude Code.

## Scope

- Source: `C:\Users\20174\.codex\skills`
- Exclude from source: `C:\Users\20174\.codex\skills\.system`
- Target: Claude user skills folder, auto-discovered from the local Claude environment
- Default target fallback: `C:\Users\20174\.claude\skills`

Default behavior is to sync **user/custom Codex skills only**. Do **not** copy Codex built-in `.system` into Claude.

The sync logic should treat both `SKILL.md` and `skill.md` as valid skill entry files. When copying to Claude, normalize to `SKILL.md` so skill discovery is more reliable across environments.

## When To Use

Use this skill when the user asks to:

- sync Codex skills to Claude
- update Claude skills from Codex
- replace a Claude skill with the Codex version
- copy one specific skill from Codex to Claude

## Modes

### Full Sync

For requests like:

- "同步所有 Codex skill 到 Claude"
- "更新 Claude 的 skills"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\20174\.claude\skills\sync-claude-skill\scripts\sync-skills.ps1" -Mode full
```

Behavior:

- Creates a backup of existing Claude user skills
- Removes all Claude target skills
- Copies all Codex user skills except `.system`
- Resolves junction/source links by copying real contents
- Normalizes `skill.md` to `SKILL.md` when needed

### Single Skill Sync

For requests like:

- "同步 github-trending 到 Claude"
- "只更新 md2tex 这个 skill 到 Claude"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\20174\.claude\skills\sync-claude-skill\scripts\sync-skills.ps1" -Mode single -SkillName github-trending
```

Behavior:

- Backs up the current Claude copy of that skill if it exists
- Replaces only that one target skill
- Normalizes `skill.md` to `SKILL.md` when needed

## Output Handling

The script prints a JSON summary. Report to the user:

- mode used
- source and target paths
- backup path
- synced skills
- skipped items
- any errors

## Notes

- Do not copy `C:\Users\20174\.codex\skills\.system`
- First try to detect Claude via `where claude`, then use the matching user Claude data directory
- Treat `C:\Users\20174\.codex\skills` as the source of truth for Codex user skills
- If a skill exists as a junction/link, copy the real target contents
- `skill.md` and `SKILL.md` should both be accepted as source files
- Prefer writing `SKILL.md` in Claude targets
