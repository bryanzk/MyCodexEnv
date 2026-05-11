#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
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


def current_phase(payload: dict[str, Any], policy: dict[str, Any]) -> str:
    value = (
        payload.get("phase")
        or tool_input(payload).get("phase")
        or os.environ.get("CODEX_HARNESS_PHASE")
        or policy.get("default_phase")
        or "development"
    )
    phase = str(value)
    return phase if phase in policy.get("phases", {}) else "unknown"


def match_any(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return pattern
    return None


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
    phase = current_phase(payload, policy)
    phase_policy = policy.get("phases", {}).get(phase)
    if phase_policy is None:
        phase_policy = {"allow_repo_write": False, "allow_network": False, "allow_remote": False, "require_approval": ["repo_write", "network", "remote", "secret", "destructive", "dynamic_exec"]}

    category, reason = classify(payload, policy)
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
