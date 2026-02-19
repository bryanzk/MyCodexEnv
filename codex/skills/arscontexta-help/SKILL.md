---
name: arscontexta-help
description: Use when users need state-aware guidance for Ars Contexta workflows, including command discovery, mode selection, and next-step suggestions based on vault status.
---

# Ars Contexta Help

## 概述

用于提供上下文感知帮助（Contextual Help）：根据当前知识库状态输出“现在该做什么”，而不是静态命令列表。

## 快速流程

1. 读取当前状态：notes/inbox/ops/queue/sessions。
2. 判定模式：新手引导 / 上下文建议 / 紧凑参考。
3. 输出最多 1 个首要建议动作。
4. 附上相关命令入口与简短理由。

## 输出契约

- 当前状态摘要（不超过 3 行）
- 首要建议（只给一个）
- 相关命令（不超过 5 条）

## 常见错误

- 罗列所有命令但不给优先级。
- 忽略当前仓库状态，给固定模板答案。
