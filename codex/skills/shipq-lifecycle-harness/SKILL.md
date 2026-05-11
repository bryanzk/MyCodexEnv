---
name: shipq-lifecycle-harness
description: Use when working in the ShipQ repo on a complex task, ambiguous request, quote/workbook/runtime/demo change, browser/API verification, security boundary, review, ship, or handoff, and Codex needs to classify the current software lifecycle stage before choosing gstack skills.
---

# ShipQ Lifecycle Harness

## Overview

Use this as the first router for non-trivial ShipQ work. It reads the repo state,
classifies the lifecycle stage, and then invokes the right gstack skill before
implementation or handoff.

## Required Startup

Run these probes before choosing the next skill:

```bash
pwd
git status --short --branch
git log --max-count=8 --pretty=format:'%h %ad %s' --date=short
test -f docs/designs/harness-state.md && sed -n '1,220p' docs/designs/harness-state.md
test -f docs/designs/harness-state.md && tail -n 220 docs/designs/harness-state.md
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
```

If the task touches workbook import, quote runtime, internal/public demo, or
handoff, also read:

```bash
sed -n '1,220p' docs/designs/mgf-workbook-handoff.md
sed -n '1,220p' docs/designs/mgf-workbook-to-quote-engine-canonical-schema.md
```

If `docs/designs/harness-state.md` is missing, stop and create or restore it
before doing lifecycle routing. Do not rely on chat history as the durable state.
`docs/designs/harness-state.md` uses append-only ongoing state updates, so read
both the header and latest bottom `State Log` entries before routing.

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

Before claiming completion, run the narrowest relevant gate and include
`command`, `exit_code`, `key_output`, and `timestamp`:

| Work type | Minimum gate |
| --- | --- |
| Any repo change | `git diff --check` |
| Code/runtime/import/API | `PATH=.venv/bin:$PATH pytest -q` |
| Workbook/runtime harness | `PATH=.venv/bin:$PATH python scripts/verify_harness.py` |
| Internal quote API | `PATH=.venv/bin:$PATH pytest -q tests/test_internal_quote_api.py` |
| Browser demo | Start `scripts/run_internal_quote_server.py` with `SHIPQ_INTERNAL_DEMO_TOKEN`, then use gstack browser/QA to check public, internal FCL, internal LCL, `prototype.html`, and `prototype-en.html`. |
| Docs/config only | Check referenced paths and run `git diff --check`; run tests if docs affect commands, scripts, or behavior. |

## Output Contract

After routing, state:

1. Lifecycle stage selected.
2. gstack skill(s) invoked or reason no extra skill is needed.
3. State files read.
4. Verification gates required for completion.
5. Any blocker that requires user decision.

Do not implement before routing when the task is complex or touches ShipQ
workbook/runtime/demo/security surfaces.
