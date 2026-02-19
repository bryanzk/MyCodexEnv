---
name: arscontexta-setup
description: Use when creating a new Ars Contexta-style Markdown knowledge workspace, deriving domain vocabulary, and scaffolding self/notes/ops structure with manifest, queue, and session files.
---

# Ars Contexta Setup

## 概述

用于把空目录初始化为 Ars Contexta 知识系统（Knowledge System）工作区，并固定三空间结构（Three-Space Architecture）。不用于通用软件项目初始化。

## 快速流程

1. 收集输入：`domain`、`notes_dir`、`inbox_dir`。
2. 执行脚本：
```bash
~/.codex/skills/arscontexta-setup/scripts/bootstrap_arscontexta_vault.sh <root_dir> [notes_dir] [inbox_dir]
```
3. 验证关键文件：
- `self/identity.md`
- `<notes_dir>/moc-index.md`
- `ops/derivation-manifest.md`
- `ops/queue/queue.yaml`
- `ops/sessions/session-template.md`

## 输出契约

完成初始化后，必须返回：
- 目录结构摘要
- 词汇映射（notes/inbox 实际目录名）
- 下一步建议（通常是 reduce 或 ingest）

## 常见错误

- 把它用于通用代码仓库脚手架：应改用通用工程初始化技能。
- 跳过 `ops/derivation-manifest.md`：后续 health/next 会失去上下文。
