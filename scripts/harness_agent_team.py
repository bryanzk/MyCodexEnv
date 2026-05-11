#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


READ_ONLY_ROLES = {"planner", "reviewer", "security", "qa"}
WRITE_ROLES = {"worker"}
VALID_ROLES = READ_ONLY_ROLES | WRITE_ROLES


def git_root() -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_write_path(value: Any, repo_root: Path, agent_id: str, errors: list[str]) -> str | None:
    if not isinstance(value, str):
        errors.append(f"ERROR[path_type] agent={agent_id}: write_set entry must be a string")
        return None
    raw = value.strip()
    if not raw:
        errors.append(f"ERROR[path_empty] agent={agent_id}: write_set entry is empty")
        return None

    path = Path(raw).expanduser()
    if ".." in path.parts:
        errors.append(f"ERROR[path_traversal] agent={agent_id} path={raw}: '..' is not allowed")
        return None
    resolved = path.resolve(strict=False) if path.is_absolute() else (repo_root / path).resolve(strict=False)
    if not is_relative_to(resolved, repo_root):
        errors.append(f"ERROR[path_outside_repo] agent={agent_id} path={raw}: write_set must stay inside {repo_root}")
        return None
    return resolved.relative_to(repo_root).as_posix()


def paths_overlap(left: str, right: str) -> bool:
    left_path = Path(left)
    right_path = Path(right)
    return left == right or left_path in right_path.parents or right_path in left_path.parents


def validate_plan(plan: dict[str, Any], repo_root: Path) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    summary: list[dict[str, Any]] = []
    agents = plan.get("agents")
    if not isinstance(agents, list) or not agents:
        return ["ERROR[plan_agents]: plan must contain a non-empty agents[] list"], summary

    worker_paths: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for index, agent in enumerate(agents):
        if not isinstance(agent, dict):
            errors.append(f"ERROR[agent_object] agent_index={index}: agent must be an object")
            continue
        agent_id = str(agent.get("id", "")).strip()
        if not agent_id:
            agent_id = f"<index:{index}>"
            errors.append(f"ERROR[agent_id] agent={agent_id}: id is required")
        elif agent_id in seen_ids:
            errors.append(f"ERROR[duplicate_agent_id] agent={agent_id}: id must be unique")
        seen_ids.add(agent_id)

        role = str(agent.get("role", "")).strip()
        scope = str(agent.get("scope", "")).strip()
        verification = str(agent.get("verification_command", "")).strip()
        write_set = agent.get("write_set")

        if role not in VALID_ROLES:
            errors.append(f"ERROR[role] agent={agent_id}: role must be one of {', '.join(sorted(VALID_ROLES))}")
        if not scope:
            errors.append(f"ERROR[scope] agent={agent_id}: scope is required")
        if not verification:
            errors.append(f"ERROR[verification_command] agent={agent_id}: verification_command is required")
        if not isinstance(write_set, list):
            errors.append(f"ERROR[write_set_type] agent={agent_id}: write_set must be a list")
            write_set = []

        normalized = [
            path
            for path in (normalize_write_path(item, repo_root, agent_id, errors) for item in write_set)
            if path is not None
        ]
        if len(set(normalized)) != len(normalized):
            errors.append(f"ERROR[duplicate_write_path] agent={agent_id}: write_set contains duplicate paths")

        if role in READ_ONLY_ROLES and normalized:
            errors.append(f"ERROR[read_only_write_set] agent={agent_id}: {role} must use an empty write_set")
        if role == "worker" and not normalized:
            errors.append(f"ERROR[worker_write_set] agent={agent_id}: worker must own a non-empty write_set")
        if role == "worker":
            for path in normalized:
                worker_paths.append((agent_id, path))

        summary.append(
            {
                "id": agent_id,
                "role": role,
                "scope": scope,
                "write_set": sorted(set(normalized)),
                "verification_command": verification,
            }
        )

    for idx, (left_agent, left_path) in enumerate(worker_paths):
        for right_agent, right_path in worker_paths[idx + 1 :]:
            if left_agent != right_agent and paths_overlap(left_path, right_path):
                errors.append(
                    "ERROR[write_set_overlap] "
                    f"agents={left_agent},{right_agent} path={left_path} conflict_path={right_path}: worker write_sets overlap"
                )
    return errors, summary


def cmd_validate(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else git_root()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR[plan_read]: {exc}", file=sys.stderr)
        return 1
    if not isinstance(plan, dict):
        print("ERROR[plan_object]: plan must be a JSON object", file=sys.stderr)
        return 1

    errors, summary = validate_plan(plan, repo_root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("Agent team valid")
    print(f"repo_root: {repo_root}")
    for agent in summary:
        owned = ", ".join(agent["write_set"]) if agent["write_set"] else "read-only"
        print(
            "- "
            f"{agent['id']} role={agent['role']} scope={agent['scope']} "
            f"write_set={owned} verification={agent['verification_command']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Harness Runtime agent team plans.")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate PLAN.json")
    validate_parser.add_argument("plan")
    validate_parser.add_argument("--repo-root", help="Repository root for write_set normalization")
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
