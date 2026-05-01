---
name: mevscan-review-csv-from-block-level
description: Use when reviewing a CSV or tx hash collection in MEVScan and the verdict must be derived from block-level MEV events before applying the full reviewer pipeline, including entity FP matcher, arbitrage balance config, tx-level arbitrage pruning, and quality-report rules.
---

# MEVScan Review CSV From Block Level

Review a CSV or tx set with MEVScan using the same order as the current pipeline. The final verdict must start from `block_mev_reports`, not from tx-level `mev_reports`.

## When to Use

- User asks to rejudge or review a CSV of tx hashes
- User wants the latest code path, not historical labels
- User cares about sandwich or JIT roles at block level
- User asks why a tx was or was not treated as sandwich, JIT, or FP after review

Do not use this skill for single-tx recognizer debugging without a tx list. Use code-specific recognizer skills for that.

## Core Rule

Always use this order:

1. Resolve every target tx to its block
2. Re-run the current code on those blocks
3. Read `block_mev_reports` first
4. Only after block-level mapping, read tx-level `mev_reports`
5. Apply reviewer pruning and quality rules exactly as configured

If block-level and tx-level disagree, report block-level as the primary verdict and tx-level as secondary evidence.

## Required Workflow

### 1. Fresh Runtime Data

- Use the current workspace code
- Re-run the relevant blocks through `traceBlock -> parseActions -> analyzeMEVs -> calculatePNL -> reviewMEVs`
- Do not reuse stale labels without saying so

### 2. Block-Level First

For each target tx, inspect `reviewMEVs/*/<block>.json`:

- Search `block_mev_reports[*].transactions`
- If the tx appears in a block-level event, classify it from that event first
- For `SANDWICH`, map role from `front_run_txs`, `victim_txs`, `back_run_txs`
- For `JIT`, map role from membership in the event; keep the role label explicit if available, otherwise use `member`

Recommended final statuses:

- `sandwich_front_run`
- `sandwich_victim`
- `sandwich_back_run`
- `jit_member`
- `block_level_mev_detected`
- `no_block_mev_detected`

### 3. Full Reviewer Rules

After block-level mapping, preserve the current reviewer behavior and require both reviewer configs to be enabled.

Mandatory built-in pruning and review behavior:

- Remove tx-level arbitrage false positives caused by lending position flows
- Remove duplicate tx-level arbitrage on sandwich or JIT attack legs
- Apply OneInch suppress logic
- Apply entity-to-address suppress logic with `entity-fp-config`
- Apply arbitrage balance rule with `arb-balance-config`
- `CoinPNL == nil` -> `review_pass=false`
- After restoring gas, if all token deltas are still non-positive -> `review_pass=false`

Do not review a CSV to completion unless you verified the reviewer process loaded both configs.

### 4. Config Gating

Always check reviewer startup arguments or logs:

- `--entity-fp-config`
- `--arb-balance-config`

Both are mandatory:

- `--entity-fp-config`
- `--arb-balance-config`

Required report values:

- `entity_fp_review=enabled`
- `arb_balance_review=enabled`

If either config is missing, stop, mark the run invalid, and rerun with both configs instead of reporting a final verdict.

## Output Shape

For every tx, prefer these columns:

- `tx_hash`
- `block_number`
- `block_level_status`
- `block_level_mev_types`
- `block_level_roles`
- `block_level_event_ids`
- `block_level_review_pass`
- `block_level_confidence`
- `block_level_notes`
- `tx_level_mev_types`
- `tx_level_event_ids`
- `entity_fp_review`
- `arb_balance_review`

## Common Mistakes

- Treating tx-level `ARBITRAGE` as the final verdict when block-level `SANDWICH` or `JIT` exists
- Saying a tx was not sandwich because tx-level reports do not include `SANDWICH`
- Treating a run without `--entity-fp-config` as acceptable final evidence
- Treating a run without `--arb-balance-config` as acceptable final evidence
- Mixing stale runtime JSON with freshly rerun blocks

## Verification

Before claiming the review is complete, provide fresh evidence with:

- `command`
- `exit_code`
- `key_output`
- `timestamp`

Minimum evidence should prove:

- input tx count
- rerun block count
- output row count
- that entity FP config was enabled
- that arbitrage balance config was enabled

## Hard Requirement

For this workflow, `entity_fp_review=disabled` or `arb_balance_review=disabled` means the run is incomplete.

Default config paths in this repo:

- `configs/reviewer_entity_fp_targets.yaml`
- `configs/reviewer_arb_balance.yaml`
