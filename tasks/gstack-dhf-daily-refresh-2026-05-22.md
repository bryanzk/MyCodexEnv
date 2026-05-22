# Gstack & DHF Daily Refresh - 2026-05-22

## 结果概览

- 状态：ready / changed
- 仓库：`/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/repo`
- 当前基线 commit：`b5276514e3abeb8b248316e0ab2b7560c38b1187`
- 本地 vendored gstack 旧版本：`1.42.2.0`
- 上游 gstack 新版本：`1.43.3.0`
- gstack 同步：已执行实际同步；本轮引入上游 iOS/device skill、gbrain/ship/review 路由增强，以及 browse/server 生命周期修复
- DHF skill 调整：changed
- 额外修复：将 `scripts/verify_codex_env.sh` 与 `scripts/install_prereqs.sh` 的 Codex CLI 版本白名单扩展到 `0.133.0`，消除当前 `codex-cli 0.133.0-alpha.1` 的假失败
- runtime 修复：安装 `bun 1.3.14`，同步 `~/.codex` 后成功执行 `~/.codex/skills/gstack/setup`

## 上游差异摘要

- 新增整套 iOS workflow：`gstack-ios-qa`、`gstack-ios-design-review`、`gstack-ios-fix`、`ios-sync`、`ios-clean`
- `browse/src/server.ts` 与相关测试补上 dual-instance / headed Chromium 生命周期修复，避免 embedder 场景 30 分钟 idle 后误自杀
- gbrain / ship / review / retro / cso / land-and-deploy 等 skill 文本与支撑脚本继续演进，repo 内 vendored snapshot 已整体更新到 `1.43.3.0`

## skill-evaluator 结论

- Existence verdict：`delivery-harness-framework` 仍然必须存在；它承载跨仓库 durable state 恢复、生命周期分类、generic vs repo-specific vs gstack 边界和 evidence gate，不是普通 prompt tweak 能稳定替代的
- Routing findings：本轮上游新增 live-device iOS workflow 后，generic DHF 原文只写 browser QA，存在漏路由风险；已补到 `QA/browser/device`，明确把真机 iOS QA / design review / fix 导向 gstack skill，而不是 generic harness
- Progressive-loading findings：runtime helper 仍然只在命中 requirements / recovery / env-probe / checkpoint 等条件时加载；本轮没有把 iOS 细节硬编码进 generic skill，只补了路由边界
- End-to-end findings：新增 `routing-negative-ios-qa` eval，并在 `test_runner.py` 中把 `gstack-ios-qa`、`gstack-ios-design-review`、`gstack-ios-fix` 变成强制回归项，避免后续 router 再次忽略 iOS/device 路由
- Next edits：none

## 本轮 repo 侧改动

- 同步 vendored gstack 快照到 `1.43.3.0`
- 更新 `codex/skills/delivery-harness-framework/SKILL.md`
  - 将 QA 阶段扩展为 `QA/browser/device`
  - 明确 `gstack-ios-qa`、`gstack-ios-design-review`、`gstack-ios-fix`、`ios-sync`、`ios-clean` 的路由边界
- 更新 `codex/skills/delivery-harness-framework/evals/evals.json`
  - 新增 live-device iOS QA 负例路由用例
- 更新 `docs/LIFECYCLE_SKILL_ROUTING.md` 与 `README.md`
  - 同步新增 iOS namespaced skills 与 richer upstream routing posture
- 更新 `scripts/verify_codex_env.sh`、`scripts/install_prereqs.sh`、`test_runner.py`
  - 放行 `codex-cli 0.133.0-alpha.1`

## 运行时附加检查

- 问题：`~/.codex/skills/gstack/setup` 初次执行失败，原因为本机缺少 `bun`
- 处理：下载并审查 bun 官方安装脚本后执行安装，安装结果为 `bun 1.3.14`
- 结果：补齐 `PATH` 后重跑 `~/.codex/skills/gstack/setup` 成功，runtime gstack supporting files 已重建

## 本轮验证结果

1. `export PATH="$HOME/.bun/bin:$PATH" && ~/.codex/skills/gstack/setup`
   - exit_code: `0`
   - key_output: `gstack ready (claude).`
   - timestamp: `2026-05-22T13:07:19Z`
2. `python3 test_runner.py`
   - exit_code: `0`
   - key_output: `[PASS] all tests`
   - timestamp: `2026-05-22T13:07:19Z`
3. `git diff --check`
   - exit_code: `0`
   - key_output: `无输出`
   - timestamp: `2026-05-22T13:07:19Z`
4. `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`
   - exit_code: `0`
   - key_output: `Verification passed.`
   - timestamp: `2026-05-22T13:07:19Z`

## 下一次最小自动动作

- 下一轮 daily refresh 仍先执行：
  - `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json`
- 若上游继续扩充非 browser 的 specialized workflow，优先检查 `delivery-harness-framework` 与 `docs/LIFECYCLE_SKILL_ROUTING.md` 是否还保持正确 ownership 边界
