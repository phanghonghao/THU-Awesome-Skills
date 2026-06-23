---
name: training-log-update
description: Append or create the daily training-log entry (one YYYY-MM-DD.md per day) in the established house style — a one-line Headline plus explicit Done / Issues-and-fixes / Pending / Key-paths sections, with NO media copied in (reference real paths). Use whenever the user says "update the training log", "记录一下今天的 training log", "写 training log", "log today's work", or wants to record what was done vs what's pending. Auto-detects the log folder for the current repo and carries context forward from the latest entry.
---

# training-log-update

Maintain a per-day training log that records **what was done vs what's pending**,
in a consistent house style. One Markdown file per day, referenced by a README
index. No media is copied into the log — it only references real artifact paths.

## 1. Locate the log folder for the current repo

From the current working directory, pick the **first existing** candidate:

| repo pattern | log folder | README | example entry |
|---|---|---|---|
| OmniLab_GMR | `Document/Training Log/` | `README.md` | `2026-06-20.md` |
| UniLab | `docs/training-log/` | `README.md` | `2026-06-20.md` |

If neither exists, ask the user where to keep the log (and create the folder +
README on first use). Do not invent a third location without asking.

## 2. Carry context forward (always do this first)

1. Read the folder's `README.md` — it states the house rules and the **Index**
   table of past entries.
2. List the folder and read the **latest `YYYY-MM-DD.md`** (and skim 1–2 prior
   ones if today continues that work). Match its tone, section order, table
   style, and heading conventions. If today extends a pending item from a prior
   entry, explicitly reference it ("follows up on [2026-06-20] pending #2").

This is the whole reason the format exists — each update builds on the last.

## 3. Create or update today's file

Path: `<log folder>/<TODAY_YYYY-MM-DD>.md` where TODAY is the real current date.

- If today's file already exists, **append/merge** into it (don't duplicate
  sections; update metrics, append new sub-sections, move items Done→Pending as
  their status changes).
- If new, use the template below.

### Daily file template (match prior entries' style)

```markdown
# YYYY-MM-DD — <Project short name>

**Headline**: one sentence — the single most important outcome of the day.

## <Done section 1 — e.g. "Z1 retarget calibration">
What was built/run/fixed. Use tables for metrics. Reference real paths.

| metric | before | after |
|---|---|---|
| ... | ... | ... |

## <Done section 2 ...>
...

## Issues hit & fixes
| issue | cause | fix |
|---|---|---|
| ... | ... | ... |

## Pending / next session
1. **<thing>** — why it's blocked / what to run next.
2. ...

## Key paths today
- `<real/absolute/or/relative path>` — what it is
- ...
```

### House rules (non-negotiable)

- **Done vs Pending must be explicit.** That is the entire point of this log.
- **Never copy media into the log.** Reference the real path to any
  figure/video/csv (e.g. `` `gmr_demo/videos/z1_real_dance.mp4` ``). The log is
  text-only.
- **Be concrete and technical.** Real paths, real numbers, real commands. No
  filler ("today was productive").
- **Tables for metrics and issue/fix** — they scan fast.
- **Honest status.** If something failed or was abandoned, say so in Issues and
  Pending. Don't mark partial work Done.
- **Reference prior entries** when continuing work.

## 4. Update the README Index

Append (or update) one row in the README's `## Index` table:

```
| [YYYY-MM-DD](YYYY-MM-DD.md) | <≤1-line highlights> |
```

Keep highlights to the 1–2 biggest outcomes. If today's row already exists,
refresh its highlights in place.

## 5. Report back

Tell the user:
- the file written/updated (path),
- the headline you used,
- anything moved between Done and Pending,
- any ambiguity you resolved by assumption (so they can correct it).

Do not paste the full entry back — it's in the file; just summarize the change.
