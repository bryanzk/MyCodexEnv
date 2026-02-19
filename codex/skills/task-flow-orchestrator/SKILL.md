---
name: task-flow-orchestrator
description: 任务编排/工作流顺序/规划执行指引；适用于复杂功能、重构、Bug 修复与新增逻辑，按 Karpathy→Planner→TDD 组织执行与验证。
---

# Planning and Execution Sequence

此 skill 用于将多个工作流按最合适顺序组合执行，确保“先清晰、再拆解、后实现”。

## 适用场景
- 复杂功能、重构、新增业务逻辑
- 需要明确验收标准与测试策略的任务
- 需要避免过度设计或无关改动的任务

## 标准顺序（默认）
1) Karpathy Guidelines
   - 澄清假设、权衡与不确定点
   - 简洁优先、避免额外功能
   - 外科式改动原则
   - 定义可验证的成功标准

2) Planner
   - 需求分析与验收标准
   - 架构/影响面梳理
   - 任务拆解（含依赖与风险）
   - 测试策略与验证点

3) TDD Guide
   - RED -> GREEN -> REFACTOR
   - 覆盖率与边界条件
   - 验证证据记录

## 变体顺序（按任务规模）
- 中等任务：Karpathy -> TDD（Planner 简化或跳过）
- 小改动/热修：Karpathy -> TDD（最小测试与最小改动）

## 使用规则
- 任一环节发现不清楚或存在多种解释，立即回到 Karpathy 环节并提问。
- Planner 仅在需要拆解与风险识别时启用，避免过度计划。
- TDD 是实现阶段的默认方式；若用户拒绝测试，必须明确风险并记录。
