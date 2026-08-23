#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
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


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_dhf_simplification_pair as generator

    return generator


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
    generator = _generator()
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect managed-source identity freshness.")
    parser.add_subparsers(dest="command", required=True).add_parser("status")
    args = parser.parse_args()
    if args.command == "status":
        try:
            rows, fresh = status()
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print("\n".join(rows))
        return 0 if fresh else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
