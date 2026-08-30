# Global AGENTS 设计简化决策记录

- 日期：2026-08-30
- 状态：仓库源码已修改；runtime 未同步
- 唯一源码：`codex/AGENTS.md`
- 修改前备份：`tasks/archives/2026-08-30-global-agents-pre-design-simplicity/`

## 背景

对 2026-06-30 至 2026-08-30 本地 Codex 会话的复查发现一种重复失败模式：agent 正确识别了安全或质量目标，却随后把有边界的任务扩张为推测性迁移支持、未来平台能力、重复校验、额外状态或不同访问路径。同一批会话也证明，当复杂度保护当前信任边界、持久数据、已知消费者、独立 read-back、审计历史、恢复行为或公开合同时，它是必要的。

因此，本次修改不是“不惜代价采用最简单代码”，而是建立两个成对默认：

1. 删除或延后推测性复杂度；
2. 保留与当前需求、可复现故障、信任边界、已知消费者、持久数据或明确合同对应的复杂度。

## 决策

全局规则现在要求：

- 将“完美”“长远”等质量表述视为目标，而不是平台化授权；
- 拒绝推测性兼容层，同时保留当前数据、已知消费者、公开接口或明确合同需要的兼容性；
- 简化前检查调用链、数据流并执行 deletion test；
- 当授权、隐私、完整性、独立回读、审计、恢复、并发、迁移和公开接口控制关闭真实风险时保留它们；
- 保留执行真实合同的确定性 validator 和 fail-closed reason code，拒绝为主观偏好或未来假设创建规则引擎；
- 为同一不变量指定一个权威校验边界，但不把跨信任验证、defense-in-depth 或外部回读视为重复；
- 新增抽象、配置、迁移、长期状态、推测选项或明显扩大文件范围前，先给出最小版本；
- 用户最新纠正只覆盖冲突假设，不取消仍有效的安全、授权和写入边界；
- 第一次工具调用前明确目标、症状以及授权的访问和写入路径；
- 遵守用户指定的 SSH、CLI、API 或其他访问路径，禁止未经请求的 UI 自动化；
- 先诊断点名系统，变更前取证，一次实施一个最小根因修复，并复验原始症状。

## 用户介入边界

这些规则是 agent 默认行为，不是新的审批仪式。agent 应先检查本地证据并自行选择最小有效路径。只有歧义会实质改变目标、外部系统、身份、写入范围、持久数据、外部消费者或公开合同时，才问一个简短问题。

两个月反事实复查估计会新增约零至两次早期问题，但会减少更多晚期范围纠正和返工。同一授权边界内的等价只读替代不需要重新询问。

## 上下文成本

早期去重方案估算增加 460–700 tokens。最终版本加入必要复杂度保留门并压缩到仓库大小门内，实测增加 1,165 字符，估算约 613–932 tokens，相对原文件字符数增加 45.7%。项目案例、VibeGuard 专用编号和固定五文件硬阈值均未写入全局规则。

## 边界

- 本次修改仓库规则源码、修改前备份和决策记录，并通过权威 refresh 更新受管源码批准摘要及其派生 observation fixture。
- 不把 `codex/AGENTS.md` 同步到 `~/.codex/AGENTS.md`。
- 不修改 hook、runtime policy、skill、agent 或 repo-local `AGENTS.md`。
- 不 commit、push、deploy 或 publish。

## 实现记录

- 修改前 SHA-256：`5051c2289a45fd430bbf9a9719526fab3315c6f86668eea5122f5bc9b0910c27`。
- 修改后受管源码 SHA-256：`1dbeec8b26b24cfc869d7de4556177cddf8db7ae4052f94d3ac2e14a68bdfba2`。
- 初次完整门禁发现 `codex/AGENTS.md` 超过 8,192-byte 合同，并按设计报告 Identity A stale；没有把这次失败当作通过。
- 规则经语义保持压缩后为 7,905 bytes；重复的 `独立 read-back` 枚举被合并到跨信任边界例外。
- Identity 使用 `scripts/harness_refresh_identity.py refresh --approve` 权威刷新；A/B/C/D 全部 fresh，AC-16 历史 provenance 保留。
- 权威刷新修改 `runtime-approvals/approved-source-digests.txt` 和 `tests/fixtures/dhf_simplification_observations.json`；未修改 transition identity 或 runtime 文件。

## 验证

| command | exit_code | key_output | timestamp |
| --- | ---: | --- | --- |
| 聚焦 archive、规则唯一性、大小、write set、Identity 与空白检查 | 0 | archive 匹配；`source_bytes=7905`；关键条款 `7/7`；A/B/C/D fresh；6 文件 write set；无尾随空白 | `2026-08-30T17:46:23Z` |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/harness_refresh_identity.py refresh --message 'Record global AGENTS design-simplicity rules' --approve` | 0 | B/C refreshed；AC-16 provenance preserved；批准 digest `1dbeec8b…dfba2` | `2026-08-30T17:45:23Z` |
| `python3 test_runner.py` | 0 | `ran=145 passed=145 skipped=0 failed=0`；`[PASS] all tests` | `2026-08-30T17:46:29Z` |
