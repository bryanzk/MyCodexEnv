# DHF Public Site Fix Probe · 2026-08-22

Raw, read-only Slice 0 observations. No runtime promotion or `~/.codex` write was performed.

## Baseline

Command:

```text
date; count dhf-nav-links pages, languages, status markers, metadata, and accepted drift entries
```

Output:

```text
local_timestamp=2026-08-21T21:05:19-0400 zone=EDT
utc_timestamp=2026-08-22T01:05:19Z
nav_pages=48 en=25 zh-CN=23
status_markers=48 unique_status=['2026-08-11']
og_title_pages=0 canonical_pages=17
accept_entries=8
lifecycle_accept=['bilingual:project-lifecycle-harness-flow-en.html:headings', 'bilingual:project-lifecycle-harness-flow-en.html:branches']
```

## Source profile probe

Command:

```text
grep -rn -E 'light|standard|governed' codex/policy codex/hooks scripts/harness_*.py
git log -1 --format='%H %cI %s' -- <matched-file>
```

Output:

```text
grep: codex/policy: No such file or directory
codex/hooks/dhf_preprompt.py:34:PROFILE_RANK = {"light": 0, "standard": 1, "governed": 2}
codex/hooks/dhf_preprompt.py:298:    selected = "governed" if signals else "light"
codex/hooks/dhf_preprompt.py:300:        selected = "standard"
codex/hooks/dhf_preprompt.py:421:    if selection.profile == "light":
codex/hooks/dhf_preprompt.py:423:    if selection.profile == "standard":
codex/hooks/dhf_preprompt.py:472:                "governed",
codex/hooks/dhf_preprompt.py 8cfb8cfc971860c87d712c87e9f10aead0928366 2026-08-09T23:40:47-04:00 feat: complete DHF simplification evidence gates
```

Classification: source contract contains executable profile-selection branches.

## Runtime probe

Command: `python3 scripts/harness_status.py status --runtime`

Output:

```text
# Harness Environment Probe
- codex_home: `/Users/kezheng/.codex`
- config_observable: `False`
- observable_reason: sandbox_mode and approval_policy are not declared in config.toml
- hooks_enabled: `True`
- pre_tool_use: `True`
- post_tool_use: `True`
- policy_phases_present: `True`
- evidence_verification_event_present: `True`
- split_evidence_schemas_present: `True`
```

Command: `python3 scripts/harness_status.py status --evidence`

Output:

```text
total_events: 50
scanned_events: 145851
malformed_count: 0
conversion_health.status: watch
recent_verification: none
```

Command: `python3 scripts/dhf_simplification_evidence.py --repo-root "$(pwd)"`

Raw classification fields:

```json
{
  "captured_at": "2026-08-22T01:06:20.204906Z",
  "changed_paths": [
    "codex/hooks/dhf_preprompt.py",
    "codex/skills/delivery-harness-framework/SKILL.md",
    "codex/skills/delivery-harness-framework/evals/evals.json",
    "codex/skills/delivery-harness-framework/evals/validate_completion_output.py"
  ],
  "gate_pass": true,
  "promotion_difference_paths": [],
  "promotion_gate_pass": true,
  "runtime_state": "runtime_promoted",
  "source_stage_gate_pass": false
}
```

Classification: `runtime_promoted`. The fresh runtime timestamp comes from the evidence producer, not from the public status date.

## Publication probe

Command: GitHub Pages latest-build readback plus HTTP GET of the 16 core pages.

Output:

```text
pages_build status=built commit=8c41f64768196e9f957d9a273607e84e998ba79d created_at=2026-08-22T01:04:22Z updated_at=2026-08-22T01:04:46Z
16/16 core pages: HTTP 200
16/16 core pages: data-dhf-status=2026-08-11
16/16 core pages: Last-Modified=Sat, 22 Aug 2026 01:04:46 GMT
```

## Public-internal wording probe

Command: remove `<details>` blocks, then inspect Home and Beginner body/footer tokens.

Output:

```text
literal `File: docs/` grep: 0
index.html footer: docs/index.html
index-en.html footer: docs/index.html
index-zh.html footer: docs/index-zh.html
delivery-harness-beginner-guide-en.html non-details: docs/delivery-harness-beginner-guide-en.html, harness_checkpoint.py, harness_env_probe.py, harness_recover.py, test_runner.py
delivery-harness-beginner-guide-cn.html non-details: docs/HARNESS_RUNTIME.md, docs/LIFECYCLE_SKILL_ROUTING.md, docs/harness-state.md, docs/templates/harness-agent-brief.md, harness_checkpoint.py, harness_env_probe.py, harness_recover.py, scripts/harness_*.py, test_runner.py
```

## Nightly synchronization timing

The implementation started at 21:05 EDT. PR A merge is outside this task's authorization, so the before-22:00 path cannot be used. Before the authorized branch push/PR creation, fetch and rebase onto the post-22:00 `origin/main`, then rerun drift and all final gates. The automation itself remains untouched.
