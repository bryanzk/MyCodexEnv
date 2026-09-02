# T011: WP1 Runtime Approval Audit

Decision: `not_ready`

## Blocking findings

1. `scripts/external_gstack_runtime.py:116-128,498-530` accepts an approved manifest without binding the approved source, target, sidecar, non-target, warning, or fresh activity prestates. A changed runtime can therefore pass the same approval packet before the first write.
2. `scripts/external_gstack_runtime.py:600-645` trusts recovery paths and journal states without the apply-side canonical path checks. If the live sidecar contains an unexpected entry, recovery can leave the backup unrestored and still write `rolled_back`.

## Minimal closure

- Change only `scripts/external_gstack_runtime.py` and `test_runner.py`.
- Require and verify compact prestate digests plus a fresh bounded quiescence receipt before apply writes.
- Recover only a canonical operation, reject unknown states before mutation, and fail closed if an unexpected live target prevents exact prestate restoration.
- Keep the existing lock, journal, backup, 53-flat plus sidecar topology, and CLI unchanged.

Runtime apply remains unauthorized until the replacement Worker passes focused and full gates and a new Judge emits an exact approval packet.
