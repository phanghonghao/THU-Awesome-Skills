---
name: resume-builder
description: 从用户上传的简历资料(PDF/Word/Markdown/已有 YAML/口述)生成排版好的单栏中文简历 PDF。全程不依赖 LaTeX/MiKTeX/Overleaf——用 HTML 模板 + 系统 Chrome/Edge 无头打印出 PDF。当用户提到「简历」「resume」「cv」「生成简历 PDF」「套用我的简历模板」时使用。
---

# resume-builder —— 无 LaTeX 的简历生成器

把任意来源的简历资料，套用固定的单栏中文版式，输出为排版好的 **PDF**。
**关键：完全不使用 LaTeX / pdflatex / MiKTeX / Overleaf，也不使用任何个人 token。**
PDF 由系统已安装的 Chrome 或 Edge 无头打印生成（与 html2pdf 同机制）。

## 数据格式

固定结构，见 `schema/resume_schema.yaml`，可运行示例见 `examples/resume_data_example.yaml`。
板块：`personal / education / projects / lab_experience / clubs / competitions / skills / social_practice`。
每个经历板块都是**列表**，可写任意条数；字段留空或 `education[].optional: true` 自动不渲染。

## 工作流（务必按此执行）

### 1. 取输入并归一化成数据文件
根据用户给的资料，产出工作目录下的 `resume_data.yaml`（本机无 PyYAML 时改用 `resume_data.json`）：

- **已有 YAML/JSON**：直接用（字段对不上时按 schema 改写）。
- **PDF 简历**：先用 `pdf-reader`（或 `markitdown` / `pdf2word`+`word2md`）提取文本，再由你（Claude）读内容、按 schema 重组。
- **Word 简历**：用 `word2md` 或 `markitdown` 转 Markdown，再重组。
- **Markdown / TXT**：直接读，按 schema 重组。
- **纯口述**：根据用户描述组装成 schema。

重组时遵循：中文姓名进 `personal.name_cn`、英文姓名进 `name_en`；经历按时间倒序；无对应内容就留空，不要编造。

### 2. 生成 HTML
```bash
python "<SKILL_DIR>/scripts/build_resume.py" resume_data.yaml --out resume.html
```
> `<SKILL_DIR>` = 本 skill 目录。把脚本路径写全（含绝对路径）最稳。

### 3. 生成 PDF
```bash
python "<SKILL_DIR>/scripts/render_pdf.py" resume.html resume.pdf
```
输出 PDF 路径与页数会打印出来。纸张(A4)/边距由 HTML 模板的 `@page` CSS 控制。

### 4. 修改循环
用户要调整内容 → 改 `resume_data.yaml` → 重跑第 2、3 步。
要调版式（字号/间距/颜色）→ 直接改 `templates/classic_single.html` 的 CSS，无需改脚本。

## 输出位置约定

`resume_data.yaml` / `resume.html` / `resume.pdf` 写到**调用时的当前工作目录**（或用户指定路径）。
**不要**往 skill 目录里写生成物——保持 skill 目录只读、可整体打包分享。

## 禁止事项

- 不要调用 pdflatex / xelatex / tlmgr / MikTeX / Overleaf，也不要写 `.tex`。
- 不要使用任何 Overleaf token、cookie、API key（包括用户历史 `tools/` 里的那些）。
- 不要为了“修复中文”去装 TeX 相关任何东西——浏览器原生支持中文，无需额外字体。

## 常见问题

- **找不到浏览器**：提示用户安装 Chrome 或 Edge，或用 `--browser <路径>` 指定。
- **PyYAML 缺失**：把数据写成 `.json` 再跑（或 `pip install pyyaml`）。
- **想预览**：生成 `resume.html` 后可直接在浏览器打开看屏幕预览效果。
