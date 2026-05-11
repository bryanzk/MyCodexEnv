---
name: project-lifecycle-harness
description: Use when starting or resuming a complex software project task and Codex must first inspect durable project state, classify the software lifecycle stage, choose the right skill/tool workflow, define required probes and verification gates, preserve append-only evidence, or decide whether a repo-specific lifecycle harness should take over.
---

# Project Lifecycle Harness

## Overview

Use this as the generic lifecycle router before non-trivial project work. It
turns an ambiguous request into a staged workflow with explicit state, source of
truth, probes, error handling, verification, and handoff evidence.

If a repo-specific lifecycle harness exists, use this skill only to confirm the
project phase and then delegate to that repo-specific harness.

## Startup Probes

Run cheap probes before choosing a stage:

```bash
pwd
git status --short --branch
git log --max-count=8 --pretty=format:'%h %ad %s' --date=short
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
test -f README.md && sed -n '1,180p' README.md
test -f docs/repo-index.md && sed -n '1,220p' docs/repo-index.md
find . -maxdepth 3 \( -name '*harness-state.md' -o -name '*state.md' -o -name '*handoff*.md' -o -name 'TODOS.md' \) -print
```

Then read the most relevant durable state files. If a state file is append-only,
read both the header and the latest log tail:

```bash
sed -n '1,220p' PATH_TO_STATE_FILE
tail -n 220 PATH_TO_STATE_FILE
```

Do not rely on chat history when a repo state document exists. If no durable
state file exists and the task is long-running, cross-session, data-sensitive,
or release-sensitive, create or propose a state file before implementation.

## Source Of Truth Order

Prefer durable project surfaces in this order:

1. Repo or subdirectory `AGENTS.md`.
2. Low-token repo index, usually `docs/repo-index.md`.
3. Current state or handoff files, such as `harness-state.md`, `handoff.md`, or
   `TODOS.md`.
4. Design docs, requirements, contracts, ADRs, and test fixtures.
5. Source code, scripts, tests, and CI configs.
6. Chat history only as a hint, never as the sole source of truth.

If sources conflict, preserve the conflict in the output and ask only when the
choice affects architecture, data shape, public API, security, or destructive
operations.

## Stage Classifier

Choose the first matching lifecycle stage. If multiple match, choose the
earliest stage that changes the decision.

| Stage | Signals | Route |
| --- | --- | --- |
| Product boundary | What to build, who it is for, product positioning, pricing, public demo scope. | Use product/CEO review or office-hours style workflow. |
| Engineering plan | Architecture, data model, API contract, migration, runtime, cross-module workflow, exception taxonomy. | Use engineering plan review. |
| Implementation | Clear acceptance criteria and bounded files/modules. | Use TDD or the repo's implementation workflow. |
| Debug/investigation | Failing tests, wrong output, 401/500, broken UI flow, data mismatch, unclear root cause. | Use investigation/debugging workflow before patching. |
| QA/browser | User-facing page, browser smoke, console/network errors, screenshots, accessibility, responsive checks. | Use browser QA or report-only QA. |
| Security/privacy | Auth, tokens, credentials, public/private boundary, PII, approvals, audit trail, data leak risk. | Use security review/guardrails before implementation. |
| Review | Diff exists and work is near handoff, PR, or landing. | Use code/diff review. |
| Ship/deploy | Commit, push, PR, merge, release, deploy, or production verification. | Use ship/deploy/canary workflow. |
| Handoff/learning | Save state, summarize, update docs, capture operational learning, prepare next session. | Use checkpoint, learn, retro, or document-release workflow. |

## Harness Contract

For complex work, identify or create these surfaces:

```text
project state
  phase
  source of truth
  latest counts or fixtures
  blocked sources and unsafe inputs
  next safe task
  required commands
  append-only state log

execution harness
  deterministic probes
  tests and smoke checks
  public/private boundary checks
  failure-mode checks
  JSON or structured evidence when useful
```

Use append-only updates for ongoing evidence: phase transitions, refreshed
counts, blockers, approvals, rollback decisions, verification results, browser
smoke results, and handoff notes. Stable rules may be edited in place, but old
evidence should be preserved unless the user explicitly asks for cleanup.

## Exception Handling Principles

For every planned codepath or harness command, name the expected failure mode and
the required behavior.

Prefer these defaults:

- Missing source artifact: fail non-zero, print the missing path, do not write
  partial output.
- Malformed input: fail non-zero, print the parser/field error, do not guess.
- Forbidden field/string: fail non-zero, print the exact offender and location.
- Empty dataset where data is required: fail non-zero with a clear count.
- Auth-required endpoint without token: return or expect `401`, never silently
  fall back to privileged mode.
- Public/private boundary breach: block the output and report the leaking field.
- External service unavailable: surface retryable status, preserve local state,
  and avoid destructive cleanup.
- Partial write risk: write to a temp path first, validate, then promote only
  after success.

If an error can affect users, define what the user sees: clear recovery message,
retry path, fallback, or explicit unavailable state. Silent failure is a critical
gap.

## Verification Routing

Before claiming completion, identify the narrowest fresh gate and include
verification evidence with `command`, `exit_code`, `key_output`, and `timestamp`.

Common gates:

| Work type | Minimum gate |
| --- | --- |
| Any repo change | `git diff --check` plus repo status. |
| Code behavior | Existing unit/integration tests for touched modules. |
| CLI/script/harness | Success case, missing input, malformed input, forbidden input, and no partial write. |
| API boundary | Auth success, auth failure, bad request, server error path if practical. |
| Browser/UI | Local server, network/console checks, key interactions, visible error state. |
| Data/public artifact | Allowlist, denylist, count parity, source hash or provenance metadata. |
| Docs/config only | Link/path/command consistency plus `git diff --check`. |

Do not reuse stale verification as fresh evidence. If a command is blocked by
credentials, sandbox, external access, or user approval, report the exact
blocker and the safest next command.

## Output Contract

After routing, state:

1. Lifecycle stage selected.
2. State files and source-of-truth files read.
3. Existing repo-specific harness or skill to delegate to, if any.
4. Required gstack/skill/tool workflow for this stage.
5. Required probes and verification gates.
6. Failure modes that must be handled.
7. Any user decision, credential, approval, or external dependency blocking safe
   execution.

Do not start substantial implementation before this routing step when the task
is ambiguous, cross-module, security-sensitive, data-sensitive, release-facing,
or likely to span multiple sessions.
