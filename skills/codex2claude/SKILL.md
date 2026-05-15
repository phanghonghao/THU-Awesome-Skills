---
name: codex2claude
description: Synchronize Codex user skills into Claude Code. Auto-discovers the Claude environment and syncs from %USERPROFILE%\.codex\skills into the Claude skills folder. Supports full sync and single-skill sync. Excludes Codex built-in .system and accepts both skill.md and SKILL.md.
---

# Codex to Claude (codex2claude)

Synchronize user-created Codex skills into Claude Code.

## Scope

- Source: `%USERPROFILE%\.codex\skills`
- Exclude from source: `%USERPROFILE%\.codex\skills\.system`
- Target: Claude user skills folder, auto-discovered from the local Claude environment
- Default target fallback: `%USERPROFILE%\.claude\skills`

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

- "sync all Codex skills to Claude"
- "update Claude skills from Codex"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode full
```

Behavior:

- Creates a backup of existing Claude user skills
- Removes all Claude target skills
- Copies all Codex user skills except `.system`
- Resolves junction/source links by copying real contents
- Normalizes `skill.md` to `SKILL.md` when needed
- Verifies sync result before cleaning up backup

### Single Skill Sync

For requests like:

- "sync github-trending to Claude"
- "update md2tex skill to Claude"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode single -SkillName github-trending
```

Behavior:

- Backs up the current Claude copy of that skill if it exists
- Replaces only that one target skill
- Normalizes `skill.md` to `SKILL.md` when needed
- Verifies sync result before cleaning up backup

## Output Handling

The script prints a JSON summary. Report to the user:

- mode used
- source and target paths
- backup path
- synced skills
- skipped items
- any errors

## Notes

- Do not copy `%USERPROFILE%\.codex\skills\.system`
- First try to detect Claude via `where claude`, then use the matching user Claude data directory
- Treat `%USERPROFILE%\.codex\skills` as the source of truth for Codex user skills
- If a skill exists as a junction/link, copy the real target contents
- `skill.md` and `SKILL.md` should both be accepted as source files
- Prefer writing `SKILL.md` in Claude targets
