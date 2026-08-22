# Frozen DHF Token-Cost Tasks

These prompts are the immutable inputs for the P0 before/after measurements. P0-1 records them but does not run them. Every future result must also record the exact Git HEAD, `skills-lock.json` SHA-256, and `~/.codex/config.toml` SHA-256 used for that run.

## Light · Read-only answer

```text
Read CONTEXT.md and docs/repo-index.md. In no more than five bullets, explain the difference between a DHF phase, lane, checkpoint, and next safe task. Do not modify files, run tests, access the network, or use subagents. Cite the repository file that defines each term.
```

Quality gate: every definition agrees with `CONTEXT.md`; no repository changes.

## Standard · One script and one test

```text
In an isolated clean worktree, add a --version flag to a provided small Python CLI script and add one focused regression test for it. Touch only the named script and its named test file. Run the focused test and git diff --check. Do not commit, push, deploy, access customer data, or use subagents. Report command, exit_code, key_output, and timestamp.
```

Quality gate: focused regression passes; only the two authorized files change; `git diff --check` passes.

## Governed · Two-worker agent team

```text
Prepare and execute a governed two-worker agent-team task in an isolated clean worktree. Worker A may edit only one named documentation page; Worker B may edit only its disjoint focused test file. Validate the team plan before dispatch, require exact write sets and verification commands, integrate both results, and run the focused gate plus git diff --check. Do not commit, push, deploy, modify runtime state, or access private/customer data. Preserve a clear rollback and report command, exit_code, key_output, and timestamp.
```

Quality gate: agent-team validation passes; worker write sets are disjoint; the focused test and diff check pass; no runtime or remote mutation occurs.

Run policy: the light and standard tasks require at least three before runs. Under owner decision D4, the governed task gets one before run first; the owner decides whether to add runs two and three after inspecting that reporter output.

Governed accounting scope: parent rollout visible. The governed run 1 time-window probe found no independent child rollout that could be linked to the parent, so worker usage cannot be separated from the parent rollout.

## aborted_runs

### standard 2 · 2026-08-22T12:33:34.939Z

- Reason: sandbox denial interrupted the run after the following command was rejected with `zsh:1: operation not permitted: ps`:

  ```text
  ps -axo pid,ppid,etime,args | rg '(^| )81814|test_runner.py|check_codex_skill_loader|app-server'
  ```

- Before interruption: `requests_total=38`; `input=2683366`.

Every aborted run must be recorded in this section. This section is the data source for the failure/retry metric.

## identity_drift

### Governed runs 2–3 · 2026-08-22

- Decision: option (b). Governed runs 2 and 3 are not comparable with governed run 1 and are retained with `-DRIFT.json` filenames.
- Governed run 1: rollout started at `2026-08-22T12:41:39Z` and its last token event was `2026-08-22T12:51:54.707Z`; recorded config SHA-256 was `30dac4fc328443011fa7bdf5dc067a9b2380b263870649500e5cddfc61ec59a7`.
- Current config: mtime `2026-08-22T09:07:17-0400` (`2026-08-22T13:07:17Z`), before governed run 2 started at `2026-08-22T13:15:22Z`; SHA-256 is `da39d3671936efa89ee4c9a9953dbbb6bbd17393273b6f59758abcda41b4acae`.
- Backup-chain break: no `~/.codex/config.toml.backup.*` file has the governed run 1 hash. The newest matching-pattern backup is dated `2026-08-06T15:21:47-0400`, so the exact governed run 1 content is unavailable.
- `diff -u`: unavailable because the old content is absent. No substitute backup is presented as the governed run 1 file.
- Protected-field verdict: unverified. Without the old content, the diff cannot prove that `model`, reasoning/context settings, features, MCP servers, or hooks were unchanged.
- Source: owner. Owner confirmed the `2026-08-22T09:07:17-0400` local change was `model_reasoning_effort` from `medium` to `ultra`, changed manually by the owner; the absence of a matching `sync_codex_home.sh` backup, sync log, or rollout write remains consistent with that confirmation.
- Current model line: `model = "gpt-5.6-sol"`.
