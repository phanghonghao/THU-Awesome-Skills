---
name: lab-report
description: 实验报告改写工具（v5.0）。从他人的实验报告生成自己的版本，MD模板→填写→图表→PDF。命令行交互，图片/数据/主观题通过Prompt询问路径。
---

# 实验报告改写 Skill（v5.0）

从他人的实验报告生成自己的版本。保留结构和客观内容，替换个人信息、数据、图表和主观分析。

## 命令

| 命令 | 功能 |
|------|------|
| `/lab-report <课程> <报告路径>` | 读取报告 → 生成 MD 模板 |
| `/lab-report fill` | 填写个人信息、主观题、数据 |
| `/lab-report chart` | 从 Excel 生成 matplotlib 图表 |
| `/lab-report done` | MD → TEX → PDF 编译 |
| `/lab-report auto` | fill + chart + done 一键完成 |

## 工作流

```
/lab-report 材料加工 "C:\...\焊接实验报告马洛.pdf"
    │
    ├─→ 1. 询问个人信息
    │       AskUserQuestion: 姓名、学号、班级、日期
    │
    ├─→ 2. 询问图片路径
    │       AskUserQuestion: "请提供示意图/实验照片的文件路径或文件夹路径"
    │       用户可提供: 单个文件、多个文件、文件夹路径、或 "无"
    │
    ├─→ 3. 询问数据文件路径
    │       AskUserQuestion: "请提供实验数据文件路径（Excel/CSV），用于生成数据图表"
    │       用户可提供: Excel路径、CSV路径、或 "无"
    │
    ├─→ 4. 询问主观题答案
    │       AskUserQuestion: 显示识别到的主观题，用户逐个填写
    │
    ├─→ 5. 运行 report_to_md.py
    │       - 提取报告结构（PDF用pdfplumber，DOCX用python-docx）
    │       - 创建输出文件夹: <课程>/实验报告_改写/
    │       - 生成 MD 模板:
    │         ├── 姓名_学号_班级_实验报告.md
    │         └── sources/        (图片目录)
    │
    └─→ 6. 用户可编辑 MD，或执行后续命令
```

## 触发器定义

### 触发器 1: `/lab-report <课程> <报告路径>`

**匹配**: 用户输入 `/lab-report` 并附带课程名和文件路径

**流程**:

1. 读取文件（PDF/DOCX），运行 `report_to_md.py --json` 提取结构
2. 使用 `AskUserQuestion` **依次询问**:

   **第一步 - 个人信息**:
   ```
   问题: 请提供个人信息
   选项/输入:
   - 姓名: [文本输入]
   - 学号: [文本输入]
   - 班级: [文本输入]
   - 日期: [文本输入，默认今天]
   ```

   **第二步 - 图片**:
   ```
   问题: 请提供实验图片（示意图、装置图、照片等）的路径
   说明: 可以是单个文件路径、多个路径（空格分隔）、文件夹路径、或输入"无"
   示例: C:\Users\photos\  或  C:\img1.png C:\img2.png
   ```

   **第三步 - 数据文件**:
   ```
   问题: 请提供实验数据文件路径（Excel/CSV），用于生成数据图表
   说明: 如果没有单独的数据文件，输入"无"
   示例: C:\Users\data\实验数据.xlsx
   ```

   **第四步 - 主观题**:
   ```
   问题: 请提供主观题答案文件路径，或直接在此输入答案
   说明: 识别到以下主观题章节：
   - [列出识别到的章节]
   可以是文本文件路径，或直接输入内容
   ```

3. 根据用户回答运行脚本:
   ```bash
   python scripts/report_to_md.py "报告路径" \
     -o "课程/实验报告_改写/" \
     --name "姓名" --student-id "学号" --class "班级" --date "日期" \
     --images 图片1 图片2 ... \
     --data 数据文件 ...
   ```

4. 展示生成的 MD 模板给用户确认

### 触发器 2: `/lab-report fill`

**匹配**: 用户输入 `/lab-report fill`

**功能**: 交互式填写 MD 模板中的占位符

1. 读取当前目录的 MD 文件
2. 找到所有 `[待填写]`、`[请填写你的xxx]`、`<!-- [待生成: xxx] -->` 占位符
3. 逐个使用 `AskUserQuestion` 让用户填写
4. 更新 MD 文件

### 触发器 3: `/lab-report chart`

**匹配**: 用户输入 `/lab-report chart`

**功能**: 从 Excel/CSV 数据生成 matplotlib 图表

1. 询问数据文件路径
   ```
   问题: 请提供数据文件路径（Excel 或 CSV）
   ```
2. 读取列名并展示给用户
3. 询问图表配置:
   ```
   问题: 请配置图表
   - X轴列名: [选择]
   - Y轴列名: [选择]
   - 图表标题: [输入]
   - 图表类型: 折线图/散点图/柱状图
   - 是否拟合: 无/线性/多项式/指数
   ```
4. 运行 `chart_generator.py` 生成图表到 `sources/`
5. 在 MD 中替换 `<!-- [待生成: xxx] -->` 为 `![图表](sources/chart.png)`

### 触发器 4: `/lab-report done`

**匹配**: 用户输入 `/lab-report done`

**功能**: MD → TEX → PDF 编译

1. 找到当前目录的 MD 文件
2. 调用 `report_to_md.py` 的 `md_to_tex()` 生成 TEX
   - 优先使用 `assignment/md_to_latex.py` 的转换器
   - 备选使用内建简易转换
3. 调用 `compile_to_pdf()` 编译 PDF
4. 输出: `姓名_学号_班级_实验报告.pdf`

### 触发器 5: `/lab-report auto`

**匹配**: 用户输入 `/lab-report auto`

**功能**: 依次执行 fill → chart → done

## MD 模板示例

```markdown
# 焊接实验报告

**姓名**: <姓名>
**学号**: <学号>
**班级**: 机械34
**日期**: 2026-04-27

---

## 一、实验目的

了解手工电弧焊的基本操作方法...

## 二、实验原理

焊接是通过加热或加压...

## 三、实验步骤

1. 准备焊条和焊件...
2. 调整焊接电流...

## 四、实验数据

| 参数 | 数值 |
|------|------|
| 焊接电流 | [待填写] |
| 焊接电压 | [待填写] |

<!-- [待生成: 电流与电压关系图] -->

## 五、结果分析

[请填写你的结果分析]

## 六、实验感想

[请填写你的实验感想]

![实验装置](sources/装置图.png)
```

## 输出目录结构

```
课程/
└── 实验报告_改写/
    ├── 姓名_学号_班级_实验报告.md    # MD 模板
    ├── 姓名_学号_班级_实验报告.tex   # done 时生成
    ├── 姓名_学号_班级_实验报告.pdf   # done 时编译
    └── sources/                       # 图片目录
        ├── 装置图.png
        ├── chart_1.png
        └── ...
```

## Python 脚本

| 脚本 | 功能 |
|------|------|
| `scripts/report_to_md.py` | 提取报告结构 + 生成 MD + MD→TEX→PDF |
| `scripts/chart_generator.py` | Excel/CSV → matplotlib 图表 |

## 依赖

```bash
pip install pdfplumber python-docx mammoth matplotlib openpyxl numpy scipy
```

## 关键设计

1. **图片**: 不自动提取，通过 Prompt 询问用户提供文件/文件夹路径
2. **数据**: 不自动识别，通过 Prompt 询问用户提供 Excel/CSV 路径
3. **主观题**: 通过 Prompt 询问用户直接输入答案或提供文件路径
4. **MD→TEX→PDF**: 复用 `assignment/md_to_latex.py`
5. **客观内容**: 实验目的、原理、步骤等原文保留
6. **个人信息**: 用户输入替换原报告中的信息
