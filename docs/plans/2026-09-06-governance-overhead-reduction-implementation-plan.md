# Governance Overhead Reduction Implementation Plan

**Goal:** 在 MyCodexEnv 与 ShipQ 的自然交付中消除可证实的重复验证和状态维护，并保留现有安全、业务、审计与验收控制。

**Architecture:** 作为当前任务内的可选执行提示，直接复用权威规则、验证入口及交付报告；只有发现具体重复时才处理。不设跨任务观察、历史配对、持久跟踪或固定表单。

**Tech Stack:** 既有 Git、Python 验证入口和 Markdown 交付报告；无新增依赖。

**Status:** 已按消融实验与对抗审查修订。旧版满分及“无实质缺陷”结论不作为本版批准依据；本版未重新独立评分，实际收益未验证。

## 1. 范围与授权

- 本次授权仅创建、修订和评审本计划；唯一 write set 为 `docs/plans/2026-09-06-governance-overhead-reduction-implementation-plan.md`。
- 不修改 AGENTS、业务代码、测试入口、CI、runtime、ShipQ 文件或外部系统；不 commit、push、创建任务、自动提醒、归档或清理历史。
- 本文不是新的必经流程；已授权任务直接遵守现行规则，需要定位重复工作时可查阅本文。引用或采用本文不授权新增规则删改、runtime promotion 或外部写入。
- 授权、金额、隐私、数据完整性、审计、恢复、并发、持久迁移、兼容性、客户验收和 required CI 不削减。
- 当前任务由当次主代理负责，不承担其他线程的采样、排序、计数或汇总；没有新增多代理或委员会常驻要求。

## 2. 权威入口与文件责任

仓库位置：MyCodexEnv 为 `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`；ShipQ 为相邻目录 `/Users/kezheng/Codes/CursorDeveloper/ShipQ`。执行者先确认实际 checkout，不把这些路径视为任意工作区的写入许可。

| 权威文件 | 本计划如何使用 | 是否修改 |
| --- | --- | --- |
| [MCE 验证与安全](../agents/verification-and-change-safety.md) | 任务类别、证据有效期、最终门禁、promotion 后复验 | 否 |
| [MCE 全局规则源码](../../codex/AGENTS.md) | 消费者追踪、deletion test、独立回读边界 | 否 |
| [ShipQ AGENTS](../../../ShipQ/AGENTS.md) | selector、适用 Harness、S1–S5、交付要求 | 否 |
| [ShipQ State Update Policy 与 Ownership Map](../../../ShipQ/docs/designs/harness-state.md) | 每个事实源的更新触发条件 | 否 |
| [ShipQ 阶段成熟度事实源](../../../ShipQ/docs/plans/deferred-hardening-and-testing-memo.md) | S1–S5 当前判定的只读依据 | 否 |

路径基于相邻仓库布局；其他机器缺少 ShipQ 时，明确该项目证据不可得，不猜测或把缺失算作通过。执行时读取当前规则；与本计划冲突时，暂停受影响步骤并按当前授权和权威规则处理，不自行改规则。

## 3. 完成标准

本次修订交付：移除固定观察与跨线程交接承诺，保留现行控制及当前任务的处理步骤；纠正旧评审结论；引用可定位，最终仅本文件发生变化。不以追加评审轮次作为本次修订的完成条件。

实际任务按其原有完成条件交付。发现明确重复时，可说明省去了哪个动作及依据；没有发现则正常结束，不追加调查、报告字段或历史检索。不能从少跑命令、没有记录问题或未遗漏控制推导总成本下降、零缺陷或控制实际有效。

## 4. 当前任务内的执行提示

**Owner:** 当次主代理。**Files:** 只读本节引用与真实任务文件；无本计划要求的新写入。**Input:** 用户任务及实际 checkout。**Output:** 既有开工说明中的必要范围与验证选择，无固定格式。

- [ ] 复用当前任务已经取得的 checkout 与改动归属证据；确有疑点时再运行 `git status --short --branch` 和 `git rev-parse --show-toplevel`，保护既有用户改动。
- [ ] 读取该任务适用的权威规则，仅在原有开工说明中补充会影响执行选择的信息；不强制三行、空字段或新增表单。
- [ ] 根据实际改动使用目标 repo 的现行验证规则。纯文字例外不能覆盖授权门、可执行指令、配置或行为变更；ShipQ docs lane 不自动免除适用 Harness。
- [ ] 迭代使用适用 focused/domain 验证，最终执行当前规则要求的 gate。ShipQ Harness 已包含该轮 full 时，不另跑同轮全量；MCE promotion 后的仓库 gate、parity/readback 和环境验证仍独立执行。

具体 selector、前置／阶段／宿主检查和命令以§2权威入口为准。当前任务已明确这些选择时，不因为查阅本文再次运行、复述或重新审批。

## 5. 发现具体重复时如何处理

**Owner:** 当次主代理。**Files:** 仅真实任务已授权 write set；不额外要求修改 State Log、memo、README 或本计划。**Input:** 当前任务的 gate 选择与既有证据。**Output:** 原有交付报告，必要时附一句重复或复用的理由。

- [ ] 拟复用结果前，确认其命令、退出码、关键输出、时间，以及相关源码、测试、fixture、manifest、运行目标、环境和时效仍适用。没有足够证据就按现行要求验证，不新建登记系统。
- [ ] 保留所有适用的前置、阶段、失败恢复与 required CI；仅省去同一验证边界中没有理由的重复最终全量。不能为了补写回执字段重复未变的 gate。
- [ ] 按各 repo 当前事实源更新合同判断写入。ShipQ 普通修复本身、无新决定的只读检查、未变状态的重复验证和会话结束不自动触发 State Log；若同时发生里程碑、blocker、handoff、授权生命周期或其他 durable 事件，仍按合同处理。
- [ ] ShipQ 仍先读成熟度事实源，并在每次交付完整给出 S1–S5 业务问题、是／否及依据；“不更新 memo”不等于“省略回执”。MCE 不套用 ShipQ 的特殊状态合同。
- [ ] 若发现疑似重复镜像，先追踪调用方、数据流、持久格式、合同、消费者与信任边界；合法发布同步、审计、恢复证据与独立回读不计为冗余。无法证明的保持原样。
- [ ] 只有需要解释的具体冗余或合理重复才在已有交付中增加一句原因，例如“本轮 Harness 已包含 full，因此未再单跑全量 pytest”；零发现不新增统计字段，不为回执另建文件或单独 commit。

## 6. 异常、停止与条件性后续

- 没有具体重复，或无法证明某动作冗余时，保留现行控制并完成当前任务；不为填结论创建计数器、补样本或安排后续检查。
- 发现漏 gate、审计缺失、证据误用或运行能力缺口时，停止相关省略或完成声明。离线测试、health check 和正确阻断不能替代真实业务验收。
- 受影响结果不宣称可用；原任务授权内补验、修复和复验。若需要额外权限或外部动作，明确待处理的具体事项，不自动 reset、清历史、回滚 runtime 或覆盖用户修改。
- 当前任务发现具体冗余并追踪证实后，才另提单点修改建议：准确 repo-relative write set、保留的权威入口、会消失的重复动作，以及保护真实反例的最小验证。没有已确认候选时，不预先指定要删除的规则、测试或代码。
- 后续新增修改（包括规则源码和 runtime）须明确范围并取得相应授权；不得将委员会评分或本文转换成写入许可。
- 用户另有具体效率评估问题时，再按该请求确定一次只读评估的对象、证据与停止边界；本文不自动启动评估，不承诺跨线程恢复或汇总。
- 已有计划已足够时停止；不新增 skill、schema、hook、dashboard、提醒、统计脚本或常驻委员会。

## 7. 本计划的验证

以下命令仅检查计划及本次 write set，可在 MCE 根目录运行。它不能证明业务行为、runtime 生效或减负收益。

```bash
python3 - <<'PY'
from pathlib import Path
import re, subprocess
from datetime import datetime
p = Path('docs/plans/2026-09-06-governance-overhead-reduction-implementation-plan.md')
text = p.read_text()
links = re.findall(r'\]\(([^)]+)\)', text)
for link in links:
    assert (p.parent / link.split('#')[0]).resolve().is_file(), link
status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], text=True)
unexpected = [line for line in status.splitlines() if line[3:] != str(p)]
assert not unexpected, unexpected
assert all(not line.rstrip('\n').endswith((' ', '\t')) for line in text.splitlines()), 'trailing whitespace'
subprocess.run(['git', 'diff', '--check', '--', str(p)], check=True)
print(f'PASS: {len(links)} references; only planned file changed; whitespace clean')
print('timestamp=' + datetime.now().astimezone().isoformat())
PY
```

以上 write-set 检查用于本次仅有计划文件待提交的工作区；以后有既有用户改动时应与执行起点比较，不把该断言用作清理指令。检查失败只报告，不自动修复范围外文件。语义仍需人工核对权威原文，不能用字符串断言代替；本文不要求为每次使用重复组织委员会。

## 8. 评审历史与本次修订依据

2026-09-06 旧版委员会和独立盲审均曾给出 10/10。后续消融与对抗审查指出，原评审验证了合规性，却未充分验证新增流程的必要性及跨线程交接能力；旧版“无实质缺陷”结论已被修正，不继续背书本版。

消融使用同一组12个规则决策案例：完整执行说明、仅现行规则、移除观察步骤后的说明均为12/12关键边界决定符合预期。前两组使用新上下文独立回放，第三组为非盲配对复核，有记忆效应。移除观察步骤的实验版本将附加执行正文从4,886缩至3,886字符；这是旧版实验裁剪结果，不是本版字数或生产成本测量。该实验未证明真实提速、统计显著性或全面安全等价。

| 发现／旧验收项 | 本次处置 |
| --- | --- |
| F1：固定观察增加工作，尚未证明必要 | 采纳；删除默认观察、历史配对及窗口末汇总，只保留当前任务内可选提示 |
| F2／旧 A2：跨线程交接闭合结论过强 | 撤销旧 closed 结论；通过移除跨线程协议处理，不以新增状态或声称恢复能力已实现来闭合 |
| 旧 A3：固定窗口与基线 | 因相应机制移除而退役，不作为本版验收项 |
| 现行安全、gate 与事实源边界 | 保留在§1、§2、§4–6；不继承旧版评分，按当前原文核对 |

本次修订依据用户“按建议修订完整计划”的指令实施；未重新组织独立委员会或授予新分数。最终引用、write set 与空白检查回执在聊天交付中给出，避免为记录结果反复改写被检查文件。

## 9. 残余风险

现有规则仍可能被执行者忽略，简短提示是否改善真实行为尚未证明；人工判断也可能漏项。没有记录问题不等于零问题，控制未遗漏不等于控制有效。本文不提供跨任务效率统计或观察恢复能力；实际重复规模、总成本变化及长期效果未知。所有步骤以执行时的实际规则、证据、权限和用户指令为准。
