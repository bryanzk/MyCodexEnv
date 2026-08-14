# Evaluation Results

Date: 2026-08-14

Method: manual paired test. No external model runner was used. The without-skill baseline is the observed behavior in local thread `019dea4e-b799-7d60-ac24-8f278f526dc0`; the with-skill result is a dry run of the analogous incomplete-input case against the current `SKILL.md` and the rubric in `eval-matrix.md`.

## Existence verdict

Pass, narrowly. A generic PDF skill covers export mechanics but not ShipAI's stale-customer guard, exact financial-field coupling, approved-template constraint, or export/send/bookkeeping state separation.

## Routing review

- Positive prompts: 4/4 should load from the explicit ShipAI invoice creation or export intent.
- Negative prompts: 4/4 should not load because the description excludes ingestion, bookkeeping, receipts, and generic PDF work.
- Forbidden-load prompts: the skill cannot authorize email, accounting, or receipt-collection actions.
- Neighbor boundary: the generic PDF skill may co-load for rendering, while `shipai-sync-reimbursement-expense` owns personally paid expense synchronization rather than customer invoice creation.

## Paired result

Prompt shape: continue the current ShipAI invoice, change its date, description, hours, and rate, then export it as PDF while the template already contains customer and tax values.

| Assertion | Without skill | With skill |
| --- | --- | --- |
| Does not silently reuse stale customer or financial fields | Fail: the response did not surface a critical-field preservation check before reusing bill-to and 13% tax from the current template | Pass: Step 4 blocks export until critical fields are supplied or explicitly preserved |
| Verifies arithmetic and currency rounding | Pass | Pass |
| Validates source before export | Pass | Pass |
| Visually checks the complete one-page PDF | Fail: page count was checked, but the attempted browser readback did not complete | Pass: Steps 7 and 9 require complete rendered inspection and readback |
| Separates export, send, and accounting states | Pass | Pass |

Score: without skill `3/5`; with skill `5/5`; lift `+2`, with no identified safety regression.

## Progressive-loading result

- Normal invoice generation: do not read evaluation files.
- Skill review or revision: read `eval-matrix.md`; read this file only for the latest evidence.
- No script or asset loading exists, so there is no unused bundled runtime content.

## Remaining evidence gap

The paired test is manual and single-model. Before changing the description or broadening the workflow, rerun `evals/evals.json` with a baseline-capable runner across the primary and a smaller model.
