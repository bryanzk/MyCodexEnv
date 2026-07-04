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

Objective:
<user objective>

Scope:
<allowed local files or text excerpt>

Current Codex result:
<Codex committee findings, revisions, and verification evidence>

Return exactly these sections:
verdict: continue|stop|blocked
committee_skill_access:
committee_rating:
threshold_status:
must_fix_before_pass:
revision_brief:
feedback_for_codex:
verification_evidence:
```

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

Use `--tools ""` when Claude does not need local file reads. Increase `--max-budget-usd` only when the previous run failed solely due to budget and the prompt is already minimized.

## Response Intake

Treat Claude output as evidence, not truth. Codex must re-review it before applying changes or stopping.

Accept only responses that include:

- `verdict`
- `committee_skill_access`
- `committee_rating`
- `threshold_status`
- `must_fix_before_pass`
- `revision_brief`
- `feedback_for_codex`
- `verification_evidence`

If any field is missing, ask Claude once for a structured retry. If the retry fails, stop and report the malformed response.

## Failure Recovery

- `Not logged in`: stop and ask the user to authenticate Claude CLI.
- `Exceeded USD budget`: reduce prompt/context once, then retry with a documented budget.
- Permission/tool denial: retry once with the narrowest necessary read-only tool set.
- Skill inaccessible: stop unless the user authorizes installing or syncing Claude skills.
- Sensitive data detected: stop, redact locally, and ask for user direction.
