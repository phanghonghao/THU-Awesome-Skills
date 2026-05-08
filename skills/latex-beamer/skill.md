---
name: latex-beamer
description: >-
  LaTeX Beamer 幻灯片制作 - 将 Markdown 转换为 Beamer 演示文稿。
  支持 CJKutf8/ctex 中文、数学公式、图片、表格。适用于答辩、汇报、演讲。
---

# LaTeX Beamer 智能同步 Skill

将 Markdown 笔记转换为 LaTeX Beamer 演示文稿，支持增量更新。

## Overview

**核心功能**：
1. **不存在则生成** - 如果 .tex 文件不存在，从 .md 完整生成
2. **存在则同步** - 如果 .tex 已存在，先检测 .md 变化，然后增量更新
3. **双向同步** - 支持 .md 和 .tex 内容的智能对比和同步
4. **双版本支持** - 自动生成 CJKutf8 (pdflatex) 和 ctex (XeLaTeX) 两个版本

## Workflow

### Step 1: 文件状态检测

检查目标 LaTeX 文件是否存在：

```bash
# 检查文件是否存在
ls docs/presentation/templates/latex/xxx/main.tex
ls docs/presentation/templates/latex/xxx/main_ctex.tex
```

**判断逻辑**：
- 如果不存在 → 走 **Step 2: 完整生成流程**
- 如果存在 → 走 **Step 3: 增量同步流程**

---

## Step 2: 完整生成流程（文件不存在时）

### 2.1 分析 Markdown 文件

读取并分析 .md 文件结构：

```python
# 关键信息提取
- 项目名称: 从标题或 # 中提取
- 作者信息: 从 "团队成员" 或类似章节提取
- 章节结构: ## 标记的章节
- 图片引用: ![alt](path) 或 <img> 标签
- 表格数据: Markdown 表格格式
- 数学公式: $...$ 或 $$...$$
```

### 2.2 选择文档类型

根据用户需求选择：
- **Beamer 演示文稿**: `\documentclass{beamer}`
- **Article 文档**: `\documentclass{article}`

### 2.3 生成双版本 .tex 文件

#### 版本 A: CJKutf8 (pdflatex 兼容)

```latex
\documentclass[aspectratio=169, 10pt]{beamer}
\usepackage{CJKutf8}
% ... 其他设置
\begin{document}
\begin{CJK*}{UTF8}{gbsn}
% 内容
\end{CJK*}
\end{document}
```

#### 版本 B: ctex (XeLaTeX，支持生僻字)

```latex
\documentclass[aspectratio=169, 10pt]{beamer}
\usepackage[UTF8]{ctex}
% ... 其他设置
\begin{document}
% 内容（无需 CJK* 环境）
\end{document}
```

### 2.4 处理图片

1. 复制图片到 `sources/` 目录
2. 重命名为英文（中文转拼音）
3. 更新 LaTeX 中的引用路径

### 2.5 生成 README.md

说明两个版本的区别和使用方法。

---

## Step 3: 增量同步流程（文件存在时）

### 3.1 对比 .md 文件变化

读取最新的 .md 文件，对比关键内容：

```python
# 检测变化的内容类型
1. 新增图片: 新的 ![alt](path) 或 <img> 标签
2. 新增章节: 新的 ## 标题
3. 数据更新: 数字、名称等信息变化
4. 结构调整: 章节顺序、层级变化
```

### 3.2 先更新 .md 文件

**如果 .md 文件在 docs/documentation/ 目录中**：

1. **定位对应的 .md 文件**：
   - 例：`main.tex` → `项目分享答辩框架.md`
   - 例：`team.tex` → `团队介绍.md`
   - 例：`presentation.tex` → `项目介绍.md`

2. **对比 .tex 和 .md 的内容差异**

3. **将 .tex 的变化反向同步到 .md**：

   #### A. 新增图片同步到 .md（智能定位）

   **分析图片内容，定位到对应章节**：

   1. **提取图片描述关键词**：
      - `solidworks_structure.png` → 关键词: "SolidWorks"、"硬件"、"结构"
      - `prototype_hardware.png` → 关键词: "原型"、"硬件"
      - `isbn_recognition.jpg` → 关键词: "ISBN"、"识别"
      - `ai_smart_cabinet.png` → 关键词: "智能柜"、"AI"

   2. **匹配章节规则**：

      | 图片关键词 | 匹配章节 | 插入位置 |
      |------------|----------|----------|
      | SolidWorks、硬件结构 | ### 2.2 硬件终端原型 | 该章节内 |
      | 原型、开发 | ### 2.2 硬件终端原型 | 该章节内 |
      | ISBN、识别 | ### 2.3 软件闭环功能 | 该章节内 |
      | 智能柜、AI | ### 2.1 产品定位 | 该章节内 |
      | 小程序、界面 | ### 2.3 软件闭环功能 | 该章节内 |
      | 商业、盈利 | ### 3.1 盈利模型 | 该章节内 |
      | SWOT、优势 | ### 3.2 SWOT分析 | 该章节内 |

   3. **插入到对应章节**：

      ```markdown
      ## 二、项目内容（原型与技术指标）(2.5 min)

      ### 2.2 硬件终端原型

      | 组件 | 规格参数 |
      |------|----------|
      | **机身规格** | 碳钢板结构 + 透明屏蔽玻璃，单柜 40-60 个独立格口（270×200×90mm/格） |
      | **控制核心** | 树莓派（Raspberry Pi）操作系统 |
      ...

      **🆕 新增图片**：
      - SolidWorks 硬件结构设计：
        ![SolidWorks 设计图](b8f5b5fba769e1ae4ddad46b23847fc7.png)
      - 开发原型配套图：
        ![原型硬件](image.png)
      ```

   4. **多张相关图片合并插入**：

      如果图片属于同一主题，使用组合插入：

      ```markdown
      ### 2.3 软件闭环功能

      ... 原有内容 ...

      **🆕 ISBN 识别功能测试**：
      ![识别成功案例](226a10bce9c554ec6ffd5f5b99c44834.jpg)
      ![ISBN 样例](image-1.png)
      ```

   5. **图片插入格式规范**：

      ```markdown
      **[图片类别]**：
      ![图片描述](图片路径)
      ```

   #### B. 添加更新日志

   在 .md 文件末尾添加更新记录：

   ```markdown
   ---
   ## 更新日志

   ### 2025-04-16
   - 新增 SolidWorks 硬件结构设计图
   - 新增开发原型配套图
   - 新增 ISBN 识别功能测试截图
   - 更新团队信息
   ```

   #### C. 同步规则优先级

   | 优先级 | 内容类型 | 同步要求 | 示例 |
   |--------|----------|----------|------|
   | **必须** | 人名信息 | .tex → .md | "<姓名>" |
   | **必须** | 项目名称 | .tex → .md | "<项目名>" |
   | **必须** | 新增图片 | .tex → .md | 新增图片引用 |
   | **应该** | 核心数据 | .tex ↔ .md | "4000万" |
   | **应该** | 章节标题 | .tex ↔ .md | 章节名称 |
   | **可选** | 具体描述 | 不强制同步 | 解释性文字 |

### 3.3 再更新 .tex 文件

**只更新变化的部分**：

#### A. 新增图片（智能定位插入）

1. **检测 .md 中新增的图片**

2. **分析图片归属章节**：

   ```python
   # 章节映射规则
   CHAPTER_MAP = {
       "solidworks|硬件结构|建模": "硬件终端原型",
       "原型|开发|配套": "硬件终端原型",
       "isbn|识别|扫描": "软件闭环功能",
       "智能柜|示意图": "产品定位",
       "小程序|界面|截图": "软件闭环功能",
       "盈利|收入|商业模式": "盈利模型",
       "swot|优势|劣势": "SWOT分析",
   }
   ```

3. **定位插入位置**：

   在 .tex 文件中找到对应章节的 `\section` 或 `\frametitle`，在其后插入：

   ```latex
   % ============================================================
   % 在 "硬件终端原型" 章节中
   % ============================================================

   \begin{frame}{硬件终端原型}
       % 原有内容...
   \end{frame}

   % 🆕 在该章节末尾插入新图片页面
   \begin{frame}{SolidWorks 硬件结构设计}
       \centering
       \includegraphics[width=\imgwidth]{solidworks_structure.png}
       \vspace{0.3cm}
       \small 智能书柜硬件结构建模（SolidWorks 设计）
   \end{frame}

   \begin{frame}{开发原型与硬件集成}
       \centering
       \includegraphics[width=\imgwidth]{prototype_hardware.png}
       \vspace{0.3cm}
       \small 开发原型配套图 - 硬件模块集成示意图
   \end{frame}
   ```

4. **相关图片合并插入**：

   如果多张图片属于同一主题，创建一个对比页面：

   ```latex
   % 🆕 ISBN 识别功能测试（双图对比）
   \begin{frame}{ISBN 识别功能测试}
       \centering
       \begin{columns}[T]
           \begin{column}{0.48\textwidth}
           \centering
           \includegraphics[width=0.95\textwidth]{isbn_recognition.jpg}
           \vspace{0.2cm}
           \small ISBN 识别成功案例
           \end{column}

           \begin{column}{0.48\textwidth}
           \centering
           \includegraphics[width=0.95\textwidth]{isbn_sample.png}
           \vspace{0.2cm}
           \small ISBN 条码样例
           \end{column}
       \end{columns}

       \vspace{0.5cm}

       \begin{block}{}
           \centering
           \small 基于视觉识别的自动 ISBN 扫描功能
       \end{block}
   \end{frame}
   ```

5. **插入位置优先级**：

   | 优先级 | 位置 | 条件 |
   |--------|------|------|
   | 1 | 对应章节内 | 能匹配到章节关键词 |
   | 2 | 章节结束后 | 该章节有明显结束标记 |
   | 3 | 下一章节前 | 无法匹配时，放在相关章节前 |
   | 4 | 文档末尾 | 兜底位置 |

#### B. 智能定位完整示例

**场景**：用户在 .md 文件开头添加了 4 张新图片

**Step 1: 分析图片**

```python
images = [
    "solidworks_structure.png",  # 描述: "solidworks的硬件结构图"
    "prototype_hardware.png",    # 描述: "开发原型配套图"
    "isbn_recognition.jpg",      # 描述: "测试ISBN识别成功案例"
    "isbn_sample.png",           # 描述: "ISBN样例"
]
```

**Step 2: 匹配章节**

```python
# 关键词匹配
solidworks_structure.png → ["solidworks", "硬件", "结构"] → 匹配: "硬件终端原型"
prototype_hardware.png → ["原型", "硬件"] → 匹配: "硬件终端原型"
isbn_recognition.jpg → ["isbn", "识别"] → 匹配: "软件闭环功能"
isbn_sample.png → ["isbn"] → 匹配: "软件闭环功能"
```

**Step 3: 插入位置定位**

在 .tex 文件中搜索：

```latex
% 搜索: \section{产品制作与改进方案}
% 找到该章节后，继续搜索子章节

% 搜索: \frametitle{硬件终端原型}
% 找到该 frame 后，在其后插入新图片页面

\begin{frame}{硬件终端原型}
    % 原有内容...
\end{frame}

% 🆕 在此位置插入 SolidWorks 相关图片
\begin{frame}{SolidWorks 硬件结构设计}
    \centering
    \includegraphics[width=\imgwidth]{solidworks_structure.png}
    \vspace{0.3cm}
    \small 智能书柜硬件结构建模（SolidWorks 设计）
\end{frame}

\begin{frame}{开发原型与硬件集成}
    \centering
    \includegraphics[width=\imgwidth]{prototype_hardware.png}
    \vspace{0.3cm}
    \small 开发原型配套图 - 硬件模块集成示意图
\end{frame}

% 继续搜索: \frametitle{软件闭环功能}
% 在该章节末尾插入 ISBN 相关图片
```

**Step 4: .md 文件同步**

在 .md 文件的对应章节中插入图片引用：

```markdown
## 二、项目内容（原型与技术指标）(2.5 min)

### 2.2 硬件终端原型

| 组件 | 规格参数 |
|------|----------|
| **机身规格** | 碳钢板结构 + 透明屏蔽玻璃，单柜 40-60 个独立格口（270×200×90mm/格） |
...

**🆕 硬件设计图**：
- SolidWorks 硬件结构设计：
  ![SolidWorks 设计图](b8f5b5fba769e1ae4ddad46b23847fc7.png)
- 开发原型配套图：
  ![原型硬件](image.png)

### 2.3 软件闭环功能

... 原有内容 ...

**🆕 ISBN 识别功能测试**：
| 识别成功案例 | ISBN 样例 |
|--------------|----------|
| ![案例](226a10bce9c554ec6ffd5f5b99c44834.jpg) | ![样例](image-1.png) |
```

#### B. 更新数据

对比并更新关键数据：
- 人名: `\author{...}` 中的内容
- 标题: `\title{...}` 中的内容
- 数据: 正文中的数字

#### C. 新增章节

在对应位置插入新的章节内容

#### D. 结构调整

根据 .md 的新结构重新排序

### 3.4 同步双版本

更新 `main.tex` 和 `main_ctex.tex` 两个版本：
- CJKutf8 版本：确保 `\begin{CJK*}...\end{CJK*}` 正确包裹
- ctex 版本：无需 CJK* 环境，直接使用中文

---

## 转换规则

### 标题转换

```markdown
# 一级标题     →  \section{一级标题} + 章节页
## 二级标题    →  \frametitle{二级标题}
### 三级标题   →  \textbf{三级标题}
```

### 图片转换

```markdown
<img src="image.png" style="max-width: 70%;">
↓
\includegraphics[width=\imgwidth]{image.png}
```

### 表格转换

```markdown
| 列1 | 列2 |
|-----|-----|
| A   | B   |
↓
\begin{tabular}{|c|c|}
\hline
列1 & 列2 \\
\hline
A & B \\
\hline
\end{tabular}
```

---

## 文件结构

```
docs/presentation/templates/latex/project_name/
├── main.tex           # CJKutf8版本 (pdflatex)
├── main_ctex.tex      # ctex版本 (XeLaTeX)
├── README.md          # 使用说明
└── sources/           # 图片目录
    ├── image1.png
    ├── image2.jpg
    └── ...

docs/documentation/
└── 项目分享答辩框架.md  # 对应的 Markdown 源文件
```

---

## 同步报告

每次同步后输出报告：

```
## 同步完成

### 检测到的变化:
✅ 新增图片: solidworks_structure.png
✅ 新增图片: prototype_hardware.png
✅ 新增图片: isbn_recognition.jpg
✅ 新增图片: isbn_sample.png

### 更新的文件:
✅ docs/documentation/项目分享答辩框架.md
   - 添加图片引用（4张）
   - 添加更新日志
✅ docs/presentation/.../main.tex
   - 新增 3 个页面
✅ docs/presentation/.../main_ctex.tex
   - 新增 3 个页面

### 新增页面:
- 第 13 页: SolidWorks 硬件结构设计
- 第 14 页: 开发原型与硬件集成
- 第 14.5 页: ISBN 识别功能测试

### .md 文件同步状态:
✅ 图片引用已添加到文件顶部
✅ 更新日志已添加到文件末尾
✅ 人名信息已确认一致
✅ 项目名称已确认一致
```

### .md 文件更新示例

**更新前**：
```markdown
# "<项目名>"项目分享答辩框架

**总时长**: 约 7-8 分钟
...
```

**更新后**：
```markdown
SolidWorks 硬件结构图
![alt text](b8f5b5fba769e1ae4ddad46b23847fc7.png)

开发原型配套图，放入硬件的地方
![alt text](image.png)

测试ISBN识别成功案例
![alt text](226a10bce9c554ec6ffd5f5b99c44834.jpg)

ISBN样例
![alt text](image-1.png)

# "<项目名>"项目分享答辩框架

**总时长**: 约 7-8 分钟
...

---

## 更新日志

### 2025-04-16
- 新增 SolidWorks 硬件结构设计图
- 新增开发原型配套图
- 新增 ISBN 识别功能测试截图
- 同步更新团队信息（<姓名1>、<姓名2>、<姓名3>）
```

---

## Step 4: MiKTeX 编译生成 PDF

**每次生成或更新 .tex 后，必须调用 MiKTeX 编译为 PDF。**

### 4.1 编译命令

```bash
# 进入工作目录
cd <folder_path>

# XeLaTeX 编译 ctex 版本（推荐）
xelatex -interaction=nonstopmode main_ctex.tex
xelatex -interaction=nonstopmode main_ctex.tex  # 第二遍，生成正确目录

# 备选: pdflatex 编译 CJKutf8 版本
# pdflatex -interaction=nonstopmode main.tex
# pdflatex -interaction=nonstopmode main.tex
```

### 4.2 编译后清理辅助文件（可选）

```bash
rm -f *.aux *.log *.out *.toc *.nav *.snm *.vrb *.fls *.fdb_latexmk *.synctex.gz
```

### 4.3 工作区文件结构

同一文件夹管理同名文件：

```
<project_folder>/
├── <name>.md            # Markdown 源文件
├── main_ctex.tex        # ctex 版本 (XeLaTeX)
├── main.tex             # CJKutf8 版本 (pdflatex)
├── main_ctex.pdf        # 编译输出的 PDF
├── README.md            # 使用说明
└── sources/             # 图片目录
    ├── image1.png
    └── ...
```

### 4.4 打开文件夹（/latex-beamer <path>）

当用户提供文件夹路径时：

1. **扫描目录** — 列出 .MD / .tex / .pdf 文件和 sources/ 图片
2. **判断状态**:
   - 有 .MD 但无 .tex → 走 Step 2 完整生成 + 编译
   - 有 .tex 但无 .pdf → 走 Step 4 编译
   - .MD 比 .tex 新 → 走 Step 3 增量同步 + 编译
   - 三者都有且 .tex 最新 → 提示"已是最新"
3. **执行对应步骤** → 生成/同步 + 编译

---

## Usage Examples

- "/latex-beamer" — 打开当前目录，扫描并处理
- "/latex-beamer docs/presentation/templates/latex/智绘晚晴AR眼镜" — 打开指定文件夹
- "同步 LaTeX" — 检测并同步变化
- "更新幻灯片" — 根据 .md 更新 .tex
- "生成 LaTeX" — 完整生成新文件
- "/latex" — 执行智能同步

---

## Dependencies

- **MiKTeX** — `C:\MiKTeX\miktex\bin\x64\` (xelatex + pdflatex)
- **xelatex** — 用于 ctex 版本（推荐，支持生僻字）
- **pdflatex** — 用于 CJKutf8 版本
- **在线编译**: Overleaf（需将 Compiler 改为 XeLaTeX 使用 ctex 版本）
