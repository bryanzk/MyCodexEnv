---
name: arscontexta-recommend
description: Use when users ask for architecture recommendations before building an Ars Contexta workspace, including dimension tradeoffs, folder vocabulary choices, and operation model decisions.
---

# Ars Contexta Recommend

## 概述

用于“先建议、后落地”。在未初始化或准备重构前，给出知识系统架构建议，不直接执行大规模文件改动。

## 输入

- 域类型（research/personal/mixed）
- 规模预期（low/medium/high）
- 主要操作者（human/agent/hybrid）
- 主要痛点（检索难、维护重、结构乱）

## 输出格式

1. 推荐配置（8 维）
2. 关键权衡（2-4 条）
3. 风险点（1-3 条）
4. 下一步命令（通常是 setup 或 add-domain）

## 常见错误

- 直接给“唯一正确答案”，不说明权衡。
- 未区分“建议阶段”和“执行阶段”。
