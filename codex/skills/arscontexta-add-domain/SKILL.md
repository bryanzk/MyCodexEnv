---
name: arscontexta-add-domain
description: Use when extending an existing Ars Contexta workspace with a new domain while preserving current self/notes/ops invariants, navigation coherence, and queue operations.
---

# Ars Contexta Add Domain

## 概述

用于在现有系统中新增一个领域（Domain），同时保持旧领域可用且不破坏三空间边界。

## 快速流程

1. 定义新领域词汇：notes/inbox 命名、核心主题。
2. 创建新领域入口 MOC 与最小模板。
3. 在 `ops/derivation-manifest.md` 补充域映射。
4. 调整 queue 路由规则，避免跨域任务混乱。

## 验收标准

- 新领域有可用入口（MOC）
- 新旧领域都可被 next/health 识别
- 不影响既有链接导航

## 常见错误

- 只建目录不建导航入口。
- 覆盖旧域约定导致回归。
