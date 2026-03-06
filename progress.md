# 多级 AGENTS 管理进度

## 2026-03-06
- 已确认范围：顶层 repo + 真正独立子repo，排除 `.worktrees/*`
- 已确认通用层唯一源码：`codex/AGENTS.md`
- 已确认运行时副本：`~/.codex/AGENTS.md`
- 已确认需要统一备份四层：codex_source / codex_runtime / repo_root / repo_local
- 已新增 `scripts/manage_agents.py`，支持 `scan / backup / generate / restore / verify`
- 已新增 `sync_codex_home.sh --sync-agents-only`
- 已重写 `codex/AGENTS.md` 为 Codex 通用层
- 已扩展 `verify_codex_env.sh` 的 AGENTS 结构与一致性检查
- 已创建备份批次：`20260306141411`
- 已对真实工作区生成/补齐 21 个缺失的根级 `AGENTS.md`
- 已补齐 `manage_agents.py verify` 的路径引用与命令来源校验
- 已补齐 `backup_id` 防覆盖与 `report.md` 保留策略
- 已完成全量验证、代码审查与证据归档
