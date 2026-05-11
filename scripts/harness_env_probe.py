#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REQUIRED_PHASES = ["research", "requirements", "planning", "development", "validation", "review", "ship", "handoff"]


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def parse_simple_toml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    section: dict[str, Any] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section_name = line.strip("[]").strip().strip('"')
            section = data.setdefault(section_name, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        parsed: Any
        if value.lower() == "true":
            parsed = True
        elif value.lower() == "false":
            parsed = False
        elif value.startswith('"') and value.endswith('"'):
            parsed = value[1:-1]
        else:
            parsed = value
        if section is None:
            data[key] = parsed
        else:
            section[key] = parsed
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_probe(home: Path) -> tuple[int, dict[str, Any] | None, list[str]]:
    config_path = home / "config.toml"
    hooks_path = home / "hooks.json"
    policy_path = home / "runtime" / "tool-policy.json"
    schema_path = home / "runtime" / "evidence.schema.json"
    required_files = [config_path, hooks_path, policy_path, schema_path]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        return 1, None, [f"missing required runtime file: {path}" for path in missing]

    try:
        config = parse_simple_toml(config_path)
        hooks = load_json(hooks_path)
        policy = load_json(policy_path)
        schema = load_json(schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return 1, None, [str(exc)]

    sandbox_mode = config.get("sandbox_mode")
    approval_policy = config.get("approval_policy")
    observable = bool(sandbox_mode or approval_policy)
    observable_reason = "config declares sandbox or approval fields" if observable else "sandbox_mode and approval_policy are not declared in config.toml"
    feature_config = config.get("features", {})
    hooks_config = hooks.get("hooks", {}) if isinstance(hooks.get("hooks"), dict) else {}
    policy_phases = policy.get("phases", {}) if isinstance(policy.get("phases"), dict) else {}
    schema_event_types = (
        schema.get("properties", {}).get("event_type", {}).get("enum", [])
        if isinstance(schema.get("properties"), dict)
        else []
    )

    payload = {
        "codex_home": str(home),
        "config": {
            "path": str(config_path),
            "observable": observable,
            "observable_reason": observable_reason,
            "sandbox_mode": sandbox_mode,
            "approval_policy": approval_policy,
            "codex_hooks_feature": bool(feature_config.get("codex_hooks")),
        },
        "hooks": {
            "path": str(hooks_path),
            "enabled": bool(feature_config.get("codex_hooks")) and bool(hooks_config),
            "session_start": "SessionStart" in hooks_config,
            "pre_tool_use": "PreToolUse" in hooks_config,
            "post_tool_use": "PostToolUse" in hooks_config,
        },
        "runtime": {
            "tool_policy": str(policy_path),
            "evidence_schema": str(schema_path),
            "policy_phases_present": all(phase in policy_phases for phase in REQUIRED_PHASES),
            "evidence_verification_event_present": "verification_result" in schema_event_types,
        },
    }
    return 0, payload, []


def render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Harness Environment Probe",
            "",
            f"- codex_home: `{payload['codex_home']}`",
            f"- config_observable: `{payload['config']['observable']}`",
            f"- observable_reason: {payload['config']['observable_reason']}",
            f"- sandbox_mode: `{payload['config']['sandbox_mode']}`",
            f"- approval_policy: `{payload['config']['approval_policy']}`",
            f"- hooks_enabled: `{payload['hooks']['enabled']}`",
            f"- pre_tool_use: `{payload['hooks']['pre_tool_use']}`",
            f"- post_tool_use: `{payload['hooks']['post_tool_use']}`",
            f"- policy_phases_present: `{payload['runtime']['policy_phases_present']}`",
            f"- evidence_verification_event_present: `{payload['runtime']['evidence_verification_event_present']}`",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe observable Codex Harness Runtime environment configuration.")
    parser.add_argument("--codex-home")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    code, payload, errors = build_probe(codex_home(args.codex_home))
    if code != 0:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return code
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
