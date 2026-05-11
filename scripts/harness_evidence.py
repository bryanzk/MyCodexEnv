#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PHASES = {
    "research",
    "requirements",
    "planning",
    "development",
    "validation",
    "review",
    "ship",
    "handoff",
    "unknown",
}

EVENT_TYPES = {
    "startup_probe",
    "tool_call",
    "approval_request",
    "sandbox_failure",
    "verification_result",
    "browser_smoke",
    "subagent_report",
    "checkpoint",
    "handoff",
    "guardrail_decision",
}

APPROVAL_STATES = {"not_required", "required", "approved", "denied", "blocked", "unknown"}
FAILURE_CLASSES = {
    "none",
    "missing_source",
    "malformed_input",
    "forbidden_input",
    "empty_dataset",
    "auth_required",
    "boundary_breach",
    "external_unavailable",
    "partial_write_risk",
    "sandbox_blocked",
    "unknown",
}


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def evidence_path(home: Path, timestamp: str) -> Path:
    date = timestamp[:10]
    return home / "harness" / "evidence" / f"{date}.jsonl"


def validate_event(event: dict[str, Any]) -> None:
    missing = [key for key in ("schema_version", "timestamp", "event_type", "cwd", "phase") if key not in event]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    if event["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if event["event_type"] not in EVENT_TYPES:
        raise ValueError(f"invalid event_type: {event['event_type']}")
    if event["phase"] not in PHASES:
        raise ValueError(f"invalid phase: {event['phase']}")
    if event.get("approval_state", "not_required") not in APPROVAL_STATES:
        raise ValueError(f"invalid approval_state: {event.get('approval_state')}")
    if event.get("failure_class", "none") not in FAILURE_CLASSES:
        raise ValueError(f"invalid failure_class: {event.get('failure_class')}")
    if event["event_type"] == "verification_result":
        for key in ("command", "exit_code", "key_output"):
            if key not in event or event[key] in ("", None):
                raise ValueError(f"verification_result missing {key}")
    if "exit_code" in event and not isinstance(event["exit_code"], int):
        raise ValueError("exit_code must be an integer")


def append_event(home: Path, event: dict[str, Any]) -> Path:
    validate_event(event)
    target = evidence_path(home, str(event["timestamp"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return target


def build_event(args: argparse.Namespace) -> dict[str, Any]:
    metadata = json.loads(args.metadata) if args.metadata else None
    event: dict[str, Any] = {
        "schema_version": 1,
        "timestamp": args.timestamp or now_iso(),
        "event_type": args.event_type,
        "cwd": args.cwd or os.getcwd(),
        "phase": args.phase,
        "approval_state": args.approval_state,
        "failure_class": args.failure_class,
    }
    optional = {
        "session_id": args.session_id,
        "tool_name": args.tool_name,
        "command": args.command,
        "exit_code": args.exit_code,
        "key_output": args.key_output,
        "message": args.message,
        "metadata": metadata,
    }
    for key, value in optional.items():
        if value is not None:
            event[key] = value
    return event


def cmd_append(args: argparse.Namespace) -> int:
    try:
        event = build_event(args)
        target = append_event(codex_home(args.codex_home), event)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(str(target))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        event = json.loads(Path(args.path).read_text(encoding="utf-8"))
        validate_event(event)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and append Codex harness evidence events.")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    append_parser = subparsers.add_parser("append", help="Append one evidence event to local Codex home")
    append_parser.add_argument("--codex-home")
    append_parser.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES))
    append_parser.add_argument("--phase", default="unknown", choices=sorted(PHASES))
    append_parser.add_argument("--cwd")
    append_parser.add_argument("--timestamp")
    append_parser.add_argument("--session-id")
    append_parser.add_argument("--tool-name")
    append_parser.add_argument("--command")
    append_parser.add_argument("--exit-code", type=int)
    append_parser.add_argument("--key-output")
    append_parser.add_argument("--approval-state", default="not_required", choices=sorted(APPROVAL_STATES))
    append_parser.add_argument("--failure-class", default="none", choices=sorted(FAILURE_CLASSES))
    append_parser.add_argument("--message")
    append_parser.add_argument("--metadata", help="JSON object string")
    append_parser.set_defaults(func=cmd_append)

    validate_parser = subparsers.add_parser("validate", help="Validate one JSON event file")
    validate_parser.add_argument("path")
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
