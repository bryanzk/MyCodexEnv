---
name: arscontexta-tasks
description: Use when managing Ars Contexta queue tasks, including listing, reprioritizing, blocking/unblocking, and phase transitions with explicit state integrity checks.
---

# Ars Contexta Tasks

## 概述

用于管理任务队列（queue）：查看、重排、阻塞处理、状态迁移，确保状态机一致。

## 快速流程

1. 列出待办与阻塞任务。
2. 根据优先级和依赖重排。
3. 更新 phase 状态。
4. 记录操作原因与影响。

## 输出契约

- 变更前后队列摘要
- 被阻塞任务与解除条件
- 下一批推荐执行任务

## 常见错误

- 只改优先级不改依赖关系。
- phase 直接跳转导致状态不一致。
