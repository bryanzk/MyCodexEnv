# MyCodexEnv

通过 Git clone + 一条命令在新机器复现 Codex + Claude 双环境工作流。

## 快速开始

```bash
git clone https://github.com/bryanzk/MyCodexEnv.git
cd MyCodexEnv
./bootstrap.sh
```

## 说明

- 目标平台：macOS ARM（Apple Silicon）
- 认证不随仓库迁移；新机器执行 `codex login`
- superpowers 固定版本见 `locks/superpowers.lock`
- bootstrap 会安装固定版本 `chrome-devtools-mcp@0.20.0`；默认关闭 usage statistics 与 performance CrUX URL 查询
- EigenPhi MCP server 默认禁用；`--eigenphi-backend-root` 仅作为兼容旧命令的可选参数保留
- 若本机缺少 Google Chrome，bootstrap 会补装 `google-chrome`
- Codex skills 单一来源：`codex/skills/*`（同步到 `~/.codex/skills/*`），其中 `gstack` 也作为全局 skill 集合由本仓库托管
- Codex 通用层入口源码：`codex/AGENTS.md`（同步到 `~/.codex/AGENTS.md`）
- Codex 远程访问流程规则：`codex/remote-access.md`（同步到 `~/.codex/remote-access.md`）；远程主机登记表：`codex/remote-hosts.md`（同步到 `~/.codex/remote-hosts.md`）
- Codex hooks 来源：`codex/hooks.json` 与 `codex/hooks/*`（同步到 `~/.codex/hooks.json` 与 `~/.codex/hooks/*`）
- Codex harness runtime 来源：`codex/runtime/*`（同步到 `~/.codex/runtime/*`），当前包含阶段化工具权限策略与 evidence schema
- Codex zsh 标题钩子来源：`codex/zsh/*`（同步到 `~/.codex/zsh/*`）
- Codex / Claude workflow 来源分别为 `codex/workflow/*`、`claude/workflow/*`，但都排除 `workflow/memory/` 这类运行态热数据
- Claude workflow 同步到 `~/.claude/workflow/*`，通过注入块挂到 `~/.claude/CLAUDE.md`
- 默认启用 Codex hooks；全局 `SessionStart` hook 会在新会话启动时提醒会话名采用 `<项目缩写>-<YYYYMMDD>-<概要>` 格式
- Harness runtime 默认启用薄 hooks：`PreToolUse` 读取 `tool-policy.json` 做客观 guardrail，`PostToolUse` 尝试把工具事件写入本机 `~/.codex/harness/evidence/*.jsonl`
- 全局 zsh 会话标题钩子默认生成 `<项目缩写>-<YYYYMMDD>-summary`，避免被旧的 `[Repo] zsh` 标题覆盖
- 若 Codex Desktop 在新建会话时对 `~/Documents` 或 `~/Desktop` 报 `EPERM: operation not permitted, mkdir`，优先将会话根目录切到 `~/Codes/Codex` 这类非受保护目录，或在 macOS `隐私与安全性 -> 文件与文件夹 / 完全磁盘访问权限` 中授权 `Codex`

## 全局技能

仓库托管两类全局 Codex skills：

- 本仓库维护的通用 skills，例如 `planner`、`verification-loop`、`thread-topic-guard`、`project-lifecycle-harness`
- 从 `garrytan/gstack` 同步的完整全局 skill 集合，包括 `gstack` 根支持目录和 `gstack-*` namespaced skills

`project-lifecycle-harness` 是通用生命周期路由 skill，只定义跨项目的状态读取、阶段分类、错误处理与验证协议；项目专属路径、命令和安全边界应放在 repo-specific adapter skill 中，例如 `shipq-lifecycle-harness`。

## Harness Runtime

本仓库新增一层 generic Harness Runtime，用来把规则、技能、hooks、验证脚本组织成可恢复、可观测、可验证的运行时系统：

- `docs/repo-index.md`：低 token 项目导航，作为 Codex 开局读取入口
- `docs/harness-state.md`：append-only 状态日志，记录 phase、source of truth、next safe task、latest verification 和 checkpoint
- `docs/HARNESS_RUNTIME.md`：Workflow + Infra 合同，覆盖生命周期、权限、证据、checkpoint 与 subagent team
- `docs/AGENT_HARNESS_STATUS.md`：参照 Agent Harness 架构图维护当前状态图谱
- `codex/runtime/tool-policy.json`：按 `research / requirements / planning / development / validation / review / ship / handoff` 定义工具和权限策略
- `codex/runtime/evidence.schema.json`：本机 evidence JSONL 事件结构
- `scripts/harness_evidence.py`：验证并追加结构化 evidence
- `scripts/harness_report.py`：汇总本机 evidence JSONL，支持 Markdown 与 JSON 输出
- `scripts/harness_agent_team.py`：校验 subagent team 的 role、scope、write set 和 verification contract
- `scripts/harness_checkpoint.py`：追加 `docs/harness-state.md` checkpoint，不自动 commit
- `docs/templates/harness-requirements.md`：Harness 需求 artifact 模板
- `scripts/harness_requirements.py`：校验需求 artifact 的字段、验收标准和验证命令
- `scripts/harness_recover.py`：从 repo index、state、git 和 evidence 恢复 next safe task
- `scripts/harness_env_probe.py`：观测本机 Codex runtime 配置、hooks、policy 和 schema 状态
- `codex/hooks/harness_guard.py`：`PreToolUse` guardrail，处理 destructive、secret、remote、dynamic execution 和越阶段写入
- `codex/hooks/harness_observer.py`：`PostToolUse` observer，非阻塞记录工具事件

运行态证据默认保存在 `~/.codex/harness/evidence/`，不进入 Git。`docs/harness-state.md` 只保存可公开的阶段、验证与 handoff 事实。Memory / subconscious 只能作为提示，行动前必须回查 repo 文件、git 状态或 fresh verification。

生命周期阶段、覆盖流程、对应 skill 和 helper 用途见 `docs/LIFECYCLE_SKILL_ROUTING.md`。中文可视化说明见 `docs/project-lifecycle-harness-flow-cn.html` 和 `docs/project-lifecycle-harness-flow-skills.html`。

相关文档互链入口：

- `docs/repo-index.md`：低 token 项目导航与 runtime surface 索引
- `docs/HARNESS_RUNTIME.md`：生命周期、证据、checkpoint、权限和 subagent 合同
- `docs/AGENT_HARNESS_STATUS.md`：Agent Harness workflow/infra 状态图谱
- `docs/CODEX_ENV_REPRODUCTION.md`：Codex + Claude 环境复现说明
- `docs/LIFECYCLE_SKILL_ROUTING.md`：生命周期阶段、workflow、skill 和 helper 路由
- `docs/project-lifecycle-harness-flow-cn.html`：中文纵向生命周期流程图
- `docs/project-lifecycle-harness-flow-skills.html`：中文 skill/helper 路由可视化速查页

早期已适配的短名 gstack skills 仍保留：

- `plan-ceo-review`
- `plan-eng-review`
- `review`
- `ship`
- `retro`
- `browse`
- `qa`
- `setup-browser-cookies`

完整 gstack 集合使用 namespaced 目录，例如 `gstack-qa`、`gstack-ship`、`gstack-review`、`gstack-design-review`、`gstack-investigate`。它们依赖 `codex/skills/gstack/*` 中的共享支持文件。首次使用需要在同步后执行：

```bash
~/.codex/skills/gstack/setup
```

该 setup 只在 `~/.codex/skills/gstack` 内构建本地支持二进制，不会把 skill 迁移成指向 `/Users/kezheng/gstack` 的本机 symlink。早期短名 `browse` 也带 supporting files，首次使用前可在 `codex/skills/browse` 或同步后的 `~/.codex/skills/browse` 下执行一次 `./setup`。上游来源为 MIT License。

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
- 远程访问运行时规则：`~/.codex/remote-access.md`
- 远程主机运行时登记表：`~/.codex/remote-hosts.md`
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
