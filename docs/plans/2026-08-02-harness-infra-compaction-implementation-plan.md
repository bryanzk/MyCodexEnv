# Harness Infra 实施计划:压缩治理五项能力 + 卫生项

日期:2026-08-02 · 状态:计划(未实施) · 经 3 轮委员会评审定稿(终分 10/10)

## 与校验门计划的分工(硬边界)

本计划只交付**可执行 infra**(脚本、hook、schema、测试)。`codex/AGENTS.md`、`README.md` 的政策文本修改**全部**属于《2026-08-02-thread-discipline-compaction-gate-plan.md》,本计划不碰,避免双计划编辑同一契约文件。门计划落地时引用本计划交付的 helper 名称即可。

## 实施顺序(每个工作流 = 一个独立 commit,revert 即回滚;唯一例外 W2 = W2a+W2b 两个 commit,见 W2 节)

### W6 卫生项(先行,信任基座)

- W6a:修复 runtime parity 4 项失败(`./scripts/verify_codex_env.sh`),恢复 `harness-state.md` 验证全绿。涉及 `~/.codex` 同步,**需用户批准 sync 后执行**;未批准前,后续 hook 类工作流(W2)只做 source + 测试,不部署。
- W6b:关闭 harness_guard fail-open 待办——重跑 2026-07-28 的隔离 probe,确认所有原 ask 类别已按 `docs/HARNESS_RUNTIME.md` L74 升级为 block,把结论写入 evidence 与记忆,清除"修复待办"状态。

### W1 transition 持久层(最小成本、最大收益)

- 新增 `scripts/harness_transition.py`:
  - `record --key K --task-id T`:单行 JSON,O_APPEND 原子追加到 `~/.codex/harness/transitions.jsonl`;**追加后重读**,同 key 首条记录胜出(CAS 语义);若已存在同 key 不同 task-id 的先行记录,退出非零并输出先行者——调用方视为"继任已创建"。
  - `query --key K`:返回该 key 首条记录或明确的 not-found;文件缺失 = not-found,非错误。
  - 容错:malformed 行跳过并计数(与 evidence reader 同款行为)。
- 测试:新增 `test_harness_transition_record_and_query`(roundtrip、同 key 竞态首条胜出、不同 task-id 拒绝、malformed 容忍、文件缺失)。
- 效果:AGENTS.md 序列步骤 3/5 的"inspect already-available lifecycle state"从无处落地变为可执行查询;"idempotency 不确定→terminal handoff"从常态变为罕见。

### W2 实时压缩探测(Phase-0 探针是硬门)

- Phase 0(硬门):临时 hook 记录一次真实 UserPromptSubmit payload 到本地 evidence,确认是否含 session/thread id,**同时记录 usage/token 字段是否存在**(供角色计划 R4 计量员消费,一次探针服务两个消费者)。**未完成此探针前不写实现。**
- Phase 1:抽取 `report_active_sessions.py` L153-163 的 `compacted` 事件计数为共享函数(scanner 同步改为调用,防止两处逻辑漂移;scanner 输出契约不变,`test_codex_fluent_active_session_report` L6025 必须保持全绿)。
- Phase 2:新增 `codex/hooks/compaction_probe.py`,挂入 `codex/hooks.json` UserPromptSubmit 链:
  - 会话定位:优先 payload session id;否则要求 cwd 匹配 + mtime 在窗口内 + 候选唯一,三者不齐则**不注入**(注入错会话计数比不注入更糟)。
  - 命中则注入 `compaction_ordinal=N (host-observed)` 上下文;未命中写一条 routine evidence `probe_inconclusive`。
  - 预算:<100ms,超时或任何异常静默退出,不阻塞正常工作(与 observer 同款 fail-open-for-observability 原则)。
  - **增量扫描(强制)**:长会话 JSONL 可达几十 MB,每轮全量扫描必破预算。探针必须缓存上次读取 offset(存 `~/.codex/harness/probe_state.json`,按会话文件路径分键),每轮只读增量;检测到文件缩短或 offset 状态缺失/损坏时,回退全量重扫一次并重建状态。这是全方案唯一可能写坏变慢的点。
- 测试:新增 `test_compaction_probe_session_resolution`(id 命中、启发式三条件、不齐不注入、超时静默);新增 `test_compaction_probe_incremental_scan`(增量追加计数正确、offset 缓存生效、文件缩短回退全扫、状态损坏重建、大 fixture 下增量路径不读全文件)。
- commit 步骤:W2 拆两个 commit——
  - **W2a**:共享计数函数抽取 + scanner 改造 + Phase-0 探针证据落档(含 session id 与 usage 字段存在性);
  - **W2b**:`compaction_probe.py` 实现(含增量扫描与 probe_state)+ 两个新测试 + hooks.json 注册。
  W2a 的探针证据必须早于 W2b 合入,天然满足合同的"证据先于实现"硬门。
- 部署:依赖 W6a 批准的 sync;source 与测试可先行合入。

### W3 checkpoint/evidence 字段(向后兼容加法)

- `scripts/harness_checkpoint.py` 增加可选参数:`--compaction-ordinal`、`--transition-key`、`--gate-decision {continue-to-boundary,immediate-successor,none}`;写入 state 条目与 Current Snapshot。
- `codex/runtime/evidence.schema.json` 及 `evidence/decision-evidence.schema.json` 增加同名**可选**字段;旧事件无字段读作 absent,不迁移(遵守既有 schema 演进政策)。
- 测试:扩展 `test_harness_checkpoint_helper`(L4566)与 `test_harness_evidence_append_and_observer_failure_mode`(L3661);断言新旧格式互操作。

### W4 boundary 裁决

- `scripts/harness_recover.py` 增加 `--boundary`:输出 `boundary_verdict: safe|unsafe|unknown` 及理由。
  - safe 需同时:`dirty_status == clean`;最新验证 `exit_code == 0`;验证时间戳晚于最后一次 repo 变更(git log 最新 commit 时间与 dirty 状态联合判断),且不早于 `--max-verification-age`(默认 24h)。
  - 任一无法判定 → unknown(fail-closed,调用方按 unsafe 处理)。
- 测试:扩展 `test_harness_recovery_smoke`(L4875):clean+新鲜绿证据→safe;dirty→unsafe;陈旧证据→unknown;无证据→unknown。

### W5 S_state 暴露(只做管道,不做政策)

- `harness_recover.py` payload 增加 `task_demand`:从最近的已验证 requirements 工件读取 `estimated_level` 与 `S_state`,缺失读作 unknown。政策消费(低状态任务免强制切换)归门计划,本计划不写政策文本。
- 测试:扩展 `test_harness_recovery_smoke` 断言字段存在与缺失回退。

## 每工作流验证(统一)

`python3 test_runner.py` 全绿 + `git diff --check` + 涉及 `~/.codex` 的工作流跑 `./scripts/verify_codex_env.sh`。每 commit 用 `harness_checkpoint.py` 记录验证四字段。

## 成功度量

- W1:weekly 审计中 "idempotency 不确定" 回退次数趋零。
- W2:probe_inconclusive 占比 <10%,错误注入为零(抽查 evidence 对照 scanner 计数)。
- W4:boundary unknown 占比可观测且随 W6a 修复下降。
- 任一指标恶化:revert 对应 commit,零连带(工作流间无共享代码,除 W2 的共享计数函数——其契约由 scanner 测试锁定)。

## 已知限制

- 压缩探测仍是轮询式(UserPromptSubmit 时点),不是压缩事件的即时回调——宿主无该 hook,这是平台上限。
- W6a 依赖用户批准 sync;在此之前 W2 hook 不部署,门计划的实时触发暂以"agent 自报 + weekly scanner 事后审计"过渡。
