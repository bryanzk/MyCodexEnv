#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_COMMIT = "00818ae174f039899a2757ee4c67fcf9db1effa0"
SCHEMA = "dhf_simplification_observations_v4"
HOOK_SOURCE = "codex/hooks/dhf_preprompt.py"
SKILL_ROOT = "codex/skills/delivery-harness-framework"
MIRRORS = (
    "README.md",
    "docs/HARNESS_RUNTIME.md",
    "docs/LIFECYCLE_SKILL_ROUTING.md",
    "docs/repo-index.md",
    "docs/surfaces.json",
)
EXCLUSIONS = ("unmanaged files", "plugins", "caches", "logs", "__pycache__", "*.pyc", "directory metadata")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _git_bytes(root: Path, revision_path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", revision_path], cwd=root, capture_output=True, check=False
    )
    return proc.stdout if proc.returncode == 0 else None


def managed_source_paths(root: Path) -> list[str]:
    skill = root / SKILL_ROOT
    paths = [HOOK_SOURCE]
    paths.extend(
        path.relative_to(root).as_posix()
        for path in sorted(skill.rglob("*"))
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    return paths


def _record(path: str, payload: bytes | None) -> dict[str, str]:
    return {"path": path, "type": "absent" if payload is None else "regular", "sha256": "absent" if payload is None else sha256_bytes(payload)}


def base_expected_runtime_manifest(root: Path) -> dict[str, Any]:
    records = []
    for source_path in managed_source_paths(root):
        runtime_path = (
            Path.home() / ".codex" / "hooks" / "dhf_preprompt.py"
            if source_path == HOOK_SOURCE
            else Path.home() / ".codex" / "skills" / "delivery-harness-framework" / Path(source_path).relative_to(SKILL_ROOT)
        )
        payload = _git_bytes(root, f"{BASE_COMMIT}:{source_path}")
        record = _record(str(runtime_path), payload)
        record["source_path"] = source_path
        records.append(record)
    manifest = {
        "schema_version": 1,
        "kind": "base_expected_runtime_manifest",
        "base_commit": BASE_COMMIT,
        "managed_roots": [
            str(Path.home() / ".codex" / "hooks"),
            str(Path.home() / ".codex" / "skills" / "delivery-harness-framework"),
        ],
        "managed_relative_paths": [item["source_path"] for item in records],
        "records": records,
        "exclusions": list(EXCLUSIONS),
    }
    manifest["aggregate_sha256"] = sha256_bytes(canonical_bytes(records))
    return manifest


def _live_record(runtime_path: Path, source_path: str) -> dict[str, str]:
    try:
        mode = runtime_path.lstat().st_mode
    except FileNotFoundError:
        record = _record(str(runtime_path), None)
    else:
        if stat.S_ISLNK(mode):
            raise ValueError(f"managed runtime target is a symlink: {runtime_path}")
        if not stat.S_ISREG(mode):
            raise ValueError(f"managed runtime target is not a regular file: {runtime_path}")
        record = _record(str(runtime_path), runtime_path.read_bytes())
    record["source_path"] = source_path
    return record


def current_runtime_snapshot(root: Path) -> dict[str, Any]:
    hook_root = Path.home() / ".codex" / "hooks"
    skill_root = Path.home() / ".codex" / "skills" / "delivery-harness-framework"
    for managed_root in (hook_root, skill_root):
        try:
            mode = managed_root.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"managed runtime root is a symlink: {managed_root}")
        if not stat.S_ISDIR(mode):
            raise ValueError(f"managed runtime root is not a directory: {managed_root}")
    records = []
    for source_path in managed_source_paths(root):
        runtime_path = (
            hook_root / "dhf_preprompt.py"
            if source_path == HOOK_SOURCE
            else skill_root / Path(source_path).relative_to(SKILL_ROOT)
        )
        records.append(_live_record(runtime_path, source_path))
    snapshot = {
        "schema_version": 1,
        "kind": "current_runtime_snapshot",
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "managed_roots": [str(hook_root), str(skill_root)],
        "managed_relative_paths": [item["source_path"] for item in records],
        "records": records,
        "exclusions": list(EXCLUSIONS),
    }
    snapshot["aggregate_sha256"] = sha256_bytes(canonical_bytes(records))
    return snapshot


def runtime_boundary_evidence(root: Path) -> dict[str, Any]:
    base = base_expected_runtime_manifest(root)
    live = current_runtime_snapshot(root)
    base_by_path = {item["source_path"]: item for item in base["records"]}
    live_by_path = {item["source_path"]: item for item in live["records"]}
    changed = sorted(
        path for path in base_by_path
        if (base_by_path[path]["type"], base_by_path[path]["sha256"])
        != (live_by_path[path]["type"], live_by_path[path]["sha256"])
    )
    promotion_difference = sorted(
        path for path, item in live_by_path.items()
        if item["type"] != "regular" or item["sha256"] != sha256_file(root / path)
    )
    return {
        "base_expected_runtime_manifest": base,
        "current_runtime_snapshot": live,
        "changed_paths": changed,
        "promotion_difference_paths": promotion_difference,
        "gate_pass": not changed and bool(promotion_difference),
    }


def _load_dispatcher(root: Path):
    path = root / HOOK_SOURCE
    spec = importlib.util.spec_from_file_location("dhf_evidence_dispatcher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import dispatcher: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper_registry_identity(root: Path) -> dict[str, Any]:
    dispatcher = _load_dispatcher(root)
    registry = dispatcher.MANDATORY_HELPERS_BY_SIGNAL
    return {
        "version": 1,
        "sha256": sha256_bytes(canonical_bytes(registry)),
    }


def candidate_manifest(root: Path, corpus_path: Path, *, initial: bool) -> dict[str, Any]:
    source_paths = managed_source_paths(root)
    source_hashes = {path: sha256_file(root / path) for path in source_paths}
    dispatcher = _load_dispatcher(root)
    profile_contract = {
        "profile_rank": dispatcher.PROFILE_RANK,
        "governed_signal_patterns": dispatcher.GOVERNED_SIGNAL_PATTERNS,
        "standard_patterns": dispatcher.STANDARD_PATTERNS,
        "helpers_by_signal": dispatcher.MANDATORY_HELPERS_BY_SIGNAL,
    }
    helper = helper_registry_identity(root)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "kind": "initial_candidate_manifest" if initial else "promotion_candidate_manifest",
        "base_commit": BASE_COMMIT,
        "source_hashes": source_hashes,
        "profile_contract_sha256": sha256_bytes(canonical_bytes(profile_contract)),
        "normative_mirror_hashes": {path: sha256_file(root / path) for path in MIRRORS},
        "corpus_sha256": sha256_file(corpus_path),
        "runner_sha256": sha256_file(root / "scripts" / "run_dhf_simplification_pair.py"),
        "helper_registry_version": helper["version"],
        "helper_registry_sha256": helper["sha256"],
    }
    if initial:
        manifest["informational_only"] = True
    else:
        manifest["created_after_slice"] = 3
        manifest["immutable_for_slice_4"] = True
    manifest["manifest_sha256"] = sha256_bytes(canonical_bytes(manifest))
    return manifest


def validate_manifest(manifest: object, expected: dict[str, Any], *, check_current: bool) -> list[str]:
    if not isinstance(manifest, dict):
        return [f"missing {expected['kind']}"]
    errors = []
    stored = dict(manifest)
    digest = stored.pop("manifest_sha256", None)
    if digest != sha256_bytes(canonical_bytes(stored)):
        errors.append(f"{expected['kind']} canonical manifest hash mismatch")
    if check_current and manifest != expected:
        errors.append(f"{expected['kind']} identity drift")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--corpus", default="tests/fixtures/dhf_simplification_scenarios.json")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    corpus = (root / args.corpus).resolve()
    payload = {
        "artifact_schema": SCHEMA,
        "base_expected_runtime_manifest": base_expected_runtime_manifest(root),
        "runtime_boundary": runtime_boundary_evidence(root),
        "promotion_candidate_manifest": candidate_manifest(root, corpus, initial=False),
        "helper_registry": helper_registry_identity(root),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["runtime_boundary"]["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
