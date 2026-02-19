---
name: arscontexta-graph
description: Use when analyzing knowledge-graph structure in Ars Contexta, including hub detection, isolated clusters, weak-link zones, and navigation impact assessment.
---

# Ars Contexta Graph

## 概述

用于图结构分析：识别枢纽节点、孤岛簇、弱连接区域，并评估对导航与检索的影响。

## 快速流程

1. 统计节点与边。
2. 识别高中心性节点与孤立节点。
3. 标注薄弱连接带。
4. 提出修复动作（通常是 reflect/reweave）。

## 输出契约

- 图结构风险清单
- 关键节点列表
- 修复优先级

## 常见错误

- 只做可视化不做行动建议。
- 把高连接误判为高质量。
