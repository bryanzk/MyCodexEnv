#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def load_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def load_policy() -> dict[str, Any]:
    path = codex_home() / "runtime" / "tool-policy.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


def command_text(payload: dict[str, Any]) -> str:
    data = tool_input(payload)
    for key in ("command", "cmd"):
        if key in data:
            return str(data[key])
    for key in ("command", "cmd"):
        if key in payload:
            return str(payload[key])
    return ""


def candidate_paths(payload: dict[str, Any]) -> list[str]:
    data = tool_input(payload)
    paths: list[str] = []
    for key in ("path", "file", "file_path", "filename", "cwd", "workdir"):
        value = data.get(key) or payload.get(key)
        if isinstance(value, str):
            paths.append(value)
    return paths


def phase_from_state_snapshot(root: Path | None) -> str | None:
    if root is None:
        return None
    state = root / "docs" / "harness-state.md"
    try:
        text = state.read_text(encoding="utf-8")
    except OSError:
        return None

    in_snapshot = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## current snapshot"):
            in_snapshot = True
            continue
        if in_snapshot:
            if stripped.startswith("## "):
                break
            match = re.match(r"\s*-\s*phase:\s*([A-Za-z_]+)\s*$", line)
            if match:
                return match.group(1)
    return None


def current_phase(payload: dict[str, Any], policy: dict[str, Any], root: Path | None) -> str:
    value = (
        payload.get("phase")
        or tool_input(payload).get("phase")
        or os.environ.get("CODEX_HARNESS_PHASE")
        or phase_from_state_snapshot(root)
        or "unknown"
    )
    phase = str(value)
    return phase if phase in policy.get("phases", {}) else "unknown"


def unknown_phase_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("unknown_phase_behavior") == "default_phase":
        default_phase = str(policy.get("default_phase") or "")
        default_policy = policy.get("phases", {}).get(default_phase)
        if isinstance(default_policy, dict):
            return default_policy
    return {
        "allow_repo_write": False,
        "allow_network": False,
        "allow_remote": False,
        "require_approval": ["repo_write", "network", "remote", "secret", "destructive", "dynamic_exec"],
    }


def match_any(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return pattern
    return None


def configured_evidence_dir(policy: dict[str, Any]) -> Path:
    override = os.environ.get("CODEX_HARNESS_EVIDENCE_DIR")
    if override:
        return Path(override).expanduser()
    raw = str(policy.get("evidence_dir") or "")
    if raw == "~/.codex":
        return codex_home()
    if raw.startswith("~/.codex/"):
        return codex_home() / raw.removeprefix("~/.codex/")
    if raw:
        return Path(raw).expanduser()
    return codex_home() / "harness" / "evidence"


def payload_value(payload: dict[str, Any], key: str) -> Any:
    data = tool_input(payload)
    if key in data:
        return data[key]
    return payload.get(key)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def receipt_is_fresh(event: dict[str, Any], now: datetime) -> bool:
    timestamp = parse_timestamp(event.get("timestamp"))
    if timestamp is None:
        return False
    age = now - timestamp.astimezone(timezone.utc)
    return timedelta(0) <= age <= timedelta(minutes=10)


def has_fresh_validation_receipt(payload: dict[str, Any], policy: dict[str, Any], root: Path | None) -> bool:
    plan_hash = payload_value(payload, "plan_sha256")
    if not isinstance(plan_hash, str) or not plan_hash.strip() or root is None:
        return False
    expected_root = root.resolve(strict=False)
    expected_worker_count = int_or_none(payload_value(payload, "worker_count"))
    evidence_dir = configured_evidence_dir(policy)
    if not evidence_dir.exists() or not evidence_dir.is_dir():
        return False

    now = datetime.now(timezone.utc)
    try:
        paths = sorted(evidence_dir.glob("*.jsonl"))
    except OSError:
        return False

    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event_type") != "agent_team_validated" or event.get("evidence_kind") != "decision":
                continue
            metadata = event.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if metadata.get("plan_sha256") != plan_hash.strip():
                continue
            receipt_root = metadata.get("repo_root")
            if not isinstance(receipt_root, str):
                continue
            if Path(receipt_root).expanduser().resolve(strict=False) != expected_root:
                continue
            if expected_worker_count is not None and int_or_none(metadata.get("worker_count")) != expected_worker_count:
                continue
            if receipt_is_fresh(event, now):
                return True
    return False


def classify(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str | None]:
    cmd = command_text(payload)
    name = tool_name(payload).lower()
    path_text = "\n".join(candidate_paths(payload))
    if match_any(policy.get("secret_path_patterns", []), f"{cmd}\n{path_text}"):
        return "secret", "secret path or token-like string"
    if match_any(policy.get("destructive_command_patterns", []), cmd):
        return "destructive", "destructive command pattern"
    if match_any(policy.get("dynamic_exec_patterns", []), cmd):
        return "dynamic_exec", "dynamic download or execution pattern"
    if match_any(policy.get("remote_command_patterns", []), cmd):
        return "remote", "remote or infrastructure command"
    if match_any(policy.get("network_command_patterns", []), cmd):
        return "network", "network command pattern"
    agent_dispatch_names = {str(item).lower() for item in policy.get("agent_dispatch_tool_names", [])}
    if name in agent_dispatch_names or match_any(policy.get("agent_dispatch_command_patterns", []), cmd):
        return "agent_dispatch", "multi-agent dispatch"
    if name in {"apply_patch", "write", "edit", "multi_edit"} or match_any(policy.get("repo_write_command_patterns", []), cmd):
        return "repo_write", "repo write pattern"
    return "read", None


def git_root(cwd: str) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd or os.getcwd(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def decision(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy:
        return {}
    data = tool_input(payload)
    cwd = data.get("cwd") or payload.get("cwd") or os.getcwd()
    root = git_root(str(cwd))
    phase = current_phase(payload, policy, root)
    phase_policy = policy.get("phases", {}).get(phase)
    if phase_policy is None:
        phase_policy = unknown_phase_policy(policy)

    category, reason = classify(payload, policy)
    if category == "agent_dispatch":
        if has_fresh_validation_receipt(payload, policy, root):
            return {}
        return {
            "permissionDecision": "ask",
            "message": "[harness] validate the worker plan with scripts/harness_agent_team.py validate --emit-evidence before dispatch.",
        }
    if category == "read":
        return {}

    if category == "repo_write" and phase_policy.get("allow_repo_write") is True:
        return {}
    if category == "network" and phase_policy.get("allow_network") is True:
        return {}
    if category == "remote" and phase_policy.get("allow_remote") is True:
        return {}

    approval_required = set(phase_policy.get("require_approval", []))
    message = f"[harness] {category} is restricted during phase '{phase}': {reason or category}."
    if category in {"secret", "dynamic_exec"}:
        return {"permissionDecision": "deny", "message": message}
    if category in approval_required or category in {"destructive", "remote"}:
        return {"permissionDecision": "ask", "message": message}
    return {"permissionDecision": "deny", "message": message}


def main() -> int:
    payload = load_payload()
    result = decision(payload, load_policy())
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
