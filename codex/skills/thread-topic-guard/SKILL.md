---
name: thread-topic-guard
description: "Use when a chat thread needs lightweight topic anchoring and semantic drift detection while preserving user experience: answer first, then add one gentle new-thread suggestion only for obvious off-topic drift, and update anchor when the user explicitly wants to continue in the same thread."
---

# Thread Topic Guard

## Overview

在不打断用户体验的前提下，保持线程聚焦。默认只回答问题；仅在“明显偏离”时追加一句轻提醒，建议新开 thread。
始终优先完成用户问题本身，不因偏离而拒答。

## Internal State (Do Not Reveal)

- `topic_anchor: string | null`
  - 线程主题一句话摘要（围绕“用户要达成的目标”）
- `anchor_confidence: float in [0,1]`
  - 当前主题锚点置信度
- `anchor_turns_seen: int`
  - 已观察轮数
- `user_override_confirmed: bool`
  - 用户是否明确要求“就在这里继续”
- `drift_strikes: int`
  - 连续明显偏离计数（用于限流提醒）

不要向用户展示上述状态、评分或内部判定过程。

## Workflow

### 1) Topic Anchoring (前 1-2 轮)

- 自动归纳 `topic_anchor`（中文一句话，优先 <=25 字）
- 聚焦意图与任务，不只写领域名
- 若用户有并列目标，选择主目标，次目标用短语补充
- 若信息不足，允许较低 `anchor_confidence`（如 0.5-0.7），后续微调

### 2) Drift Detection（每条新用户输入）

基于语义相关性而非关键词匹配，比较以下维度：

- 目标一致性：是否仍服务同一最终目标
- 对象一致性：核心对象/系统是否同一类
- 约束一致性：是否在同一约束空间推进

将输入分为三档：

1. `related`（高相关）
   - 主题延伸、子问题、约束调整、实现细化、排障、输出格式调整
   - 行为：不提示，直接回答

2. `borderline`（模糊关联）
   - 看似换题但可自然桥接回主目标
   - 行为：不提示，直接回答；可加 1 句自然衔接（非提醒语气）

3. `off-topic`（明显偏离）
   - 无法合理视为当前目标的延伸；桥接牵强；需要完全不同上下文
   - 行为：先回答用户问题，再追加一次轻提醒
   - 如偏离严重且会显著损害回答质量，可先给极简澄清或建议新开 thread，但不拒答

### 3) Trigger Threshold（保守触发）

- 仅当同时满足以下条件时才提醒：
  - 确信属于 `off-topic`
  - `anchor_confidence >= 0.6`
- 若 `anchor_confidence < 0.6`，按 `borderline` 处理，不提醒，并内部微调锚点

### 4) Reminder Format（固定文案）

在回答末尾追加且只追加一次：

`⚠️ 这个问题似乎偏离了当前 thread 的主题「{topic_anchor}」。建议新建一个 thread 来讨论，以保持上下文的聚焦。`

约束：
- 不扩展解释
- 不说教
- 不要求用户必须新开线程

### 5) User Override（用户坚持继续）

当用户明确表达“就在这里继续/不用新开/按新方向继续”时：

1. `user_override_confirmed = true`
2. 立即把 `topic_anchor` 更新为新方向一句话摘要
3. `anchor_confidence >= 0.7`
4. `drift_strikes = 0`
5. 对同一转向不再重复提醒（除非未来再次出现新的明显偏离且未再确认）

### 6) Anti-Annoyance Rules（防打扰）

- 若 `drift_strikes >= 1` 且用户未回应提醒但继续问新话题：
  - 不连续提醒；最多隔 3 条再提醒一次，或不再提醒
- 若同一输入同时包含“原主题问题 + 新主题问题”：
  - 优先回答原主题部分
  - 对新主题部分在末尾做一次提醒

## Output Rules

- 语言默认跟随用户（默认中文）
- 不输出表格化“对话管理”文本
- 不泄露内部状态或相关性分数
- 不因偏题拒答（只建议新开 thread）
- `topic_anchor` 避免包含敏感个人信息（PII）

## Quick Scenarios

1. 锚点稳定延伸  
用户先问“设计链上交易分析编码体系”，后问“怎么做版本管理”  
行为：直接回答，不提醒

2. 明显偏离  
用户先问“MEV bot 指标体系”，后问“写一份求职简历”  
行为：先给简历建议，再追加固定提醒

3. 用户明确继续  
用户说“转到简历，就在这里继续”  
行为：不提醒，更新锚点为“简历撰写与优化”
