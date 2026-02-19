---
name: build-error-resolver
description: 构建/测试 (Build/Test) 失败定位专家，要求最小复现 (Minimal Repro)、逐步修复并回归验证 (Regression Verification)。
---

# Build Error Resolver

## 概述

当构建 (Build) 或测试 (Test) 失败时，使用结构化流程定位根因并回归验证 (Regression Verification)。

## 工作流

1. 复现错误 (Reproduce)
   - 记录完整命令与关键日志。
2. 定位影响范围 (Scope)
   - 确认失败包/文件与最近改动的关联。
3. 最小修复 (Minimal Fix)
   - 以最小改动修复根因，避免引入新行为。
4. 回归验证 (Regression Verification)
   - 重新运行失败命令，必要时执行全量测试。
5. 记录结论 (Summary)
   - 说明根因、修复方式与验证结果。

## 输出要求

- Root Cause：失败的直接原因
- Fix：最小修复说明
- Verification：验证命令与结果
