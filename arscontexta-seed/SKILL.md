---
name: arscontexta-seed
description: Use when creating or queuing new source-processing seeds, including duplicate checks, metadata capture, and phase assignment for Ars Contexta pipelines.
---

# Ars Contexta Seed

## 概述

用于把新来源（文章、笔记、录音摘要等）登记为可处理任务，并进行去重与优先级标记。

## 快速流程

1. 标准化来源标识（标题、URL、日期、域）。
2. 执行去重检查（标题相似、URL一致、近重复）。
3. 生成 seed 任务并写入 queue。
4. 设定初始 phase 与优先级。

## 输出契约

- 新建任务ID
- 去重结果
- 推荐处理顺序

## 常见错误

- 跳过去重直接入队，造成重复处理。
- 来源字段不完整，后续 reduce 失败。
