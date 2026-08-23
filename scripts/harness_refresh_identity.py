#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APPROVALS = Path("runtime-approvals/approved-source-digests.txt")
CORPUS = Path("tests/fixtures/dhf_simplification_scenarios.json")
OBSERVATIONS = Path("tests/fixtures/dhf_simplification_observations.json")


def source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "codex/"],
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise RuntimeError("tracked source enumeration failed")
    for relative in sorted(part for part in tracked.stdout.split(b"\0") if part):
        path = root / os.fsdecode(relative)
        content = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
        digest.update(relative + b"\0" + str(len(content)).encode("ascii") + b"\0" + content)
    return digest.hexdigest()


def _generator(root: Path = ROOT):
    sys.path.insert(0, str(root / "scripts"))
    import run_dhf_simplification_pair as generator

    return generator


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _capture(root: Path, corpus_path: Path, observations_path: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / ".codex" / "hooks").mkdir(parents=True)
        (home / ".codex" / "skills").mkdir(parents=True)
        shutil.copy2(root / "codex" / "hooks" / "dhf_preprompt.py", home / ".codex" / "hooks")
        shutil.copytree(
            root / "codex" / "skills" / "delivery-harness-framework",
            home / ".codex" / "skills" / "delivery-harness-framework",
        )
        output = home / "observations.json"
        env = os.environ.copy()
        env["HOME"] = str(home)
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / "run_dhf_simplification_pair.py"), "capture",
             str(corpus_path), "--observations", str(observations_path), "--output", str(output)],
            cwd=root, env=env, capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        return json.loads(output.read_text(encoding="utf-8"))


def _transition(identities: dict[str, Any], generator: Any) -> dict[str, Any]:
    runner = identities["runner_identity"]
    value = {
        "schema_version": 1,
        "kind": "dhf_simplification_transition_identity",
        "authorized_slices": [5, 6],
        "runner_name": runner["name"],
        "runner_version": runner["version"],
        "runner_sha256": runner["sha256"],
        "managed_source_hashes_sha256": generator._canonical_sha256(
            identities["promotion_candidate_manifest"]["source_hashes"]
        ),
    }
    value["identity_sha256"] = generator._canonical_sha256(value)
    return value


def _observation_identity(observations: dict[str, Any], generator: Any) -> dict[str, Any]:
    skill_hashes = sorted({
        item["candidate_capture"]["provenance"]["skill_sha256"]
        for item in observations["observations"]
    })
    return {
        "artifact_schema": observations["artifact_schema"],
        "base_identity": observations["base_identity"],
        "corpus_identity": observations["corpus_identity"],
        "helper_registry_identity": observations["helper_registry_identity"],
        "promotion_candidate_manifest": observations["promotion_candidate_manifest"],
        "promotion_skill_sha256": skill_hashes,
    }


def status(root: Path = ROOT) -> tuple[list[str], bool]:
    generator = _generator(root)
    corpus = json.loads((root / CORPUS).read_text(encoding="utf-8"))
    identities = generator.identity_bundle(corpus, root)

    expected_a = source_digest(root)
    approval_text = (root / APPROVALS).read_text(encoding="utf-8")
    approved = re.findall(r"^sha256:([0-9a-f]{64})  .+$", approval_text, re.MULTILINE)
    fresh_a = expected_a in approved
    current_a = expected_a if fresh_a else (approved[-1] if approved else "absent")

    current_b = json.loads((root / generator.TRANSITION_IDENTITY).read_text(encoding="utf-8"))
    expected_b = _transition(identities, generator)
    fresh_b = current_b == expected_b

    observations = json.loads((root / OBSERVATIONS).read_text(encoding="utf-8"))
    current_c_value = _observation_identity(observations, generator)
    expected_c_value = {
        "artifact_schema": identities["artifact_schema"],
        "base_identity": identities["base_identity"],
        "corpus_identity": identities["corpus_identity"],
        "helper_registry_identity": identities["helper_registry_identity"],
        "promotion_candidate_manifest": identities["promotion_candidate_manifest"],
        "promotion_skill_sha256": [identities["promotion_candidate_manifest"]["source_hashes"][
            "codex/skills/delivery-harness-framework/SKILL.md"
        ]],
    }
    current_c = generator._canonical_sha256(current_c_value)
    expected_c = generator._canonical_sha256(expected_c_value)
    fresh_c = current_c_value == expected_c_value

    snapshot = observations["producer_evidence"]["PRODUCER-AC-16-S4-1"]["evidence"]["current_runtime_snapshot"]
    captured_at = snapshot.get("captured_at", "absent")
    captured_in_commit = snapshot.get("captured_in_commit", "absent")
    commit_time = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%aI", str(captured_in_commit)],
        capture_output=True, text=True, check=False,
    )
    try:
        fresh_d = commit_time.returncode == 0 and abs(
            datetime.fromisoformat(commit_time.stdout.strip())
            - datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
        ).total_seconds() <= 900
    except ValueError:
        fresh_d = False

    rows = [
        f"A current=sha256:{current_a} expected=sha256:{expected_a} state={'fresh' if fresh_a else 'stale'}",
        f"B current={current_b.get('identity_sha256', 'absent')} expected={expected_b['identity_sha256']} state={'fresh' if fresh_b else 'stale'}",
        f"C current={current_c} expected={expected_c} state={'fresh' if fresh_c else 'stale'}",
        f"D current={captured_in_commit}@{captured_at} expected=git-author-date-within-15m state={'fresh' if fresh_d else 'stale'}",
    ]
    return rows, fresh_a and fresh_b and fresh_c and fresh_d


def refresh(root: Path, message: str, *, approve: bool) -> None:
    generator = _generator(root)
    corpus_path = root / CORPUS
    observations_path = root / OBSERVATIONS
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    observations = json.loads(observations_path.read_text(encoding="utf-8"))

    _write_json(root / generator.TRANSITION_IDENTITY, _transition(generator.identity_bundle(corpus, root), generator))
    print("B refreshed")

    captured = _capture(root, corpus_path, observations_path)
    producer_id = "PRODUCER-AC-16-S4-1"
    historical = observations["producer_evidence"][producer_id]["evidence"]
    refreshed = captured["producer_evidence"][producer_id]
    for field in ("current_runtime_snapshot", "changed_paths", "promotion_difference_paths"):
        refreshed["evidence"][field] = copy.deepcopy(historical[field])
    refreshed["evidence_sha256"] = generator._canonical_sha256(refreshed["evidence"])
    _write_json(observations_path, captured)
    print("C refreshed")
    provenance = historical["current_runtime_snapshot"]["captured_in_commit"]
    print(f"AC-16 preserved (historical, provenance {provenance[:8]})")

    rows, _ = status(root)
    if not all(any(row.startswith(layer + " ") and row.endswith("state=fresh") for row in rows) for layer in ("B", "C", "D")):
        raise RuntimeError("identity refresh layer verification failed")

    digest = source_digest(root)
    approval = f"sha256:{digest}  {message}"
    print(approval)
    if approve:
        path = root / APPROVALS
        lines = path.read_text(encoding="utf-8").splitlines()
        if not any(line.startswith(f"sha256:{digest}  ") for line in lines):
            path.write_text("\n".join([*lines, approval]) + "\n", encoding="utf-8")
        rows, _ = status(root)
        if not any(row.startswith("A ") and row.endswith("state=fresh") for row in rows):
            raise RuntimeError("approval layer verification failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect managed-source identity freshness.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--message", required=True)
    refresh_parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()
    if args.command == "status":
        try:
            rows, fresh = status()
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print("\n".join(rows))
        return 0 if fresh else 1
    if args.command == "refresh":
        try:
            refresh(ROOT, args.message, approve=args.approve)
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
