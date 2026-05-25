---
name: shipq-gmail-quote-workflow
description: Use when working in the ShipQ repo on Gmail/Chrome quote intake, Gmail thread scope analysis, MGF/ShipAI quote phase pricing, GeminiExtractor capture, sanitized Gmail fixtures, location normalization, Get Rate eligibility, or local-vs-remote sequencing for Gmail AI quote workflows.
---

# ShipQ Gmail Quote Workflow

## Overview

Use this after `shipq-lifecycle-harness` when the request is specifically about the Gmail quote workflow. Keep source evidence, local implementation slices, live provider capture, and remote production integration separated.

## Startup

```bash
cd /Users/kezheng/Codes/CursorDeveloper/ShipQ
git status --short --branch
test -f AGENTS.md && sed -n '1,220p' AGENTS.md
test -f docs/repo-index.md && sed -n '1,220p' docs/repo-index.md
test -f docs/designs/harness-state.md && tail -n 220 docs/designs/harness-state.md
find docs -maxdepth 3 -type f \( -iname '*gmail*' -o -iname '*quote*' -o -iname '*handoff*' -o -iname '*location*' \) | sort
```

Read the relevant design/handoff files before editing. Prefer repo artifacts over chat memory.

## Workflow

1. Classify the request:
   - Gmail thread estimate or client email: extract explicit ask, implementation prerequisites, phase split, pricing floor, and security controls.
   - Gmail intake implementation: stay inside the approved local slice unless the task explicitly opens remote/live integration.
   - Gemini capture: keep protocol/fake-client tests separate from live capture; never promote provider JSON until local contract validation passes.
   - Location handling: treat stable ShipQ-owned IDs as primary keys; keep aliases in master data or alias rules, not shipment payloads.
2. State the boundary before making changes:
   - Local: parser, contract, fake clients, tests, sanitized fixtures, docs, handoff.
   - Live provider: Gemini key use, capture CLI, captured JSON review.
   - Remote/production: Cloud SQL cutover, OAuth/admin install, Cloud Run, Apps Script, customer credentials.
3. Preserve these recurring rules:
   - Manual key-field repair may save recoverable fixes, but structural/source/audit/contract errors still block mutation.
   - `validation_failed` is recoverable only for allowed key-field edits; invalid extracted payload writes still roll back.
   - Sanitized Gmail fixtures contain Gmail-safe input plus provider-capture metadata, not hand-authored expected payloads.
   - Local/demo Gemini capture may use developer credentials; production must use customer-owned credentials such as Vertex AI where applicable.
4. For client-facing scope/pricing work, keep security and business-rule complexity visible. OAuth, minimal permissions, manual trigger, selected-thread access, preview before send, audit logs, rate/markup control, quote template generation, approval, and send flow are real scope items.
5. If producing a handoff, write a repo-local durable document and include the resume prompt in the final answer when the user asks for it.

## Verification

Run the narrowest relevant gate first, then broader gates when code paths or contracts changed:

```bash
git diff --check
PATH=.venv/bin:$PATH pytest -q tests/test_gmail_quote_intake_endpoints.py
PATH=.venv/bin:$PATH pytest -q tests/test_gmail_quote_intake_cloud_sql_adapter.py
PATH=.venv/bin:$PATH pytest -q tests/test_gmail_quote_intake_gemini_capture_script.py tests/test_gmail_quote_intake_gmail_samples.py
PATH=.venv/bin:$PATH pytest -q
```

Only run live Gemini capture when credentials and explicit opt-in are present:

```bash
SHIPQ_ALLOW_LIVE_GEMINI_CAPTURE=1 SHIPQ_GEMINI_PROVIDER=developer_api_key PATH=.venv/bin:$PATH python scripts/capture_gmail_quote_gemini_samples.py --help
```

Final answers that claim completion must include `command`, `exit_code`, `key_output`, and `timestamp`.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating Chronicle-visible pytest or merge output as proof | Re-run the relevant command in the current session. |
| Blending local hardening with Cloud SQL/OAuth/live deployment | Split the plan into local, live-provider, and remote production slices. |
| Hand-authoring expected Gemini output in sanitized fixtures | Store input and capture metadata only until contract validation passes. |
| Cutting scope to hit a pricing floor after the user rejected that tradeoff | Use package pricing while preserving scope unless asked otherwise. |
