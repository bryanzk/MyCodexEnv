---
name: shipq-lifecycle-harness
description: Use for ShipQ state recovery, handoff, or tasks including reviews that depend on runtime, deployment, protected-data, or authorization boundaries.
---

# ShipQ Lifecycle Harness

Use this adapter only when current ShipQ work needs governed lifecycle state:
state recovery or handoff, a real source-to-runtime/deployment transition, or
an authorization/protected-data boundary. A mention of Gmail, runtime, demo,
pricing, or a workbook does not trigger it by itself.

Questions, scoped edits, and reviews that do not depend on these boundaries
start from their target files, callers, and tests without lifecycle routing.

## Startup

- Reuse the applicable `AGENTS.md` already in context unless it is missing or
  may have changed. Its `Read First` table owns task-specific reading.
- Apply its `Authorization Levels` before any governed operation.
- Before edits, check current worktree state and preserve user-owned changes.
- Read only the facts, policy, and latest state needed for the boundary being
  crossed. For recovery or handoff, use the relevant entries in
  `docs/designs/harness-state.md`. For workbook/runtime contract work, read the
  applicable handoff or canonical-schema source named by `AGENTS.md`.
- Missing required state is a blocker for the dependent operation. Do not create
  or reconstruct it without matching write authority.

Classify the request only far enough to choose the next applicable workflow.
Use product or engineering planning for unresolved decisions, investigation for
observed failures, browser QA for real UI evidence, security review for trust
boundaries, and release workflows only when the user requests release work.
Concrete implementation with clear acceptance criteria proceeds directly under
the repository rules.

Follow `AGENTS.md` for any subagent routing. Delegation does not widen write
scope or permit commit, push, deploy, remote, or shared-runtime operations.

## Hard Gates

For workbook/runtime/demo work:

- Do not expose `API USER ID`, raw workbook rows, `source_row`, `raw_header`,
  `component_trace`, customer group details, tier details, or internal generated
  artifacts through public surfaces.
- Do not mutate `data/internal/shipq_quote_demo.sqlite` without explicit runtime
  replacement approval and rollback evidence.
- Keep `Tariff calulator` reference-only; it must not feed runtime calculation.
- Use `/tmp/shipq-workbook-runtime-smoke.sqlite` for finalize smoke by default.

## Verification

Use ShipQ `AGENTS.md` as the single verification authority. Run its narrowest
applicable focused gate during iteration and its final gate only when required.
Do not add a second full pytest, repeat tests already included by a harness, or
rerun valid evidence when its inputs and environment have not changed.

Keep evidence lanes distinct: source checks do not prove runtime activity,
deployment, live Gmail/provider behavior, or customer acceptance. Completion
receipts must use the fields required by `AGENTS.md`.
