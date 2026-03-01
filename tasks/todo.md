# TODO - 清理顶层 arscontexta 冗余目录

## 任务拆解
- [x] T1 识别并确认待删除范围：仅顶层 `arscontexta*` 目录，不触碰 `codex/skills/*`
- [x] T2 删除顶层 `arscontexta*` 目录
- [x] T3 更新文档，明确仓库唯一生效 skill 来源为 `codex/skills/*`
- [x] T4 运行验证（路径存在性、脚本引用、差集检查）

## 依赖关系
- T2 依赖 T1
- T3 依赖 T2
- T4 依赖 T2、T3

## 验收标准
- 顶层不存在 `arscontexta*` 目录
- `codex/skills/arscontexta*` 目录保持完整
- `scripts/sync_codex_home.sh`、`docs/CODEX_ENV_REPRODUCTION.md` 与 README 表述一致且不误导
- 验证命令通过并可提供日志证据
