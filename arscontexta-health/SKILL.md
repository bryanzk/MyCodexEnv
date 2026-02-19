---
name: arscontexta-health
description: Use when auditing current vault health, including inbox pressure, sparse-link notes, queue backlog, and stale maintenance signals in Ars Contexta workspaces.
---

# Ars Contexta Health

## 概述

用于巡检知识系统健康度（Health）：发现积压、断链、老化结构和流程阻塞。

## 巡检项

1. Inbox 积压量与最旧条目年龄。
2. 稀疏连接笔记数量。
3. Queue 待处理任务与阻塞阶段。
4. 最近 session 是否持续记录。
5. tensions/observations 是否堆积。

## 输出模板

- 当前状态摘要（3 行以内）
- Top 3 风险
- 建议的下一步动作（单一最高价值动作）

## 常见错误

- 输出统计但不给行动建议。
- 忽略“最旧未处理项”导致拖延雪球。
