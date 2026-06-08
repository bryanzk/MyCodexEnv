# Harness Requirements — Runtime Surfaces Single-Source Manifest Slice

> Vertical slice plan for Top-3 Task #3: give the runtime "surface inventory" a
> single machine-readable source of truth and make the existing
> hand-maintained copies (a hardcoded list in `test_runner.py`, the three
> overlapping lists in `docs/repo-index.md`, and the doc nav blocks) **derive
> from or validate against it**, so the framework stops violating its own
> single-source-of-truth principle and stops drifting.

## Goal

One file, `docs/surfaces.json`, lists every harness runtime surface with its
path, one-line role, and audience. A checker (`scripts/check_surfaces.py`, run
standalone and from `test_runner.py`) enforces, bidirectionally:

1. every manifest path exists on disk;
2. every runtime surface referenced in `docs/repo-index.md`'s "Runtime Surfaces"
   section appears in the manifest, and vice versa (no orphans either way).
3. the one-time migration seed covers every path from the current hardcoded
   `required_paths` list before that list is removed.

After this slice, humans edit only `docs/surfaces.json`; the test reads it
instead of a hardcoded list.

## Problem (current behavior, verified)

- `test_runner.py::test_harness_runtime_surfaces_exist_and_parse()` hardcodes a
  24-entry `required_paths` list, including `codex/hooks/shipq_dhf_preprompt.py`,
  the two harness templates, and `docs/skill-governance-20260608.md`.
- `docs/repo-index.md` lists the same surfaces in **three** sections ("Read
  First", "Runtime Surfaces", "Related Documentation"), partly overlapping and
  already mutually inconsistent.
- The public HTML nav blocks repeat the list again, in two languages.
- No single source ties these together. Adding or renaming a surface means
  editing 4–6 places by hand; missing one is undetected until something breaks.
  This is the framework contradicting its own first principle.

## Desired behavior

1. `docs/surfaces.json` is the inventory:

   ```json
   {
     "version": 1,
     "surfaces": [
       {"path": "docs/repo-index.md", "role": "low-token repo navigation", "audience": ["codex", "human"]},
       {"path": "codex/runtime/tool-policy.json", "role": "stage-aware tool and permission policy", "audience": ["runtime"]}
     ]
   }
   ```

2. `scripts/check_surfaces.py` exits non-zero with the exact offending path(s)
   on any of: manifest path missing on disk; a repo-index Runtime-Surfaces bullet
   whose backticked path is not in the manifest; a manifest path with no
   repo-index mention.
3. `test_harness_runtime_surfaces_exist_and_parse()` is refactored to load paths
   from the manifest (keeping the policy-parse assertions it already has).
4. JSON, not YAML: the repo is stdlib-only and YAML is not in the standard
   library. `json` parses the manifest with no new dependency.
5. Path normalization is explicit: manifest paths are repo-relative, have no
   leading `./`, and directories use no trailing slash (`codex/hooks`, not
   `codex/hooks/`). The checker normalizes repo-index backticked tokens the same
   way before comparison.
6. Repo-index extraction is deliberately narrow: under `## Runtime Surfaces`,
   only the **first backticked repo-relative path** in each bullet is treated as
   the surface path. Later backticked tokens in the same bullet may describe
   runtime destinations, branch names, GitHub repo slugs, commands, or examples
   and must not enter manifest comparison.

## Audience

- Maintainer adding/renaming a runtime surface.
- Future agent trusting `repo-index.md` as the source-of-truth index.

## Scope

- New `docs/surfaces.json` — the inventory (seeded from the current
  `required_paths` list + repo-index Runtime Surfaces section).
- New `scripts/check_surfaces.py` — bidirectional validator + `--json`.
- `test_runner.py` — refactor `test_harness_runtime_surfaces_exist_and_parse()`
  to read the manifest; add `test_surfaces_manifest_no_orphans()` invoking the
  checker.
- `docs/repo-index.md` — add a one-line pointer naming `docs/surfaces.json` as
  the canonical surface inventory and make the "Runtime Surfaces" section a
  complete checkable mirror (do not delete the human-readable section; the
  checker keeps it honest).
- `docs/HARNESS_RUNTIME.md` / `docs/AGENT_HARNESS_STATUS.md` — note the manifest
  as the single source and add an "Observability/Docs drift" status row.

## Non-Goals

- Auto-generating the HTML nav blocks from the manifest (worth doing later;
  this slice covers `repo-index.md` + the test, the two highest-value drift
  sources). HTML stays manual for now, optionally checked in a follow-up.
- Deleting the human-readable lists. The manifest backs them; it does not
  replace prose meant for humans.
- Introducing YAML or any parser dependency.
- Reorganizing the docs tree or pruning the ~40 doc files (separate effort).

## Migration Decisions

- Keep `codex/hooks/shipq_dhf_preprompt.py` in the seed. It is already part of
  the current `test_harness_runtime_surfaces_exist_and_parse()` required paths
  and is a repo-owned hook surface, even though its trigger is ShipQ-specific.
  Dropping it from the seed would be a separate test-surface policy decision, not
  part of this manifest migration.
- Include the new `docs/surfaces.json` and `scripts/check_surfaces.py` in the
  manifest. They are first-class runtime governance surfaces after this slice, so
  `docs/repo-index.md` `## Runtime Surfaces` must mention both or the checker
  should flag `in_manifest_not_index`.
- The `docs/repo-index.md` Runtime Surfaces edit is expected to be the largest
  text diff in the slice: it must add any seed paths currently missing from that
  section, including `codex/hooks/shipq_dhf_preprompt.py`,
  `docs/skill-governance-20260608.md`, `docs/surfaces.json`, and
  `scripts/check_surfaces.py`.

## Constraints

- Python standard library only (`json`, `re`, `pathlib`).
- Preserve append-only state and unrelated files; this slice is additive plus a
  test refactor.
- The checker must name the exact offending path and exit non-zero — no silent
  pass on drift (matches the repo's "silent failure is a critical gap" rule).

## Task Demand (D_task)

- estimated_level: medium
- L (reasoning/action steps): ~8 — author manifest, write checker with
  normalization and JSON output, refactor one test, add one test, update the
  repo-index mirror and two docs, gates.
- H_tool (tool-selection ambiguity): low — stdlib only; clear seam (the existing
  hardcoded list).
- S_state (cross-module state tracking): medium — the checker must keep the
  manifest and repo-index Runtime Surfaces mirror reconciled; the one-time seed
  must also cover the current legacy test list before that list is removed.
- N_obs (observation/external noise): low — purely local file parsing; fully
  deterministic and unit-testable, including false-positive cases for
  `~/.codex/*`, `origin/main`, and `garrytan/gstack`.

## Execution Lane

- `local_dev`. No external systems. The checker reads only repo files.

## Source Of Truth

- `AGENTS.md`, `docs/repo-index.md` (the lists being reconciled)
- `docs/harness-state.md`, `docs/HARNESS_RUNTIME.md`, `docs/AGENT_HARNESS_STATUS.md`
- `test_runner.py::test_harness_runtime_surfaces_exist_and_parse` (lines 596–624)
- current legacy seed paths:
  `docs/repo-index.md`, `docs/harness-state.md`, `docs/HARNESS_RUNTIME.md`,
  `docs/AGENT_HARNESS_STATUS.md`, `codex/runtime/tool-policy.json`,
  `codex/runtime/evidence.schema.json`,
  `codex/runtime/evidence/decision-evidence.schema.json`,
  `codex/runtime/evidence/routine-gate-receipt.schema.json`,
  `codex/hooks/harness_guard.py`, `codex/hooks/harness_observer.py`,
  `codex/hooks/model_router.py`, `codex/hooks/shipq_dhf_preprompt.py`,
  `scripts/harness_evidence.py`, `scripts/harness_feedback.py`,
  `scripts/harness_report.py`, `scripts/harness_agent_team.py`,
  `scripts/harness_checkpoint.py`, `scripts/harness_requirements.py`,
  `scripts/harness_recover.py`, `scripts/harness_env_probe.py`,
  `scripts/audit_skills.py`, `docs/templates/harness-requirements.md`,
  `docs/templates/harness-agent-brief.md`,
  `docs/skill-governance-20260608.md`
- new manifest governance surfaces:
  `docs/surfaces.json`, `scripts/check_surfaces.py`

## First Failing Test (write first — must fail on current code)

```python
def test_surfaces_manifest_no_orphans():
    # fails today: docs/surfaces.json and scripts/check_surfaces.py do not exist
    manifest = ROOT / "docs" / "surfaces.json"
    checker = ROOT / "scripts" / "check_surfaces.py"
    require(manifest.exists(), "docs/surfaces.json manifest must exist")
    require(checker.exists(), "scripts/check_surfaces.py must exist")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    listed = {s["path"] for s in data["surfaces"]}
    require(listed, "docs/surfaces.json must contain at least one surface")
    for item in data["surfaces"]:
        require(item.get("path") in listed, f"surface item missing path: {item}")
        require(item.get("role"), f"surface item missing role: {item}")
        require(isinstance(item.get("audience"), list) and item["audience"], f"surface item missing audience: {item}")
        require(not item["path"].startswith("./"), f"surface path must be repo-relative without ./: {item['path']}")
        require(not item["path"].endswith("/"), f"surface directory path must not use trailing slash: {item['path']}")
        require((ROOT / item["path"]).exists(), f"manifest path does not exist on disk: {item['path']}")

    # the standalone checker must agree (exit 0, no drift)
    code, out, err = run_cmd([sys.executable, str(checker), "--repo-root", str(ROOT)])
    require(code == 0, f"check_surfaces reported drift: {err or out}")
    code, out, err = run_cmd([sys.executable, str(checker), "--repo-root", str(ROOT), "--json"])
    require(code == 0, f"check_surfaces --json reported drift: {err or out}")
    require(json.loads(out).get("ok") is True, "check_surfaces --json should report ok=true")

    print("[PASS] surfaces manifest no orphans")
```

## Implementation Sketch

`scripts/check_surfaces.py` (stdlib only):

```python
import argparse, json, re, sys
from pathlib import Path

def normalize_path(value: str) -> str:
    value = value.strip().strip("`").strip()
    value = re.sub(r"^\\./", "", value)
    return value.rstrip("/")

def is_repo_surface_path(value: str) -> bool:
    return value.startswith(("docs/", "codex/", "scripts/"))

def repo_index_surface_paths(repo_root: Path) -> set[str]:
    text = (repo_root / "docs" / "repo-index.md").read_text(encoding="utf-8")
    # collect the first backticked repo-relative surface path from each bullet
    # under the "## Runtime Surfaces" section. Ignore later tokens such as
    # ~/.codex runtime destinations, branch names, commands, and GitHub slugs.
    out, in_section = set(), False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## runtime surfaces"
            continue
        if not in_section or not line.startswith("- "):
            continue
        for token in re.findall(r"`([^`]+)`", line):
            path = normalize_path(token)
            if is_repo_surface_path(path):
                out.add(path)
                break
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    data = json.loads((root/"docs"/"surfaces.json").read_text())
    manifest = {normalize_path(s["path"]) for s in data["surfaces"]}
    errors = []
    for p in sorted(manifest):
        if not (root / p).exists():
            errors.append(f"ERROR[missing_on_disk] {p}")
    index_paths = repo_index_surface_paths(root)
    for p in sorted(index_paths - manifest):
        errors.append(f"ERROR[in_index_not_manifest] {p}")
    for p in sorted({m for m in manifest if m.startswith(("docs/","codex/","scripts/"))} - index_paths):
        errors.append(f"ERROR[in_manifest_not_index] {p}")
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "manifest_count": len(manifest)}, sort_keys=True))
    elif errors:
        print("\n".join(errors), file=sys.stderr)
    else:
        print("surfaces manifest consistent")
    return 1 if errors else 0
```

Then refactor `test_harness_runtime_surfaces_exist_and_parse()` to build
`required_paths` from `docs/surfaces.json` instead of the inline list, keeping
its existing `tool-policy.json` phase-parse assertions.

Migration rule: before deleting the inline `required_paths` list, seed the
manifest from the full current list named in `Source Of Truth` and make
`docs/repo-index.md` Runtime Surfaces mention those paths. After the refactor,
the long legacy list must not remain in `test_runner.py` or
`scripts/check_surfaces.py`; the manifest is canonical and repo-index is the
checked human-readable mirror.

The manifest also includes `docs/surfaces.json` and `scripts/check_surfaces.py`
themselves. Add matching repo-index Runtime Surfaces bullets in the same change;
do not special-case the checker or manifest out of drift detection.

## Acceptance Criteria

- [ ] `test_surfaces_manifest_no_orphans()` added and **fails on current `main`**
      (manifest + checker absent), passes after.
- [ ] `docs/surfaces.json` lists every surface from the legacy `required_paths`
      list, each with `path`, `role`, `audience`; the seed includes
      `codex/hooks/shipq_dhf_preprompt.py`, both harness templates, and
      `docs/skill-governance-20260608.md`.
- [ ] `docs/surfaces.json` and `scripts/check_surfaces.py` are also listed in
      the manifest and in `docs/repo-index.md` Runtime Surfaces; neither is
      exempted from checker coverage.
- [ ] `docs/repo-index.md` Runtime Surfaces gains any seed paths it currently
      lacks, rather than shrinking the seed to match the old prose section.
- [ ] Manifest paths are normalized repo-relative strings with no leading `./`
      and no trailing slash; directories are allowed but checked with
      `Path.exists()`.
- [ ] `scripts/check_surfaces.py --repo-root .` exits 0 on a consistent repo and
      non-zero naming the exact path on: missing-on-disk, in-index-not-manifest,
      or in-manifest-not-index.
- [ ] The checker does not treat non-surface backtick tokens such as
      `~/.codex/hooks/`, `origin/main`, `garrytan/gstack`, or command examples as
      manifest entries.
- [ ] `scripts/check_surfaces.py --repo-root . --json` emits parseable JSON with
      `ok`, `errors`, and `manifest_count`.
- [ ] `test_harness_runtime_surfaces_exist_and_parse()` now derives its paths
      from the manifest; the inline `required_paths` literal is gone and is not
      reintroduced in the checker as a second source of truth.
- [ ] `docs/repo-index.md` names `docs/surfaces.json` as the canonical inventory
      and its "Runtime Surfaces" section is a complete checked mirror.
- [ ] Docs sync decision is explicit: `docs/HARNESS_RUNTIME.md` and
      `docs/AGENT_HARNESS_STATUS.md` describe the manifest/checker;
      `docs/CODEX_ENV_REPRODUCTION.md` is unchanged unless a setup or sync
      command changes.
- [ ] RED/GREEN evidence is captured for the checker and focused test with
      `command`, `exit_code`, `key_output`, and `timestamp`.
- [ ] Deliberately removing one manifest entry, or renaming a file without
      updating the manifest, makes the checker (and the test) fail — verified
      manually once.
- [ ] `python3 test_runner.py` → `[PASS] all tests`; `git diff --check` clean.

## Verification Gate

- Focused: `python3 scripts/check_surfaces.py --repo-root "$(pwd)"`
  then `python3 -c "import test_runner as t; t.test_surfaces_manifest_no_orphans()"`
- Full: `python3 test_runner.py`
- Formatting: `git diff --check`
- Sync: `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude" --skip-check app_google_chrome`

## Exception / Failure Modes

- `docs/surfaces.json` missing/malformed → checker exits non-zero with the parse
  error; do not fall back to an empty set (that would mask drift).
- `repo-index.md` "Runtime Surfaces" heading renamed → parser yields empty set →
  surfaces flagged `in_manifest_not_index`; this is intended pressure to keep the
  heading stable, documented in the checker's `--help`.
- Later backticked token in a Runtime Surfaces bullet is prose/runtime detail,
  not the surface path → ignored unless it is the first repo-relative path in
  that bullet. Non-repo-relative examples such as `~/.codex/hooks/`,
  `origin/main`, and `garrytan/gstack` are ignored.
- Repo-index directory token such as `codex/hooks/` → normalized to
  `codex/hooks` before comparison; the manifest stores the no-trailing-slash
  form.
- Empty manifest → checker reports every index path as orphaned; fail-closed.

## Risks

- **Index-parse brittleness:** scraping backticked paths from Markdown is
  heuristic. Mitigation: scope strictly to the "## Runtime Surfaces" section and
  to path-like tokens; the manifest, not the scrape, is canonical, and any
  mismatch degrades to a loud failure, never a silent pass.
- **Migration churn:** seeding the manifest must capture the full current list;
  the migration checklist and repo-index mirror guard against an incomplete
  seed without preserving a second long-term hardcoded truth.

## Handoff Notes

Append after the slice lands:

- `scripts/harness_checkpoint.py append --phase development --summary "added
  docs/surfaces.json single-source surface manifest + check_surfaces.py; test
  derives paths from manifest" ...` with fresh `test_runner.py` evidence and
  dirty-state classification (agent_owned: manifest + checker + test + 2 docs).
- Next safe task: optional follow-up to generate the HTML nav blocks from the
  same manifest, closing the remaining drift source.
- effective_feedback_check: run the checker once (informative), focused test
  once (valid), full suite once (non-redundant); flag any repeated green run as
  low_conversion.
