---
name: committee-review-loop
description: Use when a user explicitly asks for a committee or subagents to iteratively review, score, and revise an output until a calibrated target such as 10/10 is reached with evidence.
---

# Committee Review Loop

Use this skill to turn a broad quality target into a structured review-and-revision loop. The committee discovers checks the user may not know to request, converts them into a frozen evidence ledger, and converges the artifact and its score together.

## Preconditions

- Confirm the task output, editable scope, non-goals, rating target, and `max_rounds`. Defaults: `committee.rating >= 10/10` and `max_rounds=5`.
- The user does not need to supply a complete verification rubric. When checks are incomplete, the first committee round must generate them before revision begins.
- Use subagents only when the user explicitly asks for subagents, a committee, delegation, or parallel agent work.
- Do not use this skill for one-off reviews, ordinary QA, or normal polish passes. Route those to the relevant review, QA, or design skill.
- Treat the committee as expert perspectives unless the user provides actual named reviewers. Do not imply real people reviewed the work.
- Preserve unrelated user changes. Give each revision worker a bounded write scope.

## Calibrated Scoring Contract

The numeric target is a required convergence result, not the sole pass gate. A `10/10` means: within the explicit scope and available evidence, the committee knows of no material defect, required evidence is complete, and residual risk is disclosed. It does not mean absolute or future-proof perfection.

The main agent owns the target rating. Scoring reviewers must score independently and must not be told the desired threshold while assigning ratings.

Apply these rating caps to every expert rating and the consensus rating:

- Any open `blocker` -> maximum `5/10`.
- Any open `major` -> maximum `7/10`.
- Any unverified material claim -> maximum `8/10`.
- Any open `minor` -> maximum `9/10`.
- `10/10` -> no open material finding, all required evidence passed, and `residual_risks` is explicit.

`threshold_status=pass` requires all of the following:

- The iterative committee rating and blind final rating both meet the target, and the rating caps are respected.
- No open blocker or major finding.
- Every ledger item required by the target is closed.
- Required verification passes with fresh evidence.
- The blind final review finds no new material issue.

## First-Round Rubric Bootstrap

Before asking a worker to revise anything, the first committee round must produce:

- `review_rubric`: relevant domains, criteria, counterexamples, and evidence expectations.
- `required_evidence`: deterministic checks where possible; otherwise traceability, scenario, consistency, feasibility, and adversarial evidence.
- `known_unknowns`: assumptions or blind spots that cannot yet be resolved.
- `acceptance_ledger`: findings with `finding_id`, `severity`, `claim`, `evidence`, `closure_condition`, and `status`.

Freeze `review_rubric` after round 1. Later reviewers may append a new finding with a stable ID, but must not silently change the scoring criteria or remove unresolved ledger items. A blind reviewer may return `rubric_challenges` when a material domain or criterion is missing; the main agent must record a versioned rubric amendment with evidence and reopen the affected ledger instead of mutating the rubric invisibly.

## Roles

### Main Agent

- Own the loop, scope, evidence, and final integration.
- Select the three expert domains most relevant to the task.
- Keep the committee read-only unless the user explicitly asks otherwise.
- Review worker changes before presenting them back to the committee.
- Run fresh verification before claiming the target has been met.
- Enforce the rating caps and preserve the frozen rubric and ledger across rounds.
- Keep iterative closure reviews and the blind final review separate.

### Subagent 1: Expert Committee

Ask the committee to simulate three world-class domain experts, one per relevant domain. Each expert must independently review the current output and provide:

- `domain`
- `review_focus`
- `rating`: score out of 10
- `rating_rationale`: evidence tied to the scoring anchors
- `top_findings`: concrete blockers or weaknesses
- `improvement_suggestions`: actionable changes
- `rubric_coverage`: criteria checked and evidence inspected
- `blind_spots`: missing access, assumptions, or residual uncertainty

The committee then produces:

- `committee.rating`: final consensus score out of 10
- `rating_rationale`
- `threshold_status`: `pass` or `fail`
- `must_fix_before_pass`: prioritized blockers
- `revision_brief`: concise instructions for the revision worker
- `review_rubric` and `required_evidence` in round 1
- `acceptance_ledger` plus ledger updates in every round
- `new_material_findings`
- `rubric_challenges`: material omissions in the frozen rubric, with evidence
- `residual_risks`

### Subagent 2: Revision Worker

Ask the worker to improve the task output using only the committee's `revision_brief` and scoped files. The worker must:

- Make concrete changes, not just recommendations.
- Avoid reverting unrelated edits.
- Report changed files.
- Report verification evidence when it runs checks: `command`, `exit_code`, `key_output`, `timestamp`.

## Workflow

1. Define the output, scope, non-goals, target score, and `max_rounds`. Record any known verification checks without requiring the user to make them exhaustive.
2. Run the first committee round to generate and freeze `review_rubric`, `required_evidence`, and `acceptance_ledger`, then score independently under the rating caps.
3. If ledger work remains, send only the open findings and bounded `revision_brief` to the revision worker.
4. Review the worker changes and run the relevant verification checks.
5. Present the artifact, frozen rubric, ledger, and fresh evidence to the same committee for closure consistency. Append rather than overwrite new findings.
6. Repeat steps 3-5 until a candidate pass is reached or a stopping condition applies. The initial committee is round 1, each closure re-review increments the round count, and the blind final review consumes the final round.
7. Run fresh final verification.
8. Run a blind final review using a fresh committee instance. Provide only the current artifact, objective, scope, frozen rubric, and verification evidence. Do not provide the target score, prior rating, prior verdict, revision history, or prior revision brief. Require `rubric_challenges` so the reviewer can identify a material omission in the frozen criteria.
9. If the blind committee finds a new material issue or material rubric challenge, append the finding, record a versioned rubric amendment, and continue within `max_rounds`. Otherwise apply the full pass gate and stop.

## Stopping Conditions

Stop the loop when any of these are true:

- The full calibrated pass gate succeeds, including the blind final review.
- `max_rounds` is reached. Report the current rating and unresolved ledger as `incomplete`; do not inflate the score to finish.
- The same unresolved finding or verification failure repeats twice without new evidence; shrink scope, change the evidence source, or stop as blocked.
- The task needs user input, credentials, approval, or a scope decision.
- The committee identifies a blocker that cannot be fixed within the allowed scope.
- The user interrupts, redirects, or changes the target.

## Final Response

Report:

- Final `committee.rating`.
- Iterative rating and blind final rating, without averaging them.
- `review_rubric` coverage and the final `acceptance_ledger` state.
- The three expert domains used.
- The top improvements made.
- Changed files.
- Fresh verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Any remaining risk or scope limitation.
- `residual_risks`, `known_unknowns`, and any unresolved findings when the result is incomplete or blocked.

## Maintenance Verification

When this scoring contract or `dual-committee-review-loop` changes, run `scripts/validate_scoring_contract.py`. This maintenance-only validator is not part of an ordinary artifact review.
