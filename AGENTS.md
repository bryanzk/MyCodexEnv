<!-- generated-by: manage_agents.py -->
# MyCodexEnv

## Purpose
- 通过 Git clone + 一条命令在新机器复现 Codex + Claude 双环境工作流。
- 本文件只描述当前仓库的导航信息；通用 Codex 规则由上层环境提供。

## Read First
- `README.md`
- `docs/`
- 局部目录含专用 `AGENTS.md`，任务落入对应子目录时继续下钻。

## Repo Map
- `scripts/`: 脚本与运维入口
- `docs/`: 说明文档与设计记录
- `tasks/`: 任务与运行记录

## Source Of Truth
- 仓库缺少标准 manifest；请以 README、脚本和测试目录为准。
- `codex/AGENTS.md`

## Common Workflows
- 先阅读 README 或脚本目录，再执行与本仓库匹配的最小验证命令。
- 处理 Codex runtime、skill 同步或全局配置时，先确认 `git status` 和目标来源；`codex/skills/*` 是托管 skill 的 repo source-of-truth，运行时副本再通过脚本或明确的定向复制同步。
- 安装或新增 skill 时，按用户给出的安装/创建入口执行，随后验证新增 `SKILL.md` frontmatter、运行 repo gate；复杂 skill 评审优先使用 `skill-evaluator` 与 `committee-review-loop`。
- 处理 DHF/helper/runtime evidence 改动时，按 helper 读写边界逐步推进；代码和测试 green 后，同步更新 `docs/HARNESS_RUNTIME.md`、`docs/repo-index.md`、`docs/CODEX_ENV_REPRODUCTION.md` 中的相关说明。

## Verification
- 优先运行 `python3 test_runner.py`。
- 修改文档或配置时，确认引用路径、脚本入口和说明一致。
- 修改 Codex runtime/config 同步逻辑后，补充运行 `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`；涉及插件或 MCP 状态时同时检查 `codex plugin list` 和 `codex mcp list`。

## High-Risk Areas
- `scripts/`: 脚本可能触发批量操作或写入
- `scripts/sync_codex_home.sh`、`codex/skills/`、`~/.codex/config.toml`、`~/.codex/skills/`: 可能影响本机 Codex runtime、插件/MCP 状态或个人 skill；避免 broad mirror / `--delete`，优先定向同步和验证。
- Codex state / maintenance 任务默认 report-only；除非用户明确授权，不删除、归档、移动、清理 worktree、session 或本地状态。
- 局部 `AGENTS.md` 对应的子目录通常有额外规则，改动前先下钻阅读。

## Change Rules
- 不要在本文件复制通用 Codex 规则；只保留仓库特有约束。
- 变更入口命令、目录结构或对外接口时，同步更新 README、docs 和相关测试。
- 若任务仅落在某个局部目录，先阅读该目录下的 `AGENTS.md` 再修改。

## When To Ask
- 需要改变公开接口、部署方式、配置默认值或数据格式时。
- 需要删除目录、重命名关键文件或绕过现有验证入口时。

## Subdirectory AGENTS
- `codex/AGENTS.md`
