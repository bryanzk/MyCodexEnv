# Adaptive Persistent Subagent Team Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a 13-role persistent Codex subagent roster and make the primary agent automatically decide, per request, whether bounded delegation is useful.

**Architecture:** Keep role identity, model, reasoning effort, sandbox, and role instructions in standalone `codex/agents/*.toml` source files. Keep cross-project delegation judgment in the global `codex/AGENTS.md`; use existing native `spawn_agent` behavior and the existing sync path instead of adding a semantic hook, model router, skill, or dispatcher. Treat repository implementation, tests, runtime promotion, runtime parity, and loaded runtime activity as separate gates.

**Tech Stack:** TOML custom-agent definitions, Markdown global instructions and documentation, Python 3 stdlib test harness (`test_runner.py`), existing MyCodexEnv runtime verification scripts.

## Global Constraints

- The final roster contains exactly 13 roles: the existing `explorer`, `reviewer`, and `worker`, plus the ten roles defined below.
- Model assignment rationale: `gpt-5.6-sol` for reasoning-heavy read-only analysis and review, `gpt-5.6-terra` for hands-on implementation roles, `gpt-5.6-luna` for browser-focused QA. Only `gpt-5.6-sol` is currently exercised anywhere in this repository, so `gpt-5.6-terra` and `gpt-5.6-luna` are unverified assumptions: before requesting Task 6 approval, verify both IDs are valid selectable models on this Codex install (model picker, models listing, or a prior successful session receipt) and put that evidence in the approval packet. If either ID is invalid, stop and ask the user for a model decision; never substitute a model silently.
- Preserve existing `explorer.toml`, `reviewer.toml`, and `worker.toml` byte-for-byte unless a failing contract proves a required change.
- Add no dependency, hook, router, skill, plugin, or synchronization script, and change no global model configuration; the per-role `model` fields inside `codex/agents/*.toml` are part of the roster contract, not a configuration change.
- Automatic delegation normally uses zero to three subagents; small, serial, tightly coupled, or same-write-surface tasks remain with the primary agent.
- Delegation never expands user authorization. The primary agent owns integration, final verification, external mutations, and the user-facing result.
- Preserve all pre-existing dirty and untracked files, including `tasks/p0-token-cost-plan-2026-08-22.md`, `tasks/p1-1-skill-split-plan-2026-08-23.md`, and `tasks/p1-2-refresh-identity-plan-2026-08-23.md`.
- Do not commit, push, deploy, restart Codex, or write under `~/.codex` without separate current-turn authorization.
- Run `python3 test_runner.py` exactly once during repository implementation (Tasks 1–5), after the final repository source change. The Task 7 rerun is a different gate in a separate approval-gated promotion turn and does not violate this rule. If it reports the documented sandbox-only host skips, follow `docs/agents/verification-and-change-safety.md` instead of rerunning the full suite.
- Every verification receipt records `command`, `exit_code`, `key_output`, and UTC `timestamp`.

---

## File Map

**Create:**

- `codex/agents/architect.toml` — read-only architecture and interface planning.
- `codex/agents/python_data.toml` — Python/API/data implementation.
- `codex/agents/web_cloudflare.toml` — TypeScript/web/Cloudflare implementation.
- `codex/agents/browser_qa.toml` — read-only browser and extension QA.
- `codex/agents/apple_platform.toml` — SwiftUI/macOS implementation.
- `codex/agents/elixir_orchestrator.toml` — Elixir/OTP/Phoenix implementation.
- `codex/agents/ai_researcher.toml` — read-only AI research and evaluation.
- `codex/agents/security_privacy.toml` — read-only security, authorization, and privacy review.
- `codex/agents/product_content.toml` — product and content implementation.
- `codex/agents/operations_release.toml` — read-only runtime, release, rollback, and evidence planning.

**Modify:**

- `test_runner.py` — exact roster/config contract and global auto-delegation contract.
- `codex/AGENTS.md` — concise cross-project auto-delegation rules.
- `docs/CODEX_ENV_REPRODUCTION.md` — custom-agent source-to-runtime mapping.

**Review artifact, no implementation dependency:**

- `docs/proposals/global-agents-subagent-team.md` — human-readable design draft; keep it unless the user separately asks to delete or revise it.

**Runtime targets, approval-gated and outside repository implementation:**

- `/Users/kezheng/.codex/AGENTS.md`
- `/Users/kezheng/.codex/agents/{architect,python_data,web_cloudflare,browser_qa,apple_platform,elixir_orchestrator,ai_researcher,security_privacy,product_content,operations_release}.toml`

**Anchor note:** line anchors such as `test_runner.py:1457` locate positions in the pre-change file; once an earlier task has edited a file, resolve later anchors by the named function or heading, not the raw line number.

---

### Task 1: Add the failing persistent-roster contract

**Files:**

- Modify: `test_runner.py:1457`
- Test: `test_runner.py::test_sync_renders_template_and_copies_skills`

**Interfaces:**

- Consumes: standalone TOML fields `name`, `description`, `model`, `model_reasoning_effort`, `sandbox_mode`, and `developer_instructions`.
- Produces: one exact `agent_specs` roster used to verify repository source and temporary-home synchronization.

- [ ] **Step 1: Replace the three-entry test mapping with the exact 13-role contract**

Use this structure so model choice is validated per role instead of assuming every role uses Sol:

```python
agent_specs = {
    "ai_researcher": ("gpt-5.6-sol", "high", "read-only"),
    "apple_platform": ("gpt-5.6-terra", "high", "workspace-write"),
    "architect": ("gpt-5.6-sol", "high", "read-only"),
    "browser_qa": ("gpt-5.6-luna", "medium", "read-only"),
    "elixir_orchestrator": ("gpt-5.6-sol", "high", "workspace-write"),
    "explorer": ("gpt-5.6-sol", "low", "read-only"),
    "operations_release": ("gpt-5.6-sol", "high", "read-only"),
    "product_content": ("gpt-5.6-terra", "medium", "workspace-write"),
    "python_data": ("gpt-5.6-terra", "high", "workspace-write"),
    "reviewer": ("gpt-5.6-sol", "high", "read-only"),
    "security_privacy": ("gpt-5.6-sol", "high", "read-only"),
    "web_cloudflare": ("gpt-5.6-terra", "high", "workspace-write"),
    "worker": ("gpt-5.6-sol", "medium", "workspace-write"),
}
actual_agent_names = {path.stem for path in (ROOT / "codex" / "agents").glob("*.toml")}
require(actual_agent_names == set(agent_specs), f"custom-agent roster drifted: {sorted(actual_agent_names)}")
for name, (model, effort, sandbox) in agent_specs.items():
    source = ROOT / "codex" / "agents" / f"{name}.toml"
    require(source.is_file(), f"missing custom-agent source: {source}")
    text = source.read_text(encoding="utf-8")
    for setting in [
        f'name = "{name}"',
        f'model = "{model}"',
        f'model_reasoning_effort = "{effort}"',
        f'sandbox_mode = "{sandbox}"',
        "description = ",
        "developer_instructions = ",
    ]:
        require(setting in text, f"{name} custom-agent missing setting: {setting}")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 -c 'import test_runner; test_runner.test_sync_renders_template_and_copies_skills()'
```

Expected: non-zero exit with `custom-agent roster drifted: ['explorer', 'reviewer', 'worker']` — the roster-equality assertion fires before the per-file checks and prints the actual on-disk roster, so the message names the three existing roles, not the missing ones. A syntax error or unrelated sync failure is not an acceptable RED.

---

### Task 2: Create the ten specialist role definitions

**Files:**

- Create: the ten `codex/agents/*.toml` files listed in the File Map.
- Test: `test_runner.py::test_sync_renders_template_and_copies_skills`

**Interfaces:**

- Consumes: the exact roster contract from Task 1.
- Produces: Codex-native persistent custom-agent definitions discoverable by role name.

- [ ] **Step 1: Create `codex/agents/architect.toml`**

```toml
name = "architect"
description = "Read-only architect for system boundaries, interfaces, data flow, and decision-complete implementation plans."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Map the relevant system before recommending a design.
Resolve interfaces, data flow, edge cases, risks, and verification boundaries without editing files.
"""
```

- [ ] **Step 2: Create `codex/agents/python_data.toml`**

```toml
name = "python_data"
description = "Python implementation specialist for APIs, parsers, SQLite, data pipelines, PDFs, and deterministic business logic."
model = "gpt-5.6-terra"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = """
Trace the existing Python and data path, then make the smallest bounded change.
Preserve schemas, privacy boundaries, unrelated work, and run the assigned focused verification.
"""
```

- [ ] **Step 3: Create `codex/agents/web_cloudflare.toml`**

```toml
name = "web_cloudflare"
description = "Web implementation specialist for TypeScript, React, Vue, static sites, and Cloudflare Workers or Pages."
model = "gpt-5.6-terra"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = """
Follow the repository's existing frontend and Cloudflare patterns.
Implement only the assigned surface, preserve accessibility and privacy basics, and run the assigned checks.
"""
```

- [ ] **Step 4: Create `codex/agents/browser_qa.toml`**

```toml
name = "browser_qa"
description = "Read-only browser QA specialist for Chrome extensions, Playwright flows, accessibility, responsive behavior, and visual evidence."
model = "gpt-5.6-luna"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = """
Reproduce the bounded user flow and report observable browser, console, network, accessibility, and layout evidence.
Do not edit source or turn local smoke checks into deployment or attended-acceptance claims.
"""
```

- [ ] **Step 5: Create `codex/agents/apple_platform.toml`**

```toml
name = "apple_platform"
description = "Apple-platform implementation specialist for SwiftUI, macOS, local files, YAML configuration, and system integration."
model = "gpt-5.6-terra"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = """
Follow the existing Swift and macOS integration boundaries and make the smallest assigned change.
Use fixtures for local-system behavior unless the user explicitly authorizes live home-directory writes or redeploy actions.
"""
```

- [ ] **Step 6: Create `codex/agents/elixir_orchestrator.toml`**

```toml
name = "elixir_orchestrator"
description = "Elixir specialist for OTP supervision, Phoenix, LiveView, concurrency, recovery, and agent orchestration."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = """
Trace process ownership, supervision, message flow, and failure recovery before editing.
Keep changes bounded, preserve workspace and authorization isolation, and run the assigned Mix gates.
"""
```

- [ ] **Step 7: Create `codex/agents/ai_researcher.toml`**

```toml
name = "ai_researcher"
description = "Read-only AI researcher for LLMs, RAG, evaluation, translation, experiments, and technical source synthesis."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Separate verified facts, source-backed findings, inferences, and assumptions.
Report experimental requirements and limits without editing files, spending money, or calling live providers unless separately authorized.
"""
```

- [ ] **Step 8: Create `codex/agents/security_privacy.toml`**

```toml
name = "security_privacy"
description = "Read-only reviewer for credentials, PII, authorization, privacy, financial data, trust boundaries, and production risk."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Review the exact data flow, permissions, secret handling, mutation surface, rollback, and failure behavior.
Lead with concrete exploitable or loss-causing findings and do not edit files or expose private values.
"""
```

- [ ] **Step 9: Create `codex/agents/product_content.toml`**

```toml
name = "product_content"
description = "Product and content specialist for positioning, bilingual copy, SEO, community growth, and evidence-bounded job materials."
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
developer_instructions = """
Use current project facts and the assigned audience to produce the smallest complete content change.
Preserve evidence boundaries, existing voice, localization structure, and publication authorization.
"""
```

- [ ] **Step 10: Create `codex/agents/operations_release.toml`**

```toml
name = "operations_release"
description = "Read-only operations specialist for runtime promotion, deployment, release gates, rollback, parity, and executable evidence."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Separate source, tests, runtime parity, loaded activity, publication, deployment, and production outcomes.
Produce an exact approval packet, rollback path, and fresh verification requirements without performing mutations.
"""
```

- [ ] **Step 11: Run the focused test and verify GREEN**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 -c 'import test_runner; test_runner.test_sync_renders_template_and_copies_skills()'
```

Expected: exit `0` and `[PASS] sync renders template and copies skills`.

---

### Task 3: Add and test global automatic delegation policy

**Files:**

- Modify: `test_runner.py:10489`
- Modify: `codex/AGENTS.md:54`
- Test: `test_runner.py::test_global_agents_layering_workflow_and_size_contract`

**Interfaces:**

- Consumes: role descriptions from `codex/agents/*.toml` and existing authorization/thread rules.
- Produces: stable cross-project instructions telling the primary agent when and how to delegate.

- [ ] **Step 1: Add the failing global-policy assertions**

Add these exact strings to the `required` list in `test_global_agents_layering_workflow_and_size_contract`:

```python
"主代理在每个请求开始时判断子代理是否能实质改善并行速度、上下文隔离、专业准确性或独立验证",
"适合委派时使用最小充分团队，通常为一至三个子代理",
"委派不扩大用户授权；主代理负责集成、最终验证与对用户交付",
"子代理报告是待复核证据，不是完成证明",
```

- [ ] **Step 2: Run the focused policy test and verify RED**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 -c 'import test_runner; test_runner.test_global_agents_layering_workflow_and_size_contract()'
```

Expected: non-zero exit with `global AGENTS missing stable workflow term` for the first new sentence.

- [ ] **Step 3: Insert the minimal policy after `## Workflow`**

Add this block after the existing Workflow bullets and before `## Repo AGENTS Expectations`:

```markdown
## Adaptive Subagent Team
- 主代理在每个请求开始时判断子代理是否能实质改善并行速度、上下文隔离、专业准确性或独立验证。
- 小型、串行、紧耦合或共享同一写入面的任务由主代理直接完成；适合委派时使用最小充分团队，通常为一至三个子代理。
- 按 `~/.codex/agents/*.toml` 的职责描述选择成员；每个成员只接收一个边界明确、上下文最小且结果可检查的任务。
- 调查、计划、诊断、研究、QA 与 review 默认使用只读成员；并行实现必须使用互不重叠的写入范围。
- 委派不扩大用户授权；主代理负责集成、最终验证与对用户交付。
- 子代理报告是待复核证据，不是完成证明；主代理必须重读改动并运行 fresh gates。
```

- [ ] **Step 4: Run the focused policy test and verify GREEN**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 -c 'import test_runner; test_runner.test_global_agents_layering_workflow_and_size_contract()'
```

Expected: exit `0` and `[PASS] global AGENTS layering, workflow, and size contract`. The existing 90-line and 8192-byte limits must remain green.

---

### Task 4: Document the persistent source-to-runtime mapping

**Files:**

- Modify: `docs/CODEX_ENV_REPRODUCTION.md:19`
- Verify: `docs/CODEX_ENV_REPRODUCTION.md`, `docs/proposals/global-agents-subagent-team.md`

**Interfaces:**

- Consumes: the existing `scripts/sync_codex_home.sh` behavior that copies every `codex/agents/*.toml` file.
- Produces: an accurate reproduction contract without changing the sync script.

- [ ] **Step 1: Add the missing mapping**

Insert immediately after the `codex/AGENTS.md` mapping:

```markdown
- `codex/agents/*.toml` -> `~/.codex/agents/*.toml`
```

- [ ] **Step 2: Verify documentation and write-set formatting**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
rg -n 'codex/agents/\*\.toml.*~/.codex/agents/\*\.toml' docs/CODEX_ENV_REPRODUCTION.md
git diff --check -- codex/AGENTS.md codex/agents test_runner.py docs/CODEX_ENV_REPRODUCTION.md docs/proposals/global-agents-subagent-team.md
```

Expected: one mapping match, then exit `0` with no diff-check output.

---

### Task 5: Run final repository verification and freeze the source allowlist

**Files:**

- Verify only; no new files.

**Interfaces:**

- Consumes: Tasks 1–4 final source tree.
- Produces: source-implementation receipt and exact source hashes for a later runtime approval packet.

- [ ] **Step 1: Parse every agent TOML with the Python standard library**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 -c 'import pathlib,tomllib; paths=sorted(pathlib.Path("codex/agents").glob("*.toml")); assert len(paths)==13, len(paths); [tomllib.loads(p.read_text()) for p in paths]; print("agents=13 toml=valid")'
```

Expected: exit `0`, `agents=13 toml=valid`.

- [ ] **Step 2: Run the final repository gate exactly once**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 test_runner.py
```

Expected: exit `0` with zero failed tests. Record any explicit sandbox skip exactly; follow the repository host-only rule without rerunning the complete suite.

- [ ] **Step 3: Capture final repository state without staging or committing**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
git status --short
git diff --check
git diff -- codex/AGENTS.md codex/agents test_runner.py docs/CODEX_ENV_REPRODUCTION.md
```

Expected: only the authorized team implementation plus pre-existing untracked files; no whitespace errors. Do not stage, commit, or push.

---

### Task 6: Generate the exact runtime-promotion approval packet and stop

**Files:**

- Read: the 11 approved repository source candidates.
- Read: the 11 matching `/Users/kezheng/.codex` target states.
- Write: none.

**Interfaces:**

- Consumes: final verified source files and current runtime state.
- Produces: the approval packet required by `mce-targeted-runtime-promotion`; this task does not promote anything.

- [ ] **Step 1: Capture immutable repository anchors**

Run:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
```

- [ ] **Step 2: Resolve and hash the exact source/target rows**

Use these 11 mappings and no inferred siblings:

```text
codex/AGENTS.md -> /Users/kezheng/.codex/AGENTS.md
codex/agents/architect.toml -> /Users/kezheng/.codex/agents/architect.toml
codex/agents/python_data.toml -> /Users/kezheng/.codex/agents/python_data.toml
codex/agents/web_cloudflare.toml -> /Users/kezheng/.codex/agents/web_cloudflare.toml
codex/agents/browser_qa.toml -> /Users/kezheng/.codex/agents/browser_qa.toml
codex/agents/apple_platform.toml -> /Users/kezheng/.codex/agents/apple_platform.toml
codex/agents/elixir_orchestrator.toml -> /Users/kezheng/.codex/agents/elixir_orchestrator.toml
codex/agents/ai_researcher.toml -> /Users/kezheng/.codex/agents/ai_researcher.toml
codex/agents/security_privacy.toml -> /Users/kezheng/.codex/agents/security_privacy.toml
codex/agents/product_content.toml -> /Users/kezheng/.codex/agents/product_content.toml
codex/agents/operations_release.toml -> /Users/kezheng/.codex/agents/operations_release.toml
```

For each row, record canonical source, canonical target, source SHA-256, target state (`absent`, `regular`, or `symlink/other`), target SHA-256 when regular, and whether creation is requested. Stop on any symlink or non-regular target.

- [ ] **Step 3: Ask for one explicit approval covering the complete packet**

The approval request must include repository root, branch, HEAD, runtime root, all 11 rows and hashes, permission to create absent targets, the focused/final gate receipts, the `gpt-5.6-terra`/`gpt-5.6-luna` model-validity evidence required by Global Constraints, and the statement that no directory mirror, `rsync`, `--delete`, bootstrap, or broad sync will run.

Stop here until the user approves that exact packet in a later turn.

---

### Task 7: Promote only the approved runtime rows

**Precondition:** The user approved the unchanged Task 6 packet in the current promotion turn. If root, branch, HEAD, source hash, target state/hash, or authorization differs, return to Task 6.

**Files:**

- Create or replace only the 11 approved `/Users/kezheng/.codex` targets.
- Create: one task-specific backup directory under `/private/tmp` using `mktemp -d`.
- Do not modify any sibling runtime file.

**Interfaces:**

- Consumes: approved Task 6 packet.
- Produces: exact source/runtime byte parity plus a retained rollback directory.

- [ ] **Step 1: Re-read `mce-targeted-runtime-promotion` and run its preflight**

Recheck anchors, hashes, target states, source gates, and a non-target runtime manifest. The non-target manifest must cover regular files under `/Users/kezheng/.codex/agents` while excluding the ten exact approved agent targets by resolved path.

- [ ] **Step 2: Back up every existing approved target**

Create the backup directory with `mktemp -d /private/tmp/MCE-20260826-subagent-team.XXXXXX`. Copy each existing target individually with metadata, verify `cmp`, and record an absent marker for every approved new target. Keep the backup directory after completion.

- [ ] **Step 3: Copy the allowlist one file at a time**

For each approved row, run direct `cp -p SOURCE TARGET`, then immediately run:

```bash
cmp SOURCE TARGET
shasum -a 256 SOURCE TARGET
```

Stop at the first mismatch and execute the skill's exact-target rollback. Do not run `scripts/sync_codex_home.sh`, `rsync`, bootstrap, or a directory copy.

- [ ] **Step 4: Verify runtime parity and unchanged siblings**

Run file-by-file `cmp` and SHA-256 checks for all 11 rows, regenerate the non-target manifest, and compare it byte-for-byte with the preflight manifest.

- [ ] **Step 5: Run post-promotion gates**

Run in order and capture full receipts:

```bash
date -u '+timestamp=%Y-%m-%dT%H:%M:%SZ'
python3 test_runner.py
./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "/Users/kezheng/.codex" --claude-home "/Users/kezheng/.claude"
git status --short
git diff --check
```

Any new test/verifier failure, target mismatch, or non-target drift triggers exact-target rollback. Report the original failure and rollback verification separately.

- [ ] **Step 6: Report lanes independently**

Report:

```text
source_implementation: proven | not_proven
runtime_parity: proven | not_proven
runtime_activity: not_proven
rollout_observation: not_proven
```

Include every target, source/target SHA-256, backup path, non-target manifest comparison, gate receipts, final Git status, and whether restart, commit, push, deployment, or publication occurred.

---

### Task 8: Prove loaded runtime activity in a fresh Codex session

**Precondition:** Task 7 runtime parity is proven and the user has restarted or reloaded Codex. Do not terminate or restart the application automatically.

**Files:**

- Read-only runtime observation; no writes.

**Interfaces:**

- Consumes: newly loaded `/Users/kezheng/.codex/AGENTS.md` and custom-agent roster.
- Produces: runtime-activity evidence distinct from disk parity.

- [ ] **Step 1: Confirm the new session exposes the custom roles**

Inspect the available `spawn_agent` role metadata. Require all 13 role names and their configured model/reasoning pairs; disk files alone do not satisfy this step.

- [ ] **Step 2: Run one harmless bounded dispatch**

Dispatch `architect` with a read-only task that reports its role identity and reads no private project content. Verify that the returned task metadata identifies `architect`, `gpt-5.6-sol`, and `high` reasoning.

- [ ] **Step 3: Handle a failed activity check without guessing**

If Step 1 is missing any role or Step 2 fails (for example the dispatch rejects an unknown model ID), stop: report `runtime_activity: not_proven` with the exact error, keep `runtime_parity` at whatever Task 7 separately proved, do not retry with substituted models, and give the user the choice between exact-target rollback (using the retained Task 7 backup directory) and a role or model revision that restarts at Task 6.

- [ ] **Step 4: Report final state**

Only after Steps 1–2 pass may `runtime_activity` be reported as `proven`. `rollout_observation` remains `not_proven` unless a separately requested timed observation exists.

---

## Execution Handoff

Plan implementation has two safe choices:

1. **Subagent-driven:** use `superpowers:subagent-driven-development` for Tasks 1–5 with a fresh implementation worker and read-only review between tasks. Tasks 6–8 remain approval-gated and sequential.
2. **Inline:** use `superpowers:executing-plans` for Tasks 1–5 in this session with RED→GREEN checkpoints. Tasks 6–8 still require their stated approvals.

Neither choice authorizes commits, pushes, runtime writes, application restart, deployment, or publication.
