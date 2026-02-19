---
name: arscontexta-next
description: Use when selecting the single highest-value next action in an Ars Contexta workflow based on inbox load, graph quality, queue state, and verification gaps.
---

# Ars Contexta Next

## 概述

用于在多个候选动作中选择“现在最该做的一件事”，降低上下文切换成本（Context Switching Cost）。

## 决策顺序

1. 若 verify 存在失败项：先修失败项。
2. 否则若 inbox 积压超阈值：先 reduce 最旧条目。
3. 否则若图谱稀疏：先 reflect。
4. 否则若历史漂移明显：先 reweave。
5. 否则执行 rethink 或小步采集。

## 输出契约

- 推荐动作（只给一个）
- 选择理由（最多三条）
- 完成该动作后的下一跳

## 常见错误

- 同时给出多个“第一优先级”。
- 忽略 verify 失败直接推进新处理。
