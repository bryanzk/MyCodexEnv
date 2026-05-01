---
name: search-codex-conversations
description: Use when a user asks to search local Codex conversation history by keyword, recall how something was handled before, find prior thread titles or chat snippets, or look up past decisions stored in this machine's ~/.codex sessions.
---

# Search Codex Conversations

## Overview

Use the bundled script instead of manually grepping `~/.codex`.
It reads thread metadata from `~/.codex/state_5.sqlite`, follows each thread's
`rollout_path`, and returns matched thread titles plus relevant user/assistant
snippets from the local Codex JSONL session store.

Do not use this for repo code search. Use `rg` in the repo for that.
If you want a shell command, use `codex-chat-search`.

## Workflow

1. Start with the default search:

```bash
codex-chat-search <keyword ...>
```

2. Keep the default role filter (`user,assistant`) unless you explicitly need
   prompt or AGENTS text.
3. Narrow broad searches with `--scope`, `--role`, `--after`, `--before`,
   `--archived`, or `--limit`.
4. Use `--json` when the result needs to be fed into another step.
5. Run `--help` for the full flag list.

## Quick Reference

| Need | Command |
| --- | --- |
| Search title + messages | `codex-chat-search arbitrage morpho` |
| Only thread titles | `codex-chat-search morpho --scope title` |
| Only user prompts after a date | `codex-chat-search pipeline --role user --after 2026-03-01` |
| Archived threads only | `codex-chat-search skill --archived only` |
| OR match instead of AND | `codex-chat-search price missing --any` |
| Machine-readable output | `codex-chat-search pnl review --json` |

## Common Mistakes

- Do not grep `~/.codex` blindly first; the script already handles metadata,
  archive status, title matching, and snippet extraction.
- Do not include `developer` unless you really want system prompts, AGENTS text,
  or tool policies. It creates a lot of noise.
- If a keyword is too broad (`skill`, `test`, `bug`), add another keyword or a
  date filter.
- Default matching is case-insensitive AND across all keywords. Use `--any` if
  you want OR semantics.
- If `codex-chat-search` was just installed in the current `zsh` shell and does
  not run immediately, execute `rehash` once.
