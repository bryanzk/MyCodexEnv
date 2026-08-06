# Codex Global AGENTS

## Purpose
- 本文件是通用 Codex 环境 `AGENTS.md` 的唯一源码，只定义跨仓库稳定规则。
- 具体 repo 的导航、命令、验证入口和业务背景必须写在该 repo 的 `AGENTS.md` 中。

## Working Language
- 默认使用简体中文进行说明、计划、review 与交付。
- 代码标识符、命令、文件名与 Git commit message 保持英文。
- 代码注释遵循目标仓库已有风格；无明确风格时优先简体中文。

## Core Rules
- 优先读取 repo 本地 `README.md`、`docs/`、测试和脚本，不依赖猜测。
- 最小改动完成任务，不顺手重构、优化或处理范围外问题；范围外发现只汇报。
- 不得伪造命令输出、测试结果、来源引用或验证结论。
- 发现现有用户改动时，除非明确要求，否则不覆盖、不回退。
- 不留临时文件、死代码、死文件或无意义目录。

## Verification Gate
- 任何“完成 / 修复 / 通过”结论都必须附带 `command`、`exit_code`、`key_output` 和 `timestamp`。
- 缺少任一字段，视为未通过验证门禁。
- 优先使用仓库现有测试入口、脚本和 CI 同名命令。

## Completion Standard
- 只有 change、build、fix 或 implementation 请求授权修改；修改前明确完成标准和影响范围。
- plan、review、diagnose 与 report-only 只允许检查和报告，不得实施修复。
- 同时出现 mutation 与 no-write 约束时，停止修改并向用户确认。
- 在获准修改的任务中，发现与交付目标直接相关的异常时先修复并重新验证；范围外异常只汇报。
- 默认交付可直接使用的完整成果；只有需要用户决策、授权、凭据或外部依赖时才求助。

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
- Skill 只在用户明确点名或任务与其描述匹配时使用。
- 并行 agent 只用于可独立执行、边界清晰且确实可以并行推进的子任务。
- 新建会话统一使用 `<项目缩写>-<YYYYMMDD>-<概要>`；同一 repo 内项目缩写保持一致。
- 交付前必须重新运行相关验证，不使用旧结果替代 fresh evidence。

## Repo AGENTS Expectations
- Repo 级 `AGENTS.md` 应优先包含 `Purpose`、`Read First`、`Repo Map`、`Source Of Truth`、`Common Workflows`、`Verification`、`High-Risk Areas`、`Change Rules`、`When To Ask` 和 `Subdirectory AGENTS`。
- Repo 级文件只写 repo-specific 内容，不复制本文件全文。
- 子目录已有局部 `AGENTS.md` 时，根级文件负责路由，不覆盖局部规则。
