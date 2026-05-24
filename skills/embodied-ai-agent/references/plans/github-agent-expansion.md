# GitHub 扩展计划

## 目标

把 `Multi-Source-Research-Agent` 从 `Bilibili-only` 扩展成 `Bilibili + GitHub` 的双源研究代理。

当前 GitHub 链路关注两类任务：

- 按关键词搜索相关开源仓库
- 把代表性仓库整理成中文 Wiki 草稿，并路由到对应课题板块

## 计划范围

1. 新增 `scripts/search_github.py`
   - 输入关键词
   - 输出 GitHub 仓库候选列表
   - 参考 `github-trending` 的 GitHub API 检索方式

2. 新增 `scripts/github_repo_research_pipeline.py`
   - 支持 `repo URL / owner/repo / keyword`
   - 自动选择代表性仓库
   - 抓取 metadata / README / releases
   - 生成中文 `report.md`、`wiki-draft.md`、`topics/*.md`
   - 输出本地 `SVG` 技术图

3. 新增 `scripts/run_github_workspace_pipeline.py`
   - 让本机安装的 skill 可以在任意工作区定位 GitHub 流水线

4. 更新 Skill 与参考文档
   - 明确支持 GitHub 入口
   - 保持 skill id 仍为 `embodied-ai-agent`
   - 对外展示名继续使用 `Multi-Source-Research-Agent`

5. 进行 smoke test
   - `World Model`
   - `World Action Model`

## 输出落点

GitHub 调研产物落在：

`outputs/embodied-ai-daily/topics/<topic>/github/<date>_<owner>_<repo>/`

与 Bilibili 链路的 `videos/` 并列，而不是混放。

## 部署方式

1. 修改仓库版本：
   - `D:\Desktop_Files\FuRoC\tmp\Multi-Source-Research-Agent`
2. 同步到本机 skill：
   - `C:\Users\20174\.codex\skills\embodied-ai-agent`
3. 若 smoke test 通过，再按 `git-push` 规范提交并推送到同一 GitHub 仓库
