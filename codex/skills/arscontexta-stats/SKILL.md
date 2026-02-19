---
name: arscontexta-stats
description: Use when generating quantitative summaries for an Ars Contexta workspace, including note volume, link density, queue throughput, and maintenance trend indicators.
---

# Ars Contexta Stats

## 概述

用于输出量化指标（Metrics），帮助判断系统是否健康增长。

## 核心指标

- 笔记总量与增长率
- 链接密度
- queue 吞吐与积压
- verify 通过率

## 输出契约

- 当前快照
- 与上次对比变化
- 异常信号（如增长失衡）

## 常见错误

- 只给绝对值，不给趋势对比。
- 指标很多但没有结论。
