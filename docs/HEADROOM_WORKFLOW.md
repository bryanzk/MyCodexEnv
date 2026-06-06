# Headroom Workflow

This repo uses Headroom as an optional local filter for large command outputs
before those outputs are pasted into Codex, Claude, or another agent context.
It is most useful for `rg` results, test/build logs, large JSON arrays, and
other tool outputs. It is not a replacement for reading source code when exact
code is needed.

## Install

Use an isolated Python 3.12 environment. The default Homebrew `python3` may be
newer than the wheels published by `headroom-ai`.

```bash
/opt/homebrew/bin/python3.12 -m venv /tmp/headroom
/tmp/headroom/bin/pip install headroom-ai
```

The wrapper disables Headroom telemetry by default unless the environment
already sets `HEADROOM_TELEMETRY`.

## Command Output Filter

Use `scripts/headroom_filter.py` as a stdin-to-stdout filter:

```bash
command-producing-large-output \
  | /tmp/headroom/bin/python scripts/headroom_filter.py --mode auto --stats
```

The compressed output is written to stdout. A compact JSON receipt is written to
stderr when `--stats` is present.

Modes:

| Mode | Use for |
| --- | --- |
| `auto` | Detect search, diff, JSON, or log output. |
| `search` | `rg`, `grep`, or `ag` output shaped as `path:line:text`. |
| `log` | Test output, build output, harness logs, long Markdown state logs. |
| `diff` | Unified diffs. This may intentionally save little when every changed line matters. |
| `json` | JSON arrays or objects containing arrays, such as API/tool results. |

Detection without importing Headroom:

```bash
rg -n "gmail|quote|extract" src tests docs \
  | python3 scripts/headroom_filter.py --detect-only
```

## ShipQ Examples

Compress large ShipQ search output:

```bash
cd /Users/kezheng/Codes/CursorDeveloper/ShipQ
rg -n "gmail|quote|extract|review|customer|route|cargo" src tests docs html \
  | /tmp/headroom/bin/python /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/scripts/headroom_filter.py \
      --mode search \
      --context "ShipQ Gmail quote extraction review customer route cargo" \
      --stats
```

Compress a ShipQ test log:

```bash
cd /Users/kezheng/Codes/CursorDeveloper/ShipQ
PATH=.venv/bin:$PATH pytest -q 2>&1 \
  | /tmp/headroom/bin/python /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/scripts/headroom_filter.py \
      --mode log \
      --context "ShipQ pytest failures warnings summary" \
      --stats
```

Compress the latest harness state tail:

```bash
cd /Users/kezheng/Codes/CursorDeveloper/ShipQ
tail -n 2000 docs/designs/harness-state.md \
  | /tmp/headroom/bin/python /Users/kezheng/Codes/CursorDeveloper/MyCodexEnv/scripts/headroom_filter.py \
      --mode log \
      --context "latest ShipQ state blockers verification next safe task" \
      --stats
```

## Where To Use It

Use Headroom before sending bulky command output into a model:

- `rg` output with hundreds or thousands of matches.
- `pytest`, build, or server logs where failures and warnings matter most.
- JSON-heavy API responses, database rows, or fixture arrays.
- Long append-only state logs when the current tail is more important than
  every historical line.

Avoid using it for:

- Source files that you are about to edit.
- Short outputs.
- Security-sensitive material, secrets, tokens, or customer data.
- Diffs where every changed line must be reviewed exactly.

For normal Codex work, keep the source command in the final verification
evidence and mention that `headroom_filter.py` only compressed the displayed
context, not the underlying command output.
