# resume-builder —— 无 LaTeX 的简历生成器

把任意来源的简历资料，套用固定的单栏中文版式，输出排版好的 **PDF**。
**全程不装 LaTeX / MiKTeX，不用 Overleaf，不需要任何账号或 token。**
PDF 由系统已有的 Chrome 或 Edge 无头打印生成。

灵感来自 [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) 的 report 渲染方式
（HTML → 无头浏览器 → PDF），但用更轻量的浏览器命令行打印，无需安装 Playwright。

## 目录结构

```
resume-builder/
├── SKILL.md                     # Claude 的工作流指令（skill 入口）
├── README.md                    # 本文件
├── schema/resume_schema.yaml    # 数据格式说明（字段 + 注释）
├── examples/resume_data_example.yaml  # 可直接运行的数据示例
├── templates/classic_single.html      # 单栏中文版式 HTML 模板（含 A4 打印 CSS）
└── scripts/
    ├── build_resume.py          # 数据(YAML/JSON) → resume.html
    └── render_pdf.py            # resume.html → resume.pdf（Chrome/Edge 无头）
```

## 三步出 PDF

```bash
# 1. 准备数据：复制示例并改成自己的信息
cp examples/resume_data_example.yaml resume_data.yaml
#   （编辑 resume_data.yaml）

# 2. 生成 HTML
python scripts/build_resume.py resume_data.yaml --out resume.html

# 3. 生成 PDF
python scripts/render_pdf.py resume.html resume.pdf
```

依赖：仅需 **Python 3** + **Chrome 或 Edge**（系统已有即可）。
读 YAML 需 `pip install pyyaml`；不想装就用 `.json` 数据文件。

## 输入来源（在 Claude Code 里直接对话即可）

把这个 skill 放进 `~/.claude/skills/` 后，在 Claude Code 里说：
- 「用我的简历模板，帮我把这份 PDF 重新排版」→ 上传 PDF
- 「把这份 Word 简历套成我的版式」→ 上传 .docx
- 「按这个 Markdown 生成简历 PDF」
- 或直接口述经历，Claude 会组装成数据再出 PDF。

Claude 会自动：提取文本 → 按 schema 重组 → build → render，并告诉你 PDF 路径与页数。

## 数据格式速览

```yaml
personal:        { name_cn, name_en, phone, email, address, target }
education:       [{ school, start, end, city, major, gpa, courses, optional }]
projects:        [{ name, start, end, role, tech, desc, details }]
lab_experience:  [{ name, start, end, desc }]
clubs:           [{ name, start, end, role, desc }]
competitions:    [{ name, date, desc }]
skills:          { software, languages, hardware, languages_spoken }
social_practice: { org, desc }
```

- 每个经历板块都是列表，可写任意条数。
- 任意字段留空 → 该内容自动不渲染。
- `education[].optional: true` → 保留数据但不显示那一段。

## 自定义版式

直接改 `templates/classic_single.html` 里的 CSS：
- 纸张/边距：`@page { size: A4; margin: ... }`
- 字体/字号：`html, body { font-family / font-size }`
- 板块标题下划线、条目间距等都在文件顶部 `<style>` 内，带注释。

改 CSS 不用动 Python 脚本。

## 分享给别人

把整个 `resume-builder/` 目录打包成 zip 发给对方，对方解压到自己的
`~/.claude/skills/` 即可在 Claude Code 里使用。**不含任何个人密钥。**

## 设计取舍

| 维度 | 选择 | 原因 |
|------|------|------|
| PDF 引擎 | 浏览器 `--print-to-pdf` | 零安装、原生支持中文、无需 LaTeX |
| 模板 | HTML+CSS | 可视化好改、版式可控 |
| 数据 | YAML/JSON | 结构化、易填、可程序化 |
| 跨文档解析 | 由 Claude 读懂后重组 | 比正则鲁棒，版式来源不限 |
