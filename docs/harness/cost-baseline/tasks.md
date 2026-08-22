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
