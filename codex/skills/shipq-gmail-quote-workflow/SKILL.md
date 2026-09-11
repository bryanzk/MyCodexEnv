---
name: shipq-gmail-quote-workflow
description: Use for ShipQ Gmail or Chrome quote intake, thread analysis, Gemini capture, sanitized fixtures, location normalization, Get Rate eligibility, or Gmail quote delivery boundaries.
---

# ShipQ Gmail Quote Workflow

Start directly from the current ShipQ repository, its applicable `AGENTS.md`,
and the target files. Read design, handoff, state, or policy documents only when
the current task depends on them. Invoke `shipq-lifecycle-harness` only for
state recovery or a real runtime, deployment, protected-data, authorization, or
handoff boundary.

Keep source evidence, local implementation, live provider capture, and remote
production integration as separate lanes.

## Workflow Boundaries

- For a Gmail thread estimate or client email, extract the explicit ask,
  implementation prerequisites, phase split, pricing floor, and security
  controls from the supplied evidence.
- Keep Gmail intake implementation inside the approved local slice unless the
  task explicitly opens live provider or remote integration.
- Keep Gemini protocol and fake-client tests separate from live capture. Do not
  promote provider JSON before local contract validation passes.
- Use stable ShipQ-owned location IDs as primary keys; keep aliases in master
  data or alias rules rather than shipment payloads.
- Manual key-field repair may save allowed recoverable fixes. Structural,
  source, audit, and contract errors still block mutation; invalid extracted
  payload writes still roll back.
- Sanitized Gmail fixtures contain Gmail-safe input and provider-capture
  metadata, not hand-authored expected provider payloads.
- Local/demo capture may use authorized developer credentials. Production uses
  customer-owned credentials, such as Vertex AI where applicable.
- Client-facing scope keeps OAuth, minimal permissions, manual trigger,
  selected-thread access, preview before send, audit logs, rate/markup control,
  quote generation, approval, and sending visible when they apply.
- Create a repo-local handoff only when the user requests one and authorizes its
  path.

## Verification

Use ShipQ `AGENTS.md` as the only verification router. Run the narrowest
applicable gate, reuse valid evidence for unchanged inputs, and do not add a
separate full suite or duplicate harness-covered tests.

Live Gemini capture requires credentials and explicit opt-in. Keep source-test,
runtime, provider, remote deployment, and customer-acceptance receipts distinct.
Completion receipts must use the fields required by `AGENTS.md`.
