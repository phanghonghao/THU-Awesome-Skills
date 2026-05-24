---
name: embodied-ai-agent
description: 调研和整理 Bilibili 与 GitHub 上的中文具身智能相关内容，输出按课题路由的中文 Wiki 草稿，并在需要时继续推送到飞书。用户提到 Embodied-Ai-agent、B 站具身智能视频、GitHub 仓库调研、Embodied AI 视频整理、VLA/WM/GR00T/ALOHA 课题归档、视频转 Wiki、仓库转 Wiki、飞书知识库整理时使用。若用户没有提供 VideoUrl 或 RepoUrl，但希望 agent 自己找内容，也使用本 skill：先向用户索取 2-5 个中文关键词，再检索候选内容并继续调研。
---

# Embodied-Ai-agent

始终用中文执行和回复。

当前对外展示名可以使用 `Multi-Source-Research-Agent`，但为了兼容现有调用方式，skill id 暂时仍保持 `embodied-ai-agent`。

## 工作流

### 1. 收集入口信息

- 支持两类来源：`Bilibili` 与 `GitHub`。
- 如果用户提供 `VideoUrl`，按视频链路执行。
- 如果用户提供 `RepoUrl`、`owner/repo` 或明确说要调研 GitHub 仓库，按 GitHub 链路执行。
- 如果用户没有提供具体链接，先问一句：`请直接发 Bilibili 视频链接、GitHub 仓库链接，或者给我 2-5 个中文关键词，我先帮你筛选候选内容。`
- 如果用户只给关键词：
  - 面向视频：运行 `scripts/search_bilibili.py "<关键词>"`
  - 面向仓库：运行 `scripts/search_github.py "<关键词>"`
- 如果用户说“你来选”或没有明确指定候选项，基于标题或仓库名、发布时间/活跃度、技术密度、主题匹配度，选 1 个最适合继续整理的对象，并说明一句理由。

### 2. 运行本地整理流水线

- Bilibili：
  - 先确认当前工作区存在 `scripts/bilibili_embodied_ai_pipeline.py`
  - 运行 `scripts/run_workspace_pipeline.py "<video_url>"`
- GitHub：
  - 先确认当前工作区存在 `scripts/github_repo_research_pipeline.py`
  - 运行 `scripts/run_github_workspace_pipeline.py "<repo_url_or_keyword>"`
- 这两个入口都会默认启用飞书安全模式，避免把本地相对路径图片直接写入飞书正文。

### 3. 读取产物并组织结论

- 优先读取生成目录中的 `manifest.json`、`metadata.json`、`report.md`。
- 如果内容适合进一步沉淀，额外生成 `wiki-draft.md` 作为飞书专题模板版总览页。
- 把一个视频或一个仓库拆成 2-3 个独立课题页，放在产物目录下的 `topics/` 中，而不是只留单篇整理稿。
- 如果内容包含架构、流程、对比或拆分关系，优先补充本地 `SVG` 图，而不是只留纯文字。
- Bilibili 链路结合 `report.md`、章节时间线和截图文件，补全视频的核心判断、内容主线、可拆分 Wiki 主题和延伸研究。
- GitHub 链路结合 `report.md`、README、release 和相关候选仓库，补全仓库的定位、主线、横向对比和延伸研究。
- 维持“按课题路由”的组织方式，不要把所有来源都放在同一个统一板块里。
- 课题至少检查这些常见板块：`VLA`、`WM`、`GR00T`、`ALOHA`、`DiffusionPolicy`、`RL`。
- 需要更多规范时，再读取 `references/workflow.md`。

### 3.5 可视化与生图判断

- 对以下内容，优先用本地 `SVG` 图整理框架：
  - 架构分层
  - 训练流程
  - 课题拆分关系
  - 方法对比
- 对以下场景，不自动生图，而是先提示用户一句：`这部分适合补一张示意图，你要不要我用 $ai-gen 生成一版？`
  - 用户要做飞书专题头图、封面图、海报或对外分享图
  - 截图不足以表达抽象概念，需要补“概念示意图”
  - 用户明确要更强的视觉表达，而不仅是技术整理
- 只有用户明确同意后，才切换到 `$ai-gen` 继续执行。

### 4. 对外展示结果

- 默认先展示本地整理结果，不自动推送飞书。
- 汇报时优先给：
  - 选择了哪个视频或仓库
  - 被路由到哪个主课题/相关课题
  - 生成了哪些本地文件
  - Wiki 草稿的核心判断和可拆分专题
- 如果用户要求继续推送飞书，再进入下一步。

### 5. 飞书推送约束

- 推送前必须再次确认目标空间、父节点 token 或 `.wiki-sync.json` 配置。
- 推送前必须获得用户明确批准。
- 推送图片时，不要依赖 Markdown 相对路径自动导入；需要使用 `lark-cli docs +media-insert` 或等价流程上传真实素材。
- 如果本地产物是 `SVG` 图，不要直接把 `.svg` 路径写进飞书 Markdown。
- 正确流程是：
  1. 本地先产出和保存 `SVG`
  2. 推送前把 `SVG` 渲染成 `PNG`
  3. 用 `lark-cli docs +media-insert` 上传 `PNG`
  4. 再用飞书返回的图片 token 覆盖文档中的 `## 技术地图`
- 如果直接用 `docs +create` 或 `docs +update` 导入本地 `.svg` 路径，飞书通常会产生空图片占位或下载失败警告。

## 命令

### 关键词检索候选视频

```powershell
python "$env:USERPROFILE\\.codex\\skills\\embodied-ai-agent\\scripts\\search_bilibili.py" "具身智能 VLA pi0"
```

### 关键词检索候选仓库

```powershell
python "$env:USERPROFILE\\.codex\\skills\\embodied-ai-agent\\scripts\\search_github.py" "World Model"
```

### 调用当前工作区流水线

```powershell
python "$env:USERPROFILE\\.codex\\skills\\embodied-ai-agent\\scripts\\run_workspace_pipeline.py" "https://www.bilibili.com/video/BV1TP9WBjEvA/"
```

### 调用当前工作区 GitHub 流水线

```powershell
python "$env:USERPROFILE\\.codex\\skills\\embodied-ai-agent\\scripts\\run_github_workspace_pipeline.py" "World Action Model"
```

## 资源

- `scripts/search_bilibili.py`
  用关键词检索 Bilibili 候选视频，返回适合给用户确认的结构化结果。
- `scripts/search_github.py`
  用关键词检索 GitHub 候选仓库，返回适合继续整理的结构化结果。
- `scripts/run_workspace_pipeline.py`
  在当前工作区定位并调用已有的 `Embodied-Ai-agent` 本地流水线。
- `scripts/run_github_workspace_pipeline.py`
  在当前工作区定位并调用 GitHub 仓库研究流水线。
- `references/workflow.md`
  记录课题路由、产物结构和飞书推送边界。
- `references/github-search-queries.md`
  记录 GitHub 侧可复用的查询模板，参考 `github-trending` 的检索方式。
