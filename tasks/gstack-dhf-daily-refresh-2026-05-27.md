# Gstack & DHF Daily Refresh - 2026-05-27

## 结果概览

- 状态：ready / changed
- 仓库：`/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/repo`
- 当前基线 commit：`208fe13`
- 本地 vendored gstack 旧版本：`1.45.0.0`
- 上游 gstack 新版本：`1.48.0.0`
- gstack 同步：已执行实际同步；本轮新增 `/spec` specialized workflow、5+ 选项 AskUserQuestion split 规则、plan-mode `GSTACK_PLAN_MODE` 提示、以及 `/ship` 的 linked spec 关闭链路
- DHF skill 调整：已执行最小补丁，新增 backlog/spec authoring 路由，并同步 eval/test/doc
- repo 改动：同步 `codex/skills/gstack/*`，更新 `delivery-harness-framework`、`docs/LIFECYCLE_SKILL_ROUTING.md`、`test_runner.py`，新增今日日报，并在 `docs/harness-state.md` 追加 append-only checkpoint

## prepare 结论

- `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json` 返回 `status=ready`
- standalone clone：`/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/repo`
- `dry_run.needs_update=true`、`diff_files=118`
- 因此按规则执行：
  - `python3 scripts/sync_gstack_vendor.py --repo-root "$(pwd)" --source https://github.com/garrytan/gstack.git --json`

## 上游差异摘要

- `codex/skills/gstack/VERSION` 从 `1.45.0.0` 升级到 `1.48.0.0`
- 新增 vendored gstack `spec` skill，用于把模糊意图整理成 backlog-ready issue / executable spec，并与 `/ship` 的 issue auto-close 流程联动
- gstack preamble 新增 “5+ 选项不得静默裁剪” 规则：
  - 当 AskUserQuestion 遇到 5+ 真实选项时，必须 split 或 batch，而不是自己砍掉一个选项
  - runtime checker 会阻止 `*-split-*` 的 AUTO_DECIDE 偏好，确保这类问题继续显式询问
- gstack preamble 新增 `GSTACK_PLAN_MODE` 提示，供 `/spec` 等 workflow 在 plan-mode 与 execute-mode 间切换行为
- `/ship` 新增 linked spec 段：当当前分支对应 `/spec` archive 且 plan-completion 完整时，会在 PR body 自动写入 `Closes #N`

## skill-evaluator 结论

- Existence verdict：`delivery-harness-framework` 仍然必须存在；上游新增的是 specialized workflow，不是 repo README 或一条全局提示就能稳定替代的 generic 生命周期边界判断
- Routing review：
  - 这次不再是纯 no-op
  - 原 DHF 只有 requirements / planning / implementation 等泛化阶段，但没有显式处理“先把模糊请求沉淀成 backlog-ready spec/issue，再开始实施”的 specialized route
  - 随着 vendored gstack `spec` 成为正式 workflow，DHF 需要新增一条 backlog/spec authoring 路由，避免把这类请求模糊落到 requirements 或 engineering planning
- Progressive-loading findings：
  - `delivery-harness-framework` 不需要读取新的 accessory 文件；仍应先读 durable state / requirements context，再把该类请求交给 vendored gstack `spec`
  - 现有 `scripts/harness_requirements.py`、`scripts/harness_recover.py` progressive-loading 规则保持不变
- End-to-end findings：
  - 已补 `routing-positive-backlog-spec-authoring` eval case
  - 已补 `test_runner.py` 对 `vendored gstack \`spec\`` 路由与新 positive eval id 的断言
  - 已同步 `docs/LIFECYCLE_SKILL_ROUTING.md`，让 runtime 文档与 skill 行为一致

## 本轮修正

- `codex/skills/delivery-harness-framework/SKILL.md`
  - 在 lifecycle ownership 中显式声明 gstack 负责 backlog-ready spec / issue authoring
  - 在 stage classifier 中新增 `Backlog/spec authoring` 路由，交给 vendored gstack `spec`
- `codex/skills/delivery-harness-framework/evals/evals.json`
  - 新增 `routing-positive-backlog-spec-authoring`
- `test_runner.py`
  - 新增对 `vendored gstack \`spec\`` 路由和新 eval id 的回归断言
- `docs/LIFECYCLE_SKILL_ROUTING.md`
  - 新增 backlog-ready issue/spec authoring workflow、specialist map 与 routing rule 说明
- 同步引入的格式噪音最小清理：
  - 去掉 `codex/skills/gstack/plan-tune/SKILL.md` 一处 trailing whitespace
  - 去掉 `codex/skills/gstack/test/gstack-developer-profile.test.ts` 末尾空白行

## 运行时说明

- `./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex"` 已执行，用于把 repo managed skills 同步到 runtime
- `export PATH="$HOME/.bun/bin:$PATH" && ~/.codex/skills/gstack/setup` 已执行，重新生成并链接最新 gstack skill
- `verify_codex_env.sh` 在同步完成前短暂出现过一次 `FAIL:skills_managed_present`，随后复核发现 runtime 已包含 `.system`，重跑通过；未形成持续 blocker

## 本轮验证结果

1. `python3 test_runner.py`
   - exit_code: `0`
   - key_output: `[PASS] all tests`
   - timestamp: `2026-05-27T13:16:35Z`
2. `git diff --check`
   - exit_code: `0`
   - key_output: `无输出`
   - timestamp: `2026-05-27T13:14:45Z`
3. `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`
   - exit_code: `0`
   - key_output: `Verification passed.`
   - timestamp: `2026-05-27T13:14:52Z`

## 下一次最小自动动作

- 下一轮 daily refresh 仍先执行：
  - `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json`
- 若上游继续扩展 gstack specialized workflow，优先检查是否出现新的 generic lifecycle 边界；没有则维持 DHF no-op，只更新 report / memory
