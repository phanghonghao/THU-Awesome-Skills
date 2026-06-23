---
name: project-managing
description: >-
  Create and update project meeting records and progress-tracking documents.
  Use when the user asks to write meeting minutes,鏁寸悊浼氳绾, track project
  progress, update action items, summarize blockers, assign owners, or maintain
  a structured project status record.
---

# Project Managing

Create and maintain structured project meeting notes and progress summaries.

## Working Style

Prefer Markdown unless the user explicitly asks for another format.

Extract and organize:
- meeting title
- date and time
- participants
- agenda
- decisions
- action items
- owners
- due dates
- blockers
- next steps

Do not leave notes as a raw transcript when a structured summary is expected.

## Default Output Structure

Use this structure unless the user already has a required template:

```markdown
# <椤圭洰鍚?浼氳璁板綍

## 鍩烘湰淇℃伅
- 浼氳涓婚锛?- 鏃堕棿锛?- 鍙備細浜猴細
- 璁板綍浜猴細

## 璁涓庣粨璁?| 璁 | 璁ㄨ缁撹 | 澶囨敞 |
|---|---|---|

## 琛屽姩椤?| ID | 浠诲姟 | 璐熻矗浜?| 鎴鏃堕棿 | 鐘舵€?| 澶囨敞 |
|---|---|---|---|---|---|

## 椋庨櫓涓庨樆濉?| 闂 | 褰卞搷 | 澶勭悊鏂规 | 璐熻矗浜?|
|---|---|---|---|

## 涓嬫璺熻繘
- 
```

## Progress Update Rules

When updating an existing project record:

1. Preserve the existing document structure if it is already usable.
2. Update status fields instead of duplicating old tasks.
3. Mark completed items clearly.
4. Add new action items only when they are distinct.
5. Keep owner and due-date fields explicit whenever the source material provides them.

## Summarization Rules

When the source is a transcript, chat log, or rough notes:

- compress repetitive discussion
- keep concrete decisions
- keep unresolved questions
- convert vague promises into explicit action items only when ownership is clear
- separate facts from assumptions

## Response Style

Prefer concise, execution-oriented notes.
Use tables for action items and blockers when that improves readability.
Call out missing owners or missing deadlines instead of silently inventing them.