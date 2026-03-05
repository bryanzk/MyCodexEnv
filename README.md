# MyCodexEnv

通过 Git clone + 一条命令在新机器复现 Codex + Claude 双环境工作流。

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
- Codex skills 单一来源：`codex/skills/*`（同步到 `~/.codex/skills/*`）
- Claude workflow 来源：`claude/workflow/*`（同步到 `~/.claude/workflow/*`，通过注入块挂到 `~/.claude/CLAUDE.md`）

## 常用文本记录

如果你需要记录命令、提示、对话等文本，可直接使用：

```bash
python scripts/capture_text.py "要记录的文本"
```

分类规则与输出目录见 `docs/USAGE_TEXT_RECORDING.md`。

详细说明见：`docs/CODEX_ENV_REPRODUCTION.md`
