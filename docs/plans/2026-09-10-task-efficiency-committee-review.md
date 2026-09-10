# 任务效率改进计划：委员会评审记录

> 历史快照：下文“当前”“尚未实施”“实施未开始”等表述指 2026-09-10 计划评审收口时点；后续实施与调查的交付回执见 [SHI-240](https://linear.app/shipaica/issue/SHI-240) 及其子票。原评分仅针对计划，不证明首次自然调度行为或实际效率收益。

## 范围与评审合同

- 产物：[任务效率改进落地计划](2026-09-10-task-efficiency-improvement-plan.md)。当前只编写与评审计划，不实施规则、runtime 或 automation 变更。
- 当前 write set：本文件与计划文件；初始工作区 clean，MCE `main`，HEAD `ba3bc7c6912e4b1e31a2edc6df3ba70affead401`。
- 目标：迭代委员会与独立盲审均达到 10/10；最多 5 轮，盲审占一轮；分数不平均。不满足则如实交付 incomplete。
- 评分锚：open blocker ≤5；major ≤7；未核实重要断言 ≤8；minor ≤9。10 表示明确范围内无已知实质缺陷、必需证据完整且残余风险明确。
- 三个视角：运营效率与人机协作；工程验证与工具执行；安全与运行治理。由 AI 子代理模拟专家视角，不是真实外部专家背书。
- 评分者只读计划和相关证据，不接收期望分数。独立盲审不接收本文件、历史评分、结论或修订指令。
- 首轮冻结 rubric 与 required evidence；发现逐项 admission 后才修订，不因追分强制新增架构、状态或流程。
- 同类未解决问题连续两轮出现，先做简化复核再决定继续；新增实质 rubric challenge 必须版本化记录并重开相关项。

## 初始依据

2026-09-10 已只读核对 MCE 验证规则、ShipQ AGENTS、现有活动发布 skill、定向 promotion skill 和相关 automation 配置。现行活动发布 skill 已含分离调用、期限、恢复和重试预算，故计划默认 NO-OP。既有 2026-09-06 减负计划禁止新增常驻观察或跨任务追踪，新计划复用这一边界。

## Round 1：rubric bootstrap

评审计划 SHA-256：`f8e6b91435ca5e6b12bb21de2dc95ec97c567286f11230dfb51cfed8fd626c68`。

| 专家视角 | 分数 | 独立判断与覆盖 |
| --- | ---: | --- |
| 运营效率与人机协作 | 6.5/10 | 人工接手与 NO-OP 合理；B4 可能漏原始目标。覆盖 R1、R2、R7、R8 |
| 工程验证与工具执行 | 6.5/10 | 批次与 gate 清楚；四项证据锚点及闭环输入合同不足。覆盖 R3、R4、R6、R8 |
| 安全与运行治理 | 7/10 | 授权、未知写入、并发与恢复边界保留；仍受 open major 上限约束。覆盖 R3、R5、R6、R7 |

共识：`committee.rating=6.5/10`，`threshold_status=fail`，两个 open major；未平均专家分数。所有专家明确：实际效率、工具硬取消和未来配置回读不属于本轮已验证实施。

### Frozen rubric v1

| ID | 标准 | 必须防止的反例 | 证据期待 |
| --- | --- | --- | --- |
| R1 | 必要性与复用；已覆盖则 NO-OP | 为历史卡顿新增常驻状态、监控或并行流程 | 当前规则、skill、automation 与删除该机制的后果 |
| R2 | 运营连续性 | 工具稍慢即停工；无回复视为批准；人工完成报成自动化成功 | 直接入口、人工接手、必要长任务、无回复场景 |
| R3 | 准确 repo、write set、owner、顺序与停止条件 | 模糊更新范围；评分变成写入许可 | 每批准确目标、前置核对和未授权动作 |
| R4 | 验证与证据匹配 | 文案逐次全量；API 200 代替按钮；链接不支持断言 | 行级依据、focused/final gate、真实入口反例 |
| R5 | 授权与未知写入 | 重发可能成功的发布；改写命令绕过同一拒绝 | 授权变化、readback、partial/unknown 分支 |
| R6 | 并发、dirty 与恢复 | 旧快照覆盖新状态；移动有 owner 的锁 | 前后配置、drift、逐目标恢复边界 |
| R7 | 隐私与跨任务复用 | 假设 cron 共享状态；cutoff 丢失扫描范围 | 访问权、扫描边界、通知内容与 freshness |
| R8 | 计划与实施分离 | 生产发布才算计划通过；parity 证明 activity | source/parity/activity/acceptance 分开和已知未知 |

冻结后不得默改标准或删除未闭合发现；盲审可提出 rubric_challenges，并通过版本化 amendment 处理。

### Required evidence v1

| ID | 必需证据 | Round 1 状态 |
| --- | --- | --- |
| RE1 | E1–E6 精确直接的可定位证据 | incomplete，F1 |
| RE2 | A1/A2/A3 与 promotion 的当前权威入口 | met |
| RE3 | B1–B5 六个 automation ID 与配置存在性 | met |
| RE4 | 四个正向场景和四个反例 | met at plan level |
| RE5 | write set、focused/final gate、回执字段 | met at plan level |
| RE6 | 并发 drift、dirty、unknown 与恢复 | met at plan level |
| RE7 | B4 每条候选链的最小闭环证据 | incomplete，F2 |
| RE8 | B5 跨任务访问权、cutoff、freshness | deferred safely；能力不明即不改，未来实施证据不纳入计划通过门禁 |

### Acceptance ledger 与 admission

| ID | 严重度 | claim 与 evidence | closure_condition | admission | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| F1 | major | 计划 E1–E4 部分链接只指向调用或 task_started；E4 仅指较早成功报告，未给后续按钮 400 和缺 JSON body 证据 | 改成直接支撑观察的结果行；跨事件给起点与结果；E4 写明较早成功报告→实际入口失败 | MITIGATE_IN_V1：只改 E1–E4 证据表，不重扫历史、不增加机制 | OPEN |
| F2 | major | B4 的“元数据＋近期变化回合”未明确保留当前 automation 所需 user request、final、blocker、handoff、terminal successor | metadata 只枚举；逐链保留上述最小证据；缺失即无法确认，不计已结项 | MITIGATE_IN_V1：补充原有证据合同，不新增共享状态或全量读取 | OPEN |

主代理接受这两个发现进入修订。其余已存在能力保持 NO-OP；没有 rubric challenge。known_unknowns：人工耗时未实测、纯展示需按未来实际 diff 分类、工具取消能力未知、B5 检查点未证实、未来规则可漂移、实际收益未验证。

### 修订与主代理集成核对

- Revision worker 仅修改计划的 E1–E4 证据与 B4 闭环输入；未写其他文件。worker gate：`exit_code=0`，`reference_check=ok references=17 evidence_anchors=13 whitespace=ok b4_contract=ok`，`timestamp=2026-09-10T18:37:52Z`，worker 版本 SHA-256 为 `2f4bfbfab7525f15cf8b533e03f9074e8630ea7a838db5d4ea2cb980bf154b1b`。
- 主代理定向解析确认 E1 结果实际在日志 665 行，纠正首轮提到的 664；E2 的三个 `duration_ms` 为 400494、534284、656007；E3 为 1567990。没有照抄未经复核的子代理行号。
- F1 补充 admission：E5 的跨事件断言也应给出前一晚实现与次日建议两端证据；作为同一 RE1 证据修正，MITIGATE_IN_V1，仅补一个现有日志链接，不增加新流程。
- 两项修订提交闭合复核时 F1/F2 保持 OPEN；状态由下述 Round 2 覆盖，不追改首轮历史。

## Round 2：闭合复核

评审计划 SHA-256：`e65b8296b88f5748d02f965f7213a6c8f6dbd640b2e9c13f865adf2575e3ad1f`。rubric v1 未变。

| 专家视角 | 分数 | 闭合判断与覆盖 |
| --- | ---: | --- |
| 运营效率与人机协作 | 10/10 | F2 已补逐链证据与 unknown 处理；人工接手、独立工作、NO-OP 完整。R1、R2、R7、R8 |
| 工程验证与工具执行 | 10/10 | F1 已给结果／跨事件两端锚点；gate、写集及恢复未削弱。R3、R4、R6、R8 |
| 安全与运行治理 | 10/10 | B4 覆盖、授权、unknown、并发、dirty 与 B5 边界完整。R3、R5、R6、R7 |

迭代共识 `committee.rating=10/10`，候选 `threshold_status=pass`；最终门禁仍等待独立盲审，不平均分数。没有 new_material_findings 或 rubric_challenges。

| Finding | 当前状态 | 闭合依据 |
| --- | --- | --- |
| F1 | CLOSED | 计划 E1–E5 给出直接结果／跨事件两端；E1=665、E2合计1590785 ms、E3=1567990 ms、E4真实400与根因、E5实现与误推荐均已核对 |
| F2 | CLOSED | B4 元数据只枚举，逐链读五类证据，区分 absent/unavailable；无法判断即 unknown，必要时回溯原始目标 |

RE1、RE7 complete；RE2、RE3 met 且未变；RE4–RE6 met at plan level；RE8 met for plan，跨任务能力与实施效果继续安全延后。所有专家仍披露自然任务收益、工具硬取消、未来配置与检查点可用性未验证。

修订后主代理 fresh gate：`command=python3 -`（两文档引用与行界、选定 JSON 事件／数值、准确 write set、空白／围栏、git diff --check）；`exit_code=0`；`key_output=23 references / 18 line anchors / evidence_values verified / exact two documents`；`timestamp=2026-09-10T18:39:47.158517Z`。计划内容此后未变化，该证据提供给独立盲审复核。

## Round 3：独立盲审

新只读 reviewer 仅接收当前计划、scope envelope、frozen rubric v1 和有效验证证据；未接收目标分数、历史评分、结论或修订 brief。本文件不在盲审读取范围。

盲审计划仍为 `e65b8296b88f5748d02f965f7213a6c8f6dbd640b2e9c13f865adf2575e3ad1f`。共识 `7/10`，`threshold_status=fail`。运营专家原始 7；工程专家原始 9；安全专家原始 8。后两者没有遵守“每位专家也受任一 open major 上限约束”，主代理按冻结合同将有效分数分别封顶为 7、7；保留原始分数供追溯，不将其用作通过证据。

RE1–RE3、RE5–RE7 在计划阶段已满足；RE4、RE8 由新的反例重新判为 partial。F1/F2 的历史闭合保持，但旧版本迭代满分不能覆盖新发现。

| ID | 严重度 | claim 与 evidence | closure_condition | admission | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| BF1 | major | A1 将“同一步无进展”并列为人工接手条件，未明确排除仍在支持时限内的单纯变慢；可能过早停车 | 人工接手限定为已确认无入口／明确限制，或现行 skill 的预算耗尽；增加稍慢但在时限内继续等待的验收反例 | MITIGATE_IN_V1：只收窄 A1 条件，不新建预算器 | OPEN |
| BF2 | 重要未验证断言，cap 8 | B5 已保留 access/cutoff，但未明确 observation timestamp 与当前消费者窗口覆盖，可能复用陈旧晨报 | source/account/scope、访问权、cutoff覆盖、observation timestamp 全部匹配且仍适用才复用；未知／陈旧／不等价即 defer | MITIGATE_IN_V1：补齐已有读取合同，不新增共享状态 | OPEN |

### Rubric amendment v1.1

主代理接受本次两项 rubric_challenges 并记录增量，不覆写 frozen v1：

- R2 增补可判定反例：工具仍在支持时限内的单纯变慢，不触发人工接手；重开 RE4。
- R7/RE8 增补 freshness 证据：观察时间戳与当前消费者窗口／cutoff 的覆盖关系，以及 source/account/scope 等价；重开 RE8。
- 依据为 BF1/BF2 指向的计划 A1/B5 当前文本。其他标准、scope 和非目标不变；不是要求增加新机制。

本轮残余风险仍为工具硬取消、配置漂移、跨任务能力未知和真实收益未证实；不能以这些已披露风险抹掉 BF1/BF2 的文本缺口。

### 第二次修订与验证

worker 仅修改 A1 第 55/59/61 行和 B5 第 97 行；没有重读历史日志或扩大文件范围。主代理逐段复核了人工接手的限定、正常稍慢的反例，以及来源／窗口／观察时间戳等价和 defer 条件。

主代理 gate：`command=python3 -`（文档引用、准确两文件 write set、空白／围栏、git diff --check）；`exit_code=0`；`key_output=23 references / exact two documents / PASS`；`timestamp=2026-09-10T18:47:18.096588Z`。计划 SHA-256：`7d6228f5183921c1eb74d403404fa38aa2f0c5d2d863923197848e44e9ce801a`。历史证据表没有变化，沿用 18:39:47 的行号与数值核对。

## Round 4：v1.1 闭合复核

原委员会按 rubric v1.1 重新核对 BF1、BF2 与 RE4、RE8；计划 hash 为 `7d6228f5183921c1eb74d403404fa38aa2f0c5d2d863923197848e44e9ce801a`。

| 专家视角 | 分数 | 闭合判断与覆盖 |
| --- | ---: | --- |
| 运营效率与人机协作 | 10/10 | A1 接手条件已收窄，正常稍慢继续等待。R1、R2 v1.1、R7 v1.1、R8 |
| 工程验证与工具执行 | 10/10 | 接手反例与复用等价条件可判定。R2 v1.1、R3、R4、R6、R8；RE4、RE8 |
| 安全与运行治理 | 10/10 | 来源、窗口、cutoff、时间戳均必需；未知／陈旧即 defer。R5、R6、R7 v1.1、R8 |

迭代共识 `10/10`，候选 `threshold_status=pass`；本轮每位专家均符合 caps。BF1、BF2 CLOSED，RE4、RE8 complete；RE1–RE3、RE5–RE7 维持计划阶段 complete。无 new_material_findings 或 rubric_challenges。

有效验证为 18:47:18 的主代理检查，计划内容此后未变化。最终通过仍需新独立实例盲审，旧盲审实例不作为本轮新盲审。

## Round 5：独立盲审

全新只读 reviewer 仅取得当前计划、scope、rubric v1.1 与有效证据，不接收本文件、目标分数、此前评分／结论／修订过程。评审计划 hash 为 `7d6228f5183921c1eb74d403404fa38aa2f0c5d2d863923197848e44e9ce801a`。

| 专家视角 | 分数 | 判断与覆盖 |
| --- | ---: | --- |
| 运营效率与人机协作 | 10/10 | A1 不把正常等待误作失败；A3 NO-OP；没有新增常驻流程。R1–R3，人工接手与停止反例 |
| 工程验证与工具执行 | 10/10 | 展示例外严格，API 与按钮证据分开；准确写集、六个 automation ID、gate 与回读完整。R3–R4、RE1–RE5 |
| 安全与运行治理 | 10/10 | unknown 先回读、dirty／并发保护、恢复和 promotion gate 完整；B5 来源与窗口／时效条件齐全。R5–R8、RE6–RE8 |

独立盲审共识 `committee.rating=10/10`，`threshold_status=PASS`，`top_findings=[]`；RE1–RE8 全部在计划阶段 COMPLETE。各专家没有未关闭发现，评分 caps 均满足。

盲审输出的 `rubric_challenges` 字段列了六个已经回答的反例检查：R1 是否重复规则、R2 是否中断长任务、R4 是否削弱 CI、R5 是否扩大 promotion 授权、R7 是否假设共享状态、R8 是否冒充实际收益。各项回答均指出当前计划已保留对应控制，没有提出遗漏标准或修改诉求。主代理保留其语义为 counterexample checks；`material_rubric_challenges=[]`，未据此偷偷修改 rubric。

## 最终台账与结论

| Finding | 最终状态 | 处置与证据 |
| --- | --- | --- |
| F1 | CLOSED | 原始与结果锚点、三个准确 duration_ms、E5 实现／推荐两端；18:39:47 主代理数值检查及后续未变证据表 |
| F2 | CLOSED | B4 五类闭环证据、absent/unavailable、unknown 和窗口前目标回溯 |
| BF1 | CLOSED | A1 仅无入口／明确限制／预算耗尽接手；支持时限内稍慢继续等待 |
| BF2 | CLOSED | B5 source/account/scope/access/cutoff/timestamp 与消费者窗口等价，不足即 defer |

最终 `committee.rating=10/10`；迭代评分 `10/10`，独立盲审评分 `10/10`，不平均；`threshold_status=pass`。共 5 轮：6.5 → 10 → 7（盲审）→ 10 → 10（新独立盲审）。rubric v1 加显式 v1.1 amendment；R1–R8 均覆盖，RE1–RE8 达到计划阶段要求；open blocker/major/minor/重要未验证断言均为 0。

范围限制与 known_unknowns/residual_risks：计划未实施；runtime、外部发布、自动化首次执行与效率收益未验证；UI 不保证硬取消；未来配置／规则可漂移；真实 diff 必须正确分类；B5 检查点和访问／窗口等价性需未来只读核实。不把文档或评分当作上述实施事实，不因为本次通过新增常驻委员会。

交付仅新增两个文档，无 commit/push、runtime sync、自动化更新或其他仓库变更。最终两文件机械检查的最新回执随本轮聊天交付，避免为记录其自身 hash 再次改写被检查文件。

## 验证与最终状态

可在 MCE 根目录复跑以下检查。此处 write-set 断言适用于本轮 clean 起点，不授权清理未来出现的用户修改。历史来源链接仅验证可定位，语义由委员会核对；文档检查不证明实际效率提升或 runtime 生效。

```bash
python3 - <<'PY'
from pathlib import Path
import re, subprocess, hashlib, json
from datetime import datetime, timezone
paths = [Path('docs/plans/2026-09-10-task-efficiency-improvement-plan.md'),
         Path('docs/plans/2026-09-10-task-efficiency-committee-review.md')]
references = 0
for path in paths:
    body = path.read_text()
    assert not any(line.endswith((' ', '\t')) for line in body.splitlines()), path
    assert body.count('\n```') % 2 == 0, path
    for ref in re.findall(r'\]\(([^)]+)\)', body):
        if '://' in ref:
            continue
        ref = re.sub(r':\d+$', '', ref.split('#')[0])
        target = Path(ref) if ref.startswith('/') else path.parent / ref
        assert target.is_file(), target
        references += 1
status = subprocess.check_output(
    ['git', 'status', '--porcelain', '--untracked-files=all'], text=True)
assert all(line[3:] in {str(p) for p in paths} for line in status.splitlines()), status
subprocess.run(['git', 'diff', '--check', '--', *map(str, paths)], check=True)
print(json.dumps({'result': 'PASS', 'references': references,
                  'plan_sha256': hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                  'timestamp': datetime.now(timezone.utc).isoformat()}))
PY
```

初检：`command=python3 -`（等价的引用、write set、空白、围栏与 diff 检查）；`exit_code=0`；`key_output=13 references; exact two-file write set; PASS`；`timestamp=2026-09-10T18:23:30.433401Z`。计划初检 SHA-256：`f8e6b91435ca5e6b12bb21de2dc95ec97c567286f11230dfb51cfed8fd626c68`。后续修订不继承这一 hash 的证明。

当前状态：complete（计划与评审交付；实施未开始）。
