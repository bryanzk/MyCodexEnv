---
name: arscontexta-router
description: Use when users describe Ars Contexta tasks in natural language and Codex must select the best matching sub-skill, return one primary route, and provide optional next-hop sequence.
---

# Ars Contexta Router

## 概述

这是 Ars Contexta 的统一路由入口。职责是把用户意图映射到单一主技能（primary skill），并给出最多一个下一跳技能。

## 路由规则

1. 先识别阶段：初始化 / 处理 / 运维 / 演进 / 诊断。
2. 为每个请求只选一个 primary skill。
3. 仅在必要时给一个 next-hop skill。
4. 若信息不足，先给最小澄清问题，再路由。

## 意图到技能映射

- 初始化与规划
  - 新建工作区: `arscontexta-setup`
  - 架构建议: `arscontexta-recommend`
  - 架构演进: `arscontexta-architect`
  - 新增领域: `arscontexta-add-domain`
  - 升级流程/规范: `arscontexta-upgrade`
  - 全局重推导: `arscontexta-reseed`

- 日常处理流水线
  - 入队来源: `arscontexta-seed`
  - 端到端执行: `arscontexta-pipeline`
  - 单步提炼: `arscontexta-reduce`
  - 连接增强: `arscontexta-reflect`
  - 历史回织: `arscontexta-reweave`
  - 质量校验: `arscontexta-verify`

- 运维与执行控制
  - 任务队列: `arscontexta-tasks`
  - 健康巡检: `arscontexta-health`
  - 下一动作: `arscontexta-next`
  - 指标统计: `arscontexta-stats`
  - 图谱分析: `arscontexta-graph`

- 学习与认知演化
  - 引入外部知识: `arscontexta-learn`
  - 沉淀经验教训: `arscontexta-remember`
  - 挑战假设: `arscontexta-rethink`
  - 结构重构: `arscontexta-refactor`

- 交互辅助
  - 状态化帮助: `arscontexta-help`
  - 证据化问答: `arscontexta-ask`
  - 分步教学: `arscontexta-tutorial`

## 输出格式

- `primary_skill`: 唯一主技能名
- `why`: 1-2 句理由
- `next_hop`: 可选，最多一个

## 常见错误

- 同时返回多个“主技能”。
- 把路由器当执行器，直接跑完整流程。
- 未区分“建议类”与“执行类”请求。
