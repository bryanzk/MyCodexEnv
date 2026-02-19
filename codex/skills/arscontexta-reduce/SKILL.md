---
name: arscontexta-reduce
description: Use when turning raw sources from inbox into durable atomic notes with claims, provenance, and wiki links in an Ars Contexta knowledge graph.
---

# Ars Contexta Reduce

## 概述

用于执行 6R 中的 Reduce：把原始材料压缩成可复用笔记。目标是“可链接、可追溯、可检索”。

## 快速流程

1. 读取一个来源（source）并抽取 1-5 个核心 claim。
2. 每个 claim 生成或更新一条笔记，包含：`description`、`source`、正文。
3. 为每条新笔记补至少一个关联链接（若存在相关上下文）。
4. 更新相关 MOC（Map of Content）。

## 最小笔记模板

```markdown
---
title: "..."
type: note
description: "..."
source: "..."
---

## Claim
...

## Evidence
...

## Links
- [[...]]
```

## 常见错误

- 只摘录不归纳：会导致检索命中低。
- 一次塞入太多主题：应拆成原子笔记（Atomic Notes）。
- 缺失来源字段：后续 verify 无法通过。
