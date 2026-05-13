---
name: skill-evaluator
description: Use when creating, reviewing, or refining an agent skill and you need to decide whether the skill should exist, define routing/load/end-to-end evals, compare with_skill vs without_skill, or diagnose off-target loads, missed loads, and weak skill lift.
---

# Skill Evaluator

## 概述

评估 skill 是否必要、是否能被正确路由、是否按需读取附属文件，以及是否比 baseline 有可测量提升。先写评估，再改 skill；先看失败模式，再扩正文。

## 工作流

1. 先判断这个问题是否真的需要 skill
   - 若一条全局提示、普通文档或模型已有常识足以解决，优先不要建 skill。
   - 若内容变化过快、维护成本高于收益，也不要固化进 skill。
   - 只保留“模型在没有额外上下文时大概率会做错”的内容。
2. 先写评估矩阵，再改 skill
   - 至少覆盖路由、渐进加载、端到端质量三个面向。
   - 优先使用真实用户表达、已知失败案例、邻域混淆案例。
   - 负例与 forbidden load 用例通常比正例更有信息量。
3. 先审 `description`
   - 把它当成路由触发器，不要当成功能说明。
   - 用用户意图和真实说法描述“何时加载”，不要总结工作流。
   - 保持短而密；每个词都要服务路由精度。
4. 再审正文与目录层级
   - 删除显而易见的命令序列、系统提示重复项、通用常识。
   - 保留判断、边界、gotchas、失败处理和非显然约束。
   - 条件性或重内容移到 `references/`、`scripts/`、`assets/`，避免把 `SKILL.md` 写成 README。
5. 运行评估并产出证据
   - 用 `references/eval-matrix.md` 设计完整评估。
   - 用 `references/agent-skills-eval.md` 跑 `with_skill / without_skill` 对比，或在无法跑 CLI 时做手工 paired test。
6. 追加式迭代
   - agent 失败一次，就补一个 gotcha 或一个负例。
   - 若修改 `description`，必须同步补路由评估，避免 action at a distance。

## 输出要求

当用户要求“评估一个 skill”时，默认输出以下四项：

- `Existence verdict`：这个问题是否值得成为 skill，而不是 prompt tweak、普通文档或脚本。
- `Routing review`：`name` / `description` 是否容易误触发、漏触发，是否与邻近 skill 冲突。
- `Eval plan`：给出正例、负例、forbidden load、渐进加载、端到端用例。
- `Evidence summary`：说明当前 skill 预计提升点、baseline 风险、下一轮最小修改。

## 快速检查

- 模型在没有这个 skill 时，真的会稳定做错吗？
- 这个知识足够稳定、值得维护吗？
- 成功标准能被测到，而不是只能靠主观感受吗？
- skill 的提升来自非显然知识、判断或边界，而不是显而易见的命令列表吗？

只要其中一项答案偏弱，就先挑战 skill 的存在性，不要急着扩写正文。

## Review Red Flags

- `description` 在解释流程，而不是描述何时加载。
- 正文在重复系统提示、通用 Git 命令或模型本来就知道的操作。
- 没有邻近 skill 的负例或 forbidden load 测试。
- skill 有 `references/` 或 `assets/`，却没有测试 agent 是否真的会去读。
- 只看 `with_skill` 单边效果，没有和 baseline 比较。
- 合并后还频繁改 `description`，但没有补新的路由评估。

## 参考资料

- 设计评估矩阵、证据格式与回归检查时，读取 `references/eval-matrix.md`。
- 使用 `agent-skills-eval` 或手工 paired test 时，读取 `references/agent-skills-eval.md`。
