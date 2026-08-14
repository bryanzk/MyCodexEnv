---
name: shipai-generate-invoice-pdf
description: Create, revise, or export a ShipAI customer invoice from the approved Option 3 HTML template. Use when a user asks to make or update a ShipAI invoice, provides invoice fields such as invoice number, date, customer, description, hours, rate, or tax, asks to export the current ShipAI invoice as PDF, or references invoice-option-3-compact-executive.html; do not use for invoice ingestion, bookkeeping, expense receipts, or generic PDF work.
---

# ShipAI Invoice PDF

Produce a reviewed invoice HTML source and a verified one-page PDF. Keep creation, export, sending, and bookkeeping as separate states.

## Workflow

1. Read the target repository instructions and inspect the current worktree. Reuse `html/invoice-option-3-compact-executive.html`; do not redesign the invoice or add another template.
2. Freeze the requested write set. Preserve unrelated and user-owned changes. If the user says to continue the current invoice, inspect its present values before editing.
3. Require or explicitly preserve every business-critical field:
   - invoice number and invoice date
   - bill-to identity and address
   - description, quantity, unit, and unit price
   - currency, tax rate or tax treatment, subtotal, tax, and total
   - payment terms and remittance details
4. Stop for missing or conflicting customer, tax, currency, payment, or remittance data. Never infer these values from an older invoice. Treat visible template values as unverified until the user explicitly supplies or preserves them.
5. Recalculate with exact decimal arithmetic: line total equals quantity times unit price; subtotal equals the sum of line totals; tax uses the approved rate and base; total equals subtotal plus tax. Round currency to two decimals. Do not assume a default tax rate.
6. Make the smallest field-only HTML edit. Update every visible copy of the changed values and remove stale duplicates. Do not alter branding, layout, or unrelated content.
7. Validate the HTML before export:
   - assert all approved values are present
   - assert superseded invoice numbers, dates, customers, and amounts are absent
   - confirm the arithmetic identities
   - render the page and inspect the complete invoice
8. Export with the existing browser/PDF tooling to the repository-approved invoice output directory. Derive a stable filename from the invoice number. Exporting does not authorize emailing, uploading, posting to accounting software, or changing external records.
9. Reopen the PDF and verify it is non-empty, exactly one page, legible, and free of clipping, overlap, broken glyphs, stale fields, browser headers, or footers. Compare its visible values with the approved input.
10. Return links to the HTML and PDF plus fresh receipts containing `command`, `exit_code`, `key_output`, and `timestamp`. State separately whether the invoice was only drafted, exported, sent, or recorded.

## Failure Handling

- If the PDF is multi-page or visually defective, adjust only print CSS or the smallest relevant layout rule, then rerender and recheck.
- If the template is dirty in overlapping fields and ownership is unclear, stop instead of overwriting it.
- If PDF text extraction is incomplete, use visual inspection; do not treat extraction failure as proof that visible fields are missing.
- If export succeeds but readback fails, keep the failed receipt and fix locally. Do not send or post the invoice.

## Evaluation Maintenance

Read `references/eval-matrix.md` only when reviewing or changing this skill. Normal invoice generation must not load evaluation files.
