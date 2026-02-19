---
name: arscontexta-refactor
description: Use when restructuring Ars Contexta vault artifacts (notes, MOCs, queue conventions) to reduce complexity while preserving semantics and link integrity.
---

# Ars Contexta Refactor

## 概述

用于结构重构：减少冗余、统一约定、提升可维护性，同时保持语义不丢失。

## 快速流程

1. 识别重复结构与命名漂移。
2. 制定最小变更重构方案。
3. 执行迁移并修复链接。
4. 运行 verify/health 回归。

## 输出契约

- 重构前后结构对比
- 链接修复结果
- 潜在回归点

## 常见错误

- 大范围重写而非最小变更。
- 重构后不做链接完整性检查。
