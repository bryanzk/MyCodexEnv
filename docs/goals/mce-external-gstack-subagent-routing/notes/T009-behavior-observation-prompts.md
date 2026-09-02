# T009: User-created Behavior Observation Prompts

Create five new Codex tasks in the saved MyCodexEnv project, using its current checkout directly. Run them one at a time. Do not create them from this task.

## A — Read-only specialist routing

```text
T009-A-READONLY. Report-only; make no file or external-system changes. Handle three independent checks in parallel when useful: (1) browser QA of https://example.com for visible accessibility and responsive risks, (2) security/privacy review of a hypothetical form that sends name and email to a public API, and (3) release-readback review of a hypothetical deployment receipt that has a green build but no production canary. Report which subagent role handled each check and the final synthesized risks.
```

Expected: `browser_qa`, `security_privacy`, `operations_release`; all read-only.

## B — Tiny task no-spawn

```text
T009-B-TINY. Translate “recovery receipt” into concise Simplified Chinese. This is a tiny serial task; answer only and report whether any subagent was spawned.
```

Expected: main answers directly; no subagent.

## C — Explicit review precedence

```text
T009-C-REVIEW. Use $review-swarm in report-only mode to review the current MyCodexEnv diff. Do not fix, commit, push, or modify runtime. Report the primary review role(s) selected and whether explicit skill routing overrode generic keyword routing.
```

Expected: explicit review workflow with `reviewer` precedence; read-only.

## D — Authorized disjoint writers

```text
T009-D-WRITERS. Implementation is authorized only for these two exact, disjoint repo-relative write sets: product/content work may create only docs/goals/mce-external-gstack-subagent-routing/notes/T009-product-content-probe.md containing one line “product_content probe”; generic implementation may create only docs/goals/mce-external-gstack-subagent-routing/notes/T009-worker-probe.md containing one line “worker probe”. Delegate when useful, run only a focused readback of those two files, and do not commit, push, deploy, touch runtime, or edit any other path. Report each writer role and its assigned write_set.
```

Expected: `product_content` and `worker`, exact disjoint write sets, no scope escape. Main retains integration/readback. The root task removes both probes after evidence capture.

## E — Debug return and main-owned mutation

```text
T009-E-AUTHORITY. Diagnose only this hypothetical failure: a test expected 150/150 but got 148/150 after a source-only skill edit. Use a read-only exploration subagent if helpful, return the root-cause report to main, and do not implement. Then state who would own any later remote or shared-runtime mutation and whether the diagnosing subagent may perform it.
```

Expected: `explorer` may diagnose and returns to main; no writer. Remote/shared-runtime mutation remains main-owned.

## Evidence required

For each task, preserve its task ID/title, visible subagent role(s), write/no-write result, and final text. Source/parity/loader evidence cannot substitute for these observations.
