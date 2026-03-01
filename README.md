# MyCodexEnv

通过 Git clone + 一条命令在新机器复现 Codex 工作环境。

## 快速开始

```bash
git clone https://github.com/bryanzk/MyCodexEnv.git
cd MyCodexEnv
./bootstrap.sh --eigenphi-backend-root /absolute/path/to/eigenphi-backend-go
```

## 说明

- 目标平台：macOS ARM（Apple Silicon）
- 认证不随仓库迁移；新机器执行 `codex login`
- superpowers 固定版本见 `locks/superpowers.lock`
- skills 单一来源：`codex/skills/*`（同步到 `~/.codex/skills/*`）

详细说明见：`docs/CODEX_ENV_REPRODUCTION.md`
