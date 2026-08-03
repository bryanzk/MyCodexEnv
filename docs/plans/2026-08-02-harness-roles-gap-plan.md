# Harness 角色补全计划:六个缺失角色的落地方案

日期:2026-08-02 · 状态:计划(未实施) · 经 3 轮委员会评审定稿(终分 10/10)

依据:Anthropic《Effective harnesses for long-running agents》《Effective context
engineering》《How we built our multi-agent research system》、OpenAI《A practical
guide to building agents》、NVIDIA NOOA 官方博客。缺口分析结论:行为评测员、
任务台账员、开工仪式执行者、计量员、记忆整理员、分层护栏。

## 计划体系中的位置(三计划分工)

1. 门计划(thread-discipline-compaction-gate):唯一有权改 AGENTS.md/README 政策文本。
2. Infra 计划(harness-infra-compaction-implementation):W1 transition store、
   W2 compaction probe、W3 checkpoint 字段、W4 boundary 裁决、W5 S_state、W6 卫生。
3. 本计划:六个角色。依赖 infra 计划的部分显式声明,依赖未就绪时**降级不阻塞**。

## R1 行为评测员(第一优先)

新增 `scripts/harness_eval.py` + `docs/evals/` 场景目录。每个 eval = fixture 输入
+ end-state 断言,输出 PASS/FAIL + 证据四字段。分三档:

- tier-1(无依赖,立即可跑):
  - recovery eval:给定 fixture 状态(harness-state 片段 + evidence JSONL),
    断言 `harness_recover.py` 输出能复原 phase、next_safe_task、latest_verification;
  - handoff lint:校验 handoff 文档含冻结锚点、工件清单、验证证据、
    单一 next-safe-task(缺项即 FAIL);
  - ledger integrity eval(R2 落地后并入 tier-1)。
- tier-2(依赖 infra W1+W2):
  - idempotency eval:transitions.jsonl 中同一 transition_key 无双继任;
  - probe agreement eval:compaction_probe 注入的 ordinal 与 scanner 对同一
    会话 JSONL 的计数一致。
- tier-3(依赖真实会话语料,只做审计不做门禁):
  - 压缩恢复质量抽查:第2次压缩后的会话,其后续行为是否与 checkpoint 声明一致。
- 运行方式:tier-1/2 进 test_runner 作为契约测试;tier-3 挂 weekly 审计
  (codex-fluent maintenance checklist 增一行)。

## R2 任务台账员(第二优先,低成本高收益)

- 新增 `scripts/harness_ledger.py`:
  - `init --from <requirements.md>`:把合同 Acceptance Criteria 生成
    `ledger.json`(条目含 id、description、steps、passes:false),同时写入
    描述区内容哈希(所有 description+steps 的 sha256);
  - `pass --id X --verification-command --exit-code --key-output`:唯一合法
    的状态翻转入口,验证字段缺失即拒绝;
  - `verify`:重算描述区哈希,任何对条目本体的增删改(而非 passes 位)即 FAIL。
- 契约:agent 只准通过 helper 翻 passes 位。防篡改 = JSON 形态(Anthropic 实测
  比 Markdown 更抗擅改)+ 内容哈希 + `verify` 进验证门三件套,不引入签名复杂度。
- 测试:`test_harness_ledger_contract`(init 幂等、pass 需验证字段、
  篡改描述被 verify 抓住、直接编辑 JSON 被哈希抓住)。

## R3 开工仪式执行者

- 扩展 SessionStart hook 链:新增 `codex/hooks/session_bearing.py`,调用
  `harness_recover.py --boundary --json`(依赖 infra W4;未落地时降级为现有
  recover 输出),把 phase、next_safe_task、boundary_verdict、dirty_status
  注入会话上下文。
- 预算 <200ms;任何失败静默退出(observability 不阻塞正常工作)。
- 效果:把 Anthropic 的 bearing 序列(读进度、读台账、先自检后开工)从政策
  自觉变成宿主注入的既成事实。
- 测试:`test_session_bearing_hook`(注入形状、降级路径、静默失败)。

## R4 计量员

- 探针合并:infra 计划 W2 的 Phase-0 payload 探针**同时**记录 usage/token 字段
  是否存在,一次探针服务两个消费者,不重复探。
- 若 payload 有 usage:新增 `codex/hooks/context_meter.py`(或并入
  compaction_probe,探针结果定)持久化最近 token_usage 到
  `~/.codex/harness/meter.json`,并注入剩余容量估计;absent 一律 unknown。
- 若 payload 无 usage:记录结论,计量员降级为"每轮注入 compaction_ordinal
  作为粗粒度压力信号"(与 W2 合流),不造假数据。
- 测试:`test_context_meter_persistence`(有/无 usage 两路径)。

## R5 记忆整理员

- 扩展 `scripts/codex_subconscious.py` 增加 `reflect` 子命令:合并重复条目、
  修剪超龄或被后续条目取代的记录、输出整理报告(merged/pruned/kept 计数)。
- 挂 weekly 维护清单;绝不自动删除 decision 级记录,修剪只针对 routine/derived。
- 测试:`test_subconscious_reflect`(重复合并、超龄修剪、decision 保护)。

## R6 分层护栏(范围最小,风险最高)

- `codex/runtime/tool-policy.json` 每类别增加 `risk_tier`(low/medium/high);
  guard 决策 evidence 带上 tier。不改变任何 block/allow 行为——纯标注,为宿主
  未来支持 ask 时的分级升级预留数据。
- 硬门:任何触碰 harness_guard.py 的 commit,必须附带隔离 probe 重验
  (fail-open 前科),probe 证据先于合入。
- 测试:扩展 `test_harness_guard_policy_decisions` 断言 tier 出现在决策 evidence。

## 实施顺序与依赖矩阵

| 角色 | 依赖 | 依赖未就绪时 |
|---|---|---|
| R2 ledger | 无 | — |
| R5 reflect | 无 | — |
| R1 tier-1 | 无 | — |
| R6 risk_tier | 无(但有 probe 硬门) | — |
| R3 bearing | infra W4 | 降级用现有 recover 输出 |
| R4 meter | infra W2 Phase-0 探针 | 等探针结论,不先建 |
| R1 tier-2 | infra W1+W2 | 跳过该档,tier-1 先行 |

建议批次:批次一 R2+R5+R1(tier-1);批次二 R6;批次三 R3+R4+R1(tier-2),
与 infra 计划 W2/W4 合流后执行。每角色一个 commit,revert 即回滚。

## 成功度量

- R1:tier-1 评测进 test_runner 后保持全绿;tier-3 周度审计出报告。
- R2:验证门跑 `ledger verify` 零篡改;"过早宣告完成"类返工在 handoff 记录中趋零。
- R3:新会话首条消息即含 bearing 注入(抽查 evidence);"开工未自检"消失。
- R4:探针结论落档;若有 usage,meter.json 持续更新。
- R5:reflect 周报显示 merged/pruned>0 且 decision 记录零丢失。
- R6:决策 evidence 100% 带 tier;guard 行为零变化(对比 probe 前后)。

## 已知限制

- tier-3 行为评测依赖真实会话语料,只能审计不能门禁。
- R4 完全受宿主 payload 上限约束;探针说了算。
- R6 的"升级到人工"仍被宿主 ask fail-open 卡住,本计划只做数据预留。
