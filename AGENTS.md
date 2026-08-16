# MyCodexEnv

通过 Git clone 和一个 bootstrap 命令，在 Apple Silicon Mac 上复现可审查、可同步、可验证的 Codex 与 Claude 工作环境。

## Command

- Final repository gate: `python3 test_runner.py`; it is not an iteration gate. Select scoped gates and receipt validity through [Verification and change safety](docs/agents/verification-and-change-safety.md).

## Task-specific guidance

只读取与当前任务相关的指南：

- [Repository navigation and sources of truth](docs/agents/repository.md)
- [Runtime and skill changes](docs/agents/runtime-and-skills.md)
- [Verification and change safety](docs/agents/verification-and-change-safety.md)
- Changes under `codex/`: [Codex global rules source](codex/AGENTS.md)
- Changes under vendored gstack: [gstack local rules](codex/skills/gstack/AGENTS.md)
