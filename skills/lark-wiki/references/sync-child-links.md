# wiki +sync-child-links

自动同步父页面的子节点链接导航。

## 功能说明

- 自动扫描指定父节点的所有子节点
- 生成/更新父页面的 `## 📑 子页面导航` 章节
- 支持批量更新整个空间的所有父节点

## 使用场景

1. 添加新子页面后，需要更新父页面导航
2. 批量整理 Wiki 结构，确保所有父页面都有子页面链接
3. 维护 Wiki 导航的一致性

## 命令格式

```bash
# 更新单个父节点
lark-cli wiki +sync-child-links --node "Ie11wO6PDiVgcOklR6ncaIpNnsf"

# 更新整个空间的所有父节点
lark-cli wiki +sync-child-links --space "7627374063735851969" --all

# 预览模式（不实际更新）
lark-cli wiki +sync-child-links --node "Ie11wO6PDiVgcOklR6ncaIpNnsf" --dry-run
```

## 实现逻辑

1. 获取父节点的所有子节点（`wiki.nodes.list`）
2. 获取父节点文档的当前内容（`docs +fetch`）
3. 检查是否存在 `## 📑 子页面导航` 章节
4. 如果存在，更新链接列表；如果不存在，在文档开头添加
5. 保留文档的其他内容
6. 更新父节点文档（`docs +update`）

## 页面格式规范

```markdown
## 📑 子页面导航

- [子页面标题](https://lcnxgbkker34.feishu.cn/wiki/{node_token})
- [子页面标题](https://lcnxgbkker34.feishu.cn/wiki/{node_token})

---
```

## 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `--node` | 父节点 token | 是（与 --space 二选一）|
| `--space` | 空间 ID | 是（与 --node 二选一）|
| `--all` | 更新空间中所有父节点 | 否 |
| `--dry-run` | 预览模式，不实际更新 | 否 |

## 示例

```bash
# 更新首页的子页面导航
lark-cli wiki +sync-child-links --node "Ie11wO6PDiVgcOklR6ncaIpNnsf"

# 更新 Awesome_Repo_WAM 的子页面导航
lark-cli wiki +sync-child-links --node "Md5IwfRSMiDSQuk21V4cXYwNnOc"

# 批量更新整个空间
lark-cli wiki +sync-child-links --space "7627374063735851969" --all
```

## 注意事项

- 父节点文档必须已存在
- 子页面链接格式：`https://lcnxgbkker34.feishu.cn/wiki/{node_token}`
- 不会删除文档中的其他内容
- 使用 `--dry-run` 可以预览将要做的更改
