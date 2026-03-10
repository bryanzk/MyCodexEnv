---
name: importing-codex-home
description: Use when syncing current ~/.codex changes back into a repository that treats codex/AGENTS.md, codex/skills/*, codex/workflow/*, and codex/config.template.toml as source-of-truth files, especially when the user asks to copy or merge their global Codex environment into the project without importing secrets or runtime state.
---

# Importing Codex Home

## Overview

用于把当前运行时 `~/.codex` 的可复现配置回灌到仓库里的 `codex/` 源码目录。

固定原则：
- 只回灌可复现源码：`AGENTS.md`、`skills/`、`workflow/`、`config.template.toml`。
- 不导入运行态、缓存、数据库、认证信息或会话数据。
- 默认做“合并不删除”，避免误删仓库已有内容。

## Output Language

默认使用简体中文输出说明、差异摘要和验证结论。
命令、路径、文件名、环境变量和代码标识符保持英文。

## When To Use

当用户出现以下意图时使用：
- “把我的 Codex 全局环境同步回仓库”
- “复制一份 `~/.codex` 到当前项目并合并”
- “把当前运行时 skills / AGENTS / workflow / config 回灌到 repo”

以下情况不要使用：
- 用户要迁移认证、会话、SQLite、usage-data、automations
- 用户要把 `workflow/memory/*` 这类运行态热数据写进仓库
- 用户只想从仓库同步到 `~/.codex`，那应使用仓库已有同步入口

## Scope

允许导入：
- `~/.codex/AGENTS.md` -> `codex/AGENTS.md`
- `~/.codex/skills/*` -> `codex/skills/*`
- `~/.codex/workflow/*` -> `codex/workflow/*`，但排除 `memory/`
- `~/.codex/config.toml` -> `codex/config.template.toml`

必须排除：
- `~/.codex/auth.json`
- `~/.codex/sessions/`
- `~/.codex/sqlite/`
- `~/.codex/usage-data/`
- `~/.codex/worktrees/`
- `~/.codex/tmp/`
- `~/.codex/automations/`
- `~/.codex/skills/.backup-skills/`
- `__pycache__/`
- `workflow/memory/`

## Quick Start

先做 dry-run：

```bash
codex/skills/importing-codex-home/scripts/import_codex_home.sh \
  --repo-root "$(pwd)" \
  --dry-run
```

确认无误后执行实际导入：

```bash
codex/skills/importing-codex-home/scripts/import_codex_home.sh \
  --repo-root "$(pwd)"
```

如果当前 `~/.codex/config.toml` 里写死了 EigenPhi 后端路径，可显式传入：

```bash
codex/skills/importing-codex-home/scripts/import_codex_home.sh \
  --repo-root "$(pwd)" \
  --eigenphi-backend-root /absolute/path/to/eigenphi-backend-go
```

## Workflow

### 1. 先确认仓库边界

检查仓库是否把 `codex/AGENTS.md`、`codex/skills/*`、`codex/workflow/*`、`codex/config.template.toml` 作为源码。

### 2. 先 dry-run，再实际导入

第一次执行必须先跑 `--dry-run`，确认不会把运行态目录带进仓库。

### 3. 导入后做一致性检查

建议至少验证：

```bash
python3 test_runner.py
diff -rq ~/.codex/skills codex/skills --exclude='.backup-skills' --exclude='__pycache__'
diff -rq ~/.codex/workflow codex/workflow --exclude='memory'
```

### 4. 汇报时说明排除项

交付结论里要明确指出没有导入 `auth.json`、`sessions/`、`sqlite/`、`usage-data/`、`automations/` 和 `workflow/memory/`。

## Script

使用固定脚本入口：

```bash
codex/skills/importing-codex-home/scripts/import_codex_home.sh --help
```

脚本行为：
- 默认合并，不删除仓库已有内容
- `skills/` 自动排除 `.backup-skills`、`__pycache__`、`.DS_Store`
- `workflow/` 自动排除 `memory/`
- `config.toml` 会尽量把 EigenPhi 绝对路径还原成 `${EIGENPHI_BACKEND_ROOT}`

## Common Mistakes

- 直接把整个 `~/.codex` 目录复制进仓库
- 把 `auth.json`、`sessions/`、`sqlite/` 一起提交
- 用 `--delete` 做反向同步，误删仓库已有 skill
- 回灌 `workflow/memory/`，把当天工作热数据污染成模板
- 把本机绝对路径直接写进 `codex/config.template.toml`

## Output Requirements

执行这个 skill 后，回答里至少包含：
- 实际回灌了哪些目录
- 明确排除了哪些运行态/敏感内容
- 使用了哪些验证命令
- 每条验证的 `command`、`exit_code`、`key_output`、`timestamp`
