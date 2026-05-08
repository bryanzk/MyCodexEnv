# Remote Access Policy

## Purpose
- 本文件是 Codex 远程访问流程规则的唯一源码。
- 它只定义 SSH、remote host、tunnel 和认证失败处理规则，不记录具体主机清单。
- 具体主机元数据登记在 `~/.codex/remote-hosts.md`，不得在本文件保存密码、passphrase、token 或私钥内容。

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
- 对带 passphrase 的私钥，要求用户在会话开始前先完成一次解锁，并保证 `ssh-agent` / Keychain 中可用；本规则可以约束流程，但不能替代解锁动作。

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
