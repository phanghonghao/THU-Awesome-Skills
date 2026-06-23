---
name: md2docx
description: >-
  Fill an existing Word `.docx` template using data and images from a Markdown
  file. Use when the user mentions `md2docx`, wants to write Markdown content
  back into a Word document, populate Word tables, preserve merged cells, or
  insert images into a `.docx` template.
---

# md2docx

Fill an existing Word document from a Markdown source with the bundled `md2docx.py` script.

## Run

From this skill directory, run:

```bash
python md2docx.py "<input.md>" "<template.docx>" ["<output.docx>"]
```

## Inputs

Require:
- a Markdown file containing table data and optional image references
- an existing `.docx` template to modify

If the output path is omitted, let the script create the default filled output file.

## What the Script Handles

Use the script for:
- matching Markdown table data into Word tables
- merged cells, including horizontal and vertical merges
- inserting images referenced from Markdown
- mixed numeric and text values

## Workflow

1. Confirm the Markdown file exists.
2. Confirm the template `.docx` exists.
3. Run `md2docx.py`.
4. Report the output document path.
5. If image paths are relative, resolve them relative to the Markdown file location first.

## Dependencies

Require `python-docx`.

If it is missing, install it with:

```bash
python -m pip install python-docx
```

## Operating Notes

- Do not rebuild the document from scratch when the task is to fill an existing template.
- Prefer the script over manual XML edits unless the script itself needs patching.
- If headers in Markdown and Word do not match well enough for filling, explain which columns failed to align.
- If the user asks for a change in mapping behavior, inspect and patch `md2docx.py` rather than hand-editing the `.docx`.