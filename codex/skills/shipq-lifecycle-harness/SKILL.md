---
name: shipq-lifecycle-harness
description: Route ShipQ quote, runtime, workbook/demo, browser QA, security, review, ship, or handoff work when AGENTS.md requires lifecycle context. Excludes ordinary questions, wording edits, and read-only instruction audits.
---

# ShipQ Lifecycle Harness

## Overview

Route actual ShipQ work that needs lifecycle or governed-state decisions.
Ordinary questions, wording edits, and read-only instruction audits use only
their targets and direct references; mentions of runtime/demo are not actions.

## Required Startup

- Reuse `AGENTS.md` already in context unless missing or changed. Its `Read First`
  table owns the task-specific reading requirements.
- Before edits, check `git status --short --branch` and preserve user-owned work;
  reuse the current check until another actor or operation may have changed it.
- For work routed here by `AGENTS.md` → `Read First`, read the relevant top
  rules and latest `State Log` entries in
  `docs/designs/harness-state.md`. Follow applicable `delivery-harness-framework`
  gates and the project's `Authorization Levels` before acting.
- Read `docs/designs/mgf-workbook-handoff.md` and
  `docs/designs/mgf-workbook-to-quote-engine-canonical-schema.md` when the actual
  operation depends on workbook/runtime contracts. Do not use fixed head/tail
  batches or read unrelated business state for a wording change.
- If required state is missing, report the missing evidence and stop the
  dependent operation. Creating or restoring state needs its own write scope.

## Stage Classifier

Choose the first matching stage. If multiple match, use the earliest stage that
changes the decision; for example, unclear product scope beats implementation.

| Stage | Signals | Invoke |
| --- | --- | --- |
| Product boundary | Asking what to build, whether scope is right, public demo positioning, quote/pricing packaging. | `gstack/office-hours`, then `gstack/plan-ceo-review` if product direction changes. |
| Engineering plan | Architecture, data model, runtime, importer, SQLite, API, exceptions, rollback, or cross-file plan. | `gstack/plan-eng-review`. |
| Implementation | A concrete code/doc change with clear acceptance criteria. | `superpowers:test-driven-development` for code; update docs with the change. |
| Debug/investigation | Test failure, wrong quote, import mismatch, 401/500, browser error, broken workflow. | `gstack/investigate`. |
| Browser QA | Public quote demo, prototype pages, console/network checks, screenshots, responsive behavior. | `gstack/qa` for fix flow or `gstack/qa-only` for report-only. |
| Security boundary | OAuth, token, public/internal split, sensitive workbook data, approvals, audit logs. | `gstack/cso`, and `gstack/guard` if edits may touch risky files. |
| Review | Diff exists and the work is near handoff or PR. | `gstack/review`. |
| Ship/deploy | User asks to commit, push, create PR, merge, deploy, or land. | `gstack/ship`; use `gstack/land-and-deploy` after PR/merge when production verification is needed. |
| Post-deploy | Live URL, deployment health, regressions, monitoring. | `gstack/canary`. |
| Handoff/learning | Save state, resume, summarize week, document release, update project knowledge. | `gstack/checkpoint`, `gstack/retro`, `gstack/learn`, or `gstack/document-release`. |

## Subagent Role Routing

Main 先决定是否委派；关键词本身不触发 spawn，显式 skill role 优先，Product/Handoff 标签本身不路由。小型、串行、紧耦合任务由 main 完成。

- Read-only：Browser QA → `browser_qa`；Security/privacy → `security_privacy`；Release/runtime readback → `operations_release`；Architecture → `architect`；Exploration → `explorer`；Review/review-swarm → `reviewer`；Non-browser QA 无匹配 specialist → main。
- 授权 implementation：Python/data/API → `python_data`；Web/Cloudflare → `web_cloudflare`；Apple → `apple_platform`；Elixir/OTP → `elixir_orchestrator`；Product/content → `product_content`；无匹配 specialist 的授权 implementation → `worker`。
- 原始用户请求已授权 implementation，且 main 分配互不重叠的 exact repo-relative write_set 后，workspace-write agent 才可编辑该范围并运行 assigned focused gate。read-only agent 永不写入；writer 不得 commit、push、deploy、操作 remote/shared runtime 或写未分配路径。
- Debug explorer 只读定位后返回 main；main 保留授权判断、任务拆分、集成、remote/shared runtime mutation 与 fresh final verification。

## ShipQ Hard Gates

For workbook/runtime/demo work, preserve these boundaries from
`docs/designs/harness-state.md`:

- Do not expose `API USER ID`, raw workbook rows, `source_row`, `raw_header`,
  `component_trace`, customer group details, tier details, or internal generated
  artifacts through public surfaces.
- Do not mutate `data/internal/shipq_quote_demo.sqlite` unless the user
  explicitly approves runtime replacement and rollback evidence exists.
- Keep `Tariff calulator` reference-only; it must not feed runtime calculation.
- Use `/tmp/shipq-workbook-runtime-smoke.sqlite` for finalize smoke by default.

## Verification Routing

Use the project's `AGENTS.md` → `Test Commands` as the single verification
entry point, including its instruction-only exception and CI lane selector.
Do not maintain a separate work-type test table in this skill.

- During implementation, use the relevant focused checks.
- When required by the repo, `scripts/verify_harness.py` already includes serial
  full pytest. Run it once for the final state; do not add a separate full pytest
  or repeat the internal quote API tests it already collects.
- Reuse evidence for unchanged inputs. New behavior changes, failed checks, or
  concrete unresolved concerns require the relevant verification again.
- Report `command`, `exit_code`, `key_output`, and `timestamp`; a green source
  gate does not prove live Gmail, provider, or runtime acceptance.

## Output Contract

For work requiring lifecycle routing, report only the applicable items:

1. Lifecycle stage selected.
2. gstack skill(s) invoked or reason no extra skill is needed.
3. State files read.
4. Verification gates required for completion.
5. Any blocker that requires user decision.

Do not implement before routing when the task is complex or touches ShipQ
workbook/runtime/demo/security surfaces.
