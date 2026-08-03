# Thread Discipline 修改计划:第2次压缩从强制切换降级为强制校验门

日期:2026-08-02 · 状态:计划(未实施) · 经 3 轮委员会评审定稿(终分 10/10)

## 目标

把 `codex/AGENTS.md` 中"确认第2次压缩 → 立即停止工作并创建继任任务"改为:

- 第2次压缩 → 执行 `COMPACTION_FIDELITY_GATE_V1`(强制校验门)
- 校验失败或不确定 → 立即执行现有 `COMPACTION_SUCCESSOR_SEQUENCE_V1`(fail-closed,行为等同现状)
- 校验通过 → 只允许把 in-flight 子任务推进到**有证据的安全边界**,然后执行继任序列
- 第3次确认压缩 → 无条件立即执行继任序列(兜底上限)

继任序列本身(步骤 2–11:handoff 内容、幂等键、≤3 次自动迁移、fail-closed 回退、不自动归档)**完全不动**。

## 设计决策(已锁定)

- D1:只改触发层,不改继任机制。序列保留 V1 名称;新增门为独立命名 `COMPACTION_FIDELITY_GATE_V1`,旧会话恢复时按"无门记录=旧语义"处理,无歧义。
- D2:codex-fluent 扫描器(`report_active_sessions.py:200` 的 `handoff_required: compaction_count >= 2`)语义不变——它是保守审计标记,不是执行触发器,保持 ≥2 阈值零回归。
- D3:门的判定必须全部基于客观证据,任何"无法判定"一律 fail-closed 走立即继任。
- D4:门的规则文本预算 ≤8 行,避免重蹈 11 步序列的 prompt 复杂度问题。

## 门的规范(将写入 AGENTS.md 的内容骨架)

COMPACTION_FIDELITY_GATE_V1,在确认第2次压缩时触发:

1. 立即禁止 new-direction 工作(与 anchor mismatch 同款约束)。
2. 校验三项,全部需外部证据:frozen anchors 可精确解析且匹配;当前子任务、约束与验证证据可从 artifacts(plan/decision log/checkpoint)复原;compaction ordinal 可信。任一失败或无法执行校验 → 立即执行 COMPACTION_SUCCESSOR_SEQUENCE_V1。
3. 全部通过 → 记录 gate 判定、边界条件、预计算的 compaction_transition_key 到 checkpoint(防止推迟窗口内再压缩丢失判定),然后仅推进当前 in-flight 子任务至安全边界。
4. 安全边界 = 以下任一客观证据:该子任务验证命令 exit 0;`git status` 显示无半成品编辑;本无 in-flight 操作。到达边界 → 执行继任序列。
5. 确认第3次压缩,或边界在当前子任务内无法到达 → 无条件立即执行继任序列(transition_key 已预计算,幂等性由现有步骤 3 保证)。

## 受影响文件清单(全部已核实存在)

1. `codex/AGENTS.md`
   - L63 前插入 GATE 定义(≤8 行)
   - L64 步骤1 触发措辞改为"when COMPACTION_FIDELITY_GATE_V1 routes to successor creation (a confirmed second compaction with failed or uncertain fidelity check, a reached safe boundary, or a confirmed third compaction)"——保留 "confirmed second compaction" 短语以维持测试契约
   - L156-158 触发 bullet 同步改写
   - L154-155 首次压缩 checkpoint 规则不动
2. `README.md:121` Thread discipline bullet 同步改写(第2次压缩→校验门,第3次→无条件切换)
3. `test_runner.py`
   - `test_global_agents_second_compaction_successor_contract`(L6662-6746):required terms 中 "confirmed second compaction"(L6671)保留可过;新增 required terms:GATE 名称、"fail closed"、"safe boundary"、"confirmed third compaction"、checkpoint 记录项;ordered_terms L6726 首项措辞随 L64 更新
   - 新增 `test_global_agents_compaction_fidelity_gate_contract`:校验门的 5 步顺序、fail-closed 优先、行数预算(门文本 ≤8 行)
   - codex-fluent 测试(L6094-6100、L6429)不动(D2)
4. `docs/CODEX_ENV_REPRODUCTION.md` L66-77、L106-111 叙述同步
5. 不动:`codex/skills/codex-fluent/**`、`tests/fixtures/codex_fluent_report.golden.md`(D2)

## 实施顺序与验证

1. 一个 commit 完成 1-4 全部修改(策略文本与测试契约必须原子同步)。
2. 验证:`python3 test_runner.py` 全绿;全仓 grep `"At a confirmed second compaction, execute"` 确认旧触发措辞仅存在于新语境;grep `COMPACTION_FIDELITY_GATE_V1` 确认 AGENTS.md、test_runner.py、README、REPRODUCTION 四处一致。
3. 回滚:单 commit revert;扫描器未动,观测面零回归。

## 成功度量

经 weekly scanner 与 handoff 记录观察两项:过早切换次数(压缩2次但状态完好仍被迫切换)应下降;anchor 丢失/重复继任事件应保持为零。任一恶化即回滚。

## 已知风险

- 门仍是 prompt 执行而非可执行状态机(与现有序列同一局限,`CODEX_ENV_REPRODUCTION.md` L106-111 已声明);靠测试契约锁定文本、靠第3次压缩硬上限兜底。
- 推迟窗口内崩溃:gate 判定与 transition_key 已写入 checkpoint,恢复后按步骤 5 处理,幂等键防止重复继任。
