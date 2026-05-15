---
name: git-push
description: Push git changes to GitHub. Use whenever user wants to upload/commit/push code changes to GitHub repository.
---

# Git Push Skill

Quickly commit and push git changes to GitHub.

## Workflow

### Step 1: Ask User for Description

**FIRST**: Ask the user to provide their own description for this commit:

```
请输入本次提交的描述（简短说明你做了什么改动）：
```

### Step 2: Ask about README.md update

Ask the user:

```
是否需要更新 GitHub 首页 README.md？
如果需要，请提供素材目录路径（包含 gif、reward 趋势图等）：
（留空跳过，默认路径示例：RTX6000\Magicbot_Z1\docs\github_readme）
```

If the user provides a path:
1. Read the current `README.md` at the repo root
2. List all files in the provided素材目录 (gifs, pngs, etc.)
3. Compare with what's already referenced in README.md
4. Propose updates to README.md (new images, updated sections, etc.)
5. Apply the changes after user confirms

This step runs **in parallel** with Step 3 (git status check).

### Step 3: Check git status

Run `git status` and `git diff --stat` to see what files have changed.

### Step 4: List Changes for Confirmation

**Clearly display** what will be uploaded:

```
=== 将要上传的更改 ===

新增文件:
- file1.ext
- file2.ext

修改文件:
- file3.ext
- file4.ext

删除文件:
- file5.ext

=== AI 生成的总结 ===
[AI's summary of changes]

请确认是否上传？(yes/no)
```

**Wait for user confirmation before proceeding.**

### Step 5: Add and Commit

After user confirms:

1. Add relevant files:
   - DO add: source code (.py, .js, .md, etc.), data files (.csv), images/docs
   - DON'T add: __pycache__, venv, node_modules, .claude, .git, etc.

2. Create commit with **combined message format**:

```
(User's description), (AI's summary)

- [key change 1]
- [key change 2]

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

Example:
```
修复笔记图片显示问题, 更新材料加工笔记结构和图片路径

- 图片重命名为 English_Pinyin 格式
- 更新 MD 和 HTML 中的图片引用路径
- 修复 3_17.html 图片不显示问题

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

### Step 6: Push to GitHub

Run `git push origin main` (or `origin master` if that's the branch).

## Important Notes

- **Always ask user for their description first**
- **Always list changes and wait for confirmation**
- **After confirmation, execute without further prompts**: add → commit → push
- Commit message format: `(User's description), (AI's summary)`
