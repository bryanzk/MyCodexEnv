# LinkedIn Flow Visuals

## Objective

Produce a complete English LinkedIn-ready visual package derived from the existing HTML lifecycle flow: a fuller process-flow image, an introductory image, and multiple polished style samples inspired by Anthropic and OpenAI design language, then continue execution until final usable image artifacts exist.

## Original Request

Use GoalBuddy to create a board, then without further questions generate a relatively complete flowchart from the HTML flow diagram, add an introductory image, and create several samples whose design style may reference Anthropic and OpenAI.

## Intake Summary

- Input shape: `specific`
- Audience: potential customers and LinkedIn viewers
- Authority: `requested`
- Proof type: `artifact`
- Completion proof: final image artifacts exist, are visually inspected for readability, and map back to the HTML flow content and requested style directions.
- Likely misfire: creating generic pretty posters that do not preserve the actual lifecycle flow, or stopping after board setup without producing final images.
- Blind spots considered: text readability, LinkedIn aspect ratio, exact flow fidelity, over-copying brand styles, generated-image text drift, and lack of verification receipts.
- Existing plan facts: source HTML is `docs/project-lifecycle-harness-flow-skills.html`; previous poster assets exist under `/Users/kezheng/.agent/diagrams/`; reference style requests include blue glass variants, Anthropic-inspired, OpenAI-inspired, complete flowchart, and intro image.

## Goal Kind

`specific`

## Current Tranche

Continuously execute safe verified slices until the full owner outcome is complete: inspect source artifacts, extract the complete lifecycle flow, define design directions, generate or render multiple image candidates, select and polish final artifacts, save them to durable paths, and run a final audit against the original request.

## Non-Negotiable Constraints

- Do not ask the user for more design choices unless execution is blocked by missing access, policy, or impossible constraints.
- Preserve the source flow meaning from the HTML lifecycle diagram.
- Produce final image artifacts, not just plans or board cards.
- Keep generated outputs suitable for LinkedIn publishing.
- Avoid claiming direct Anthropic or OpenAI brand ownership; use design-style references rather than logos or brand marks unless already present in the source.
- Maintain readable English text in final candidates.
- Record verification evidence for completion claims.

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after a single verified Worker slice when the broader owner outcome still has safe local follow-up slices. After each slice audit, advance the board to the next highest-leverage safe Worker task and continue.

Do not stop because a slice needs owner input, credentials, production access, destructive operations, or policy decisions. Mark that exact slice blocked with a receipt, create the smallest safe follow-up or workaround task, and continue all local, non-destructive work that can still move the goal toward the full outcome.

## Canonical Board

Machine truth lives at:

`docs/goals/linkedin-flow-visuals/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/linkedin-flow-visuals/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Run the bundled GoalBuddy update checker when available and mention a newer version without blocking.
4. Re-check the intake: original request, input shape, authority, proof, blind spots, existing plan facts, and likely misfire.
5. Work only on the active board task.
6. Assign Scout, Judge, Worker, or PM according to the task.
7. Write a compact task receipt.
8. Update the board.
9. If Judge selected a safe Worker task with `allowed_files`, `verify`, and `stop_if`, activate it and continue unless blocked.
10. Treat a slice audit as a checkpoint, not completion, unless it explicitly proves the full original outcome is complete.
11. Finish only with a Judge/PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
