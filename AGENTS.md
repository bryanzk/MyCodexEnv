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
- 新建任何会话时，必须在会话标识、标题或记录中带上当前 repo 的两个字母缩写，并保持同一 repo 内使用一致。

## Verification
- 优先运行 `python3 test_runner.py`。
- 修改文档或配置时，确认引用路径、脚本入口和说明一致。

## High-Risk Areas
- `scripts/`: 脚本可能触发批量操作或写入
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
