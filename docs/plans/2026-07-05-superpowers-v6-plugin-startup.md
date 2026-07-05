# Superpowers v6 Plugin Startup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Start the local `obra/superpowers` `v6.1.1` skills through the Codex plugin path, with durable repo sync and verification support.

**Architecture:** Keep `~/.codex/superpowers` as the pinned upstream checkout, but make Codex plugin marketplace/install state the runtime activation path. Do not change DHF core behavior; update only the Codex environment surfaces that pin, register, install, verify, and document Superpowers startup.

**Tech Stack:** Bash, Python standard library, Codex CLI plugin commands, Markdown docs, Git.

## Current Facts

- Current lock: `locks/superpowers.lock` points at `1143f9b`.
- Target upstream: `d884ae04edebef577e82ff7c4e143debd0bbec99`, tag `v6.1.1`.
- Target plugin manifest: `origin/main:.codex-plugin/plugin.json` declares `superpowers` version `6.1.1` with `skills: "./skills/"`.
- Target marketplace manifest: `origin/main:.agents/plugins/marketplace.json` declares marketplace `superpowers-dev` and selector `superpowers@superpowers-dev`.
- Existing curated plugin `superpowers@openai-curated` is not installed and is not the target because that marketplace snapshot is older.

## Definition Of Done

- `locks/superpowers.lock` pins the full target SHA: `d884ae04edebef577e82ff7c4e143debd0bbec99`.
- `~/.codex/superpowers` is checked out at that SHA without local dirty state.
- `superpowers-dev` marketplace is registered from `/Users/kezheng/.codex/superpowers` exactly once.
- `superpowers@superpowers-dev` is installed and enabled.
- New Codex sessions expose `superpowers:*` skills from the plugin path.
- Repo docs and verification explain plugin-first startup; legacy `.codex/superpowers-codex` is only a conditional fallback when present.
- Fresh verification evidence includes `command`, `exit_code`, `key_output`, and `timestamp`.

## Tasks

### Task 1: Pin Superpowers v6.1.1

**Files:**
- Modify: `locks/superpowers.lock`

**Steps:**
1. Change `commit=` to `d884ae04edebef577e82ff7c4e143debd0bbec99`.
2. Run `git -C "$HOME/.codex/superpowers" fetch --all --tags --prune`.
3. Run `git -C "$HOME/.codex/superpowers" checkout d884ae04edebef577e82ff7c4e143debd0bbec99`.
4. Verify:
   - `git -C "$HOME/.codex/superpowers" status --short`
   - `git -C "$HOME/.codex/superpowers" describe --tags --exact-match HEAD`
   - expected key output: clean status and `v6.1.1`.

### Task 2: Make Sync Plugin-Aware

**Files:**
- Modify: `scripts/sync_codex_home.sh`

**Steps:**
1. After the checkout step, stop assuming `.codex/superpowers-codex` exists.
2. Read `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` from the checked-out repo before registration; fail fast if either file is missing or the plugin version is not `6.1.1`.
3. Check `codex plugin marketplace list --json` for an existing marketplace with `name == "superpowers-dev"` and root `/Users/kezheng/.codex/superpowers`.
4. Only run `codex plugin marketplace add /Users/kezheng/.codex/superpowers --json` when that exact marketplace is absent.
5. Check installed plugin state before install; only run `codex plugin add superpowers@superpowers-dev --json` when it is not already installed and enabled.
6. Preserve existing runtime config merge behavior for `plugins.*`, `marketplaces.*`, `projects.*`, `hooks.state*`, `desktop*`, `memories`, and `mcp_servers.node_repl*`.

### Task 3: Verify Plugin Startup

**Files:**
- Modify: `scripts/verify_codex_env.sh`
- Modify: `test_runner.py`

**Steps:**
1. Keep the existing checkout check, but compare the full lock SHA with `git rev-parse HEAD`.
2. Add checks for:
   - marketplace `superpowers-dev` registered at `/Users/kezheng/.codex/superpowers`;
   - plugin selector `superpowers@superpowers-dev` installed and enabled;
   - checked-out `.codex-plugin/plugin.json` version is `6.1.1`;
   - no verification depends on `codex plugin list --json` `available`, because that field can be empty even when table output lists plugins.
3. Add the smallest test coverage in `test_runner.py` using temp homes or command stubs already used by existing sync/verify tests.
4. The test must fail if sync treats marketplace registration as install proof.

### Task 4: Update Human-Facing Docs

**Files:**
- Modify: `codex/AGENTS.md`
- Modify: `README.md`
- Modify: `docs/CODEX_ENV_REPRODUCTION.md`

**Steps:**
1. Replace the hard requirement to run `~/.codex/superpowers/.codex/superpowers-codex bootstrap` with plugin-first guidance: use session-exposed `superpowers:*` skills when present.
2. Keep a conditional fallback only as: if `~/.codex/superpowers/.codex/superpowers-codex` exists, it may be used for older pinned checkouts.
3. Document the startup sequence:
   - sync checkout from lock;
   - register `superpowers-dev`;
   - install `superpowers@superpowers-dev`;
   - restart/open a new Codex session;
   - verify `superpowers:*` appears in the session skill list.

### Task 5: Fresh Verification And Activation Proof

**Files:**
- No additional source files unless Task 2-4 require test fixtures.

**Steps:**
1. Run `git diff --check`.
2. Run `python3 test_runner.py`.
3. Run `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"`.
4. Run `codex plugin marketplace list --json`.
5. Run `codex plugin list`.
6. Restart/open a new Codex session and confirm `superpowers:*` skills are exposed there.

## Assumptions

- Use upstream `v6.1.1`, not `superpowers@openai-curated`.
- No DHF core changes are needed for this startup; DHF only needs docs/verification awareness of the plugin-first path.
- If Claude dual review is required before implementation, rerun it after the local Claude session limit resets.
