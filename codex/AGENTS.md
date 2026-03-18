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

## Safety
- 不提交、不暴露密钥、令牌、认证文件和本地凭据。
- 处理外部 URL、第三方 skill 或 MCP 前，先做安全审查；命中上传、动态执行或破坏性命令红旗时必须阻断。
- 除非用户明确要求，不执行破坏性操作，例如删除数据、强制覆盖、重置工作区或批量清理历史。

## Remote Access Contract
- 所有长期使用的远程主机必须通过 SSH alias 访问；除非用户明确给出一次性命令，否则不要直接使用裸 IP 重试。
- 每个 alias 都必须在 `~/.ssh/config` 中显式定义至少这些字段：
  - `HostName`
  - `User`
  - `Port`
  - `IdentityFile`
  - `IdentitiesOnly yes`
- 需要跳板机时，额外显式定义 `ProxyJump`；不要把跳板逻辑留给 agent 猜测。
- 远程主机的稳定元数据统一登记在 `~/.codex/remote-hosts.md`：
  - alias
  - hostname
  - user
  - port
  - identity_file
  - jump_host
  - default_workdir
  - data_roots
  - services
  - verify_command
  - notes
- 开始任何远程操作前，先读取 `~/.codex/remote-hosts.md`（若存在）和 `ssh -G <alias>` 解析结果，不要先猜用户名、端口、私钥或目录。
- 对带 passphrase 的私钥，要求用户在会话开始前先完成一次解锁，并保证 `ssh-agent` / Keychain 中可用；`AGENTS.md` 可以约束流程，但不能替代解锁动作。

## Remote Failure Policy
- 首次 SSH 认证失败后，禁止继续轮询常见用户名、端口、私钥或路径碰运气。
- 认证失败后，只允许做以下三类排查：
  - `ssh -G <alias>`
  - `ssh-add -l`
  - `ssh -vv <alias> 'true' | tail -80`
- 若日志出现 `Server accepts key ...` 但最终仍为 `Permission denied (publickey)`，直接判定为：
  - 私钥未解锁
  - agent 没有可用 signer
  - `IdentityFile` / `IdentitiesOnly` 配置不一致
- 命中上述情况时，必须停止重试，并明确要求用户：
  - 解锁对应私钥
  - 或提供正确 alias / `User` / `Port` / `IdentityFile`
- 若用户提供的是裸 SSH 命令，先把它规范化为 alias，并建议补录到 `~/.codex/remote-hosts.md` 和 `~/.ssh/config`，避免下次重复试错。

## Layering
- Codex level：本文件，只放跨仓库稳定规则。
- Repo root level：仓库根级 `AGENTS.md`，只放该仓库独有的导航、入口、验证和风险。
- Repo local level：子目录 `AGENTS.md`，只放局部模块约束。
- 更具体的层级可以补充规则，但不能削弱本文件的安全与验证门禁。

## Workflow Hooks
- 开始复杂任务前，先运行 `~/.codex/superpowers/.codex/superpowers-codex bootstrap` 并按需加载相关 skill。
- 复杂任务优先采用：Karpathy -> Planner -> TDD -> Verification 的顺序。
- 新建任何会话时，必须在会话标识、标题或记录中带上当前 repo 的两个字母缩写，并保持同一 repo 内使用一致。
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
