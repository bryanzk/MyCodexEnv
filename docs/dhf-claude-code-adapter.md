# DHF Guard for Claude Code

Status: adapter and installer are in the repository and tested. Installed only in
the probe repository `bryanzk/dhf-host-probe`. No host probe has run yet; see
`docs/dhf-conformance.json` for the current state of every cell.

Contract: `docs/dhf-spec.md`, sections 7 to 9. The adapter covers Restrict in
the default profile. Position, Empower, Contain, Observe, Thread, and Transact
have no Claude Code adapter.

## Files

| File | Role |
| --- | --- |
| `dhf/core/guard_core.py` | Host-neutral decision and receipt. Shared with the Codex adapter |
| `dhf/adapters/claude_code/dhf_guard.py` | Claude Code adapter. Carries a verbatim copy of the core (`scripts/build_guard_bundle.py`) |
| `dhf/adapters/claude_code/settings.fragment.json` | The two `PreToolUse` registrations |
| `scripts/install_claude_code_guard.py` | Copies the adapter into a repository and merges the registrations |

## Where the Guard runs

The Guard travels with the repository: `.claude/hooks/dhf_guard.py` plus two
entries in `.claude/settings.json`.

| Kind of session | Repository hooks | Source |
| --- | --- | --- |
| Local Claude Code | run | documentation; not probed |
| Cloud session with one repository, outside a Project | run | documentation; not probed |
| Cloud thread in a claude.ai Project | do not run | documentation, and observed twice on 2026-11-27 |
| Anthropic-hosted cloud session with several repositories | do not run | documentation; not probed |

For the last two kinds the Guard is not a landing point. Enforcement there has
to come from host-external points: branch protection, CI, credential scope.

## Tool mapping

Tool names are case-sensitive on this host.

| Tool | Field read | Action kind |
| --- | --- | --- |
| `Write` | `file_path`, `content` | write |
| `Edit` | `file_path`, `old_string`, `new_string` | write |
| `MultiEdit` | `file_path`, `edits` | write |
| `NotebookEdit` | `notebook_path` | write |
| `Read` | `file_path` | read |
| `Glob` | `path` (optional) | read |
| `Grep` | `path` (optional) | read |
| `Bash` and every other tool | none | not judged |

There is no structured delete on this host. Every delete and move goes through
`Bash`, which the Guard does not parse. This is the known gap of specification
section 8, and it is wider here than on Codex.

One rule lives in the adapter, not in the core: a `Grep` whose root is a
credential location or contains one is denied with `credential_target_access`.
A content search prints matching lines of every file under its root, and the
core judges single files.

## Protected locations

Owner decision of 2026-11-26.

- Control plane, for the project: `.claude/settings.json`,
  `.claude/settings.local.json`, `.claude/hooks/`.
- Control plane, for the user: `~/.claude/settings.json`,
  `~/.claude/settings.local.json`, `~/.claude/hooks/`, `~/.claude/dhf/`.
- Credentials: `~/.claude/.credentials.json`, plus the core's own list
  (private keys under `~/.ssh`, `~/.aws/credentials`, `~/.netrc`).
- OS persistence: the core's own list (shell startup files, launch agents).

Not protected: `CLAUDE.md`, `.claude/skills/`, `.claude/agents/`. They change in
ordinary work and stay under written rules and review.

## Response and fault rule

- A denial is `hookSpecificOutput.permissionDecision = "deny"` with the reason
  `[harness] <reason code>`, exit code 0.
- No output means no decision: the host's own permission flow continues.
- When the adapter raises, it denies `Write`, `Edit`, `MultiEdit`, and
  `NotebookEdit` with `[harness] guard_fault` and lets every other call through.
- A Guard that cannot start or that times out never reaches that rule. The
  write registration therefore carries `"onFailure": "block"`, which makes the
  host block the call. The read registration does not, so a broken Guard cannot
  stop reads. `onFailure` needs Claude Code 2.1.295 or later.

## Receipt

`~/.claude/dhf/guard-receipt.json` and `~/.claude/dhf/evidence/<date>.jsonl`,
in the same format as the Codex receipt, with `host`, `remote`, `project_dir`,
and `profile` added. In a cloud session these files live in the session's
virtual machine and are lost with it. Evidence for a cloud host is the probe
receipt in the conformance table.

## Install

```
python3 scripts/install_claude_code_guard.py --repo <path>          # report only
python3 scripts/install_claude_code_guard.py --repo <path> --write  # apply
```

`--write` keeps every setting and hook that other tools registered and replaces
only the entries that run `.claude/hooks/dhf_guard.py`. A repository's
`.claude/settings.json` is a control file: run `--write` only with the owner's
authorization for that repository, and commit the two files so cloud sessions
get them.

## Not done

- No host probe yet. Probes are defined in `docs/dhf-conformance.json`
  (`restrict.cc-local-*`, `restrict.cc-cloud-*`) and in `PROBE.md` of
  `bryanzk/dhf-host-probe`.
- No `permissions.deny` rules as a second layer. The rule syntax has to be
  checked against the Claude Code permissions documentation first.
- Not installed in ShipQ.
- Whether a `deny` from a hook holds in `bypassPermissions` mode, and whether a
  subagent's tool calls reach the hook, are not confirmed.
