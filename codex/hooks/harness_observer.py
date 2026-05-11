#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def command_text(payload: dict[str, Any]) -> str | None:
    data = tool_input(payload)
    for key in ("command", "cmd"):
        if key in data:
            return str(data[key])
    for key in ("command", "cmd"):
        if key in payload:
            return str(payload[key])
    return None


def append_event(event: dict[str, Any]) -> None:
    target_dir = Path(os.environ.get("CODEX_HARNESS_EVIDENCE_DIR", str(codex_home() / "harness" / "evidence"))).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{event['timestamp'][:10]}.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def build_event(payload: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "schema_version": 1,
        "timestamp": timestamp,
        "session_id": str(payload.get("session_id") or os.environ.get("CODEX_SESSION_ID") or ""),
        "event_type": "tool_call",
        "cwd": str(payload.get("cwd") or tool_input(payload).get("cwd") or os.getcwd()),
        "phase": str(payload.get("phase") or tool_input(payload).get("phase") or os.environ.get("CODEX_HARNESS_PHASE") or "unknown"),
        "tool_name": str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "unknown"),
        "command": command_text(payload) or "",
        "exit_code": int(payload.get("exit_code")) if isinstance(payload.get("exit_code"), int) else 0,
        "key_output": str(payload.get("key_output") or payload.get("result") or payload.get("output") or "")[:500],
        "approval_state": "unknown",
        "failure_class": "none",
    }


def main() -> int:
    try:
        append_event(build_event(load_payload()))
    except Exception as exc:  # Observer must not block the originating tool call.
        print(f"[harness_observer] warning: {exc}", file=sys.stderr)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
