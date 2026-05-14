---
name: cheatsheat
description: Convert Markdown notes to compact A4 CHEATSHEET format with 3-column layout, 小六 font size (10.5px), and narrow margins (10mm). Images occupy 95% of column width. Use this skill when user mentions cheatsheet, 小抄, 速查表, compact print, or 复习资料.
---

# CHEATSHEET 技能

将 Markdown 笔记文件转换为紧凑的 A4 CHEATSHEET 格式（速查表/小抄），方便打印和复习。

## 使用方法

指定要转换的 Markdown 文件路径，技能将：
1. 读取目标 Markdown 文件
2. 添加 CHEATSHEET CSS 样式
3. 处理图片样式（移动到 sources/ 目录，添加样式）
4. 保存为新的 `_CHEATSHEET.MD` 文件

## CHEATSHEET 样式规范

- **纸张**: A4 (210mm × 297mm)
- **页边距**: 10mm
- **布局**: 三栏 (`column-count: 3`)
- **字号**: 小六 (10.5px, 约 8pt)
- **行距**: 1.3
- **栏间距**: 12px
- **图片**: 根据文件名和位置判断宽度
  - **包含"（大）"**：单独占位，`max-width: 95%`
  - **不包含"（大）"且不在表格中**：可左右并排，`max-width: 45%`
  - **在表格中**：将图片作为表格的单独一行（第一列留空，第二列放图片），使用 `max-width: 95%`
    - 正确格式：`| | <img src="..." style="max-width: 95%;"> |`
    - 不要将图片和文字放在同一表格单元中
- **表格**:
  - **最多2列**：禁止超过2列的表格，若原始表格超过2列，需拆分或改为单行公式列表
  - **公式单行显示**：表格中的数学公式应在同一行内完整显示
  - **避免跨栏截断**：使用 `break-inside: avoid` 防止表格被分到两栏

---

用户请求生成 CHEATSHEET，请执行以下操作：

1. **确定输入文件** - 如果用户未指定文件路径，请询问文件路径
2. **确定输出文件名** - 在原文件名后添加 `_CHEATSHEET` 后缀，如 `前8周CHEATSHEAT_机械制图.MD`
3. **读取原始内容**
4. **创建 sources 目录**（如不存在）
5. **处理图片**：
   - 原始笔记文件中的图片在同一文件夹下（如 `image.png`, `图1.png`）
   - 查找所有图片引用（包括 `![](image.png)` 等格式）
   - 对于本地图片（非 `sources/` 目录）：
     - **根据图片所在位置的上下文重命名**：
       - 优先使用最近的章节标题（如 `## 三、弯曲正应力` → `弯曲正应力.png`）
       - 或使用图片前后的描述性文字（如 `剪断示意图` → `剪断示意图.png`）
       - 或使用 alt 文本中的描述
       - 如有冲突，添加序号（如 `弯曲正应力_1.png`, `弯曲正应力_2.png`）
     - **重命名并移动图片到 `sources/` 目录**
     - **更新 Markdown 中的引用为 `sources/新文件名.png`**
   - 根据新文件名添加样式：有"（大）"用 95%，无"（大）"用 45%
6. **处理表格**：
   - 检查所有表格列数
   - **超过2列的表格需要重新设计**：拆分为多个2列表格，或改为单行公式列表
   - 表格添加 `class="cheat-table"` 确保不跨栏截断
7. **生成 CHEATSHEET 内容**：
   - 在文件开头添加 CSS 样式块
   - 用 `<div class="cheatsheet-container">` 包裹全部内容
   - 在文件末尾添加 `</div>`
7. **保存输出文件**

---

## CSS 模板（在转换时添加到文件开头）

```html
<!-- CHEATSHEET: A4三栏紧凑布局，小六字体 -->
<style>
@page {
  margin: 10mm;
  size: A4;
}
@media print {
  body {
    margin: 0;
    padding: 0;
  }
}
.cheatsheet-container {
  column-count: 3;
  column-gap: 12px;
  column-rule: 1px solid #ccc;
  font-size: 10.5px;
  line-height: 1.3;
}
.cheatsheet-container img {
  max-width: 95%;
  break-inside: avoid;
  page-break-inside: avoid;
  display: block;
  margin: 6px auto;
}
.cheatsheet-container h1,
.cheatsheet-container h2,
.cheatsheet-container h3,
.cheatsheet-container h4,
.cheatsheet-container h5,
.cheatsheet-container h6 {
  font-size: 10.5px;
  break-after: avoid;
  page-break-after: avoid;
  margin-top: 8px;
  margin-bottom: 4px;
}
.cheatsheet-container h1 { font-weight: 900; }
.cheatsheet-container h2 { font-weight: 800; }
.cheatsheet-container h3 { font-weight: 700; }
.cheatsheet-container h4 { font-weight: 600; }
.cheatsheet-container h5 { font-weight: 600; }
.cheatsheet-container h6 { font-weight: 600; }
.cheatsheet-container p {
  margin: 3px 0;
  text-align: justify;
}
.cheatsheet-container ul,
.cheatsheet-container ol {
  margin: 3px 0;
  padding-left: 18px;
}
.cheatsheet-container li {
  margin: 2px 0;
}
.cheatsheet-container code {
  font-size: 9px;
  background: #f5f5f5;
  padding: 1px 3px;
}
.cheatsheet-container pre {
  font-size: 9px;
  background: #f5f5f5;
  padding: 6px;
  border-radius: 3px;
  break-inside: avoid;
  page-break-inside: avoid;
}
.cheatsheet-container table {
  font-size: 9.5px;
  border-collapse: collapse;
  width: 100%;
  break-inside: avoid;
  page-break-inside: avoid;
}
.cheatsheet-container th,
.cheatsheet-container td {
  border: 1px solid #ddd;
  padding: 2px 4px;
  white-space: nowrap;
}
/* 禁止超过3列的表格，需手动拆分 */
.cheatsheet-container table td {
  max-width: 60mm;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
<div class="cheatsheet-container">
```

## 图片样式处理

根据图片文件名和位置判断：
- **包含"（大）"**：单独占位，`max-width: 95%`
- **不包含"（大）"且不在表格中**：可左右并排，`max-width: 45%`
- **在表格中**：作为表格的单独一行，`max-width: 95%`

```html
<!-- 大图 -->
<img src="sources/xxx（大）.png" alt="xxx" style="max-width: 95%; break-inside: avoid; page-break-inside: avoid;">

<!-- 普通图（可并排） -->
<img src="sources/xxx.png" alt="xxx" style="max-width: 45%; break-inside: avoid; page-break-inside: avoid;">

<!-- 表格中的图（单独占一行） -->
| 文字列 | |
| | <img src="sources/xxx.png" alt="xxx" style="max-width: 95%; break-inside: avoid; page-break-inside: avoid;"> |
```

## 预览与导出 PDF

生成完成后，告知用户：
1. 在 Typora、VS Code 或浏览器中打开输出的 `*_CHEATSHEET.MD` 文件
2. 使用"打印"功能导出为 PDF，确保选择：
   - 纸张大小: A4
   - 边距: 无（由 CSS 控制）
   - 背景图形: 勾选（保留样式）
