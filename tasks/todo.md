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

# TODO - Claude-Code-Workflow × Codex 双环境整合

## 任务拆解
- [x] P0.1 冻结上游 `claude-code-workflow` 版本并建立 `vendor/` 只读镜像
- [x] P0.2 生成双端规则映射文档（上游规则/技能 -> 本地落点）
- [x] P1.1 将“无证据不宣称完成”门禁写入 Codex 与 Claude 主入口
- [x] P1.2 建立验证证据接口（command/exit_code/key_output/timestamp）与检查清单
- [x] P2.1 接入 planning + routing 规则（关键逻辑/常规/低风险）
- [x] P2.2 固化触发词与禁用词，避免任务路由漂移
- [x] P3.1 接入 memory-flush + session-end，并定义四类写回顺序
- [x] P3.2 增加 Exit Signal 自动收尾触发
- [x] P4.1 实现第三方 skill/MCP 安全扫描脚本与规则接入
- [x] P4.2 实现每周规则健康检查脚本
- [x] V1 更新 bootstrap/sync/verify/test_runner 文档并执行回归验证

## 依赖关系
- P0.1 -> P0.2
- P0.* -> P1.* -> P2.* -> P3.* -> P4.*
- V1 依赖 P0~P4 全部完成

## 验收标准
- 存在明确上游 commit/回滚点，且 vendor 内容可追溯
- Claude/Codex 双端均具备 P0 门禁与触发契约
- 复杂任务存在文件化计划规范；路由决策可解释
- today/projects/goals/active-tasks 四类写回路径明确且可验证
- 第三方 skill 扫描可拦截 URL/上传/动态执行/破坏性命令红旗
- 健康检查可发现规则冲突/冗余/失效触发器
- 自动化验证命令通过并在 `TEST_VERIFICATION.md` 留存证据
