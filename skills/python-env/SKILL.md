---
name: venv
description: "Python 版本切换 + 虚拟环境管理。快速创建/激活指定 Python 版本的 .venv。Use when user mentions: /venv, venv, virtualenv, python env, python version, switch python, 切换python, python版本."
---

# /venv — Python 版本切换 + 虚拟环境 Skill

管理项目级 Python 虚拟环境，支持多版本切换。

## 可用 Python 版本

| 版本 | 路径 |
|------|------|
| 3.12 | `C:\Users\20174\AppData\Local\Programs\Python\Python312\python.exe` |
| 3.14 | `C:\Users\20174\AppData\Local\Programs\Python\Python314\python.exe` |

## 用法

- `/venv` — 激活项目 `.venv`（已存在时）
- `/venv 3.12` — 用 Python 3.12 创建/激活 `.venv`
- `/venv 3.14` — 用 Python 3.14 创建/激活 `.venv`
- `/venv status` — 显示当前环境信息

## 完整工作流程

### Step 1: 解析参数

从用户输入中提取参数：
- 无参数 → 激活模式
- `3.12` 或 `3.14` → 创建/激活模式
- `status` → 状态查询模式

### Step 2: 定位项目根目录

从当前工作目录向上查找，找到包含 `.git` 目录或 `pyproject.toml` 的目录作为项目根目录。

```bash
# 向上查找项目根
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
```

如果未找到 git 仓库，使用当前工作目录。

### Step 3: 根据模式执行

#### 模式 A: `status`

显示当前环境信息，执行以下命令并展示结果：

```bash
echo "=== Python 环境 ==="
echo "当前 Python: $(python --version 2>&1)"
echo "Python 路径: $(which python 2>/dev/null || where python 2>/dev/null)"
echo ""
echo "=== 虚拟环境 ==="
VENV_PATH="<PROJECT_ROOT>/.venv"
if [ -d "$VENV_PATH" ]; then
    echo ".venv 状态: 存在"
    if [ -f "$VENV_PATH/pyvenv.cfg" ]; then
        echo ".venv Python 版本:"
        grep -E "version|home" "$VENV_PATH/pyvenv.cfg" | head -2
    fi
else
    echo ".venv 状态: 不存在"
fi
echo ""
echo "=== VIRTUAL_ENV ==="
echo "VIRTUAL_ENV = ${VIRTUAL_ENV:-未设置}"
```

#### 模式 B: 无参数（激活模式）

1. 检查 `<PROJECT_ROOT>/.venv/` 是否存在
2. 如果存在 → 激活
3. 如果不存在 → 提示用户指定版本：

```
项目中没有 .venv。请使用 `/venv 3.12` 或 `/venv 3.14` 指定版本创建。
```

#### 模式 C: 指定版本（创建/激活模式）

1. 确定目标 Python 路径：
   - `3.12` → `C:\Users\20174\AppData\Local\Programs\Python\Python312\python.exe`
   - `3.14` → `C:\Users\20174\AppData\Local\Programs\Python\Python314\python.exe`

2. 验证目标 Python 存在：
```bash
"C:/Users/20174/AppData/Local/Programs/Python/Python3XX/python.exe" --version
```

3. 检查 `.venv` 是否已存在：
   - **不存在** → 直接创建
   - **已存在** → 检查当前 `.venv` 的 Python 版本：
     ```bash
     grep "version" "<PROJECT_ROOT>/.venv/pyvenv.cfg"
     ```
     - 版本匹配 → 直接激活
     - 版本不匹配 → 用 AskUserQuestion 询问用户是否重建：
       ```
       问题: ".venv 已存在（Python X.X），但请求的是 Python Y.Y。是否删除并重建？"
       选项:
         a. 是，删除并重建
         b. 否，保持现有 .venv 并激活
       ```

4. 创建 .venv（如需要）：
```bash
"C:/Users/20174/AppData/Local/Programs/Python/Python3XX/python.exe" -m venv "<PROJECT_ROOT>/.venv"
```

5. 激活：
```bash
source "<PROJECT_ROOT>/.venv/Scripts/activate"
```

6. 验证：
```bash
python --version && which python
```

7. 输出结果：
```
✓ .venv 已激活 (Python 3.12.x)
  路径: <PROJECT_ROOT>/.venv
  Python: <which python 输出>
```

## 注意事项

- Windows Git Bash 使用 `.venv/Scripts/activate`（不是 `bin/activate`）
- `source activate` 会修改当前 shell 的 PATH，使 `python` 指向 venv 内的版本
- `.venv/pyvenv.cfg` 包含 venv 的 Python 版本和 home 路径信息
- 不要在 venv 外全局安装 pip 包
