# Gstack & DHF Daily Refresh - 2026-05-29

## 结果概览

- 状态：ready / changed / DHF adjusted
- 仓库：`/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- 当前工作基线：`f0c2d63 Add ShipQ DHF prompt hook coverage`，已 merge 最新 `origin/main`
- 本地 vendored gstack 旧版本：`1.45.0.0`，远端早间自动化已到 `1.52.0.0`
- 上游 gstack 新版本：`1.52.1.0`
- gstack 同步：已执行实际同步，并同步到 `~/.codex/skills/gstack`
- DHF skill 调整：需要调整，已完成
- 核心判断：gstack `1.52.1.0` 引入 brain-aware planning；gstack `1.52.0.0` 已引入 plan-tune 问题偏好治理。这不是新的 DHF lifecycle stage，也不是 DHF 的新持久状态源。DHF 应明确把 gbrain preflight 留给 gstack planning skills，把 `gstack-plan-tune` 留给操作者偏好治理。

## prepare 结论

- 沙箱内首次 `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json` 返回 `status=deferred`，原因是 `github.com` DNS 不可达。
- 授权网络后重跑返回 `status=ready`。
- standalone clone：`/Users/kezheng/.codex/automations/gstack-dhf-daily-refresh/repo`
- `dry_run.needs_update=true`、`diff_files=46`、上游版本 `1.52.1.0`
- 当前 repo dry-run 返回 `needs_update=true`、`diff_files=199`
- 因此执行：
  - `python3 scripts/sync_gstack_vendor.py --repo-root /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv --source https://github.com/garrytan/gstack.git --json`

## 上游差异摘要

- `codex/skills/gstack/VERSION` 升级到 `1.52.1.0`
- gstack `1.52.1.0` 重点引入 brain-aware planning：
  - `office-hours`
  - `plan-ceo-review`
  - `plan-eng-review`
  - `plan-design-review`
  - `plan-devex-review`
- 上述 planning skills 可在 gbrain 已配置时读取缓存摘要：`product`、`goal`、`developer-persona`、`brand`、`competitive-intel`、`skill-run`、`user-profile`、`take`
- gstack `1.52.0.0` 重点增强 `plan-tune`：
  - 问题偏好 capture/enforcement hooks
  - developer profile 相关信号
  - free-text answer memory/distill 流程
- 上游新增多组 brain/cache/schema/plan-tune 相关脚本、测试、docs 与 host adapter 文件

## DHF 调整

### 已更新 skill

- `codex/skills/delivery-harness-framework/SKILL.md`
  - 在 lifecycle ownership 中加入：
    - brain-aware planning preflight 属于 gstack planning skills
    - question-tuning preferences 属于 gstack
  - 保留远端新增的 backlog/spec authoring route，并明确它仍委托 vendored gstack `spec`
  - 在 Product / Engineering / Design planning 路由中加入：
    - gbrain 已配置时由 delegated gstack planning skill 使用
    - DHF 仍只负责 repo state、lane、checkpoint、verification 边界
  - 在 Handoff/learning 路由中加入：
    - `gstack-plan-tune` 仅用于用户明确要求调重复问题、developer profile 或 question preferences
    - `setup-gbrain` / `sync-gbrain` 仍只在用户明确要求 gbrain setup / repo re-indexing 时使用

### 已更新 eval

- `codex/skills/delivery-harness-framework/evals/evals.json`
  - 新增正例：`planning-positive-brain-aware-boundary`
  - 新增负例：`routing-negative-plan-tune`
  - 新增负例：`routing-negative-gbrain-setup`
- `test_runner.py`
  - 增加对上述 routing/eval 边界的回归断言

### 已更新文档

- `README.md`
- `docs/repo-index.md`
- `docs/LIFECYCLE_SKILL_ROUTING.md`
- `docs/dhf-workflow-skills-cn.html`
- `docs/dhf-workflow-skills-en.html`
- `docs/project-lifecycle-harness-flow-skills-zh-status-style.html`
- `docs/project-lifecycle-harness-flow-skills-en-status-style.html`
- `docs/harness-state.md`

## skill-evaluator 结论

- Existence verdict：`delivery-harness-framework` 仍然应该存在。gstack 1.52.x 增强了 planning skill 内部上下文读取能力，但没有替代 DHF 的跨仓库 state recovery、phase/lane classification、dirty worktree ownership、checkpoint 和 evidence gate。
- Routing review：
  - 正确路由：复杂/恢复中的工程规划先加载 DHF，读取 repo state 后委托 `gstack-plan-eng-review`，gbrain preflight 由该 planning skill 自行处理。
  - 负例边界：`stop asking me that` / developer profile / repeated question tuning 应路由到 `gstack-plan-tune`，不应触发 DHF。
  - 负例边界：显式 gbrain setup / sync / repo re-indexing 应路由到 `setup-gbrain` / `sync-gbrain`，不应由 DHF 直接处理。
- Eval plan：
  - 路由正例覆盖 brain-aware planning delegation。
  - 路由负例覆盖 plan-tune 与 gbrain setup。
  - 现有 progressive-loading eval 继续覆盖 `harness_recover.py` 与 `harness_requirements.py`。
  - 现有 end-to-end eval 继续覆盖 external capture promotion 和 deployment readiness。
- Evidence summary：
  - 已更新 eval matrix，并由 `test_runner.py` 校验结构和关键边界。
  - `npx agent-skills-eval ... --baseline --strict` 已尝试运行，但当前环境没有 `OPENAI_BASE_URL` / `OPENAI_API_KEY`，远程 judge 路径不可用。
  - 本轮采用手工 paired evaluation + deterministic repo regression：对比 without-boundary 风险与 with-boundary 期望，并用新增 eval/test 保护后续 drift。

## 手工 paired evaluation

| Case | without boundary risk | with updated DHF behavior | Result |
| --- | --- | --- | --- |
| 复杂工程规划 + 已配置 gbrain | 可能把 gbrain 当成 DHF 直接状态源，跳过 repo state / lane / checkpoint | 先恢复 repo state，再委托 `gstack-plan-eng-review`；gbrain 只作为 planning skill 专用上下文 | pass |
| "stop asking me that" / developer profile | 可能误走 handoff/learning 或 generic recovery | 路由到 `gstack-plan-tune`，不触发 repo checkpoint | pass |
| 显式 gbrain setup / repo re-indexing | 可能误认为 DHF memory refresh | 路由到 `setup-gbrain` / `sync-gbrain`，DHF 保持 repo state 边界 | pass |

## 运行时说明

- `./scripts/sync_codex_home.sh ... --skip-superpowers-sync` 首次因沙箱不能写 `~/.codex` 失败，授权后成功。
- `~/.codex/skills/gstack/setup` 首次因沙箱不能创建 `node_modules` 失败，授权后成功，输出 `gstack ready (claude).`
- setup 报告 `gbrain not detected`，因此 brain-aware blocks 在当前运行态被抑制；这符合上游设计，不是失败。
- setup 报告 plan-tune hooks 未在 non-interactive setup 中安装；这是可选 hook 安装提示，不阻断本轮 sync。
- `git diff --check` 首次发现上游同步带来的两个 whitespace 问题，已做最小修正并重跑通过。
- merge 最新 `origin/main` 时保留了远端 5/27 backlog/spec authoring route、5/28 no-op report、5/29 早间 `1.52.0.0` no-op checkpoint，并在其后追加本轮 `1.52.1.0` DHF adjusted checkpoint。

## 本轮验证结果

1. `python3 -m json.tool codex/skills/delivery-harness-framework/evals/evals.json >/tmp/dhf-evals.json`
   - exit_code: `0`
   - key_output: JSON parsed
   - timestamp: `2026-05-29T20:11:00Z`
2. `npx agent-skills-eval codex/skills --include 'delivery-harness-framework/**' --target gpt-4o-mini --judge gpt-4o-mini --baseline --strict`
   - exit_code: `1`
   - key_output: `error: provide --base-url or set OPENAI_BASE_URL`
   - timestamp: `2026-05-29T20:10:00Z`
3. `git diff --check`
   - exit_code: `0`
   - key_output: `无输出`
   - timestamp: `2026-05-29T20:30:20Z`
4. `python3 test_runner.py`
   - exit_code: `0`
   - key_output: `[PASS] all tests`
   - timestamp: `2026-05-29T20:30:20Z`
5. `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`
   - exit_code: `0`
   - key_output: `Verification passed.`
   - timestamp: `2026-05-29T20:29:54Z`
6. `./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --skip-superpowers-sync`
   - exit_code: `0`
   - key_output: `Skipping superpowers sync by request.`
   - timestamp: `2026-05-29T20:29:54Z`

## 下一次最小自动动作

- 下一轮 daily refresh 仍先执行：
  - `python3 scripts/prepare_gstack_dhf_daily_refresh.py --json`
- 若上游只改变 specialized workflow 内部实现，继续记录 DHF no-op。
- 若上游新增 cross-repo lifecycle boundary、new execution lane、generic state source、checkpoint/evidence surface，必须同步更新：
  - `delivery-harness-framework`
  - `evals/evals.json`
  - `docs/LIFECYCLE_SKILL_ROUTING.md`
  - public workflow skill docs
  - `test_runner.py`
