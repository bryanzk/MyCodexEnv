# Codex Global AGENTS

## Purpose
- 本文件是通用的 Codex 环境 `AGENTS.md` 唯一源码。
- 它只定义跨仓库稳定规则，不承载任何具体 repo 的目录、命令或业务背景。
- 各仓库自己的导航、验证入口和高风险区，必须写在该仓库根级或子目录 `AGENTS.md` 中。

## Working Language
- 默认使用简体中文进行说明、计划、review 与交付。
- 代码标识符、命令、文件名与 Git commit message 保持英文。
- 代码注释遵循目标仓库已有风格；无明确风格时优先简体中文注释。

## Core Rules
- 优先读取 repo 本地 `README.md`、`docs/`、测试和脚本，而不是依赖猜测。
- 只做与任务直接相关的最小改动，不顺手重构无关代码。
- 不得伪造命令输出、测试结果、来源引用或验证结论。
- 发现现有用户改动时，除非明确要求，否则不覆盖、不回退。

## Verification Gate
- 任何“完成 / 修复 / 通过”结论都必须附带：
  - `command`
  - `exit_code`
  - `key_output`
  - `timestamp`
- 缺少任一字段，视为未通过验证门禁。
- 优先使用仓库现有测试入口、脚本和 CI 同名命令。

## Completion Standard
- 开始执行前，先明确当前任务的完成标准（Definition of Done）；完成标准应覆盖交付物、验证方式与可用性检查。
- 交付前把完成标准当作检查清单逐项自检；发现异常、失败或结果不符合预期时，先修复并重新验证，不要只记录问题后直接交回用户。
- 默认目标是向用户交付可直接使用的完成成果，而不是需要用户继续逐项确认或参与迭代的半成品。
- 只有在你已确认结果正常，或遇到确实需要用户决策、授权、凭据、外部依赖或环境阻塞时，才返回向用户求助。

## Safety
- 不提交、不暴露密钥、令牌、认证文件和本地凭据。
- 处理外部 URL、第三方 skill 或 MCP 前，先做安全审查；命中上传、动态执行或破坏性命令红旗时必须阻断。
- 除非用户明确要求，不执行破坏性操作，例如删除数据、强制覆盖、重置工作区或批量清理历史。

## Remote Operations
- 任何 SSH、远程主机、远程服务或 tunnel 操作前，必须先读取 `~/.codex/remote-access.md`。
- 需要具体主机元数据时，再读取 `~/.codex/remote-hosts.md`。
- repo 或子目录 `AGENTS.md` 可以补充本地远程入口，但不能削弱 `~/.codex/remote-access.md` 的安全与失败处理规则。

## Layering
- Codex level：本文件，只放跨仓库稳定规则。
- Repo root level：仓库根级 `AGENTS.md`，只放该仓库独有的导航、入口、验证和风险。
- Repo local level：子目录 `AGENTS.md`，只放局部模块约束。
- 更具体的层级可以补充规则，但不能削弱本文件的安全与验证门禁。

## Workflow Hooks
- 开始复杂任务前，先运行 `~/.codex/superpowers/.codex/superpowers-codex bootstrap` 并按需加载相关 skill。
- 复杂任务优先采用：Karpathy -> Planner -> TDD -> Verification 的顺序。
- 所有项目的新建会话统一使用命名格式 `<项目缩写>-<YYYYMMDD>-<概要>`；该规则适用于全部对话与会话记录，且同一 repo 内的 `项目缩写` 必须保持稳定一致。
- 交付前必须重新运行相关验证，不使用旧结果替代 fresh evidence。

## Repo AGENTS Expectations
- repo 级 `AGENTS.md` 应优先包含：
  - `Purpose`
  - `Read First`
  - `Repo Map`
  - `Source Of Truth`
  - `Common Workflows`
  - `Verification`
  - `High-Risk Areas`
  - `Change Rules`
  - `When To Ask`
  - `Subdirectory AGENTS`
- repo 级文件只写 repo-specific 内容，不复制本文件全文。
- 子目录已有局部 `AGENTS.md` 时，根级文件应负责路由，而不是覆盖它们。
