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
TASK_DEMAND_LEVELS = {"low", "medium", "high"}
TASK_DEMAND_FIELDS = ["level", "L", "H_tool", "S_state", "N_obs"]
GREEN_GATE_SCOPES = {"worker", "integrator"}
GREEN_GATE_REQUIRED_FIELDS = ["gate_scope", "command", "rationale"]
BRIEF_STRING_FIELDS = [
    "category",
    "summary",
    "current_behavior",
    "desired_behavior",
]
BRIEF_LIST_FIELDS = [
    "key_interfaces",
    "acceptance_criteria",
    "out_of_scope",
]


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


def validate_brief(agent: dict[str, Any], agent_id: str, errors: list[str]) -> dict[str, Any] | None:
    if "brief" not in agent:
        return None

    brief = agent.get("brief")
    if not isinstance(brief, dict):
        errors.append(f"ERROR[brief_type] agent={agent_id}: brief must be an object")
        return None

    normalized: dict[str, Any] = {}
    for field in BRIEF_STRING_FIELDS:
        value = brief.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"ERROR[brief_{field}] agent={agent_id}: brief.{field} is required")
        else:
            normalized[field] = value.strip()

    for field in BRIEF_LIST_FIELDS:
        value = brief.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"ERROR[brief_{field}] agent={agent_id}: brief.{field} must be a non-empty list")
            continue
        cleaned: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                errors.append(
                    f"ERROR[brief_{field}] agent={agent_id}: brief.{field}[{index}] must be a non-empty string"
                )
            else:
                cleaned.append(item.strip())
        if cleaned:
            normalized[field] = cleaned

    return normalized


def non_empty_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def validate_task_demand(agent: dict[str, Any], agent_id: str, errors: list[str]) -> dict[str, str] | None:
    demand = agent.get("task_demand")
    if not isinstance(demand, dict):
        errors.append(f"ERROR[task_demand_missing] agent={agent_id}: task_demand must be an object")
        return None

    normalized: dict[str, str] = {}
    level = non_empty_string(demand.get("level"))
    if level not in TASK_DEMAND_LEVELS:
        errors.append(
            f"ERROR[task_demand_level] agent={agent_id}: task_demand.level must be one of "
            f"{', '.join(sorted(TASK_DEMAND_LEVELS))}"
        )
    elif level:
        normalized["level"] = level

    for field in TASK_DEMAND_FIELDS:
        if field == "level":
            continue
        value = non_empty_string(demand.get(field))
        if not value:
            errors.append(f"ERROR[task_demand_{field}] agent={agent_id}: task_demand.{field} is required")
        else:
            normalized[field] = value

    return normalized


def require_gate_field(gate: dict[str, Any], field: str, agent_id: str, code: str, errors: list[str]) -> str:
    value = non_empty_string(gate.get(field))
    if not value:
        errors.append(f"ERROR[{code}] agent={agent_id}: green_gate.{field} is required")
    return value


def validate_green_gate(
    agent: dict[str, Any],
    agent_id: str,
    demand: dict[str, str] | None,
    verification: str,
    errors: list[str],
) -> dict[str, str] | None:
    gate = agent.get("green_gate")
    if not isinstance(gate, dict):
        errors.append(f"ERROR[green_gate_missing] agent={agent_id}: green_gate must be an object")
        return None

    normalized: dict[str, str] = {}
    for field in GREEN_GATE_REQUIRED_FIELDS:
        value = require_gate_field(gate, field, agent_id, f"green_gate_{field}", errors)
        if value:
            normalized[field] = value

    gate_scope = normalized.get("gate_scope", "")
    if gate_scope and gate_scope not in GREEN_GATE_SCOPES:
        errors.append(
            f"ERROR[green_gate_scope] agent={agent_id}: green_gate.gate_scope must be one of "
            f"{', '.join(sorted(GREEN_GATE_SCOPES))}"
        )

    level = (demand or {}).get("level", "")
    focused = non_empty_string(gate.get("focused_gate_command"))
    if level in {"medium", "high"} and not focused:
        errors.append(
            f"ERROR[green_gate_{level}_focused_gate] agent={agent_id}: "
            "green_gate.focused_gate_command is required"
        )
    if focused:
        normalized["focused_gate_command"] = focused

    full_gate = non_empty_string(gate.get("full_gate_command"))
    new_probe = non_empty_string(gate.get("new_probe"))
    if level == "high":
        if not full_gate:
            errors.append(f"ERROR[green_gate_high_full_gate] agent={agent_id}: green_gate.full_gate_command is required")
        if not new_probe:
            errors.append(f"ERROR[green_gate_high_new_probe] agent={agent_id}: green_gate.new_probe is required")
    if full_gate:
        normalized["full_gate_command"] = full_gate
    if new_probe:
        normalized["new_probe"] = new_probe

    integrator_gate = non_empty_string(gate.get("integrator_gate_command"))
    if gate_scope == "worker":
        if verification and normalized.get("command") and verification != normalized["command"]:
            errors.append(
                f"ERROR[green_gate_command_mismatch] agent={agent_id}: "
                "verification_command must equal green_gate.command when gate_scope=worker"
            )
    elif gate_scope == "integrator":
        if not integrator_gate:
            errors.append(
                f"ERROR[green_gate_integrator_command] agent={agent_id}: "
                "green_gate.integrator_gate_command is required when gate_scope=integrator"
            )
        elif verification and verification != integrator_gate:
            errors.append(
                f"ERROR[green_gate_integrator_mismatch] agent={agent_id}: "
                "verification_command must equal green_gate.integrator_gate_command when gate_scope=integrator"
            )
    if integrator_gate:
        normalized["integrator_gate_command"] = integrator_gate

    return normalized


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
        if role in READ_ONLY_ROLES and ("task_demand" in agent or "green_gate" in agent):
            errors.append(f"ERROR[read_only_demand_gate] agent={agent_id}: {role} must not define task_demand or green_gate")
        if role == "worker" and not normalized:
            errors.append(f"ERROR[worker_write_set] agent={agent_id}: worker must own a non-empty write_set")
        demand = None
        green_gate = None
        if role == "worker":
            demand = validate_task_demand(agent, agent_id, errors)
            green_gate = validate_green_gate(agent, agent_id, demand, verification, errors)
            for path in normalized:
                worker_paths.append((agent_id, path))
        brief = validate_brief(agent, agent_id, errors)

        summary.append(
            {
                "id": agent_id,
                "role": role,
                "scope": scope,
                "write_set": sorted(set(normalized)),
                "verification_command": verification,
                "brief": brief,
                "task_demand": demand,
                "green_gate": green_gate,
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
        brief_status = " brief=yes" if agent.get("brief") else ""
        demand = agent.get("task_demand") or {}
        green_gate = agent.get("green_gate") or {}
        demand_status = f" demand={demand['level']}" if demand.get("level") else ""
        gate_scope_status = f" gate_scope={green_gate['gate_scope']}" if green_gate.get("gate_scope") else ""
        green_gate_status = f" green_gate={green_gate['command']}" if green_gate.get("command") else ""
        print(
            "- "
            f"{agent['id']} role={agent['role']} scope={agent['scope']} "
            f"write_set={owned} verification={agent['verification_command']}"
            f"{demand_status}{gate_scope_status}{green_gate_status}{brief_status}"
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
