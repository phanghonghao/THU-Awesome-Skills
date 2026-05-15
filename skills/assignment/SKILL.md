---
name: assignment
description: 大学作业管理系统 - 读取作业文档转为MD，用 `/assignment complete` 自动完成解答，用 `/assignment done` 编译PDF。
---

# Assignment Skill - 大学作业管理系统

自动化大学作业处理：读取作业文档 → 转换为 Markdown → 自动完成解答 → 编译为 PDF。

## Overview

这个 skill 帮助你：
1. **创建作业文件夹** - 按格式 `姓名_学号_班级_课程_作业序号` 自动命名
2. **读取作业文档** - 支持 **PDF、图片 (PNG/JPG/JPEG)、DOCX** 格式
3. **转换为 Markdown** - 提取文字、公式、图片到 .md
4. **自动完成解答** - 使用 `/assignment complete` 逐题完成，遇到疑问时询问
5. **编译 PDF** - 使用 `/assignment done` 触发 MikTeX 编译

## Workflow

### Step 0: 询问作业文件夹位置

**重要**：首先询问用户作业文件夹应该放在哪里
```
"请提供作业文件夹的路径（作业文件将保存在此文件夹下）"
```

示例路径：
- `课程名/作业/` - 相对路径
- `C:/Users/xxx/Documents/作业/` - 绝对路径
- `.` - 当前目录

### Step 1: 收集作业信息

询问用户以下信息：
| 字段 | 说明 | 示例 |
|------|------|------|
| 姓名 | 学生姓名 | <姓名> |
| 学号 | 10位学号 | <学号> |
| 班级 | 班级名称 | <班级> |
| 课程 | 课程名称 | 材料加工1 |
| 作业序号 | 作业编号 | 作业8 |

### Step 2: 询问作业文档

**重要**：询问用户作业文档的路径
```
"请提供作业文档的路径"
```

支持的格式：
- `.pdf` - PDF 文档
- `.png` / `.jpg` / `.jpeg` - **图片文档（使用 PaddleOCR OCR 识别）**
- `.docx` - **Word 文档（使用 python-docx / mammoth 提取）**
- `.doc` - 旧版 Word 文档（需先转换为 .docx）
- `.md` - Markdown 文件（已有内容）

### Step 3: 创建文件夹结构

在用户指定的文件夹下创建：
```
[用户指定的文件夹]/姓名_学号_班级_课程_作业序号/
├── 姓名_学号_班级_课程_作业序号.md    # Markdown源文件
├── 姓名_学号_班级_课程_作业序号.tex   # LaTeX文件（done时生成）
├── 姓名_学号_班级_课程_作业序号.pdf   # PDF输出（done时编译）
└── sources/                          # 图片目录（提取的图片）
```

例如，用户指定 `课程名/作业/`，则创建：
```
课程名/作业/姓名_学号_班级_课程_作业序号/
├── 姓名_学号_班级_课程_作业序号.md
├── 姓名_学号_班级_课程_作业序号.tex
├── 姓名_学号_班级_课程_作业序号.pdf
└── sources/
```

### Step 4: 读取并转换文档

根据文档类型进行处理：

#### A. PDF 文档
- 使用 **pdfplumber** 提取文字内容（中文支持好，表格也能提取）
- 使用 **pdfplumber** 提取图片（如果有）
- 保存文字和图片引用到 .md 文件
- 对于扫描型 PDF（纯图片），pdfplumber 无法提取文字时，提示使用 OCR

**PDF 文字提取命令**（Python）：
```python
from md_to_latex import extract_text_from_pdf, extract_images_from_pdf
# 提取文字
text = extract_text_from_pdf("作业.pdf")
# 提取图片
images = extract_images_from_pdf("作业.pdf", output_dir="sources")
```

**统一接口**（推荐）：
```python
from md_to_latex import extract_content_from_file
result = extract_content_from_file("作业.pdf")
text = result['text']       # 提取的文字
images = result['images']   # 提取的图片列表
```

#### B. 图片文档（PNG/JPG/JPEG）- **新增**
- 使用 **EasyOCR** 进行 OCR 文字识别（兼容 Python 3.14）
- 备选：PaddleOCR（需 Python 3.10-3.12）
- 自动识别中文和英文
- 提取文字内容到 .md 文件

**安装依赖**：
```bash
# 推荐使用虚拟环境
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install easyocr
# 或使用 PaddleOCR（需要兼容的 Python 版本）
pip install paddleocr paddlepaddle
```

**图片 OCR 处理工作流程**：
1. 使用 EasyOCR/PaddleOCR 识别图片中的文字
2. 保持原文排版结构（尽可能）
3. 保存到 .md 文件

**OCR 命令**（Python）：
```python
from md_to_latex import extract_content_from_file
result = extract_content_from_file("作业.png")
text = result['text']  # 识别的文字内容
```

**命令行使用**：
```bash
# 直接提取图片文字
python md_to_latex.py 作业.png --extract
```

#### C. Word 文档（.docx / .doc）- **新增**

**.docx 格式处理**：
- 使用 **python-docx** 提取段落和表格文字
- 使用 **mammoth** 转换为 Markdown（保留格式）
- 保存到 .md 文件

**安装依赖**：
```bash
pip install python-docx mammoth
```

**Word 文档处理工作流程**：
1. 使用 mammoth 将 .docx 转为 Markdown（保留标题、列表、粗体等格式）
2. 如果 mammoth 未安装，降级使用 python-docx 提取纯文字
3. 保存到 .md 文件

**提取命令**（Python）：
```python
from md_to_latex import extract_content_from_file
result = extract_content_from_file("作业.docx")
text = result['text']  # Markdown 格式的文字内容
```

**.doc 旧格式处理**：
- 自动检测文件格式（旧版 .doc 或重命名的 .docx）
- 如果是重命名的 .docx，直接处理
- 如果是真旧版 .doc，提示用户转换：
  - 使用 Microsoft Word / LibreOffice 打开并另存为 .docx
  - 或使用命令行：`soffice --headless --convert-to docx 作业.doc`

**命令行使用**：
```bash
# 直接提取 Word 文档文字
python md_to_latex.py 作业.docx --extract
```

#### D. 已有 MD 文件
- 直接读取并显示内容
- 准备编辑

### Step 5: 生成 Markdown 模板

```markdown
# [课程名称] - [作业序号]

**姓名**: [姓名] \quad **学号**: [学号] \quad **班级**: [班级]

**提交日期**: [YYYY-MM-DD]

---

[从文档提取的内容...]

---
```

### Step 6: 用户编辑内容

用户在 .md 文件中：
- 添加解答内容
- 修改公式（使用 $$公式$$）
- 添加图片引用

**此时不编译 PDF，节省 token**

### Step 7: 完成并编译（用户触发）

用户输入 `/assignment done` 时：
1. 读取当前 .md 文件
2. 转换为 LaTeX 格式
3. 使用 MikTeX/pdflatex 编译 PDF
4. 输出完成报告

## LaTeX 转换规则

| Markdown | LaTeX |
|----------|-------|
| `# 标题` | `\section{标题}` |
| `## 标题` | `\subsection{标题}` |
| `### 标题` | `\subsubsection{标题}` |
| `$$公式$$` | `\[公式\]` |
| `$公式$` | `\(...$$` |
| `**加粗**` | `\textbf{加粗}` |
| `- 列表` | `\item 列表` |

## LaTeX 模板

```latex
\documentclass[12pt,a4paper]{ctexart}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{float}
\usepackage{enumitem}
\geometry{margin=2.5cm}

\title{[课程名称] - [作业序号]}
\author{[姓名] \quad [学号] \quad [班级]}

\date{[提交日期]}

\begin{document}

\maketitle

% 内容从MD转换而来

\end{document}
```

## Usage Examples

```
# 开始新作业
/assignment 材料加工1 作业8

# 系统询问：请提供作业文件夹的路径
# 用户：课程名/作业/
# 或者：D:/Documents/作业/
# 或者：.（当前目录）

# 系统询问：请提供作业文档路径
# 用户：作业/2026年第3章 作业-3.pdf

# 系统读取文档并转换为 MD
# 用户编辑 MD 文件...

# 完成后编译 PDF
/assignment done
```

## /assignment done 触发器

当用户输入 `/assignment done` 时：
1. 检测当前目录的 .md 文件
2. 转换为 .tex
3. 编译 .pdf
4. 清理临时文件（.aux, .log）

---

## /assignment complete 触发器

当用户输入 `/assignment complete` 时：
**自动完成作业内容** - 逐题分析并解答，遇到疑问时询问用户

### 工作流程

#### Step 1: 读取作业题目
- 从 PDF 或 MD 文件中提取所有题目
- 识别题目类型（计算题、简答题、论述题、证明题等）
- 统计题目数量

#### Step 2: 逐题完成
对每道题目：

**A. 计算题**
- 识别已知条件和求解目标
- 应用相关公式和定理
- 分步骤计算
- 使用 `$$公式$$` 格式书写数学表达式

**B. 简答题/论述题**
- 分析题目核心问题
- 组织知识点和要点
- 分层次作答
- 提供实例或公式支持

**C. 遇到疑问时询问**
当题目信息不完整或不确定时：
- 暂停当前题目
- 向用户询问具体问题
- 等待用户回答后继续

**常见的询问场景**：
```
- 题目中的图表/图片内容不清晰
- 参数值缺失或模糊
- 需要特定的解答格式要求
- 需要使用特定的方法或公式
- 需要知道课程的特定要求
```

#### Step 3: 生成解答
- 将所有解答整理为 Markdown 格式
- 保持与题目相同的编号
- 添加"解答"小节标记
- 使用合适的标题层级（### 或 ####）

#### Step 4: 写入文件
- 更新 .md 文件
- 保留原有题目
- 在每道题后添加解答内容

### 解答格式示例

```markdown
## 题目一

[题目内容...]

### 解答

**分析**：[简要分析题目]

**Step 1：[步骤名称]**

[计算过程或分析...]

$$公式 = 结果$$

**Step 2：[步骤名称]**

[继续计算...]

**答案**：

$$\boxed{最终结果}$$
```

### 题目类型识别规则

| 关键词 | 题目类型 | 解答策略 |
|--------|----------|----------|
| 计算、求解、求、估算 | 计算题 | 分步计算，公式推导 |
| 简述、说明、解释 | 简答题 | 要点列举，简洁明了 |
| 分析、讨论、比较 | 论述题 | 层次分明，深入分析 |
| 证明、推导 | 证明题 | 逻辑严密，步骤完整 |
| 画图、示意图 | 作图题 | 描述图形特征 |

### 中途询问示例

```
# 系统处理题目二时发现疑问
"题目二中提到'如图所示'，但我无法看到图片内容。
请问图中显示的是什么工艺/结构？"

# 用户回答
"是正向挤压工艺，挤压筒直径100mm，挤压杆直径30mm"

# 系统继续完成解答
"明白了，我继续完成题目二的解答..."
```

### Usage Examples

```
# 自动完成作业
/assignment complete

# 系统逐题完成
"正在读取题目... 共发现 4 道题"
"开始完成题目一（计算题）..."
"题目一已完成 ✅"
"开始完成题目二（简答题）..."
"遇到疑问：题目中提到的'如图所示'无法识别"
"请问图中显示的是什么？"
[用户回答后继续]
"题目二已完成 ✅"
...
"所有题目已完成，正在写入文件..."
"✅ 作业内容已保存到 .md 文件"
```

## 编译命令

```bash
pdflatex 姓名_学号_班级_课程_作业序号.tex
pdflatex 姓名_学号_班级_课程_作业序号.tex  # 第二次生成目录
```

## Dependencies

- **MikTeX** 或 **TeX Live** - LaTeX发行版
- **pdflatex** - PDF编译器
- **ctex** - 中文支持
- **Python 3.x** - 转换脚本（可选）
- **pdfplumber** - PDF图片提取（可选，安装：`pip install pdfplumber`）
- **EasyOCR** - 图片文字识别（推荐，安装：`pip install easyocr`）
- **PaddleOCR** - 图片文字识别备选（需要 Python 3.10-3.12，安装：`pip install paddleocr paddlepaddle`）
- **python-docx** - Word 文档读取（可选，安装：`pip install python-docx`）
- **mammoth** - Word 转 Markdown（可选，安装：`pip install mammoth`）
- **requests** - HTTP 请求（图片下载，安装：`pip install requests`）
- **beautifulsoup4** - HTML 解析（图片搜索，安装：`pip install beautifulsoup4`）

### 虚拟环境安装（推荐）

```bash
# 在 assignment skill 目录下创建虚拟环境
cd ~/.claude/skills/assignment
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装所有依赖
pip install python-docx mammoth pdfplumber easyocr requests beautifulsoup4
```

## 快速命令

```bash
# 创建作业（会询问文档路径）
/assignment [课程] [作业号]

# 自动完成作业内容（遇到疑问会询问）
/assignment complete

# 完成并编译 PDF
/assignment done
```

---

## 命令对比

| 命令 | 功能 | 是否询问 |
|------|------|----------|
| `/assignment 课程 作业号` | 创建作业文件夹，读取题目 | ✅ 询问文件夹路径和文档路径 |
| `/assignment complete` | 自动完成所有题目解答 | ⚠️ 遇到疑问时询问 |
| `/assignment done` | 编译 MD 为 PDF | ❌ 不询问 |
| `/assignment revise` | 检查并修复 LaTeX 格式问题 | ⚠️ 发现问题时询问是否修复 |

---

## /assignment auto 触发器

当用户输入 `/assignment auto` 时：**一键完成全部流程** — 自动解答所有题目 + 编译 PDF，无需分两步操作。

### 工作流程

1. **读取题目** — 从当前作业目录的 .md 文件中提取所有题目
2. **自动解答** — 逐题完成（同 `/assignment complete` 的逻辑），遇到疑问时询问用户
3. **写入文件** — 将解答写入 .md 文件
4. **编译 PDF** — 自动转为 .tex 并用 xelatex 编译（同 `/assignment done` 的逻辑）
5. **清理临时文件** — 删除 .aux, .log 等

### 执行示例

```
# 用户输入
/assignment auto

# 系统响应
正在读取题目... 共发现 5 道题
开始完成题目一（计算题）...
题目一已完成 ✅
开始完成题目二（计算题）...
题目二已完成 ✅
...
所有题目已完成，正在写入文件...
✅ 作业内容已保存到 .md 文件
正在转换为 LaTeX...
正在编译 PDF...
✅ PDF 编译成功 (3 页)
```

---

## /assignment revise 触发器

当用户输入 `/assignment revise` 时：

### 功能 1：LaTeX 格式检查与修正

**检查内容**：
- ❌ 特殊字符未转义（`%`, `&`, `#`, `_`）
- ❌ 数学公式配对问题（`$...$`, `\[...\]`）
- ❌ LaTeX 环境配对问题（`\begin...\end`）
- ❌ 图片文件路径存在性

**工作流程**：
1. 检测当前目录的 .tex 文件
2. 运行 LaTeX 语法检查
3. 报告发现的问题（按严重程度分类）
4. 提供自动修复选项
5. 重新编译 PDF 验证修复结果

### 功能 2：数学计算辅助

当遇到计算题时，可以使用以下 Python 库进行数学计算：

| 库 | 功能 | 安装命令 |
|------|------|----------|
| `sympy` | 符号计算（解方程、微积分） | `pip install sympy` |
| `numpy` | 数值计算（矩阵、函数） | `pip install numpy` |
| `scipy` | 科学计算（优化、积分） | `pip install scipy` |

**使用示例**：

```python
# 解方程 x^2 - 4 = 0
from sympy import symbols, solve, Eq
x = symbols('x')
result = solve(Eq(x**2 - 4, 0), x)  # x = [2, -2]

# 微积分：求导
from sympy import diff
diff(x**3, x)  # 3*x^2

# 微积分：积分
from sympy import integrate
integrate(x**2, x)  # x^3/3

# 数值计算
import numpy as np
np.sqrt(16)  # 4.0
```

**在作业解答中的应用**：

```markdown
### 解答

**Step 1：建立方程**

根据题意，设未知量为 x，得到方程：

$$x^2 - 4 = 0$$

**Step 2：求解方程**

使用 SymPy 解方程：

```python
from sympy import symbols, solve, Eq
x = symbols('x')
solve(Eq(x**2 - 4, 0), x)
```

解得：

$$x = \pm 2$$

**答案**：

$$\boxed{x = 2 \text{ 或 } x = -2}$$
```

### 命令行用法

```bash
# 检查 LaTeX 语法
python md_to_latex.py file.tex --check

# 自动修复问题
python md_to_latex.py file.tex --fix

# 数学计算
python md_to_latex.py --math "x**2 - 4 = 0"

# 查看数学计算帮助
python md_to_latex.py --math-help
```

### 常见问题与修复

| 问题类型 | 示例 | 修复方法 |
|----------|------|----------|
| 未转义百分号 | `完成度 50%` | `完成度 50\%` |
| 未转义安培符 | `A & B` | `A \& B` |
| 未转义下划线 | `file_name` | `file\_name` |
| 公式不配对 | `$x^2 + y^2` | `$x^2 + y^2$` |
| 环境未关闭 | `\begin{itemize}` | 添加 `\end{itemize}` |

### 执行示例

```
# 用户输入
/assignment revise

# 系统响应
🔍 检查 LaTeX 文件: 姓名_学号_班级_课程_作业序号.tex

⚠️ 发现 3 个问题:
  ❌ 行 15: 未转义的百分号: '%' [escape]
  ⚠️ 行 23: 未转义的安培符: '&' [escape]
  ❌ 行 0: \begin{itemize} 未关闭 [environment]

📦 发现 2 个可自动修复的问题
是否自动修复？(y/n)

# 用户选择 y
🔧 准备修复 2 个问题...
📦 备份已保存: 姓名_学号_班级_课程_作业序号.tex.backup
✅ 已自动修复 2 个问题

⚠️ 仍有 1 个问题需要手动处理:
  ❌ 行 0: \begin{itemize} 未关闭 [environment]

请手动修复后重新编译
```

---

## /assignment image 触发器

当用户输入 `/assignment image <搜索关键词>` 时：

### 功能：联网搜索并下载图片

**工作流程**：
1. 识别当前作业目录（查找 .md 文件）
2. 使用搜索 API 或网页抓取搜索图片
3. 下载图片到 `sources/` 目录
4. 询问用户插入位置或自动添加到文档末尾
5. 更新 .md 和 .tex 文件

### 支持的搜索方式

| 方式 | 优先级 | 说明 | 依赖 |
|------|--------|------|------|
| **Pexels API** | 1️⃣ 最高 | 免费高质量图片，每小时200次 | API Key |
| **Unsplash API** | 2️⃣ 次选 | 免费高质量图片，每小时50次 | API Key |
| **Bing 搜索** | 3️⃣ 备用 | 网页抓取，不稳定（防盗链） | `pip install requests beautifulsoup4` |
| **直接URL下载** | - | 从指定URL下载图片 | 无需额外依赖 |

### API Key 配置

创建配置文件 `~/.claude/assignment_config.json`：

```json
{
  "pexels_api_key": "YOUR_PEXELS_API_KEY",
  "unsplash_access_key": "YOUR_UNSPLASH_ACCESS_KEY"
}
```

**获取免费 API Key**：
- **Pexels**: https://www.pexels.com/api/ （推荐，中文搜索支持好）
- **Unsplash**: https://unsplash.com/developers （英文为主）

### 使用示例

```
# 搜索并下载图片
/assignment image 数控机床

# 搜索多张图片
/assignment image CNC machine tool 3

# 从URL直接下载
/assignment image https://example.com/image.jpg
```

### 图片命名规则

下载的图片按以下规则命名：
- 搜索下载：`image_{N}_{timestamp}.jpg`
- URL下载：保持原文件名
- 自动重命名冲突文件

### Python 实现

```python
from md_to_latex import search_and_download_images

# 方式1：搜索图片
images = search_and_download_images(
    query="数控机床",
    count=3,
    output_dir="sources"
)

# 方式2：直接URL下载
images = search_and_download_images(
    url="https://example.com/image.jpg",
    output_dir="sources"
)
```

### 更新文档流程

1. **更新 .md 文件**：
```markdown
![图片描述](sources/image_1_20240423.jpg)
```

2. **更新 .tex 文件**：
```latex
\begin{center}
\includegraphics[width=0.8\textwidth]{sources/image_1_20240423.jpg}\\
\small{图片描述}
\end{center}
```

### 执行示例

```
# 用户输入
/assignment image 数控机床结构图

# 系统响应
🔍 正在搜索: 数控机床结构图
📦 找到 6 张相关图片
   1. cnc-machine-structure.jpg (1200x800)
   2. lathe-components.png (800x600)
   3. milling-machine.jpg (1024x768)
   ...

选择要下载的图片编号 (用逗号分隔，如 1,3,5):
> 1,3

📥 下载中...
✅ cnc-machine-structure.jpg 已保存到 sources/
✅ milling-machine.jpg 已保存到 sources/

插入位置:
1. 文档末尾
2. 指定章节（输入章节号）
3. 手动指定位置

选择:
> 1

✅ 图片引用已添加到文档
✅ LaTeX 文件已更新
```

### 依赖安装

```bash
# 基础依赖（URL下载）
pip install requests

# 可选：图片搜索API
pip install google-search-results  # SerpAPI
pip install unsplash  # Unsplash API
```

### 配置API密钥（可选）

如需使用高级搜索功能，创建配置文件 `assignment_config.json`：

```json
{
  "image_search": {
    "bing_api_key": "YOUR_BING_API_KEY",
    "unsplash_access_key": "YOUR_UNSPLASH_KEY",
    "serpapi_key": "YOUR_SERPAPI_KEY"
  }
}
```

---

## 命令对比（更新版）

| 命令 | 功能 | 是否询问 |
|------|------|----------|
| `/assignment 课程 作业号` | 创建作业文件夹，读取题目 | ✅ 询问文件夹路径和文档路径 |
| `/assignment complete` | 自动完成所有题目解答 | ⚠️ 遇到疑问时询问 |
| `/assignment done` | 编译 MD 为 PDF | ❌ 不询问 |
| `/assignment auto` | 一键完成：complete + done | ⚠️ 遇到疑问时询问 |
| `/assignment revise` | 检查并修复 LaTeX 格式问题 | ⚠️ 发现问题时询问是否修复 |
| `/assignment image <关键词>` | 联网搜索并下载图片 | ⚠️ 选择图片和插入位置时询问 |
