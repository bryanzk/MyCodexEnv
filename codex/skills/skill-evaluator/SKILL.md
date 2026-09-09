---
name: skill-evaluator
description: Use when deciding whether an agent skill should exist, formally evaluating routing/load/end-to-end behavior, measuring skill lift, or diagnosing an observed off-target or missed load.
---

# Skill Evaluator

## 概述

按改动风险评估 skill 是否必要、是否能被正确路由、是否按需读取附属文件，以及是否比 baseline 有可测量提升。小改动做一次针对性检查；正式评估才使用完整矩阵和 baseline。

## 工作流

1. 先判断这个问题是否真的需要 skill
   - 若一条全局提示、普通文档或模型已有常识足以解决，优先不要建 skill。
   - 若内容变化过快、维护成本高于收益，也不要固化进 skill。
   - 只保留“模型在没有额外上下文时大概率会做错”的内容。
2. 按风险选择检查深度
   - 普通的小型 `description`、routing 或正文修改只做一个直接覆盖改动的 targeted check；没有实质缺陷就停止。
   - 用户要求正式评估、需要测量 skill lift，或改动触及真实授权、隐私、数据完整性、恢复/回滚边界时，才读取 `references/eval-matrix.md` 并覆盖路由、渐进加载和端到端质量。
   - 优先使用真实用户表达、已知失败案例和邻域混淆案例。
3. 先审 `description`
   - 把它当成路由触发器，不要当成功能说明。
   - 用用户意图和真实说法描述“何时加载”，不要总结工作流。
   - 保持短而密；每个词都要服务路由精度。
4. 再审正文与目录层级
   - 删除显而易见的命令序列、系统提示重复项、通用常识。
   - 保留判断、边界、gotchas、失败处理和非显然约束。
   - 条件性或重内容移到 `references/`、`scripts/`、`assets/`，避免把 `SKILL.md` 写成 README。
5. 运行所选检查并产出证据
   - targeted check 只验证本次改动对应的 agent workflow choice，不匹配固定措辞。
   - 正式测量 lift 时，用 `references/agent-skills-eval.md` 跑 `with_skill / without_skill` 对比，或在无法跑 CLI 时做手工 paired test。
   - 若目标 skill 应该触发 `committee-review-loop`，把 committee 触发、非触发和 forbidden load 都纳入 routing / progressive-loading eval。
6. 追加式迭代
   - 单次失败先确认可复现且可泛化；两项都满足才固化为 gotcha 或回归用例。
   - 修改 `description` 后运行直接覆盖受影响意图和邻近意图的 routing check。

## Committee Review Gate

评估或修订 skill 时，只有用户明确要求 committee、迭代评分、目标分数或 `10/10`，才加载并执行 `committee-review-loop`。仅要求 subagent 表示委派，不表示要求迭代委员会。真实授权、隐私、数据完整性或恢复/回滚边界需要与风险相称的独立 review；除非用户明确要求，不自动升级为 committee。

调用前先定义：

- `output`：待审的 `SKILL.md`、eval matrix、paired-test 结果、或当前 diff。
- `scope`：只允许修改目标 skill 目录及其直接相关 eval/reference/script 文件。
- `target`：用户指定的目标；未指定时使用当前任务的完成标准。
- `domains`：至少覆盖 routing precision、progressive-loading/eval design、end-to-end task lift；第三个领域可替换为目标 skill 的专业域。
- `verification`：`quick_validate.py`、相关 eval 或手工 paired test，以及仓库要求的 gate。

把 committee 输出的 `revision_brief` 作为下一轮最小修改输入；修改后重新跑验证，再把新输出交回同一个 committee 评分。不要把普通单次 review、QA 或文案润色路由到 `committee-review-loop`。

## 输出要求

当用户要求正式评估一个 skill 时，输出以下四项：

- `Existence verdict`：这个问题是否值得成为 skill，而不是 prompt tweak、普通文档或脚本。
- `Routing review`：`name` / `description` 是否容易误触发、漏触发，是否与邻近 skill 冲突。
- `Eval plan`：给出正例、负例、forbidden load、渐进加载、端到端用例。
- `Evidence summary`：说明当前 skill 预计提升点、baseline 风险、下一轮最小修改。

若本轮使用了 `committee-review-loop`，在输出中追加最终 `committee.rating`、三个专家领域、主要修订点、changed files 与 fresh verification evidence。

普通小改动只返回 targeted check 的范围、结果和证据。

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
- 正式测量 skill lift 时只看 `with_skill` 单边效果，没有和 baseline 比较。
- 修改 `description`，但没有检查受影响意图和邻近意图。

## 参考资料

- 设计评估矩阵、证据格式与回归检查时，读取 `references/eval-matrix.md`。
- 使用 `agent-skills-eval` 或手工 paired test 时，读取 `references/agent-skills-eval.md`。
