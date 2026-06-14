---
name: dual-committee-review-loop
description: Use when a user explicitly asks to involve both Codex and local Claude CLI in the same bounded review decision, asks Claude to re-review Codex committee output, requests Codex/Claude cross-check on non-sensitive local work, or says 双向复审.
---

# Dual Committee Review Loop

Coordinate a bounded review-and-revision loop between Codex and local Claude CLI without changing either side's existing `committee-review-loop` behavior.

## Preconditions

- Use only for local, non-sensitive artifacts or prompt text.
- Confirm editable scope, verification gate, target rating, and `max_rounds`. Default `max_rounds`: 5.
- **REQUIRED SUB-SKILL:** Use `committee-review-loop` for every Codex review phase and Codex re-review phase.
- Before calling Claude CLI, read `references/claude-cli-protocol.md`.
- Verify Claude CLI availability and authentication with fresh evidence before the first Claude call.
- Confirm Claude can access `committee-review-loop` either as an installed Claude skill or by reading an explicit local `SKILL.md` path.

## Inputs

Collect or infer:

- `artifact`: local path or bounded text to review.
- `scope`: files or sections Codex may change.
- `verification`: command(s) that prove the result.
- `target_rating`: default `10/10` unless the user sets another threshold.
- `max_rounds`: default `5`.
- `claude_skill_source`: prefer `~/.claude/skills/committee-review-loop/SKILL.md` when present; otherwise use an installed Claude skill name or explicit local path to `committee-review-loop/SKILL.md`.
- `claude_tools`: default read-only; allow `Read` only when Claude must inspect local files.

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
- Revision brief and revisions, if any.
- Verification evidence: `command`, `exit_code`, `key_output`, `timestamp`.
- Stop decision if Codex already judges the latest result needs no further changes and verification passes.

### 2. Claude review phase

Build a sanitized Claude request that includes only:

- The user objective and explicit scope.
- The current artifact path or bounded excerpt.
- The Codex review/revision summary.
- The requested structured output contract.
- The `committee-review-loop` skill source Claude should use.

Call Claude CLI in print mode with no session persistence. Prefer read-only tools. Record the real command, exit code, key output, and timestamp. If the command fails, recover according to the protocol reference.

Claude must return:

- `verdict`: `continue`, `stop`, or `blocked`.
- `committee_skill_access`: how Claude used or read `committee-review-loop`.
- `committee_rating` and `threshold_status`.
- `must_fix_before_pass`.
- `revision_brief`.
- `feedback_for_codex`.
- Any verification evidence Claude actually ran.

### 3. Codex re-review phase

Use `committee-review-loop` again to evaluate Claude's result and the current artifact. Decide one of:

- Apply Claude's concrete, in-scope revision brief and verify.
- Send Codex feedback back to Claude for another Claude review phase.
- Stop because Codex or Claude explicitly says no further modification is needed and verification passes.
- Stop because a blocker or safety boundary is reached.

### 4. Loop control

Each Codex -> Claude CLI -> Codex cycle increments the round count. Stop when any condition is true:

- Codex says no further changes are needed and verification passes.
- Claude says no further changes are needed and Codex accepts that result after re-review.
- `target_rating` is met and verification passes.
- `max_rounds` is reached.
- The same failure appears twice; shrink the scope or change evidence source before continuing.
- A safety, authentication, permission, sensitive-data, or user-decision blocker appears.

## Final Report

Return:

- Final verdict and who stopped the loop: Codex or Claude.
- Number of rounds completed.
- Changed files.
- Top Codex and Claude findings.
- Final verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Claude CLI round-trip evidence with `command`, `exit_code`, `key_output`, and `timestamp`.
- Remaining risks or explicit scope limits.

## Common Mistakes

- Treating Claude's response as final without a Codex re-review phase.
- Continuing after either side clearly reaches `stop`.
- Sending broad repo context when a small artifact or excerpt is enough.
- Hiding a failed Claude CLI call behind a summary.
- Using a fake Claude review result instead of real command output.
