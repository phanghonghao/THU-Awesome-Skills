---
name: claude2codex
description: Synchronize Claude Code user skills into Codex. Auto-discovers the Claude environment and syncs from the Claude skills folder into %USERPROFILE%\.codex\skills. Supports full sync and single-skill sync. Preserves Codex built-in .system skills and accepts both skill.md and SKILL.md.
---

# Claude to Codex (claude2codex)

Synchronize user-created Claude Code skills into Codex.

## Scope

- Source: Claude user skills folder, auto-discovered from the local Claude environment
- Default source fallback: `%USERPROFILE%\.claude\skills`
- Target: `%USERPROFILE%\.codex\skills`
- Preserve: `%USERPROFILE%\.codex\skills\.system`

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

- "sync all Claude skills to Codex"
- "update Codex skills from Claude"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode full
```

Behavior:

- Creates a backup of existing Codex user skills
- Removes all Codex skills except `.system`
- Copies all skills from Claude source folder into Codex
- Resolves junction/source links by copying real contents
- Normalizes `skill.md` to `SKILL.md` when needed
- Verifies sync result before cleaning up backup

### Single Skill Sync

For requests like:

- "sync github-trending to Codex"
- "update md2tex skill to Codex"

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<SKILL_ROOT>\scripts\sync-skills.ps1" -Mode single -SkillName github-trending
```

Behavior:

- Backs up the current Codex copy of that skill if it exists
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

- Do not touch `%USERPROFILE%\.codex\skills\.system`
- First try to detect Claude via `where claude`, then use the matching user Claude data directory
- Treat the discovered Claude skills directory as the source of truth for user skills
- If a skill exists in Claude as a junction/link, copy the real target contents into Codex
- `skill.md` and `SKILL.md` should both be accepted as source files
- Prefer writing `SKILL.md` in Codex targets
- If the user asks whether Anthropic built-in skills should be included, answer: no by default
