---
name: assignment
description: 大学作业管理系统。读取作业文档转为 Markdown，用 `/assignment complete` 自动完成解答，用 `/assignment done` 编译 PDF，并支持用 `/assignment figure` 插入原题图。
---

# Assignment Skill

自动化大学作业处理：读取作业文档 -> 转换为 Markdown -> 自动完成解答 -> 编译为 PDF。

## Overview

这个 skill 用于：

1. 创建作业目录与 Markdown 源文件
2. 读取 PDF、图片、DOCX、Markdown 题目
3. 整理题目为可编辑 Markdown
4. 用 `/assignment complete` 自动补全解答
5. 用 `/assignment done` 转 LaTeX 并编译 PDF
6. 用 `/assignment figure` 插入原题图到 Markdown/LaTeX

## Commands

```bash
/assignment [课程] [作业名或作业号]
/assignment complete
/assignment done
/assignment auto
/assignment revise
/assignment figure
/assignment image <关键词>
```

## Workflow

### Step 0: 确认作业目录

先确认作业应该放在哪个目录。

示例：

- `课程名/作业/`
- `D:/Documents/作业/`
- `.`

### Step 1: 收集信息

收集以下信息：

- 姓名
- 学号
- 班级
- 课程
- 作业名或作业号

补充规则：

- 如果用户已经明确给出课程，使用用户提供的课程。
- 如果用户没有明确给出课程，优先从当前作业所在文件夹或路径中推断课程名。
  - 例如路径中出现 `材料加工1/作业/`，则课程名默认取 `材料加工1`。
- 提交日期默认取当天日期，格式为 `YYYY-MM-DD`。
- 不要把课程名写死成固定值。

### Step 2: 读取题目文件

支持：

- `.pdf`
- `.png` / `.jpg` / `.jpeg`
- `.docx`
- `.doc`（必要时先转 `.docx`）
- `.md`

### Step 3: 生成目录结构

默认结构：

```text
[作业目录]/
├── [作业文件].md
├── [作业文件].tex
├── [作业文件].pdf
└── sources/
```

### Step 4: 生成 Markdown 初稿

题目整理进 `.md` 后，头部必须使用以下结构。

## 头部模板

必须使用单字段单行，不允许把多个字段写在同一行。

```markdown
# [课程名] - [作业名]

**姓名**: [姓名]
**学号**: [学号]
**班级**: [班级]
**课程**: [课程名]
**提交日期**: [YYYY-MM-DD]

---
```

示例：

```markdown
# 测试与检测基础 - 第5讲作业

**姓名**: 潘洪浩
**学号**: 2023080041
**班级**: 机械34
**课程**: 测试与检测基础
**提交日期**: 2026-06-15

---
```

### Step 5: 题目正文格式

题目与解答保持如下风格：

```markdown
## 5-1

题目内容……

![](sources/example.png)

### 解答

解答内容……
```

## 格式规则

### 1. 头部规则

- `姓名 / 学号 / 班级 / 课程 / 提交日期` 必须各占一行
- 不要写成：

```markdown
**姓名**: 张三  **学号**: 2023000000  **班级**: 机械01
```

### 2. 数学公式规则

- 数学公式不要放在反引号里
- 行内公式用 `$...$`
- 独立公式用 `$$...$$`

正确：

```markdown
$R_x(0) \ge R_x(\tau)$

$$
R_x(\tau)=E[x(t)x(t+\tau)]
$$
```

错误：

```markdown
`R_x(0) >= R_x(\tau)`
`t\frac{df(t)}{dt}`
```

### 3. 反引号规则

反引号只用于：

- 命令
- 路径
- 文件名
- 普通代码标识

例如：

```markdown
运行 `/assignment done`
文件在 `sources/` 目录
```

### 4. 图片规则

Markdown 图片统一写成：

```markdown
![](sources/xxx.png)
```

### 5. 日期规则

- 默认直接使用当天日期
- 如果用户明确指定日期，则使用用户指定日期

### 6. 课程规则

- 默认从用户输入或目录路径中提取课程名
- 例如：
  - `D:/课程/材料加工1/作业/` -> 课程名优先取 `材料加工1`
  - `D:/清华大学2026春/测试与检测基础/作业/` -> 课程名优先取 `测试与检测基础`

## /assignment complete

当用户输入 `/assignment complete` 时：

1. 读取当前作业 `.md`
2. 识别题目编号与题型
3. 逐题补全解答
4. 保留原题目与图片
5. 在每题后添加 `### 解答`

解答格式：

```markdown
## 题目编号

题目内容……

### 解答

**分析**：

……

**答案**：

$$
\boxed{...}
$$
```

## /assignment done

当用户输入 `/assignment done` 时：

1. 读取当前 `.md`
2. 检查头部结构是否合法
3. 检查公式是否错误地写在反引号中
4. 检查图片路径是否存在
5. 转换为 `.tex`
6. 编译 `.pdf`

### done 前的预检查要求

在转换前应优先检查：

- 头部字段是否单独成行
- 是否存在“同一行多个头部字段”
- 是否把数学内容写进反引号
- `$$...$$` 与 `$...$` 是否配对
- 图片文件是否存在

如果发现以下问题，应优先自动修正或提示修正：

1. `姓名 / 学号 / 班级 / 课程 / 提交日期` 写在同一行
2. 公式误写成反引号代码
3. 图片是 Markdown 语法但未转换为 LaTeX 图片环境

## /assignment figure

当用户输入 `/assignment figure` 时：

1. 读取当前作业 `.md`
2. 接收本地题图路径，支持单文件、目录或逗号分隔列表
3. 按章节标记把原题图插入到指定题目下
4. 同步更新 `.tex` 中的图片环境
5. 后续可继续执行 `/assignment done` 重新编译 PDF

推荐触发方式：

```bash
/assignment figure
```

或等价地调用脚本：

```bash
python md_to_latex.py assignment.md --figure sources/pdf_pages --figure-section "## 5-1"
```

默认规则：

- 题图说明默认写为 `原题图`
- 默认插入位置为 `after_section`
- 使用 `after_section` 时必须提供章节标记，例如 `## 5-1`
- `.md` 中插入 Markdown 图片语法，`.tex` 中插入 `\includegraphics`

适用场景：

- 用户要求“把原题目图片插进去”
- 图像题需要保留波形图、坐标图、原扫描题面
- 需要生成“题目 + 原题图 + 解答”的完整版 PDF

## /assignment auto

`/assignment auto` = `/assignment complete` + `/assignment done`

流程：

1. 读取题目
2. 自动补全解答
3. 写回 `.md`
4. 转 `.tex`
5. 编译 `.pdf`

## /assignment revise

用于检查和修复：

- 特殊字符转义
- LaTeX 环境配对
- 数学公式配对
- 图片路径问题
- 由 Markdown 转 LaTeX 时产生的格式问题

## /assignment image

用于联网搜索并下载图片到 `sources/` 目录，并插入当前文档。

## Dependencies

- MikTeX 或 TeX Live
- pdflatex
- ctex
- Python 3.x
- pdfplumber（可选）
- easyocr（可选）
- paddleocr / paddlepaddle（可选）
- python-docx（可选）
- mammoth（可选）
- requests（可选）
- beautifulsoup4（可选）

## Notes

- 优先保证 Markdown 结构稳定，再做自动解答与编译。
- 头部模板是强约束，不是建议。
- 课程名不要写死。
- 提交日期默认取当天。
