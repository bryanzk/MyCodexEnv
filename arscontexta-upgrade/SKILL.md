---
name: arscontexta-upgrade
description: Use when applying versioned updates to Ars Contexta skills or workspace conventions, with compatibility checks, change summaries, and safe rollout steps.
---

# Ars Contexta Upgrade

## 概述

用于执行升级（Upgrade）：同步新规范、调整 skill 版本、更新流程契约，并确保兼容当前仓库状态。

## 快速流程

1. 比较当前与目标版本差异。
2. 分类变更：破坏性 / 非破坏性。
3. 先应用低风险更新，再处理破坏性变更。
4. 输出升级摘要与未完成项。

## 输出契约

- 变更清单（文件级）
- 兼容性风险说明
- 回滚建议

## 常见错误

- 一次性混入太多破坏性变更。
- 升级后不做 verify/health 回归。
