---
name: notes
description: Transform Markdown notes with renamed images, auto-add heading markers, and optionally add dual-column layout for compact PDF output. Use this skill whenever the user mentions notes, markdown formatting, image renaming, adding headings, or organizing note files. Always use this skill when working with Markdown notes that need formatting or image processing.
---

# Notes Skill

Transform Markdown notes with proper image naming - without changing the original content.

## Overview

This skill helps you:
1. **Rename and organize images** - rename based on content, move to `/sources` directory
2. **Format the layout & add headings** (spacing, heading markers, lists) - Add ## ### markers for section titles
3. **Dual-column layout (OPTIONAL)** - Add HTML/CSS flexbox for compact PDF output (left fills first, then right)
4. **Generate HTML (OPTIONAL)** - only when:
   - The markdown contains `.gif` animated images
   - The markdown contains video references
   - User explicitly requests HTML output
5. **Recover broken references** (automatic) - when images can't be found, match by context to available images in `sources/`

## Important: Content Preservation Rule

**DO NOT change, rewrite, or add to the original content.** Only:
- Fix formatting (spacing, indentation)
- Add heading markers (# ## ###) to existing section titles
- Fix list formatting
- Fix table alignment

**DO NOT:**
- Rewrite sentences
- Add new sections or content that wasn't there
- Summarize or paraphrase
- Add "课堂笔记" or placeholder sections that weren't there

**Heading Markers - ALLOWED:**
- "概述：" → "## 概述"
- "3.1.2 塑形成形方法" → "## 3.1.2 塑形成形方法"
- "第三章" → "# 第三章"

## Workflow

### Step 1: Read the Markdown File

Read the target Markdown file to understand:
- Current structure and formatting
- Image references (look for `![alt text](image.png)` patterns)
- Original content that must be preserved

### Step 2: Rename Images Based on Alt Text OR Section Title

For each image reference `![alt text](filename.png)` in the Markdown:

**Priority 1: Use meaningful alt text**
If the alt text is descriptive (not `alt-text`, `image`, `图片`, etc.):
1. **Extract the alt text** from the image reference
2. **Generate a new filename** using the alt text
3. **Copy the image to `/sources` with new name** (create directory if not exists)
4. **Delete the original unnamed image file** (to avoid duplication)
5. **Update the Markdown reference** to `![alt text](sources/newfilename.png)`

**Priority 2: Extract from section heading above**
If the alt text is generic/placeholder:
1. **Find the nearest heading above** the image (##, ###, etc.)
2. **Extract key nouns/phrases** from the heading:
   - Remove parenthetical explanations like （物理+化学）、（图示）、[注]
   - Extract the core noun phrase (e.g., "干法刻蚀" from "## 干法刻蚀（物理+化学）")
   - If multiple images under same heading, add numbered suffix: _1, _2, etc.
3. **Copy the image to `/sources` with new name** (create directory if not exists)
4. **Delete the original unnamed image file** (to avoid duplication)
5. **Update the Markdown reference** to `![alt text](sources/newfilename.png)`

**IMPORTANT - Image path rule:**
- After renaming, ALL images must be copied to `/sources` subdirectory
- Original unnamed image files MUST be deleted after copying
- Markdown references must use `sources/` prefix (no `../`)

**Examples:**
```markdown
# Example 1: Using descriptive alt text
Before: ![工程中效率默认值](image-1.png)
After:  ![工程中效率默认值](sources/工程中效率默认值.png)

# Example 2: Extracting from heading
Before:
## 干法刻蚀（物理+化学）
![alt-text](image.png)

After:
## 干法刻蚀（物理+化学）
![干法刻蚀](sources/干法刻蚀.png)

# Example 3: Multiple images under same heading
Before:
## 半导体器件基础
![image](image.png)
![image-1](image-1.png)

After:
## 半导体器件基础
![半导体器件](sources/半导体器件.png)
![PN结](sources/半导体器件_PN结.png)
```

**Note:** All renamed images are copied to `/sources/` directory, original files are deleted, and referenced with `sources/` prefix.

**Heading keyword extraction rules:**
- Remove: （）、[]、()内的解释性文字
- Remove: 后缀词如"概述"、"简介"、"说明"
- Keep: 核心名词，如"干法刻蚀"、"PN结"、"氧化工艺"
- For multi-concept headings, split: "氧化与扩散" → 第一个图用"氧化"，第二个用"扩散"

### Step 2.5: Recover Mode (Only When Images Not Found)

**IMPORTANT: This mode ONLY activates when an image reference cannot be found.**

When processing image references, if the referenced file does NOT exist:

1. **Detect broken reference** - Check if the image file exists in current directory or `sources/`

2. **Extract context** - Get surrounding text:
   - 2 lines before the image reference
   - 1 line after the image reference
   - Focus on Chinese keywords and technical terms

3. **List available images** - Get all PNG files in `sources/` directory

4. **Fuzzy match** - Match keywords in context with filenames:
   - Extract meaningful Chinese terms from context (remove punctuation, common words)
   - Extract terms from filename (remove .png extension)
   - Calculate match score based on:
     - **Exact phrase matches** (highest priority) - e.g., "确保充满" matches "保证充满"
     - **Partial word matches** - e.g., "浇注" matches "浇注系统"
     - **Semantic relatedness** - e.g., "铸造" relates to "砂型铸造"

5. **Update reference** - Replace with best match if confidence > threshold:
   ```markdown
   Before: ![alt text](image-1.png)
   After:  ![保证充满](sources/保证充满.png)
   ```

6. **Log recovery** - Note the recovery action for user review

**Matching Rules (Priority Order):**
- Priority 1: Exact match between context keyword and filename
- Priority 2: Partial match (substring in filename)
- Priority 3: Semantic relatedness (同义词、相关概念)
- If no good match (score < threshold), leave original reference and add HTML comment

**Example:**
```markdown
Context:
锥面（确保充满）
![alt text](image-1.png)

Available in sources: 保证充满.png, 浇注系统.png, ...
Match: "确保充满" in context → "保证充满" in filename (HIGH CONFIDENCE)
Result: ![保证充满](sources/保证充满.png)
```

### Step 3: Format Layout & Add Headings

Improve formatting and add heading structure:

1. **Add heading markers** - Convert section titles to markdown headings (# ## ###)
   - Lines ending with "：" or containing章节/题目 → Add ## prefix
   - Lines like "第三章"、"3.1.2" → Add # or ## prefix
   - Generic section markers like "概述"、"特点"、"补充" → Add ## prefix
2. **List formatting** - Fix list syntax (do NOT change list items)
3. **Spacing** - Add consistent blank lines between sections
4. **Code blocks** - Add language identifiers if missing
5. **Table alignment** - Fix table formatting

### Step 3.5: Generate Dual-Column Layout (OPTIONAL)

**NOTE: This step adds CSS multi-column layout for compact PDF output. Content flows from top to bottom, left to right naturally.**

When user requests dual-column layout (for compact PDF output):

#### Layout Pattern

Wrap content in CSS multi-column container:

```html
<div style="column-count: 2; column-gap: 20px; column-rule: 1px solid #ddd;">
<!-- Content flows naturally: top → bottom, left → right -->
## 标题
文字内容...
<img src="sources/image.png" alt="图片" style="max-width: 100%; break-inside: avoid;">
更多内容...
</div>
```

#### Implementation Rules

1. **Identify sections** - Each major ## heading section can be wrapped separately
2. **Wrap in column container** - Use `column-count: 2` for dual-column layout
3. **Content flow** - Content naturally fills left column first, then flows to right column
4. **Image styling**:
   - Use `max-width: 100%` (relative to column width, i.e., 50% of screen)
   - Add `break-inside: avoid` to prevent images from being split across columns
5. **Add separator** - Use `---` between major sections

#### Example

Before (single column):
```markdown
## 概述
塑形成型：利用固体金属"塑性变形"，在外力下改变形状

## 特点
机械自动化——批量生产
力学性能好——致密化
![四种工艺](sources/四种工艺.png)
```

After (dual column, auto-flow):
```markdown
<div style="column-count: 2; column-gap: 20px; column-rule: 1px solid #ddd;">

## 概述
塑造成型：利用固体金属"塑性变形"，在外力下改变形状

## 特点
机械自动化——批量生产
力学性能好——致密化

<img src="sources/四种工艺.png" alt="四种工艺" style="max-width: 100%; break-inside: avoid;">
<!-- Image stays below related text, flows with content -->

</div>
```

### Step 4: Generate Static HTML (OPTIONAL - Special Cases Only)

**IMPORTANT: HTML generation is SKIPPED by default. Only generate when:**
1. The markdown contains `.gif` animated images
2. The markdown contains video references (`.mp4`, `.webm`, etc.)
3. User explicitly requests HTML output

When HTML generation is needed:

#### Step 4a: Check for Special Media

Scan the markdown for:
- `![alt](image.gif)` - GIF animations
- `<video>` tags or video file references
- User's explicit HTML request

#### Step 4b: Convert Images to Base64 (for GIF/videos only)

For GIF and video files, embed as base64 to ensure animations work:

```python
import base64

with open('sources/image.gif', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')
    data_uri = f"data:image/gif;base64,{b64}"
```

For static images (PNG, JPG), keep as external references to `sources/` directory to reduce file size.

#### Step 4c: Generate HTML with Embedded Media

Create HTML with:
- Original content preserved exactly
- **GIF/video images embedded as base64 data URIs** (e.g., `src="data:image/gif;base64,..."`)
- **Static images as external references** to `sources/` directory
- Modern CSS styling
- Responsive design
- Table of contents
- Print-friendly styles

The resulting HTML file should be viewable offline with minimal external dependencies (only static images).

**HTML file naming:** Use `{原文件名}_embedded.html` format (e.g., `3_17_embedded.html`)

**Default behavior:** If no special media detected, skip HTML generation entirely.

## HTML Template (For Special Cases Only)

**NOTE: This template is only used when generating HTML for GIF animations, videos, or when explicitly requested.**

```python
# -*- coding: utf-8 -*-
import base64
import os
from pathlib import Path

# Step 1: Convert GIF/video images to base64 (static images remain external)
sources_dir = Path('sources')

# Special media files to embed (GIF, video)
special_files = {
    "animation.gif": "动画描述",
    # Add GIF/video files only...
}

base64_map = {}
for fn, alt in special_files.items():
    with open(sources_dir / fn, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
        base64_map[alt] = b64

# Step 2: Generate HTML with embedded special media
html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note Title</title>
    <!-- Add CSS here -->
</head>
<body>
    <!-- Static images use external sources -->
    <img src="sources/static_image.png" alt="static">
    <!-- GIF/video images are embedded as base64 -->
    <img src="data:image/gif;base64,{动画描述}" alt="动画描述">
</body>
</html>'''

# Step 3: Replace placeholders with base64 data
for alt, b64 in base64_map.items():
    html = html.replace(f'{{{alt}}}', b64)

# Step 4: Save HTML with _embedded suffix
with open('原文件名_embedded.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

## HTML Structure (For Special Cases Only)

**NOTE: HTML generation is optional and only used for GIF animations, videos, or when explicitly requested.**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Note Title]</title>
    <style>
        /* CSS for readability, responsive layout, TOC, print styles */
    </style>
</head>
<body>
    <nav class="toc"><!-- Table of contents --></nav>
    <main class="content">
        <!-- Original content with styling -->
        <!-- Static images: <img src="sources/image.png" alt="..."> -->
        <!-- GIF/video: <img src="data:image/gif;base64,..." alt="..."> -->
    </main>
</body>
</html>
```

## Output Files

1. **Updated .md file** - Formatted with heading markers (# ## ###), image paths point to `sources/`
2. **Renamed image files in `/sources` directory** - Descriptive names based on alt text or headings (original unnamed files deleted)
3. **Dual-column layout (OPTIONAL)** - HTML/CSS flexbox wrappers added for compact PDF output
4. **`{原文件名}_embedded.html` (OPTIONAL)** - Only generated when:
   - Markdown contains `.gif` animations or videos
   - User explicitly requests HTML output

## Usage Examples

- "Format this note and fix image names"
- "Clean up my note formatting"
- "Add headings to my notes"
- "Add dual-column layout for PDF"
- "Fix broken image references in my note"
- "Recover missing images using context"
- "Convert markdown to HTML" (only when needed for GIF/video or explicitly requested)

## Remember

**Preserve original content. Only fix formatting.**
