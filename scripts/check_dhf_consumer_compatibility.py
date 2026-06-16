#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"same", "intentional_adapter", "drift_needs_review"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_matrix(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError("matrix version must be 1")
    if not isinstance(data.get("helpers"), list) or not data["helpers"]:
        raise ValueError("matrix helpers must be a non-empty list")
    if not isinstance(data.get("consumers"), list) or not data["consumers"]:
        raise ValueError("matrix consumers must be a non-empty list")
    return data


def resolve_root(repo_root: Path, consumer: dict[str, Any], override: str | None = None) -> Path:
    raw = override or consumer.get("root") or "."
    root = Path(raw).expanduser()
    if not root.is_absolute():
        root = repo_root / root
    return root.resolve()


def helper_path(root: Path, helper: str) -> Path:
    return root / "scripts" / helper


def classify_helper(
    baseline_root: Path,
    consumer_root: Path,
    helper: str,
    *,
    helper_policy: str,
) -> dict[str, Any]:
    baseline_path = helper_path(baseline_root, helper)
    consumer_path = helper_path(consumer_root, helper)
    result: dict[str, Any] = {
        "helper": helper,
        "baseline_path": str(baseline_path),
        "consumer_path": str(consumer_path),
    }
    if not baseline_path.exists():
        result.update({"status": "drift_needs_review", "reason": "missing baseline helper"})
        return result
    if not consumer_path.exists():
        result.update({"status": "drift_needs_review", "reason": "missing consumer helper"})
        return result

    baseline_hash = sha256(baseline_path)
    consumer_hash = sha256(consumer_path)
    result["baseline_sha256"] = baseline_hash
    result["consumer_sha256"] = consumer_hash
    if baseline_hash == consumer_hash:
        result.update({"status": "same", "reason": "helper hash matches baseline"})
    elif helper_policy == "intentional_adapter":
        result.update({"status": "intentional_adapter", "reason": "helper hash differs under intentional adapter policy"})
    else:
        result.update({"status": "drift_needs_review", "reason": "helper hash differs without adapter policy"})
    return result


def summarize_status(helper_results: list[dict[str, Any]], state_status: str) -> str:
    statuses = {item["status"] for item in helper_results}
    statuses.add(state_status)
    if "drift_needs_review" in statuses:
        return "drift_needs_review"
    if "intentional_adapter" in statuses:
        return "intentional_adapter"
    return "same"


def inspect_consumer(
    *,
    repo_root: Path,
    baseline_root: Path,
    consumer: dict[str, Any],
    helpers: list[str],
    root_override: str | None = None,
) -> dict[str, Any]:
    name = consumer.get("name")
    helper_policy = consumer.get("helper_policy", consumer.get("status", "same"))
    declared_status = consumer.get("status", "same")
    result: dict[str, Any] = {
        "name": name,
        "declared_status": declared_status,
        "helper_policy": helper_policy,
        "optional": bool(consumer.get("optional")),
        "verification_commands": consumer.get("verification_commands", []),
        "adapter_fields": consumer.get("adapter_fields", []),
        "issues": [],
    }

    if helper_policy not in STATUSES:
        result["issues"].append(f"invalid helper_policy: {helper_policy}")
    if declared_status not in STATUSES:
        result["issues"].append(f"invalid status: {declared_status}")

    root = resolve_root(repo_root, consumer, root_override)
    result["root"] = str(root)
    if not root.exists():
        result["compatibility_status"] = "root_unavailable"
        result["root_available"] = False
        if not result["optional"]:
            result["issues"].append("required consumer root is missing")
        return result

    result["root_available"] = True
    state_path = consumer.get("state_path", "")
    state_file = root / state_path
    result["state_path"] = state_path
    result["state_exists"] = state_file.exists()
    state_status = "same" if state_file.exists() else "drift_needs_review"
    if not state_file.exists():
        result["issues"].append(f"missing state path: {state_path}")

    helper_results = [
        classify_helper(baseline_root, root, helper, helper_policy=helper_policy)
        for helper in helpers
    ]
    result["helpers"] = helper_results
    for helper_result in helper_results:
        if helper_result["status"] == "drift_needs_review":
            result["issues"].append(f"{helper_result['helper']}: {helper_result['reason']}")

    result["compatibility_status"] = summarize_status(helper_results, state_status)
    return result


def validate(
    *,
    repo_root: Path,
    matrix_path: Path,
    consumer_name: str | None = None,
    consumer_root: str | None = None,
) -> dict[str, Any]:
    matrix = load_matrix(matrix_path)
    helpers = [str(item) for item in matrix["helpers"]]
    baseline_name = matrix.get("baseline_consumer")
    consumers = matrix["consumers"]
    baseline = next((item for item in consumers if item.get("name") == baseline_name), None)
    if baseline is None:
        raise ValueError(f"baseline consumer not found: {baseline_name}")
    baseline_root = resolve_root(repo_root, baseline)

    selected = [
        item
        for item in consumers
        if consumer_name is None or item.get("name") == consumer_name
    ]
    if consumer_name and not selected:
        raise ValueError(f"consumer not found: {consumer_name}")

    inspected = [
        inspect_consumer(
            repo_root=repo_root,
            baseline_root=baseline_root,
            consumer=item,
            helpers=helpers,
            root_override=consumer_root if item.get("name") == consumer_name else None,
        )
        for item in selected
    ]

    summary: dict[str, int] = {
        "same": 0,
        "intentional_adapter": 0,
        "drift_needs_review": 0,
        "root_unavailable": 0,
    }
    issues: list[str] = []
    for item in inspected:
        status = item["compatibility_status"]
        summary[status] = summary.get(status, 0) + 1
        for issue in item.get("issues", []):
            issues.append(f"{item['name']}: {issue}")

    hard_issues = [
        issue for issue in issues
        if "required consumer root is missing" not in issue
    ]
    ok = not hard_issues and summary.get("drift_needs_review", 0) == 0
    return {
        "ok": ok,
        "baseline_consumer": baseline_name,
        "matrix": str(matrix_path),
        "consumers": inspected,
        "summary": summary,
        "issues": issues,
    }


def print_human(result: dict[str, Any]) -> None:
    print(f"DHF consumer compatibility: {'ok' if result['ok'] else 'needs review'}")
    for item in result["consumers"]:
        print(f"- {item['name']}: {item['compatibility_status']}")
        for issue in item.get("issues", []):
            print(f"  issue: {issue}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only DHF consumer compatibility and drift checker.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--matrix", default="docs/dhf-consumer-compatibility.json")
    parser.add_argument("--consumer", help="Limit the check to a single consumer name.")
    parser.add_argument("--consumer-root", help="Override the selected consumer root for local read-only checks.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        repo_root = Path(args.repo_root).resolve()
        matrix_path = Path(args.matrix)
        if not matrix_path.is_absolute():
            matrix_path = repo_root / matrix_path
        result = validate(
            repo_root=repo_root,
            matrix_path=matrix_path.resolve(),
            consumer_name=args.consumer,
            consumer_root=args.consumer_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "ok": False,
            "baseline_consumer": None,
            "matrix": args.matrix,
            "consumers": [],
            "summary": {"same": 0, "intentional_adapter": 0, "drift_needs_review": 0, "root_unavailable": 0},
            "issues": [f"ERROR[load] {exc}"],
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
