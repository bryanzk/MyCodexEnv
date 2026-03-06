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
- Codex 通用层 `AGENTS.md` 唯一源码：`codex/AGENTS.md`（同步到 `~/.codex/AGENTS.md`）
- Claude workflow 来源：`claude/workflow/*`（同步到 `~/.claude/workflow/*`，通过注入块挂到 `~/.claude/CLAUDE.md`）

## 多仓库 AGENTS 管理

如果你需要为 `/Users/kezheng/Codes/CursorDeveloper` 下多个 repo 批量扫描、备份、生成、恢复与校验 `AGENTS.md`，使用：

```bash
python3 scripts/manage_agents.py scan
python3 scripts/manage_agents.py backup --backup-id "$(date +%Y%m%d%H%M%S)"
python3 scripts/manage_agents.py generate --backup-id "<backup_id>"
python3 scripts/manage_agents.py verify
```

- 统一备份目录：`/Users/kezheng/Codes/CursorDeveloper/.agents-backups/`
- 运行时 Codex 通用层副本：`~/.codex/AGENTS.md`
- 若只需同步 Codex 通用层到本机运行时：

```bash
./scripts/sync_codex_home.sh --repo-root "$(pwd)" --sync-agents-only
```

## 常用文本记录

如果你需要记录命令、提示、对话等文本，可直接使用：

```bash
python scripts/capture_text.py "要记录的文本"
```

分类规则与输出目录见 `docs/USAGE_TEXT_RECORDING.md`。

详细说明见：`docs/CODEX_ENV_REPRODUCTION.md`
