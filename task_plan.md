# 多级 AGENTS 管理任务计划

## Goal
- 为 `/Users/kezheng/Codes/CursorDeveloper` 下目标仓库实现多级 `AGENTS.md` 的扫描、备份、生成、恢复与校验。
- 将通用层唯一源码固定在 `codex/AGENTS.md`，并输出到 `~/.codex/AGENTS.md`。

## Acceptance Criteria
- 存在统一管理脚本，支持 `scan`、`backup`、`generate`、`restore`、`verify`。
- 备份目录落在 `/Users/kezheng/Codes/CursorDeveloper/.agents-backups/<backup_id>/`，包含 `manifest.json`、`entries/`、`report.md`。
- 生成后，目标 repo 均存在根级 `AGENTS.md`；已有局部 `AGENTS.md` 保留。
- `codex/AGENTS.md` 被重写为通用 Codex 层规则，且与 `~/.codex/AGENTS.md` 可同步一致。
- `scripts/verify_codex_env.sh` 能检查 `AGENTS.md` 一致性与关键结构，而不只是关键词存在。
- 自动化测试覆盖扫描、备份、生成、恢复与校验主路径。

## Phases
1. [x] 建立任务记录与测试清单
2. [x] 实现 `scripts/manage_agents.py`
3. [x] 重写 `codex/AGENTS.md` 并扩展 `verify_codex_env.sh`
4. [x] 运行脚本生成/备份/校验实际仓库
5. [x] 回归测试、代码审查、记录证据
