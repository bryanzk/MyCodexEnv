# 多级 AGENTS 管理发现记录

- `codex/AGENTS.md` 当前同时承担通用层与 repo-specific 入口，需收缩为纯 Codex 通用层。
- `scripts/sync_codex_home.sh` 当前会同步 `codex/AGENTS.md` 到 `~/.codex/AGENTS.md`，但不会备份 `~/.codex/AGENTS.md`。
- `scripts/verify_codex_env.sh` 当前仅验证 `~/.codex/AGENTS.md` 存在和 gate 文案存在，未校验结构和源码/runtime 一致性。
- `/Users/kezheng/Codes/CursorDeveloper` 下存在 symlink repo（`eigen-cli-arb-mvp` -> `eigenphi-cli-arb-mvp`），扫描时需要按 realpath 去重。
- 若干 repo 只有局部 `AGENTS.md`，例如 `symphony/elixir/AGENTS.md`、`email-to-git-worker/email-to-git/AGENTS.md`、`MEVAL/eigenphi-backend-go/AGENTS.md`。
- 顶层 repo 至少 22 个，文档完整度差异大，生成逻辑必须支持 minimal 模式。
- `backup` 需要禁止覆盖已有 `backup_id`，否则无法保证快照可回退。
- `generate` 需要保留备份报告而不是覆盖 `report.md`，否则会丢失快照层证据。
- `verify` 除了检查结构外，还需要校验生成文件中的路径引用和命令来源，否则无法发现导航漂移。
