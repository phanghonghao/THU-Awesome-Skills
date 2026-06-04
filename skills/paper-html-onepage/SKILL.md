---
name: paper-html-onepage
description: 从关键词自动检索论文PDF（arXiv优先），提取全文并生成单页A4风格HTML总结。适用于“论文->可读网页总结”场景。
---

# Paper to One-page HTML Skill

## 功能

- 输入关键词，自动检索 arXiv 论文
- 下载对应 PDF
- 按 `pdf-reader` 同款方式提取全文（PyMuPDF）
- 先生成完整全文 HTML（逐页文本，默认作为中间产物生成后删除）
- 再基于全文做一轮总结，生成单页 A4 风格 HTML（和 DreamDojo summary 类似的卡片化布局）
- 如果用户传的是外部 `--pdf <path>`，且源 PDF 不在当前输出目录，会自动复制一份源 PDF 到本地输出目录，并按论文关键词/标题重命名，保证目录里保留源文件

## 使用方式

在任意目录执行（建议在你的项目目录）：

```powershell
python "<SKILL_ROOT>\paper-html-onepage\scripts\paper_to_onepage_html.py" --query "DreamDojo world model" --out "<your_data_path>"
```

也可以不传 `--out`，脚本会自动从论文标题/关键词命名，优先提取类似 `DreamDojo`、`DreamZero`、`AMP` 这类关键词；如果没有明显关键词，再退回到标题前几项内容生成文件名。若关键词重名，脚本会自动补一个标题后缀避免覆盖旧文件。

对比模式（默认彩色简约单页，Method/Data 导向）：

```powershell
python "<SKILL_ROOT>\paper-html-onepage\scripts\paper_to_onepage_html.py" --compare --items "<your_data_path>" "<your_data_path>" --out "<your_data_path>"
```

如果不传 `--items`，脚本会交互式询问文件路径（用 `|` 分隔），不需要硬编码。

可选参数：

- `--max-pages 60`：最多读取多少页（默认 80）
- `--pick 1`：检索结果中选择第几个（默认第 1 个）
- `--keep-pdf`：保留下载的 PDF（默认生成后删除临时 PDF）
- `--keep-fulltext-html`：保留中间生成的 `*_fulltext.html`（默认生成后删除）
- `--pdf <path>`：跳过检索，直接读取本地 PDF 生成 HTML
- `--reflection <path>`：把本地 Markdown/TXT 读后感整理成一页反思页 HTML，尽量保留原内容，并自动嵌入 Markdown 图片
- `--out <path>`：显式指定输出路径；不传时自动按检测到的关键词/短标题命名
- `--compare`：进入多论文对比模式（2篇或多篇）
- `--items ...`：对比模式下输入文件路径列表（支持 pdf/html/txt）
- `--compare-style colorful|minimal`：对比页风格（默认 `colorful`）

读后感整理模式示例：

```powershell
python "<SKILL_ROOT>\paper-html-onepage\scripts\paper_to_onepage_html.py" --reflection "<your_data_path>"
```

如果不传 `--out`，默认输出到同目录下、与源文件同名的 `.html` 文件。

## 输出

默认只保留 1 个文件：

- 主输出 `*.html`：一页总结版

如果使用 `--pdf <path>` 且源 PDF 不在当前输出目录，还会额外保留：

- 源 PDF 的本地副本：自动复制到输出目录，并尽量与主输出同名，例如 `AMP.html` 对应 `AMP.pdf`；重名时自动补后缀避免覆盖

如传 `--keep-fulltext-html`，还会额外保留：

- `*_fulltext.html`：PDF 全文 HTML 展示页（完整读取）

在 `--compare` 模式下，默认生成彩色简约对比页；且相同点/异同点均使用表格（table）展示。

在 `--reflection` 模式下，默认生成双栏的一页反思页：

- 顶部：标题、导语、问题焦点
- 主体：按原文顺序保留段落、编号列表、图片
- 高亮：对带“为什么 / 待确认 / 查证 / ?”等语气的段落做提示样式

其中主输出目标是**一页内信息密集展示**：

- 顶部：标题、作者、来源、链接
- 中部：核心摘要、方法流程、关键术语解释
- 底部：指标表、局限性、给初学者的理解路径

## 约束说明

- 流程固定为：`完整读取PDF -> 全文HTML(中间产物) -> 总结一页HTML`。
- “完整详细读取”指读取所有可解析文本页；如果是扫描件图像 PDF，文本质量受 OCR 缺失影响。

## 依赖

自动安装缺失依赖：

- `requests`
- `PyMuPDF`

