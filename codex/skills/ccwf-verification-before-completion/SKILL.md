---
name: ccwf-verification-before-completion
description: Use when preparing a completion claim and checking whether verification evidence covers the final inputs and environment.
---

# Verification Before Completion

## Evidence before claims

A completion claim needs valid evidence covering the final relevant inputs and
environment. Use the repository's verification rules to select the required
checks; this skill does not add another gate.

1. Identify the claim and its required evidence.
2. Reuse an existing receipt when its relevant source, tests, fixtures, manifest,
   runtime target, environment, and applicable validity period still match.
   A new reply or commit with unchanged content does not invalidate it.
3. Run the affected checks when evidence is missing or invalidated by a relevant
   change, failure, or concrete unresolved concern. If validity is uncertain,
   resolve that uncertainty or report the gap before claiming completion.
4. Read the result, including failures and skips. State only what it proves and
   retain the original `command`, `exit_code`, `key_output`, and `timestamp`.

Required CI, promotion checks, and independent cross-environment readback retain
their own evidence and authorization boundaries. Source validation cannot replace
runtime acceptance. Once the required checks pass, stop unless new evidence
justifies more work. Do not rerun a check merely to restate its receipt or give it
a newer timestamp.

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Valid test output covering the final inputs; disclose required skips | Stale output, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Agent completed | Inspect the actual diff and applicable validation evidence | Agent reports "success" |

Missing or partial evidence supports a bounded status report, not a broader
success claim. Preserve the gap; do not invent output or infer runtime behavior
from source parity.
