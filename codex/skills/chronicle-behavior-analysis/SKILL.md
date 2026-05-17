---
name: chronicle-behavior-analysis
description: Use when analyzing Chronicle memories, desktop activity, app usage, Chrome History, shell history, workflow fragmentation, repeated habits, or productivity/security recommendations from local machine evidence.
---

# Chronicle Behavior Analysis

## Overview

Use this when the user wants evidence-backed critique from Chronicle or local machine activity. Verify the actual Chronicle source first; if it is missing or incomplete, say so before using fallback evidence.

## Evidence Order

1. Chronicle exports/resources:
   - `~/.codex/memories/extensions/chronicle/resources`
   - `~/.codex/memories_extensions/chronicle/resources`
2. macOS foreground activity:
   - `~/Library/Application Support/Knowledge/knowledgeC.db`
3. Browser activity:
   - Chrome History, queried read-only
4. Shell activity:
   - `~/.zsh_history`, including repetitive command patterns and accidental secret exposure

## Workflow

1. Locate and timestamp the data sources. Do not infer from open tabs alone.
2. Separate passive visibility from active work. A visible Codex window, browser tab, or artifact preview is context, not proof that commands ran.
3. Quantify app usage, app switching, high-frequency domains, shell friction, and repeated blockers where possible.
4. Redact sensitive details from mail, banking, chat, credentials, and private pages. Preserve only neutral workflow context.
5. If the user asks for blunt critique, lead with the highest-impact problem and a concrete fix. Avoid generic productivity advice.
6. If a secret appears in history or screenshots, tell the user to rotate it and avoid printing the secret.

## Query Notes

For Chrome History CTEs, avoid naming a CTE `visits`; that has caused `circular reference: visits`.

For Chronicle snapshots, treat OCR/browser state as secondhand evidence unless this session reruns the command or opens the live source.

## Output Contract

Return:

- Data sources used and their freshness.
- What is directly evidenced versus inferred.
- Repeated workflows or friction patterns.
- Ranked fixes with expected impact.
- Any security exposure without reproducing secrets.

For verification-sensitive claims, include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Saying "Chronicle shows" before finding Chronicle data | Verify the export/resource path first. |
| Treating open tabs as active work | Label them as passive context unless paired with command/editor evidence. |
| Giving soft productivity advice | Tie each recommendation to measured behavior. |
| Printing secrets from history | Redact and recommend rotation. |
