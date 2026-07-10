# Claude CLI Protocol

Use this reference only when preparing, running, or recovering a Claude CLI review phase for `dual-committee-review-loop`.

## Preflight

Run and record:

```bash
command -v claude
claude --version
claude -p "Return exactly CLAUDE_READY and nothing else." --model claude-fable-5 --fallback-model claude-sonnet-5 --effort high --output-format text --no-session-persistence --tools ""
```

Confirm Claude can access `committee-review-loop` without modifying global Claude config. Prefer an explicit local path:

```bash
claude -p "Use the Read tool to read $HOME/.claude/skills/committee-review-loop/SKILL.md. Return COMMITTEE_SKILL_NAME=<name>." \
  --model claude-fable-5 \
  --fallback-model claude-sonnet-5 \
  --effort high \
  --output-format text \
  --no-session-persistence \
  --tools Read \
  --allowedTools Read \
  --disallowedTools Bash,Edit,Write \
  --permission-mode dontAsk \
  --add-dir "$HOME/.claude/skills/committee-review-loop"
```

If this fails because Claude is unauthenticated, the skill is inaccessible, or permissions are insufficient, stop and ask the user.

If either preflight call fails only with `Exceeded USD budget`, retry it through
the budget ladder below before declaring Claude unavailable. This error means
the per-command cap was too low; it is not the same as an account usage limit.

Also run `claude --help` and confirm every planned flag exists in the installed CLI. Unknown or changed flags are a stop-and-ask condition unless the fix is a narrower equivalent flag shown by current help output.

## Request Template

Send only non-sensitive local content.

```text
You are Claude CLI performing a read-only committee-review-loop re-review for Codex.

Use this committee-review-loop source:
<absolute path or installed skill name>

Safety:
- Do not request secrets, credentials, production data, SSH, tunnels, or remote services.
- Do not edit files or modify Claude/Codex global config.
- If you cannot access the skill, return verdict=blocked.
- Score independently. Do not ask for or infer the desired target rating.

Objective:
<user objective>

Scope:
<allowed local files or text excerpt>

Frozen review rubric:
<criteria, counterexamples, and evidence expectations; no prior scores or verdicts>

Current acceptance ledger:
<stable finding IDs, evidence, closure conditions, and status; no prior scores or verdicts>

Verification evidence:
<fresh commands and results>

Return exactly these sections:
verdict: continue|stop|blocked
committee_skill_access:
committee_rating:
rating_rationale:
threshold_status:
review_rubric_coverage:
acceptance_ledger_updates:
new_material_findings:
rubric_challenges:
must_fix_before_pass:
revision_brief:
feedback_for_codex:
verification_evidence:
residual_risks:
known_unknowns:
```

The normal Claude phase may receive bounded Codex findings needed to understand
an open ledger item, but the prompt must not contain any prior score, prior
rating, prior verdict, target rating, or score-based conclusion.

## Blind Final Review Template

Blind final review must be independent of score targets and prior verdicts.

Use a fresh no-session-persistence call when the artifact becomes a candidate
pass. Send only:

- the current artifact or bounded excerpt,
- the user objective and scope,
- the frozen `review_rubric`, and
- fresh verification evidence.

Do not send any prior score, prior rating, prior verdict, target rating, revision
history, revision brief, or statement that the artifact is expected to pass.
Require an independent `committee_rating`, `rating_rationale`,
`review_rubric_coverage`, `new_material_findings`, `rubric_challenges`, and
`residual_risks`. If the blind review finds a material issue or a material
rubric omission, reopen or append the corresponding ledger item and record a
versioned rubric amendment instead of averaging the new score with an earlier
one.

## CLI Pattern

Use print mode and avoid session persistence:

```bash
claude -p "$PROMPT" \
  --model claude-fable-5 \
  --fallback-model claude-sonnet-5 \
  --effort high \
  --output-format text \
  --no-session-persistence \
  --max-budget-usd 1.00 \
  --tools Read \
  --allowedTools Read \
  --disallowedTools Bash,Edit,Write \
  --permission-mode dontAsk \
  --add-dir /ABS/REPO
```

Treat this as a pattern, not a timeless API contract. Confirm the exact flags against the current `claude --help` output during preflight before relying on them.

`--fallback-model` covers primary model overload, unavailability, or no access. It is not a replacement for `Exceeded USD budget` handling.

Use `--tools ""` when Claude does not need local file reads. Increase
`--max-budget-usd` only when the previous run failed solely due to budget and
the prompt is already minimized.

## Budget Ladder

For `Exceeded USD budget`, do not skip Claude. Retry in this order:

1. Reduce prompt/context once to the smallest useful artifact path or excerpt,
   frozen rubric, sanitized ledger state without scores or verdicts, and the
   required output contract.
2. Retry with the next `--max-budget-usd` step:
   `0.25`, `0.50`, `1.00`, `2.00`, `4.00`, `8.00`.
3. If `8.00` still fails only because of `Exceeded USD budget`, continue by
   doubling the prior cap for that bounded review until Claude returns the
   required structured response or a real provider/account limit appears.
4. Stop only for non-budget blockers: account usage/quota/rate limit,
   unauthenticated CLI, permission/tool denial after the narrow retry, skill
   inaccessible, malformed response after one structured retry, sensitive-data
   risk, or an explicit user/safety boundary.

Record every retry command, exit code, key output, budget step, and timestamp in
the final report. Do not label a local budget cap as "Claude skipped".

## Response Intake

Treat Claude output as evidence, not truth. Codex must re-review it before applying changes or stopping.

Accept only responses that include:

- `verdict`
- `committee_skill_access`
- `committee_rating`
- `rating_rationale`
- `threshold_status`
- `review_rubric_coverage`
- `acceptance_ledger_updates`
- `new_material_findings`
- `rubric_challenges`
- `must_fix_before_pass`
- `revision_brief`
- `feedback_for_codex`
- `verification_evidence`
- `residual_risks`
- `known_unknowns`

If any field is missing, ask Claude once for a structured retry. If the retry fails, stop and report the malformed response.

## Failure Recovery

- `Not logged in`: stop and ask the user to authenticate Claude CLI.
- `Exceeded USD budget`: reduce prompt/context once, then follow the budget
  ladder until the review completes or a real usage/account limit appears; do
  not treat this as model fallback and do not skip Claude solely for this error.
- Account usage, quota, or rate limit reached: stop and report the exact
  provider/account limit text as the blocker.
- Permission/tool denial: retry once with the narrowest necessary read-only tool set.
- Skill inaccessible: stop unless the user authorizes installing or syncing Claude skills.
- Sensitive data detected: stop, redact locally, and ask for user direction.
