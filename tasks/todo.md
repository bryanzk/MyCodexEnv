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

# TODO - 构建常用文本自动分类记录器

## 任务拆解
- [x] 定义自动分类标准（command/prompt/dialogue/other）与落盘格式
- [x] 实现记录脚本 `scripts/capture_text.py`（支持 auto 分类与手动覆盖）
- [x] 补充回归测试并挂载到 `test_runner.py`
- [x] 更新说明文档（README + 使用说明）与本地忽略配置

## 依赖关系
- 记录脚本实现依赖分类规则定义
- 测试依赖于记录脚本可执行
- 文档和 `.gitignore` 更新依赖脚本完成

## 验收标准
- 输入命令时默认分类为 `command`
- 输入提示类文本时默认分类为 `prompt`
- 输入对话类文本时默认分类为 `dialogue`
- 分类结果和原文同时落盘（`ledger.jsonl` + 分类目录）
- `python test_runner.py` 中新增测试全部通过，且包含新功能用例
