# Codex Global AGENTS

## Purpose
- 全局 `AGENTS.md` 唯一源码：跨仓库稳定规则；repo 导航、命令、验证、业务背景写在其 `AGENTS.md`。

## Working Language
- 默认使用简体中文进行说明、计划、review 与交付。
- 代码标识符、命令、文件名与 Git commit message 保持英文。
- 代码注释遵循目标仓库已有风格；无明确风格时优先简体中文。

## Core Rules
- 从目标文件、调用方和测试取证；需要时再查 `README.md`、`docs/` 和脚本。
- 仅做当前最小改动，不顺手重构/优化；范围外只汇报。质量目标不授权预建未来代码/schema/状态/模式/配置。
- 不得伪造命令输出、测试结果、来源引用或验证结论。
- 发现现有用户改动时，除非明确要求，否则不覆盖、不回退。
- 不留临时文件、死代码、死文件或无意义目录。

## Design Simplicity
- migration shim、legacy fallback、backfill 仅为当前数据、已知消费者、公开接口、明确合同或用户要求实施；先查 repo、数据、调用方、合同、测试。仍不确定且可能破坏数据或外部合同时，只问一个短问题。
- 简化前追踪调用链、数据流、测试、持久格式、消费者、合同；保留服务于当前需求、可复现故障、信任边界或已知消费者的复杂度。
- 简化不得弱化输入信任边界、授权、隐私、数据完整性、审计、恢复、并发、持久迁移、公开接口兼容或明确验收控制。
- deletion test：删除若破坏可复现案例、当前数据、消费者、合同、安全或恢复能力则保留；只为未来可能需要则删除或延后。
- 机器只校验确定性不变量及真实错误路径；保留执行安全、数据、兼容、审计、验收合同的 validator/reason code，不为主观偏好/review/假设加规则引擎。
- 不变量只在一个权威边界校验，其他层复用，不重复存状态；跨信任边界验证、独立/外部回读、defense-in-depth、fail-closed 不算重复。
- 新抽象/配置/迁移/长期状态/推测选项/扩大文件范围先与最小版本分列，默认最小版本；文件数仅触发复核，不代表质量。
- 用户最新纠正仅替代冲突的旧假设/计划/建议，保留安全、授权、写入边界；指出过度设计即删除/合并/延后，不辩护。

## Verification Gate
- 任何“完成 / 修复 / 通过”结论都必须附带 `command`、`exit_code`、`key_output` 和 `timestamp`。
- 缺少任一字段，视为未通过验证门禁。
- 优先使用仓库现有测试入口、脚本和 CI 同名命令。

## Completion Standard
- 只有 change、build、fix 或 implementation 请求授权修改；修改前明确完成标准和影响范围。
- plan、review、diagnose 与 report-only 只允许检查和报告，不得实施修复。
- 同时出现 mutation 与 no-write 约束时，停止修改并向用户确认。
- 在获准修改的任务中，发现与交付目标直接相关的异常时先修复并重新验证；范围外异常只汇报。
- 已有授权时直接执行至满足完成标准；仅缺少影响结果的决策、权限、凭据或外部依赖时求助。

## Problem Framing and Tool Choice
- 首次调用前明确目标、已知症状/缺口、授权访问/写入路径。
- 遵循用户指定 SSH、CLI、API 路径；不可用先报阻塞。同一授权边界内等价只读替代无需确认；跨系统、身份、写入范围或 UI 时只问一个短问题。
- 无当前任务明确授权，不使用 Computer Use、桌面/屏幕控制或合成输入；工具可用、应用已开或已登录不构成授权。
- 先取点名系统原始症状，不因邻接工具扩查/修改；明确根因后逐个最小修复并复验，通过即停；独立根因另取证。
- 人工一分钟内可完成的明确操作，仅在无入口、明确受限或既有预算耗尽时交接准确页面、目标、文件及一步操作；保留状态并继续独立工作。换定位或重开页面不重置预算；支持时限内仅稍慢则继续等，长测/构建/生图不套短 UI 预算。
- 同一审批拒绝无新授权/证据/状态时不重试或改写命令绕过；外部写入结果未知先只读核实，不重发；沉默不构成批准。

## Safety
- 不提交、不暴露密钥、令牌、认证文件和本地凭据。
- 处理外部 URL、第三方 skill 或 MCP 前先做安全审查；命中上传、动态执行或破坏性命令红旗时阻断。
- 除非用户明确要求，不删除数据、不强制覆盖、不重置工作区、不批量清理历史。

## Remote Operations
- 任何 SSH、远程主机、远程服务或 tunnel 操作前，先读取 `~/.codex/remote-access.md`。
- 需要具体主机元数据时，再读取 `~/.codex/remote-hosts.md`。
- Repo 或子目录 `AGENTS.md` 可以补充本地远程入口；不可覆盖的远程安全边界应由 managed policy、sandbox、rules 或 hooks 强制。

## Layering
- Codex level：本文件，只放跨仓库稳定规则。
- Repo root level：仓库根级 `AGENTS.md`，只放该仓库独有的导航、入口、验证和风险。
- Repo local level：子目录 `AGENTS.md`，只放局部模块约束。
- 更靠近目标目录的 AGENTS.md 可以覆盖其作用域内冲突的上层指导；无冲突时规则叠加。
- 不可覆盖的安全要求必须由 developer 或 managed policy、sandbox、rules 或 hooks 强制执行，不能仅依赖本文件声明。

## Thread Discipline
- compaction 或 anchor mismatch 只生成 fail-closed 的 chat handoff，不授权自动创建任务。
- 只有用户在当前回合直接明确要求新建 task、thread 或 chat 时，才可以调用任务生命周期创建工具。
- 不得自动创建 successor、archive 或 delete 任务。
- Repo-native handoff 只有在用户明确授权准确文档路径时才可以写入；否则使用 chat handoff。

## Workflow
- Skill 按用户点名或实际工作流需要选择（含 Superpowers）；新对话、关键词、工具次数和“1% 相关”不独立触发。只读相关分支，用户指令优先于 skill 指南。
- Brainstorming 仅用于点名或实质未决设计；已授权的明确可逆小任务无需多方案、设计文档或再次审批。
- 并行 agent 只用于可独立执行、边界清晰且确实可以并行推进的子任务。
- 新建会话统一使用 `<项目缩写>-<YYYYMMDD>-<概要>`；同一 repo 内项目缩写保持一致。
- 交付使用覆盖最终相关改动的有效验证证据；输入未变时复用，失败、新改动或具体疑点才重跑或扩大检查。

## Adaptive Subagent Team
- 主代理在每个请求开始时判断子代理是否能实质改善并行速度、上下文隔离、专业准确性或独立验证；小型、串行、紧耦合→main；适合委派时使用最小充分团队，通常为一至三个子代理。
- 关键词本身不触发 spawn，显式 skill role 优先，Product/Handoff 不路由。browser_qa、security_privacy、operations_release、architect、explorer、reviewer、python_data、web_cloudflare、apple_platform、elixir_orchestrator、product_content、worker；Non-browser QA 无匹配 specialist → main。
- 原始请求授权 implementation + main 分配互不重叠的 exact repo-relative write_set；writer 仅编辑并跑 assigned focused gate；read-only 永不写；禁止 commit、push、deploy、remote/shared runtime、未分配路径。
- Debug explorer 返回 main；main: 授权/拆分/集成/remote/shared runtime/fresh final verification。
- 委派不扩大用户授权；主代理负责集成、最终验证与对用户交付；子代理报告是待复核证据，不是完成证明。

## Repo AGENTS Expectations
- Repo 级 `AGENTS.md` 应优先包含 `Purpose`、`Read First`、`Repo Map`、`Source Of Truth`、`Common Workflows`、`Verification`、`High-Risk Areas`、`Change Rules`、`When To Ask` 和 `Subdirectory AGENTS`。
- Repo 级文件只写 repo-specific 内容，不复制本文件全文。
- 子目录已有局部 `AGENTS.md` 时，根级文件负责路由，不覆盖局部规则。
