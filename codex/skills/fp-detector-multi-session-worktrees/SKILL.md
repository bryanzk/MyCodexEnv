---
name: fp-detector-multi-session-worktrees
description: Use when operating fp-detector across multiple Codex sessions or git worktrees and needing to prevent branch conflicts, master checkout contention, detached HEAD confusion, or stale session cleanup. Trigger when opening a new session, switching to master, checking which worktree owns a branch, or standardizing one-session-one-worktree workflow.
---

# FP Detector Multi Session Worktrees

## Overview

为 `fp-detector` 的 Codex 多会话场景提供固定纪律：一个会话一个 worktree，一个 worktree 一个会话分支，主仓库尽量只保留为 `master` 基线。  
优先避免三类常见问题：共享 checkout 互相踩分支、多个 worktree 抢同一个分支名、会话结束后遗留僵尸 worktree。

## Quick Start

遇到下面这些请求时，直接使用本 skill：

- “给这个会话开一个独立工作区”
- “为什么切不到 `master`”
- “哪个 worktree 占用了某个分支”
- “清理不用的 fp-detector 会话 worktree”
- “给我一套 Codex 多会话规范”

默认路径约定：

- 主仓库：`/Users/kezheng/Codes/CursorDeveloper/fp-detector`
- 会话 worktree：`/Users/kezheng/Codes/CursorDeveloper/fp-detector-sessions/<session-id>`
- 会话分支：`session/<session-id>/<task-short>`

## Core Rules

始终遵守下面四条：

1. 不在多个会话里共享主仓库路径。
2. 不让两个 worktree 同时检出同一个分支名，尤其是 `master`。
3. 新会话优先新建 worktree，而不是在已有 checkout 上 `git switch`。
4. 会话结束后回收 worktree，避免长期堆积。

一句话版本：

- 主仓库长期占用 `master`
- 其他会话只用独立分支
- 需要查看主线内容时，用 `git switch --detach master`

## Standard Workflow

### 1. 新会话启动

先检查当前是否已经有对应会话 worktree；没有就新建：

```bash
scripts/create_session_worktree.sh <session-id> [<task-short>] [<base-branch>]
```

进入该 worktree 后，只在这个路径里工作，不再回主仓库路径做该任务。

### 2. 分支命名

优先使用这两种格式：

- `session/<session-id>/<task-short>`
- `codex/<task-short>`

其中第一种更适合长期并行会话，因为能直接从分支名看出归属。

### 3. 查看 master

如果只是想看 `master` 内容，不要强行在第二个 worktree 检出 `master`。  
优先使用：

```bash
git switch --detach master
```

这会让当前 worktree 指向 `master` 的提交内容，但不会占用 `master` 分支名。

### 4. 会话结束回收

优先使用仓库脚本：

```bash
scripts/cleanup_session_worktree.sh <session-id>
```

需要保留分支时加：

```bash
scripts/cleanup_session_worktree.sh <session-id> --keep-branch
```

## Branch Conflict Diagnosis

当用户说“切不到 `master`”或“某个分支被占用”时，按这个顺序排查：

1. 查看所有 worktree

```bash
git worktree list
```

2. 查看分支和绑定关系

```bash
git branch -vv --no-abbrev
```

3. 如果发现目标分支已经显示为：

```text
+ master ... (/path/to/worktree)
```

说明该分支已经被另一个 worktree 检出。根因通常不是 Git 损坏，而是多会话共享同一仓库时，没有做到“一会话一分支一工作树”。

## Recommended Responses

### 用户想切到 master

先判断用户要的是哪一种：

- 要“`master` 的代码内容”：
  - 用 `git switch --detach master`
- 要“当前 worktree 真正挂到 `master` 分支名”：
  - 先找出谁占用了 `master`
  - 再让占用方切走，或改用主仓库直接操作

### 用户想知道谁占用了某个分支

直接给出：

- 占用该分支的 worktree 路径
- 当前提交
- 当前 worktree 是否是 detached HEAD

不要只说“被占用”，要把路径说全。

### 用户只是在 Codex 多开会话

明确解释：

- 问题根因不是 Codex 本身
- 是 Git worktree 的正常限制
- Codex 多会话只是把这个限制暴露得更频繁

## Anti Patterns

不要这样做：

- 在多个 Codex 会话里都打开主仓库路径
- 在不同 worktree 间来回 `git switch master`
- 一个会话做到一半，换另一个 worktree 继续改同一分支
- 让主仓库和会话 worktree 同时承担开发任务

这些做法最容易触发：

- `fatal: '<branch>' is already used by worktree`
- 分支归属混乱
- detached HEAD 误解
- 清理困难

## Cleanup Checklist

会话结束时至少做这几件事：

- 确认该会话 worktree 是否还有未提交改动
- 决定保留还是删除会话分支
- 删除不再需要的 worktree
- 必要时执行 `git worktree prune`

如果用户只是要“安全收尾”，优先用仓库现成脚本，不要手写一串删除命令。

## Output Contract

处理这类请求时，输出顺序固定为：

1. 当前 worktree / 分支占用状态
2. 根因判断
3. 推荐动作
4. 验证证据

如果涉及 `master`，必须明确区分：

- `master` 分支名的占用
- `master` 提交内容的查看

这两个语义不能混着说。
