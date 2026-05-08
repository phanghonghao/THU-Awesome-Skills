# THU-assignment-reviser

大学作业管理 Claude Code Skill — 自动读取作业文档、完成解答、编译 PDF。

## 功能

| 命令 | 功能 |
|------|------|
| `/assignment 课程 作业号` | 创建作业文件夹，读取题目 |
| `/assignment complete` | 自动逐题完成解答 |
| `/assignment done` | 编译 MD 为 PDF |
| `/assignment auto` | 一键完成：解答 + 编译 |
| `/assignment revise` | 检查并修复 LaTeX 格式 |
| `/assignment image <关键词>` | 联网搜索下载图片 |

支持的输入格式：**PDF、图片 (PNG/JPG)、Word (.docx)、Markdown**

## 安装

### 1. 复制 Skill 文件

将 `skill.md` 和 `md_to_latex.py` 放到 Claude Code 的 skills 目录：

```bash
# 创建目录
mkdir -p ~/.claude/skills/assignment

# 下载文件（二选一）
# 方式A: git clone
git clone https://github.com/phanghonghao/THU-assignment-reviser.git
cp THU-assignment-reviser/skill.md THU-assignment-reviser/md_to_latex.py ~/.claude/skills/assignment/

# 方式B: 直接下载
curl -o ~/.claude/skills/assignment/skill.md https://raw.githubusercontent.com/phanghonghao/THU-assignment-reviser/master/skill.md
curl -o ~/.claude/skills/assignment/md_to_latex.py https://raw.githubusercontent.com/phanghonghao/THU-assignment-reviser/master/md_to_latex.py
```

### 2. 安装 Python 依赖（可选）

OCR 和 Word 文档功能需要 Python 依赖，建议用虚拟环境：

```bash
cd ~/.claude/skills/assignment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install pdfplumber easyocr python-docx mammoth requests beautifulsoup4 sympy numpy
```

### 3. 安装 LaTeX（可选）

编译 PDF 需要 LaTeX 发行版：

- **Windows**: 安装 [MiKTeX](https://miktex.org/)
- **macOS/Linux**: 安装 [TeX Live](https://www.tug.org/texlive/)

确保 `xelatex` 命令可用，且安装了 `ctex` 宏包（中文支持）。

## 使用方法

```
# 1. 创建作业（会询问学生信息和文档路径）
/assignment ODE "C:/Users/xxx/Downloads/作业.pdf"

# 2. 一键完成（解答 + 编译）
/assignment auto

# 或分步操作
/assignment complete    # 自动解答
/assignment done        # 编译 PDF
```

## 目录结构

```
课程名/作业/姓名_学号_班级_课程_作业序号/
├── 姓名_学号_班级_课程_作业序号.md
├── 姓名_学号_班级_课程_作业序号.tex
├── 姓名_学号_班级_课程_作业序号.pdf
└── sources/
```

## 依赖汇总

| 依赖 | 用途 | 必需？ |
|------|------|--------|
| Claude Code CLI | 运行 Skill | 必需 |
| MiKTeX / TeX Live + ctex | 编译 PDF | 推荐 |
| pdfplumber | PDF 文字提取 | 可选 |
| easyocr | 图片 OCR | 可选 |
| python-docx / mammoth | Word 文档 | 可选 |
| sympy / numpy | 数学计算验证 | 可选 |

## License

MIT
