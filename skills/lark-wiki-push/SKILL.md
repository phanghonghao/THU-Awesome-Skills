---
name: lark-wiki-push
version: 1.0.0
description: "推送本地 Markdown 文档到飞书知识库。类似 git-push 的体验：扫描变更→确认→一键同步。当用户需要推送到飞书知识库、wiki push、上传文档到知识库、同步文档到飞书时使用。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# lark-wiki-push

将本地 Markdown 文档一键同步到飞书知识库。类似 `git push`，但目标换成飞书 Wiki。

**CRITICAL — 开始前 MUST 先用 Read 工具读取 lark-shared SKILL.md（路径：`C:/Users/20174/.agents/skills/lark-shared/SKILL.md`），其中包含认证、权限处理。**

## 工作流

### Step 1 — 读取/创建配置

读取项目根目录下的 `.wiki-sync.json`。

**如果不存在**，引导用户完成初始化：

1. 列出可用的知识空间：
   ```bash
   lark-cli wiki spaces list --jq '.items[] | {id: .space.id, name: .space.name}'
   ```

2. 用 AskUserQuestion 让用户选择目标空间。

3. 询问是否需要指定父节点（可选，不指定则放到空间根目录）：
   ```bash
   # 如需指定父节点，先列出空间根节点的子节点
   lark-cli wiki nodes list --params '{"space_id":"<space_id>"}'
   ```

4. 写入初始 `.wiki-sync.json`：
   ```json
   {
     "space_id": "<选中的space_id>",
     "space_name": "<空间名称>",
     "parent_node_token": "<可选，父节点token>",
     "files": {}
   }
   ```

### Step 2 — 扫描变更

1. 用 Glob 扫描 `**/*.md`（排除 `node_modules/**`、`.git/**`、`.claude/**`、`.wiki-sync.json`）

2. 读取 `.wiki-sync.json` 的 `files` 字段获取已跟踪文件列表

3. 对每个文件分类：
   - **新增**：不在 `files` 中
   - **已修改**：用 `stat` 获取文件 mtime，与 `last_pushed` 比较，mtime 更新则为已修改
     ```bash
     stat -c '%Y' "<file_path>"
     ```
   - **未变化**：mtime 未变化，跳过
   - **已删除**：在 `files` 中但本地文件不存在（标记但不自动删除远端）

### Step 3 — 展示确认

**清晰展示**将要推送的变更：

```
=== 将要推送到飞书知识库 ===

新增文档:
  + docs/guide.md
  + docs/report.md

更新文档:
  ~ README.md

未变化 (跳过):
  - docs/api.md

目标空间: <space_name>
请确认推送？(yes/no)
```

**Wait for user confirmation before proceeding.**

### Step 4 — 执行推送

确认后直接执行，不再询问。

**新增文件**（用 `docs +create` 一步创建文档并挂到 Wiki 空间）：
```bash
lark-cli docs +create \
  --wiki-space <space_id> \
  --title "<文件名去掉.md后缀>" \
  --markdown "@<file_path>"
```

如果配置了 `parent_node_token`，则用 `--wiki-node` 代替 `--wiki-space`：
```bash
lark-cli docs +create \
  --wiki-node <parent_node_token> \
  --title "<文件名去掉.md后缀>" \
  --markdown "@<file_path>"
```

**已修改文件**（用 `docs +update` 覆盖更新）：
```bash
lark-cli docs +update \
  --doc <obj_token> \
  --mode overwrite \
  --markdown "@<file_path>"
```

每完成一个文件，打印进度：
```
  ✓ guide.md → 已创建 (doxcnxxxx)
  ✓ README.md → 已更新
```

如果推送失败，打印错误并继续处理下一个文件。最后汇总失败项。

### Step 5 — 更新跟踪

推送完成后，更新 `.wiki-sync.json`：

- **新增文件**：记录返回的 `doc_id` 作为 `obj_token`，以及当前时间戳作为 `last_pushed`
- **已修改文件**：更新 `last_pushed` 为当前时间
- **已删除文件**：保留记录但标记状态（不自动删除远端文档）

`.wiki-sync.json` 格式：
```json
{
  "space_id": "749xxx",
  "space_name": "项目文档",
  "parent_node_token": "wikcnxxxx（可选）",
  "files": {
    "docs/guide.md": {
      "obj_token": "doxcnxxxx",
      "last_pushed": "2026-05-02T14:30:00"
    },
    "README.md": {
      "obj_token": "doxcnyyyy",
      "last_pushed": "2026-05-02T14:30:00"
    }
  }
}
```

## 注意事项

- **标题策略**：用文件名去掉 `.md` 后缀作为文档标题
- **层级**：平铺，所有文档放在 Wiki 空间根目录或指定父节点下
- **删除安全**：本地删除的文件不会自动从飞书知识库删除，需手动处理
- **确认后不中断**：用户确认后执行所有推送，不再逐个询问
- **错误容忍**：单个文件推送失败不影响其他文件，最后汇总报告
