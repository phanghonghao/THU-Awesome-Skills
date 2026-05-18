---
name: claude2anti
description: Synchronize Claude Code user skills into Antigravity. Auto-discovers the Claude environment and syncs from the Claude skills folder into %USERPROFILE%\.gemini\antigravity\skills. Supports full sync and single-skill sync.
---

# Claude to Antigravity (claude2anti)

Synchronize user-created Claude Code skills into Antigravity.

## Scope

- Source: Claude user skills folder, auto-discovered from the local Claude environment
- Default source fallback: `%USERPROFILE%\.claude\skills`
- Target: `%USERPROFILE%\.gemini\antigravity\skills`

The sync logic should treat both `SKILL.md` and `skill.md` as valid skill entry files. When copying to Antigravity, normalize to `SKILL.md` so skill discovery is more reliable across environments.

## When To Use

Use this skill when the user asks to:

- sync Claude skills to Antigravity
- update Antigravity skills from Claude
- replace an Antigravity skill with the Claude version
- copy one specific skill from Claude to Antigravity

## Modes

### Full Sync

For requests like:

- "sync all Claude skills to Antigravity"
- "update Antigravity skills from Claude"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode full
```

Behavior:

- Creates a backup of existing Antigravity user skills
- Removes all Antigravity skills
- Copies all skills from Claude source folder into Antigravity
- Resolves junction/source links by copying real contents
- Normalizes `skill.md` to `SKILL.md` when needed
- Verifies sync result before cleaning up backup

### Single Skill Sync

For requests like:

- "sync github-trending to Antigravity"
- "update md2tex skill to Antigravity"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode single -SkillName github-trending
```

Behavior:

- Backs up the current Antigravity copy of that skill if it exists
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

- First try to detect Claude via `where claude`, then use the matching user Claude data directory
- Treat the discovered Claude skills directory as the source of truth for user skills
- If a skill exists in Claude as a junction/link, copy the real target contents into Antigravity
- `skill.md` and `SKILL.md` should both be accepted as source files
- Prefer writing `SKILL.md` in Antigravity targets
