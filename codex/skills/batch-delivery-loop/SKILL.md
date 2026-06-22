---
name: batch-delivery-loop
description: Use when a user provides source text or a source artifact and wants project-aware batch planning, reviewed per-batch implementation contracts, and sequential batch execution until complete or blocked.
---

# Batch Delivery Loop

Turn a source artifact into a reviewed batch delivery path, then execute only the approved batches. This skill orchestrates existing skills; it must not reimplement lifecycle routing, committee review, or repo-specific commands.

## Required Sub-Skills

- Use `delivery-harness-framework` first for repo state, lifecycle stage, execution lane, dirty worktree, and verification gates.
- Use repo-local `AGENTS.md`, `docs/repo-index.md`, `docs/harness-state.md`, and nearby source-of-truth docs before writing plans.
- Use `dual-committee-review-loop` for batch plan review and implementation contract review.

## Inputs

- `source_text_or_path`: bounded text or local artifact to transform.
- `objective`: user-facing outcome.
- `output_dir`: default `docs/plans`.
- `target_rating`: default `10/10`.
- `max_review_rounds`: default `5`.
- `execution_mode`: `plan_only`, `contracts_only`, or `full`; default `full`.
- `stop_conditions`: optional user-provided blockers or boundaries.

## Workflow

### Phase 0: Route And Guard

1. Read repo instructions and state in the order required by `delivery-harness-framework`.
2. Classify lifecycle stage, execution lane, dirty worktree ownership, forbidden actions, and PR-gated or approval-gated actions.
3. Define Definition of Done: created docs, review threshold, execution scope, verification command(s), usability check, and stop conditions.
4. Do not call live services, deploy, delete PR-gated artifacts, mutate external systems, or read secrets unless the active user request explicitly authorizes that action.
5. Before any dual review, sanitize or bound source content according to `dual-committee-review-loop`; stop if the artifact contains secrets, credentials, private customer data, production data, or unrelated local context.

### Phase 1: Batch Plan

1. Generate one batch execution plan under `output_dir`.
2. Split batches by dependency order, blast radius, ownership boundary, and verification gate.
3. Include objective, source artifact, assumptions, out-of-scope items, stop conditions, batch order, expected files or surfaces, and verification per batch.
4. Run `dual-committee-review-loop` on the plan with `target_rating` and `max_review_rounds`.
5. If review returns a non-rating `blocked` or `stop` verdict, surface that blocker verbatim and stop. Do not treat it as a failed score.
6. If review completes but does not reach `target_rating`, stop and report the rating gap. Do not create contracts or execute batches.
7. If `execution_mode` is `plan_only`, stop after the reviewed plan and report the next safe task.

### Phase 2: Implementation Contracts

1. Generate one contract doc per approved batch.
2. Each contract must include:
   - scope
   - allowed files or surfaces
   - forbidden files and actions
   - implementation steps
   - tests or checks
   - acceptance criteria
   - rollback or revert path
   - blocker conditions
3. Run `dual-committee-review-loop` on the contract set with `target_rating` and `max_review_rounds`.
4. If review returns a non-rating `blocked` or `stop` verdict, surface that blocker verbatim and stop. Do not treat it as a failed score.
5. If review completes but does not reach `target_rating`, stop before execution and report the rating gap.
6. If `execution_mode` is `contracts_only`, stop after the reviewed contracts and report the next safe task.

### Phase 3: Execute Batches

1. Execute batches sequentially in approved order.
2. Before each batch, use `delivery-harness-framework` to re-check repo status, execution lane, current blockers, and dirty-worktree ownership (`agent_owned` vs `user_owned`) before writing.
3. Use the current repo's test and verification entrypoints; do not hardcode project-specific commands in this skill.
4. After each batch, run the focused verification named in its contract.
5. Stop on a failed gate, unclear user decision, external dependency, dirty-state conflict, safety boundary, or changed source-of-truth.
6. After the final batch, run the final verification gate and report the next safe task.

## Final Report

Return:

- Plan docs created.
- Contract docs created.
- Batches completed or blocked.
- Changed files.
- Plan and contract review evidence, including dual-committee verdicts, round counts, and blockers.
- Verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Remaining risks.
- Next safe task.

## Common Mistakes

- Creating three separate skills for planning, contracts, and execution.
- Copying `delivery-harness-framework` or `dual-committee-review-loop` logic instead of requiring those skills.
- Hardcoding ShipQ paths, commands, fixtures, or business rules.
- Proceeding from plan to contracts, or contracts to execution, without meeting `target_rating`.
- Treating green tests as sufficient when the batch contract also requires doc, UI, safety, or usability checks.
