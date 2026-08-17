---
name: invoice-filing
description: Archive and synchronize a finalized customer invoice across approved secure storage, accounts-receivable or bookkeeping records, supporting trackers, and Linear collection follow-up. Use when the user asks to file or archive an invoice PDF, sync the invoice to related platforms or apps, record the receivable, or create or update a collection and reconciliation task. Do not use to generate or edit an invoice, send it to the customer, record a payment, or process an expense or reimbursement.
---

# Invoice Filing

File one finalized customer invoice and keep its archive, receivable record, and
collection task consistent. Treat each system as a separate state; never infer
that an invoice was sent, posted, paid, or reconciled from another action.

## Workflow

### 1. Validate The Source

Read the invoice and its current source metadata. Confirm:

- legal entity and customer
- invoice number, issue date, due date or payment terms
- currency, subtotal, tax, and total
- one readable final PDF

Do not edit the invoice. Prefer values inside the PDF over a manually typed
filename. Stop on conflicting identifiers, dates, totals, duplicate-looking
final versions, or an unreadable attachment.

### 2. Resolve Authority And Targets

Read the current repository policy, system map, and target records before any
write. Resolve the approved secure archive, formal accounting or receivables
system, optional supporting tracker, and Linear project from live metadata.

For every write, establish the target system, object, action, actor, operation
key, expected result, independent readback, failure behavior, and correction
path. A request to sync "related platforms" authorizes discovery, not guessing
which systems to mutate. Ask when the current map or write scope is ambiguous.

Never place the invoice PDF, raw financial data, credentials, or private
attachments in an operations repository or Git history.

### 3. Check For Duplicates

Search every applicable target before writing. Use the invoice number as the
primary key and customer, date, currency, and total as secondary checks. Use a
stable operation key such as `invoice:<issuer>:<invoice-number>`.

Update a matching record when safe. Stop on conflicting matches or when the
same invoice may already be posted under another identifier. Do not treat a
matching filename alone as proof of identity.

### 4. Archive The Canonical PDF

Copy the final PDF into the existing approved business-record hierarchy; do not
delete the source. Use the repository's live naming convention, derived from
verified invoice data. Reopen or read back the stored item and verify its name,
location, stable object ID, readable content, and size or digest when supported.

Keep the archive system authoritative for the attachment. Store links or
sanitized pointers elsewhere instead of additional uncontrolled copies.

### 5. Record The Receivable

If explicitly authorized, create or match the invoice in the formal accounting
or accounts-receivable system. Preserve the PDF's customer, invoice number,
issue date, due date or terms, currency, line totals, tax, and total. Do not
invent tax treatment or silently substitute today's date.

Record the invoice as issued and outstanding unless authoritative evidence
proves a later state. Do not mark it sent, paid, deposited, or reconciled and do
not create a bank transaction. Read back the transaction ID, invoice fields,
balance due, status, and archive link.

Update an existing supporting receivables tracker only when it is part of the
current system map. Preserve its structure and formulas, link to authoritative
records, and verify the written cells by readback.

### 6. Create Collection Follow-Up

Search Linear before creating anything. Update the existing issue for the
invoice when one exists; otherwise create one only when requested. Include the
invoice number, due date or terms, current outstanding state, authoritative
archive and accounting links, owner, and the next action.

Keep separate checklist items for delivery evidence, payment follow-up, payment
receipt, accounting match, and final reconciliation. Never invent a due date or
close the issue merely because filing or bookkeeping completed.

### 7. Verify End To End

Re-query or reopen every written object independently; a successful mutation
response is not readback. Report each applicable state separately:

- `source_validated`: the final PDF and invoice fields agree
- `archive_verified`: the canonical stored PDF is readable
- `receivable_recorded`: the formal outstanding receivable matches the PDF
- `tracker_synced`: the optional supporting record matches authoritative data
- `collection_task_ready`: Linear points to the verified records and next step
- `invoice_sent`: separate delivery evidence exists
- `payment_received`: separate payment evidence exists
- `payment_reconciled`: the payment is matched in the accounting system

For every completion claim, provide `command` or action, `exit_code` or result,
`key_output`, and `timestamp`. Mark unsupported states as `not_requested`,
`not_authorized`, `blocked`, or `unverified`; never collapse partial completion
into "synced" or "done".

## Stop Conditions

Stop before the affected write when the source is not final, the target or
authority is unresolved, a duplicate conflict exists, required accounting data
is missing, tax treatment is uncertain, independent readback fails, or rollback
or correction is unavailable. Preserve verified earlier states and report the
exact boundary without blind retries.
