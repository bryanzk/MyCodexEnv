# T006: Source-stage Runtime Boundary Blocker

Focused WP2 routing, skill validation, AGENTS size, Identity A-D, diff, and live compatibility gates pass. The full runner has exactly two failures with one cause:

- `dhf_simplification_evidence.runtime_boundary_evidence()` compares live runtime to fixed `BASE_COMMIT` and current source.
- WP1 already promoted runtime beyond that fixed base.
- WP2 changes only the DHF `SKILL.md`, so live is neither the fixed base nor current source and the helper returns `drifted`.
- The golden/paired tests accept only `source_stage_unsynced` (live equals fixed base) or `runtime_promoted` (live equals current source).

Changing the evidence helper/tests is outside T006 allowlist. Promoting the three WP2 targets requires T007 exact packet and T008 owner approval. Judge must decide whether the full runner is correctly a post-promotion gate for this second-stage delta or whether the approved scope must change.

Receipt: `python3 test_runner.py`, exit 1, `ran=150 passed=148 failed=2`, timestamp `2026-09-02T03:23:51Z`.
