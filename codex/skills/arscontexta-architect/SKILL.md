---
name: arscontexta-architect
description: Use when evolving an existing Ars Contexta workspace architecture, diagnosing structural bottlenecks, and proposing staged changes to MOCs, linking strategy, and maintenance rules.
---

# Ars Contexta Architect

## 概述

用于已存在知识库的结构演进（Evolution），关注长期可维护性而不是单次内容处理。

## 快速流程

1. 读取现状：目录、MOC、链接密度、queue、session。
2. 识别瓶颈：断链、主题孤岛、流程拥塞、维护债务。
3. 给出分阶段演进计划：W1/W2/W3。
4. 每阶段提供可验证验收点。

## 输出契约

- 现状问题清单（按优先级）
- 分阶段改造计划
- 风险与回滚策略

## 常见错误

- 把一次性修补当作架构演进。
- 只提目标，不给阶段验收标准。
