---
name: shipai-public-quote-sync
description: Use when the shipAI website consumes ShipQ quote-demo logic, public quote scenarios, static JSON artifacts, homepage quote demo changes, Cloudflare Pages deployment checks, or Remotion demo-video follow-up.
---

# shipAI Public Quote Sync

## Overview

Use this when `shipAI website` needs ShipQ quote-demo capability without exposing ShipQ internals. The default architecture is a static public-safe sync artifact, not a live internal API call.

## Boundaries

- ShipQ remains the quote/demo source system.
- The website consumes allowlisted public artifacts only.
- Do not expose workbook traces, `component_trace`, `source_row`, customer groups, internal generated artifacts, or private ShipQ API responses on the public site.
- If a live site looks stale after deployment, compare branch/deployment source before debugging UI code.

## Startup

```bash
cd "/Users/kezheng/Codes/CursorDeveloper/shipAI website"
git status --short --branch
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
find . -maxdepth 3 -type f \( -name '*quote*' -o -name 'test_runner.py' -o -name '*.json' \) | sort
```

If source artifacts come from ShipQ, inspect the source repo too:

```bash
cd /Users/kezheng/Codes/CursorDeveloper/ShipQ
git status --short --branch
test -f docs/repo-index.md && sed -n '1,180p' docs/repo-index.md
```

## Workflow

1. Confirm the accepted public-safe data contract before implementation.
2. Sync only allowlisted fields into website-side JSON, normally `quote-demo-scenarios.json` plus `quote-demo-source.json`.
3. Use the repo sync script when present, for example `scripts/sync_shipq_public_scenarios.py`.
4. Validate both source and website gates. Public JSON must load through an HTTP server, not only through direct file open.
5. For homepage integration, preserve high-intent CTA paths and compatibility redirects unless the user explicitly asks to remove them.
6. For Cloudflare Pages, verify the deployed branch/commit. A green deployment can still point at an older branch.
7. Keep Remotion demo-video work isolated under its own project directory unless the user asks to merge it into the static site.

## Verification

Typical source gate in ShipQ:

```bash
python3 test_runner.py
pytest -q
```

Typical website gate:

```bash
python3 test_runner.py
git diff --check
python3 -m http.server 8787 --bind 127.0.0.1
```

Browser smoke should check:

- `index.html#quote-demo` renders.
- `/quote-demo-scenarios.json` returns `200`.
- `/quote-demo-source.json` returns `200`.
- Scenario count and displayed ranges match expected public artifacts.
- Forbidden internal terms are absent.
- Console has no errors.

Final answer must include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Wiring website directly to ShipQ internal APIs | Use static public-safe JSON artifacts. |
| Opening `index.html` directly for JSON-backed demos | Use a local HTTP server and browser smoke. |
| Debugging CSS when public site is stale | Compare branch/source/commit first. |
| Publishing public workbook evidence | Keep workbook traceability inside ShipQ-only artifacts. |
