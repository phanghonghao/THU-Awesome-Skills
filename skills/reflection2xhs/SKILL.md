---
name: reflection2xhs
description: Convert a local reflection markdown file, especially `reflection.md` or `*_reflection.MD`, into a polished single-page Xiaohongshu-style A4 poster workflow. Use when the user wants to turn personal paper reflections, study notes, or structured markdown summaries into a shareable visual poster. This skill is Markdown-first and defaults to using the built-in image generation capability after local prompt extraction.
---

# Reflection2XHS

## Overview

Use this skill when the user wants to turn a local reflection markdown file into a one-page Xiaohongshu-style poster image. Prefer Markdown over PDF because this workflow depends on semantic structure rather than fixed page layout.

## Workflow

1. Read the local reflection markdown file.
2. Extract:
   - title
   - subtitle / topic line
   - 3 to 6 key takeaways
   - technical highlights
   - one bottom-line summary sentence
3. Build a stable poster prompt for image generation.
4. Generate the poster image with the built-in image generation capability by default.
5. Only use the local OpenAI image API path as an explicit fallback if the user asks for script-only generation and provides their own `OPENAI_API_KEY`.
6. Save:
   - extracted summary json
   - prompt text
   - generated image in the source file's sibling `*_xhs` folder

## Script

Use [scripts/reflection_to_xhs.py](scripts/reflection_to_xhs.py).

Preview prompt only:

```powershell
python "<SKILL_ROOT>\reflection2xhs\scripts\reflection_to_xhs.py" --input "<your_data_path>"
```

Generate prompt locally, then use built-in image generation:

```powershell
python "<SKILL_ROOT>\reflection2xhs\scripts\reflection_to_xhs.py" --input "<your_data_path>"
```

The generated `prompt.txt` is then used by the assistant's built-in image generation flow.

When the assistant uses built-in image generation, it should still place the final poster image into the same local output folder as the extracted artifacts, typically:

- `<source_stem>_xhs/summary.json`
- `<source_stem>_xhs/prompt.txt`
- `<source_stem>_xhs/poster.png`

If needed, the local script can also finalize this step by copying the most recent Codex-generated PNG into the output folder:

```powershell
python "<SKILL_ROOT>\reflection2xhs\scripts\reflection_to_xhs.py" --input "<your_data_path>" --copy-latest-codex-image
```

Script-only image generation fallback:

```powershell
$env:OPENAI_API_KEY="your_api_key"
python "<SKILL_ROOT>\reflection2xhs\scripts\reflection_to_xhs.py" --input "<your_data_path>" --generate
```

## Notes

- Prefer the built-in image generation capability after Markdown extraction.
- Use the user's own `OPENAI_API_KEY` only for the script-only fallback path.
- Default model is `gpt-image-1`.
- Prefer Markdown over PDF. Use PDF only as fallback when Markdown is unavailable.
- Final image output should not remain only under the Codex generated-images cache; copy it into the source markdown's local `*_xhs` output folder.
- This skill generates a poster prompt and image workflow. It does not preserve the original page layout pixel-for-pixel.
