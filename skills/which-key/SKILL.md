---
name: which-key
description: 识别当前 Claude Code 会话使用的是哪个 API Key。Use when user mentions "which key", "哪个key", "当前key", "what key", "用的哪个key", "key是哪个", "当前密钥", "current key".
---

# Which Key - 当前 Key 识别

快速识别当前 Claude Code 会话正在使用哪个 API Key。

## 触发条件

用户问"用的哪个 key"、"当前是 key 几"、"which key" 等类似问题时触发。

## 执行步骤

### Step 1: 检测当前 profile

运行:

```bash
python "$HOME/.claude/start_claude.py" --check
```

解析 `---JSON---` 之后的 JSON 数组，获取每个 profile 的 `name`、`key`（masked）、`status`。

### Step 2: 匹配当前 token

读取当前配置目录下的 settings.json 获取当前使用的 token:

```bash
# 读取当前 config dir
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

从 JSON 中提取 `env.ANTHROPIC_AUTH_TOKEN`，然后与 `--check` 输出中各 profile 的 key 进行匹配。

### Step 3: 显示结果

用清晰的格式告知用户:

```
🔑 当前使用: key2
   Token:  9b32...kRkKld
   状态:   ok
```

如果匹配不到任何 profile（比如使用了自定义 token），显示:

```
🔑 当前 Key 不在已知 profile 列表中
   Token:  abcd...efgh  (来自 settings.json)
```

### 简化模式（快速）

如果不需要检查 key 状态，可以直接运行:

```bash
python "$HOME/.claude/start_claude.py" --list
```

结合 settings.json 中的 token 进行匹配即可，速度更快。

## Notes

- 遵循 `start_claude` 的 masking 规则: first 8 chars + `...` + last 6 chars
- 如果用户想切换 key，引导使用 `/start_claude`
