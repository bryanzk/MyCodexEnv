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
- bootstrap 会安装固定版本 `chrome-devtools-mcp@0.20.0`；默认关闭 usage statistics 与 performance CrUX URL 查询
- 若本机缺少 Google Chrome，bootstrap 会补装 `google-chrome`
- Codex skills 单一来源：`codex/skills/*`（同步到 `~/.codex/skills/*`）
- Codex 通用层 `AGENTS.md` 唯一源码：`codex/AGENTS.md`（同步到 `~/.codex/AGENTS.md`）
- Codex hooks 来源：`codex/hooks.json` 与 `codex/hooks/*`（同步到 `~/.codex/hooks.json` 与 `~/.codex/hooks/*`）
- Codex zsh 标题钩子来源：`codex/zsh/*`（同步到 `~/.codex/zsh/*`）
- Codex / Claude workflow 来源分别为 `codex/workflow/*`、`claude/workflow/*`，但都排除 `workflow/memory/` 这类运行态热数据
- Claude workflow 同步到 `~/.claude/workflow/*`，通过注入块挂到 `~/.claude/CLAUDE.md`
- 默认启用 Codex hooks；全局 `SessionStart` hook 会在新会话启动时提醒会话名采用 `<项目缩写>-<YYYYMMDD>-<概要>` 格式
- 全局 zsh 会话标题钩子默认生成 `<项目缩写>-<YYYYMMDD>-summary`，避免被旧的 `[Repo] zsh` 标题覆盖

## 新增技能

已合并一组从 `garrytan/gstack` 适配过来的 Codex skills：

- `plan-ceo-review`
- `plan-eng-review`
- `review`
- `ship`
- `retro`
- `browse`
- `qa`
- `setup-browser-cookies`

其中 `browse` 是带 supporting files 的本地浏览器自动化 skill，首次使用前需在 `codex/skills/browse` 或同步后的 `~/.codex/skills/browse` 下执行一次 `./setup`。源码适配版保留在仓库 `codex/skills/*`，上游来源为 MIT License，许可证副本位于 `codex/skills/browse/LICENSE.gstack`。

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

## Codex Subconscious

仓库内新增一个轻量级 Codex companion 原型：`scripts/codex_subconscious.py`。

它会读取本机 `~/.codex/archived_sessions/*.jsonl` 与 `~/.codex/session_index.jsonl`，构建：
- `~/.codex/subconscious/index.json`
- `~/.codex/subconscious/memory.md`
- `~/.codex/subconscious/briefs/*.md`

常用命令：

```bash
python3 scripts/codex_subconscious.py build --emit-briefs
python3 scripts/codex_subconscious.py brief --cwd /absolute/project/path
python3 scripts/codex_subconscious.py publish-inbox --cwd /absolute/project/path
python3 scripts/codex_subconscious.py publish-inbox --limit 3
python3 scripts/codex_subconscious.py publish-inbox --limit 3 --dedupe-hours 8
```

背景说明与 automation 接法见：`docs/CODEX_SUBCONSCIOUS.md`
