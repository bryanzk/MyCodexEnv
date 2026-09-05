# MyCodexEnv

通过 Git clone 和一个 bootstrap 命令，在 Apple Silicon Mac 上复现可审查、可同步、可验证的 Codex 与 Claude 工作环境。

## Command

- Final repository gate: `python3 test_runner.py`; it is not an iteration gate. Select scoped gates and receipt validity through [Verification and change safety](docs/agents/verification-and-change-safety.md).

## Task-specific guidance

只读取与当前任务相关的指南：

- 不熟悉仓库或需要查找权威入口时：[Repository navigation and sources of truth](docs/agents/repository.md)
- 修改 runtime、配置或 skills 时：[Runtime and skill changes](docs/agents/runtime-and-skills.md)
- 选择验证入口或判断证据是否仍有效时：[Verification and change safety](docs/agents/verification-and-change-safety.md)
- Changes under `codex/`: [Codex global rules source](codex/AGENTS.md)
- Changes under vendored gstack: [gstack local rules](codex/skills/gstack/AGENTS.md)
