---
name: sync-codex-skill
description: Synchronize Claude Code user skills into Codex by discovering the Claude environment via `where claude` and syncing from the Claude skills folder into C:\Users\20174\.codex\skills. Use when the user wants to sync, update, replace, or copy one or all custom Claude skills into Codex. Supports full sync and single-skill sync. Preserves Codex built-in .system skills and accepts both skill.md and SKILL.md.
---

# Sync Codex Skill

Synchronize user-created Claude Code skills into Codex.

## Scope

- Source: Claude user skills folder, auto-discovered from the local Claude environment
- Default source fallback: `C:\Users\20174\.claude\skills`
- Target: `C:\Users\20174\.codex\skills`
- Preserve: `C:\Users\20174\.codex\skills\.system`

Default behavior is to sync **user/custom Claude skills only**. You do **not** need to include Anthropic built-in system skills because they are not stored in this source folder and Codex already has its own `.system`.

The sync logic should treat both `SKILL.md` and `skill.md` as valid skill entry files. When copying to Codex, normalize to `SKILL.md` so skill discovery is more reliable across environments.

## When To Use

Use this skill when the user asks to:

- sync Claude skills to Codex
- update Codex skills from Claude
- replace a Codex skill with the Claude version
- copy one specific skill from Claude to Codex

## Modes

### Full Sync

For requests like:

- "同步所有 Claude skill 到 Codex"
- "更新 Codex 的 skills"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\20174\.claude\skills\sync-codex-skill\scripts\sync-skills.ps1" -Mode full
```

Behavior:

- Creates a backup of existing Codex user skills
- Removes all Codex skills except `.system`
- Copies all skills from Claude source folder into Codex
- Resolves junction/source links by copying real contents
- Normalizes `skill.md` to `SKILL.md` when needed

### Single Skill Sync

For requests like:

- "同步 github-trending 到 Codex"
- "只更新 md2tex 这个 skill"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\20174\.claude\skills\sync-codex-skill\scripts\sync-skills.ps1" -Mode single -SkillName github-trending
```

Behavior:

- Backs up the current Codex copy of that skill if it exists
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

- Do not touch `C:\Users\20174\.codex\skills\.system`
- First try to detect Claude via `where claude`, then use the matching user Claude data directory
- Treat the discovered Claude skills directory as the source of truth for user skills
- If a skill exists in Claude as a junction/link, copy the real target contents into Codex
- `skill.md` and `SKILL.md` should both be accepted as source files
- Prefer writing `SKILL.md` in Codex targets
- If the user asks whether Anthropic built-in skills should be included, answer: no by default
