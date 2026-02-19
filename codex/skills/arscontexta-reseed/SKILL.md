---
name: arscontexta-reseed
description: Use when an Ars Contexta workspace has accumulated structural drift and requires first-principles re-derivation of vocabulary, architecture, and maintenance rules.
---

# Ars Contexta Reseed

## 概述

用于“从第一性原理重新推导”现有系统。适用于长期漂移、规则冲突、结构失效后的重建策略设计。

## 触发信号

- 目录与词汇约定长期不一致。
- MOC 失去导航作用。
- queue/health 信号持续异常。
- 新需求无法在现结构中低成本演化。

## 快速流程

1. 盘点现状与失败模式。
2. 定义新词汇和结构原则。
3. 设计分阶段迁移路径（非一次性重写）。
4. 每阶段执行 verify/health 回归。

## 常见错误

- 无迁移策略直接重建，导致历史知识丢失。
- 不设回滚点，失败后无法恢复。
