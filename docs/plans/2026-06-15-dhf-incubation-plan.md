# DHF Incubation Plan

Date: 2026-06-15
Repo: `MyCodexEnv`
Mode: controlled incubation, not independent extraction

## Summary

DHF stays inside `MyCodexEnv` while it is managed as a product-like platform
capability. The goal is to stabilize the reusable business contract, measure
real consumer dependency, and detect ShipQ drift before deciding whether an
independent GitHub project is justified.

This is not a rejection of extraction. It is a demand-validation stage that
keeps delivery velocity high while making the future extraction path measurable.

## Incubation Boundary

### DHF core

The core owns reusable delivery behavior:

- lifecycle routing and phase classification;
- execution-lane classification;
- source-of-truth recovery order;
- evidence contract and verification bundle shape;
- helper contract for recovery, env probe, requirements, agent team, report,
  and checkpoint;
- recovery/checkpoint protocol;
- DHF_PACKET schema as the smallest future portable interface.

The core must not encode business repo paths, customer fixtures, private service
names, live provider behavior, or machine-specific sync rules.

### MyCodexEnv local runtime

`MyCodexEnv` remains the incubation source of truth and owns local runtime
reproduction:

- Codex and Claude home sync;
- local hooks and runtime installation behavior;
- gstack vendor refresh;
- local evidence storage under Codex home;
- machine-specific verification and app/runtime probes.

These capabilities are useful for this machine and reference environment, but
they are not part of the portable DHF core contract.

### ShipQ adapter

ShipQ remains a consumer with project-owned delivery rules:

- `docs/designs/harness-state.md` as durable state source of truth;
- quote workflow, business fixtures, workbook/demo paths, and validation pages;
- ShipQ-specific safety boundaries, live-demo gates, and customer data rules;
- local helper adaptations that preserve ShipQ state shape and verification
  expectations.

The incubation program must compare ShipQ against DHF core, not replace ShipQ
automatically.

## Consumer Compatibility Matrix

The matrix in `docs/dhf-consumer-compatibility.json` is the product ledger for
consumer dependency. It records which parts of DHF are shared, which parts are
intentional adapters, and which differences require review.

Compatibility statuses:

- `same`: consumer behavior matches the DHF baseline helper.
- `intentional_adapter`: consumer differs for a documented project reason.
- `drift_needs_review`: consumer differs without a documented project reason.

The matrix is evidence for the extraction decision. It is not an installer and
does not copy files into consumers.

## ShipQ Drift Check

`scripts/check_dhf_consumer_compatibility.py` performs a read-only comparison
between the MyCodexEnv baseline and configured consumers such as ShipQ.

The checker:

- computes helper hashes;
- checks required helper and state paths;
- classifies differences as `same`, `intentional_adapter`, or
  `drift_needs_review`;
- exits non-zero only when a product or engineering decision is required;
- never writes to ShipQ or any configured consumer.

## DHF_PACKET Schema

`codex/runtime/dhf-packet.schema.json` defines the minimum portable handoff
packet for a future independent DHF core. It carries phase, execution lane,
state path, source-of-truth files, verification evidence, next safe task,
blockers, and consumer adapter metadata.

The packet explicitly excludes secrets, raw local evidence, customer data, and
machine-specific auth paths. Helper support for `--emit-dhf-packet` can be added
later; the first incubation slice only stabilizes the schema and example.

## Extraction Triggers

Start the independent repo extraction plan when any one of these becomes true:

- A second real consumer needs the same DHF core as MyCodexEnv and ShipQ.
- ShipQ/MyCodexEnv helper drift requires repeated manual repair across two
  separate slices.
- `DHF_PACKET` has no breaking change across two meaningful work slices.
- The compatibility matrix reliably distinguishes intentional adapter behavior
  from drift that needs review.

## Verification

Minimum gates for this incubation slice:

- `python3 scripts/check_dhf_consumer_compatibility.py --matrix docs/dhf-consumer-compatibility.json --json`
- `python3 scripts/check_surfaces.py --repo-root "$(pwd)"`
- `python3 test_runner.py`
- `git diff --check`
