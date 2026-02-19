---
name: arscontexta-pipeline
description: Use when running end-to-end Ars Contexta processing across phases (seed/reduce/reflect/reweave/verify), with handoff discipline and per-phase completion checks.
---

# Ars Contexta Pipeline

## 概述

用于执行端到端流水线，把来源从 seed 推进到 verify，强调阶段边界与交接一致性。

## 阶段顺序

1. seed
2. reduce
3. reflect
4. reweave
5. verify

## 输出契约

- 每阶段完成状态
- 失败阶段与原因
- 可继续执行的下一步

## 常见错误

- 跳阶段执行，导致质量门缺失。
- 不记录阶段交接信息，难以追踪回归。
