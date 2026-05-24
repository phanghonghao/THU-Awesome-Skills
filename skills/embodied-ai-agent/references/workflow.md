# Embodied-Ai-agent Workflow Reference

## 目标

- 从中文 Bilibili 内容和 GitHub 仓库里筛选和整理具身智能相关材料。
- 输出按课题路由的中文 Wiki 草稿，而不是把所有讨论塞进单一文件夹。
- 在用户明确批准前，不执行飞书推送。

## 输入优先级

1. `VideoUrl`
2. `RepoUrl` 或 `owner/repo`
3. 2-5 个中文关键词
4. 如果都没有，先向用户索取其中一种

## 候选内容筛选标准

- 标题或仓库描述是否明显命中 `具身智能`、`VLA`、`pi0`、`世界模型`、`ALOHA`、`GR00T` 等主题
- 发布时间、最近更新时间或 release 活跃度是否足够新
- 是否足以承载技术梳理，而不是只有营销描述
- 来源作者是否偏研究、工程、开源实现或论文梳理

## 标准产物

- `manifest.json`
- `metadata.json`
- `report.md`
- `wiki-draft.md`
- `topics/*.md`
- `assets/diagrams/*.svg`
- `assets/frames/*.jpg`（仅 Bilibili）

## 课题路由

- `VLA`
- `WM`
- `GR00T`
- `ALOHA`
- `DiffusionPolicy`
- `RL`

主课题用于决定主要落点；相关课题用于交叉引用，不应替代主课题。

## 源别组织

- Bilibili：`outputs/embodied-ai-daily/topics/<topic>/videos/<date>_<id>_<slug>/`
- GitHub：`outputs/embodied-ai-daily/topics/<topic>/github/<date>_<owner>_<repo>/`

两者并列存在，不应混放。

## 资源布局

- 模板：`assets/templates/feishu-topic-template.md`
- 并行流程图：`assets/graphs/parallel-multi-source-workflow.html`
- 示例案例：`examples/pi0/`
- 运行产物：`outputs/`

## 可视化规则

- 如果内容包含架构、流程、主题拆分或方法对比，优先补本地 `SVG` 图。
- `SVG` 图默认作为本地知识资产保存，不自动推送到飞书，后续推送时再转为飞书素材。
- 推送到飞书的正确方式：
  1. 保留本地 `SVG` 作为源文件
  2. 将 `SVG` 渲染成 `PNG`
  3. 用 `lark-cli docs +media-insert` 上传 `PNG`
  4. 用返回的飞书图片 token 回写文档中的 `技术地图` 段落
- 不要把本地 `.svg` 相对路径直接交给 `docs +create` 或 `docs +update`，否则会出现空图片 token 或 `IMAGE_DOWNLOAD_FAILED`。
- 如果需要封面图、概念示意图或对外传播图，先提示用户是否需要通过 `$ai-gen` 生图。
- 没有用户确认，不进入 `$ai-gen` 生成步骤。

## 飞书约束

- 需要用户批准后再推送。
- 需要用户确认目标知识库节点。
- 需要真实上传图片，不要依赖本地相对路径图片自动导入。
