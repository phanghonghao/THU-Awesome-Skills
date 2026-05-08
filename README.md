# THU-Claude-Code-Skills

> A collection of 10 general-purpose [Claude Code](https://docs.anthropic.com/en/docs/claude-code) custom skills for academic workflows, project management, and developer productivity.
>
> 10 个通用型 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 自定义 Skill，覆盖学术工具、项目管理、开发效率等场景。

---

## Skills List / Skill 列表

| # | Skill | Description / 功能 | Command / 命令 | Dependencies / 依赖 |
|---|-------|-------------------|----------------|---------------------|
| 1 | [notes](skills/notes/) | Markdown note formatting, image renaming, dual-column layout | `/notes` | None |
| 2 | [cheatsheat](skills/cheatsheat/) | Markdown → A4 three-column cheatsheet PDF | `/cheatsheat` | None |
| 3 | [assignment](skills/assignment/) | University assignment management (read → MD → solve → PDF) | `/assignment` | MiKTeX/TeX Live, Python (optional) |
| 4 | [lab-report](skills/lab-report/) | Lab report rewriter v5.0 (PDF/DOCX → MD → PDF) | `/lab-report` | pdfplumber, python-docx, matplotlib |
| 5 | [latex-beamer](skills/latex-beamer/) | Markdown → LaTeX Beamer slides (CJKutf8 + ctex) | `/latex-beamer` | MiKTeX/TeX Live (xelatex) |
| 6 | [github-trending](skills/github-trending/) | Explore trending GitHub repos across AI/tech domains | `/github-trending` | curl (optional) |
| 7 | [git-push](skills/git-push/) | Quick git commit + push with confirmation flow | `/git-push` | git |
| 8 | [merge](skills/merge/) | Merge multiple videos into grid layout (2x2, 3x1, etc.) | `/merge` | `pip install av imageio imageio-ffmpeg Pillow numpy` |
| 9 | [project-managing](skills/project-managing/) | Project meeting notes & progress tracking | `/project-managing` | python-docx (optional) |
| 10 | [which-key](skills/which-key/) | Check which API key the current Claude Code session uses | `/which-key` | None |

---

## Installation / 安装

### Quick Install / 快速安装

```bash
# Clone the repo
git clone https://github.com/phanghonghao/THU-Claude-Code-Skills.git

# Copy all skills to your Claude Code skills directory
cp -r THU-Claude-Code-Skills/skills/* ~/.claude/skills/
```

### Install a Single Skill / 安装单个 Skill

```bash
# Example: install only the merge skill
mkdir -p ~/.claude/skills/merge
cp THU-Claude-Code-Skills/skills/merge/* ~/.claude/skills/merge/
```

### Windows

```powershell
# Copy all skills
Copy-Item -Recurse THU-Claude-Code-Skills\skills\* $env:USERPROFILE\.claude\skills\

# Or install a single skill
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\merge"
Copy-Item THU-Claude-Code-Skills\skills\merge\* "$env:USERPROFILE\.claude\skills\merge\"
```

---

## Skill Details / 各 Skill 使用说明

### 1. notes — Markdown 笔记格式化

- Rename images based on content/heading context
- Auto-add heading markers (`# ## ###`)
- Optional dual-column layout for compact PDF
- Broken image reference recovery

### 2. cheatsheat — A4 三栏小抄

- Convert Markdown notes to compact A4 3-column layout
- Font size: 10.5px (小六), margins: 10mm
- Smart image sizing: large images 95%, small images 45% side-by-side
- Export to PDF via browser print

### 3. assignment — 大学作业管理

Full workflow: read assignment document → convert to Markdown → auto-solve → compile PDF.

| Command | Function |
|---------|----------|
| `/assignment [course] [hw#]` | Create assignment folder, read questions |
| `/assignment complete` | Auto-solve all questions |
| `/assignment done` | Compile MD → PDF |
| `/assignment auto` | One-click: solve + compile |
| `/assignment revise` | Check & fix LaTeX formatting |

Supports PDF, images (OCR), Word (.docx), Markdown input.

### 4. lab-report — 实验报告改写

Rewrite lab reports while preserving structure. Interactive workflow for personal info, images, data, and subjective answers.

| Command | Function |
|---------|----------|
| `/lab-report <course> <path>` | Read report → generate MD template |
| `/lab-report fill` | Fill personal info & subjective answers |
| `/lab-report chart` | Generate matplotlib charts from Excel |
| `/lab-report done` | MD → TEX → PDF |

### 5. latex-beamer — LaTeX Beamer 幻灯片

Convert Markdown to LaTeX Beamer presentations with incremental sync support.

- Dual version: CJKutf8 (pdflatex) + ctex (XeLaTeX)
- Incremental sync: detect .md changes and update .tex
- Smart image placement based on section keywords
- Auto-compile to PDF

### 6. github-trending — GitHub 热门项目探索

Browse trending repos across AI/tech domains with bilingual output.

| Flag | Domain |
|------|--------|
| `--robotics` | Robotics & Embodied AI |
| `--agents` | AI Agents & Frameworks |
| `--mcp` | Model Context Protocol |
| `--llm` | LLM Tools & Inference |
| `--cv` | Computer Vision |
| `--3d` | 3D Reconstruction & Gaussian |
| `--driving` | Autonomous Driving |
| `--rl` | Reinforcement Learning |
| `--audio` | TTS & Audio AI |
| `--vla` | Vision-Language-Action Models |

### 7. git-push — 快速 Git 推送

Interactive git commit + push workflow:
1. Ask for commit description
2. Show changes for confirmation
3. Add → commit → push

### 8. merge — 视频网格拼接

Merge multiple MP4 videos into grid layouts (2x1, 3x1, 2x2, 3x2, custom NxM) with optional labels.

```bash
python <SKILL_ROOT>/merge_videos.py v1.mp4 v2.mp4 v3.mp4 v4.mp4 -t 2x2 --labels "A" "B" "C" "D"
```

### 9. project-managing — 项目会议记录

Generate and manage project meeting notes with progress tracking tables. Supports .docx import.

### 10. which-key — API Key 查询

Quickly check which API key profile the current Claude Code session is using. Read-only, no Bash required.

---

## Requirements / 系统要求

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (installed and configured)
- Python 3.x (for skills with Python scripts)
- MiKTeX / TeX Live (for assignment, lab-report, latex-beamer)

---

## License

[MIT](LICENSE)

---

## Acknowledgements / 致谢

- [jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) — inspiration for the skill format (not included in this repo)
