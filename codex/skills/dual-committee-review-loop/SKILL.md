---
name: dual-committee-review-loop
description: Use when a user explicitly asks Codex and local Claude CLI to independently review, score, and revise the same bounded non-sensitive artifact, cross-check a committee result, or perform 双向复审.
---

# Dual Committee Review Loop

Coordinate a bounded review-and-revision loop between Codex and local Claude CLI without changing either side's existing `committee-review-loop` behavior.

## Preconditions

- Use only for local, non-sensitive artifacts or prompt text.
- Confirm editable scope, verification gate, target rating, and `max_rounds`. Default `max_rounds`: 5.
- The user may leave review and verification criteria incomplete. The first Codex committee phase must bootstrap and freeze them before score convergence.
- **REQUIRED SUB-SKILL:** Use `committee-review-loop` for every Codex review phase and Codex re-review phase.
- Before calling Claude CLI, read `references/claude-cli-protocol.md`.
- Verify Claude CLI availability and authentication with fresh evidence before the first Claude call.
- Confirm Claude can access `committee-review-loop` either as an installed Claude skill or by reading an explicit local `SKILL.md` path.
- Treat Claude CLI `Exceeded USD budget` as a retryable per-command budget cap,
  not as a review blocker. Follow the protocol's budget ladder unless Claude
  reports an account usage/quota/rate limit, authentication failure, permission
  denial, safety issue, or other non-budget blocker.

## Inputs

Collect or infer:

- `artifact`: local path or bounded text to review.
- `scope`: files or sections Codex may change.
- `verification`: command(s) that prove the result.
- `target_rating`: default `10/10` unless the user sets another threshold.
- `max_rounds`: default `5`.
- `review_rubric`: optional user criteria; the first Codex phase completes and freezes it.
- `acceptance_ledger`: stable finding IDs shared by Codex and Claude across rounds.
- `claude_skill_source`: prefer `~/.claude/skills/committee-review-loop/SKILL.md` when present; otherwise use an installed Claude skill name or explicit local path to `committee-review-loop/SKILL.md`.
- `claude_tools`: default read-only; allow `Read` only when Claude must inspect local files.

## Shared Scoring Contract

Inherit the calibrated scoring contract and rating caps from `committee-review-loop`. The target remains with the main orchestrator; Codex and Claude scoring reviewers assign ratings independently without being told the desired threshold.

Do not average Codex and Claude ratings. A disagreement is evidence to adjudicate: map it to a ledger finding, inspect the cited evidence, and revise or report the unresolved disagreement.

The dual result passes only when all are true:

- Codex and Claude independently meet `target_rating` under the rating caps.
- Neither side has an open blocker or major finding.
- `acceptance_ledger` items required by the target are closed.
- Required verification passes with fresh evidence.
- The blind final review reports no `new_material_findings` or material `rubric_challenges` that violate the target.
- `residual_risks` and unresolved `known_unknowns` are explicit.

## Safety Rules

- Do not send secrets, credentials, tokens, private customer data, production data, or unrelated local context to Claude CLI.
- Do not modify Claude global config, Claude global skills, Codex global config, or existing `committee-review-loop` skills.
- Do not install, overwrite, or sync Claude skills unless the user explicitly authorizes it.
- Do not use SSH, tunnels, remote services, destructive commands, or unbounded loops.
- If Claude CLI is missing, unauthenticated, cannot access `committee-review-loop`, or needs broader permissions, stop and ask the user.

## Workflow

### 1. Codex review phase

Use `committee-review-loop` locally to review the current artifact. Produce:

- Codex committee domains and ratings.
- Round-1 `review_rubric`, `required_evidence`, `known_unknowns`, and `acceptance_ledger`.
- Revision brief and revisions, if any.
- Verification evidence: `command`, `exit_code`, `key_output`, `timestamp`.
- Candidate-pass decision if Codex judges no further changes are needed and verification passes. Codex alone cannot stop the dual loop as passed.

### 2. Claude review phase

Build a sanitized Claude request that includes only:

- The user objective and explicit scope.
- The current artifact path or bounded excerpt.
- The frozen rubric, current artifact, verification evidence, and sanitized ledger state.
- Codex findings needed to understand open ledger items, without any Codex prior rating, verdict, target rating, or score-based conclusion.
- The requested structured output contract.
- The `committee-review-loop` skill source Claude should use.

Call Claude CLI in print mode with no session persistence. Prefer read-only tools. Record the real command, exit code, key output, and timestamp. If the command fails, recover according to the protocol reference.

If Claude fails only with `Exceeded USD budget`, shrink the prompt/context once,
then retry with the next `--max-budget-usd` step from the protocol. Continue
budget escalation until Claude returns the required structured review, the
round's review objective is satisfied, or a real usage/account limit or safety
blocker appears. Do not skip Claude solely because an earlier local budget cap
was too small.

Claude must return:

- `verdict`: `continue`, `stop`, or `blocked`.
- `committee_skill_access`: how Claude used or read `committee-review-loop`.
- `committee_rating` and `threshold_status`.
- `rating_rationale` and applied rating caps.
- `review_rubric_coverage`.
- `acceptance_ledger_updates` using stable finding IDs.
- `new_material_findings` with severity, evidence, and closure condition.
- `rubric_challenges` for a material domain or criterion missing from the frozen rubric.
- `must_fix_before_pass`.
- `revision_brief`.
- `feedback_for_codex`.
- Any verification evidence Claude actually ran.
- `residual_risks` and `known_unknowns`.

### 3. Blind final review phase

When the current artifact is a candidate pass, run a fresh no-session-persistence Claude review. Provide only the current artifact, user objective, scope, frozen `review_rubric`, and final verification evidence.

Do not provide the target rating, any prior rating, prior verdict, revision history, revision brief, or a narrative saying the artifact is ready to pass. Require Claude to return an independent rating, `rating_rationale`, `review_rubric_coverage`, `new_material_findings`, `rubric_challenges`, and `residual_risks`.

### 4. Codex re-review phase

Use `committee-review-loop` again to evaluate Claude's result and the current artifact. Decide one of:

- Apply Claude's concrete, in-scope revision brief and verify.
- Reconcile Claude `acceptance_ledger_updates` and new findings against evidence without averaging ratings.
- Send Codex feedback back to Claude for another Claude review phase.
- Mark a candidate pass when Codex or Claude says no further modification is needed, then apply the full shared scoring contract. Neither side can pass the dual loop alone.
- Stop because a blocker or safety boundary is reached.

### 5. Loop control

Each Codex -> Claude CLI -> Codex cycle increments the round count, and the blind final review consumes a round. Stop when any condition is true:

- The full shared scoring contract passes: both independent ratings meet target, the ledger is closed as required, verification passes, and the blind final review finds no new material issue or material rubric challenge.
- `max_rounds` is reached.
- The same failure appears twice; shrink the scope or change evidence source before continuing.
- A safety, authentication, permission, sensitive-data, or user-decision blocker appears.
- Claude reports an account usage/quota/rate limit or other non-retryable
  provider/account limit. A per-command `Exceeded USD budget` cap alone is not a
  stopping condition.

## Final Report

Return:

- Final verdict and who stopped the loop: Codex or Claude.
- Number of rounds completed.
- Independent Codex rating, Claude rating, rating rationales, and applied rating caps. Do not report an averaged score.
- Final `review_rubric` coverage, `acceptance_ledger` status, and blind final review result.
- Changed files.
- Top Codex and Claude findings.
- Final verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Claude CLI round-trip evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Remaining risks or explicit scope limits.
- `residual_risks`, `known_unknowns`, and unresolved rating disagreement.

## Common Mistakes

- Treating Claude's response as final without a Codex re-review phase.
- Revealing the target or any prior rating/verdict to the blind final reviewer.
- Averaging Codex and Claude scores instead of resolving the underlying findings and evidence.
- Continuing after either side clearly reaches `stop`.
- Sending broad repo context when a small artifact or excerpt is enough.
- Hiding a failed Claude CLI call behind a summary.
- Using a fake Claude review result instead of real command output.
