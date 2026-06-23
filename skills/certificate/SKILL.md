---
name: certificate
description: "从沙龙海报自动生成电子证书 PNG。Use when user mentions: certificate, 证书, 电子证书, 生成证书, generate certificate, 名人堂证书, 沙龙证书."
---

# Certificate Skill — 从沙龙海报自动生成电子证书

从沙龙海报（图片或 HTML）自动提取分享人信息，批量生成 A4 电子证书 PNG。

## 输入

支持两种输入方式（二选一）：

1. **海报图片**（PNG/JPG）— 通过 GLM-4V 视觉模型提取分享人信息
2. **海报 HTML** — 通过 HTML 解析提取分享人卡片

## 使用方式

```
/certificate <海报图片路径或HTML路径>
```

或由 Claude 调用脚本：

```bash
# 方式 1: 从海报图片提取并生成
python "C:/Users/20174/.claude/skills/certificate/certificate_gen.py" --image "<海报图片.png>"

# 方式 2: 从海报 HTML 提取并生成
python "C:/Users/20174/.claude/skills/certificate/certificate_gen.py" --html "<海报.html>"

# 方式 3: 直接传入 JSON 数据（Claude 已提取好数据时）
python "C:/Users/20174/.claude/skills/certificate/certificate_gen.py" --json '{"salon_n":"三","date":"2025.6.15","speakers":[{"name":"张三","topic":"主题"}]}'

# 指定输出目录
python "C:/Users/20174/.claude/skills/certificate/certificate_gen.py" --image "<海报.png>" -o "D:/output/certificates"
```

## 工作流程

### Step 1: 确认输入

询问用户提供海报路径，或直接使用用户给出的路径。判断文件类型：
- `.png` / `.jpg` / `.jpeg` → 图片模式
- `.html` / `.htm` → HTML 模式

### Step 2: 提取数据

**图片模式**：调用 GLM-4V-Flash（通过 img-reader 的 `vision_api.py`），提示模型返回结构化 JSON：
```json
{
  "salon_title": "第X期微沙龙",
  "salon_n": "X",
  "date": "2025.M.DD",
  "speakers": [
    {"name": "分享人姓名", "topic": "分享主题"},
    ...
  ]
}
```

**HTML 模式**：正则解析 HTML 中的 `.name` 和 `.topic` 元素。

### Step 3: 确认数据

将提取结果展示给用户确认。如有误，手动修正后再生成。

### Step 4: 生成证书

执行脚本，自动：
1. 用模板填充每位分享人的姓名、期次、主题、日期
2. Chrome headless 渲染为 A4 PNG（3x 分辨率）
3. 输出到海报同级 `certificates/` 目录（或用户指定目录）
4. 只保留 PNG，自动清理中间 HTML 文件

### Step 5: 告知结果

列出所有生成的 PNG 文件路径。

## 证书设计

- **尺寸**: A4 (210mm × 297mm)
- **配色**: 与海报一致的 teal 系 (#0d7377)
- **签名区**:
  - 左: 刘思彤（隶书）— FuRoC 科技活动中心负责人
  - 右: 潘洪浩（华文行楷）— 开源社区部 负责人
- **装饰**: 双线边框 + 四角电路板纹样（SVG）
- **输出**: 仅 PNG（无印章，无 HTML 残留）

## 输出目录结构

```
certificates/
├── 潘洪浩.png
├── Pratham_Arora.png
├── 肖铭硕.png
└── ...
```

## 文件结构

```
C:/Users/20174/.claude/skills/certificate/
├── SKILL.md                 # 本文件
├── certificate_gen.py       # 主脚本（提取 + 生成 + PNG 渲染）
├── certificate_template.html # HTML/CSS 证书模板（含占位符）
└── Profile_FuRoC.jpg        # FuRoC Logo
```

## 依赖

- Chrome/Edge headless（系统已安装）
- GLM-4V-Flash API（`ZHIPU_API_KEY` 环境变量，图片模式时需要）
- Python 3.10+

## 错误处理

- 图片提取失败：提示用户检查 `ZHIPU_API_KEY` 或改用 HTML 模式
- HTML 解析失败：提示用户检查海报 HTML 结构，或改用图片模式
- Chrome 渲染失败：检查 Chrome 是否已安装
- 如提取数据有误，用户可手动修正后用 `--json` 直接传入

## 与 poster 技能配合

本技能与 `/poster` 配合使用：
1. `/poster` 生成沙龙海报
2. `/certificate` 从海报提取信息生成证书

典型流程：
```
/poster 第三期微沙龙.MD          → 生成海报
/certificate 第三期微沙龙.png     → 从海报生成证书
```
