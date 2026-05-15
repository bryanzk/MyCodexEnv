---
name: committee-review-loop
description: Use when a user explicitly asks for a committee or subagents to iteratively review, rate, and revise a task output until a perfect target score such as 10/10 is reached.
---

# Committee Review Loop

Use this skill to turn a broad quality target into a structured review-and-revision loop. The loop has two working roles: an expert committee that reviews and scores the output, and a revision worker that improves the output from the committee's findings.

## Preconditions

- Confirm the task output to review, the editable scope, and the rating target. Default target: `committee.rating >= 10/10`.
- Use subagents only when the user explicitly asks for subagents, a committee, delegation, or parallel agent work.
- Do not use this skill for one-off reviews, ordinary QA, or normal polish passes. Route those to the relevant review, QA, or design skill.
- Treat the committee as expert perspectives unless the user provides actual named reviewers. Do not imply real people reviewed the work.
- Preserve unrelated user changes. Give each revision worker a bounded write scope.

## Roles

### Main Agent

- Own the loop, scope, evidence, and final integration.
- Select the three expert domains most relevant to the task.
- Keep the committee read-only unless the user explicitly asks otherwise.
- Review worker changes before presenting them back to the committee.
- Run fresh verification before claiming the target has been met.

### Subagent 1: Expert Committee

Ask the committee to simulate three world-class domain experts, one per relevant domain. Each expert must independently review the current output and provide:

- `domain`
- `review_focus`
- `rating`: score out of 10
- `top_findings`: concrete blockers or weaknesses
- `improvement_suggestions`: actionable changes

The committee then produces:

- `committee.rating`: final consensus score out of 10
- `threshold_status`: `pass` or `fail`
- `must_fix_before_pass`: prioritized blockers
- `revision_brief`: concise instructions for the revision worker

### Subagent 2: Revision Worker

Ask the worker to improve the task output using only the committee's `revision_brief` and scoped files. The worker must:

- Make concrete changes, not just recommendations.
- Avoid reverting unrelated edits.
- Report changed files.
- Report verification evidence when it runs checks: `command`, `exit_code`, `key_output`, `timestamp`.

## Workflow

1. Define the output, scope, target score, and verification gate.
2. Send the current output to the expert committee for review and scoring.
3. If `committee.rating >= target`, run final verification and stop.
4. If below target, send the committee's `revision_brief` to the revision worker.
5. Review and integrate the worker's changes.
6. Run the relevant verification checks.
7. Present the improved output back to the same committee for another review.
8. Repeat until the target is reached or a stopping condition applies.

## Stopping Conditions

Stop the loop when any of these are true:

- `committee.rating >= target` and fresh verification passes.
- The task needs user input, credentials, approval, or a scope decision.
- The committee identifies a blocker that cannot be fixed within the allowed scope.
- The user interrupts, redirects, or changes the target.

## Final Response

Report:

- Final `committee.rating`.
- The three expert domains used.
- The top improvements made.
- Changed files.
- Fresh verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Any remaining risk or scope limitation.
