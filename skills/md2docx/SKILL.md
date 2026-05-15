# Markdown to Word (docx) Writer

Read a Markdown file containing table data and images, then fill the data into an existing Word (.docx) document's tables using python-docx. Handles merged cells correctly.

## When to Use

- User says "md2docx", "fill docx", "write to word", "填入docx"
- User has a .md file with data and wants it written back into the original .docx template
- User needs to fill calculated data and images into a Word document's tables

## How to Use

```bash
python ~/.claude/skills/md2docx/md2docx.py "<input.md>" "<template.docx>" ["<output.docx>"]
```

- **input.md** (required): Markdown file containing the data (tables with values to fill)
- **template.docx** (required): Original Word document to modify
- **output.docx** (optional): Output file path. Default: `<template>_filled.docx`

The script reads the Markdown tables and fills matching data into the Word document's tables, handling:
- Merged cells (horizontal and vertical) via XML inspection
- Image insertion from relative paths in the Markdown
- Numeric and text data filling

## Architecture

The md2docx.py script:

1. **Parses the Markdown** to extract table data and image references
2. **Inspects the docx** table structure using XML to detect merged cells
3. **Matches columns** by header text between MD tables and docx tables
4. **Fills data** using direct XML manipulation (`w:tc` elements) to avoid python-docx's merged cell mapping issues
5. **Inserts images** via python-docx's `add_picture` API

### Key Functions

- `get_tcs(table, row_idx)` → Get actual tc elements for a row
- `set_tc_text(tc, text)` → Set cell text via XML (bypasses merge mapping)
- `set_tc_image(tc, img_path, width_cm)` → Insert image into cell

### Handling Merged Cells

The script inspects each row's `w:tc` elements directly to:
- Detect `gridSpan` (horizontal merges) — correctly maps to physical columns
- Detect `vMerge` (vertical merges) — writes value only once to the merge origin cell
- Avoids python-docx's `row.cells[N]` which returns wrong cell objects for merged regions

## Dependencies

- `python-docx`: `python -m pip install python-docx`
- `lxml`: Usually included with python-docx
