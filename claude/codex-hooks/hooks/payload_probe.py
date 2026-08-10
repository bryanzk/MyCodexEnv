#!/usr/bin/env python3
"""S0 payload schema probe.

Observation only. This hook never blocks, never alters a tool call, and never
records payload values other than the working directory (same practice as
harness_observer.py). Task identity is recorded as a short digest so repeated
calls can be correlated without creating a new identifier sink. Prompt text is
never recorded -- only its field name and size.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_INPUT_KEYS = ("tool_input", "input", "arguments", "params")
PROMPT_KEY_CANDIDATES = ("prompt", "user_prompt", "message", "text", "content", "input")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def probe_path() -> Path:
    override = os.environ.get("CODEX_HARNESS_PROBE_DIR")
    base = Path(override).expanduser() if override else codex_home() / "harness" / "probe"
    return base / "pretooluse-schema.jsonl"


def load_payload() -> tuple[dict[str, Any], str]:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}, "stdin_error"
    if not raw.strip():
        return {}, "empty"
    try:
        value = json.loads(raw)
    except Exception:
        return {}, "invalid_json"
    if not isinstance(value, dict):
        return {}, "not_object"
    return value, "ok"


def digest(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def sub_payload(payload: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    for key in TOOL_INPUT_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            return key, value
    return None, {}


def prompt_shape(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return the prompt field's name and size. Never returns its text."""
    chosen: tuple[str, str] | None = None
    for key in PROMPT_KEY_CANDIDATES:
        value = payload.get(key)
        if isinstance(value, str) and value:
            chosen = (key, value)
            break
    if chosen is None:
        strings = [(k, v) for k, v in payload.items() if isinstance(v, str) and v]
        if strings:
            chosen = max(strings, key=lambda item: len(item[1]))
    if chosen is None:
        return None
    key, text = chosen
    lines = text.splitlines()
    return {
        "field": key,
        "length": len(text),
        "line_count": len(lines),
        "first_line_length": len(lines[0]) if lines else 0,
    }


def build_record(payload: dict[str, Any], status: str, event: str) -> dict[str, Any]:
    tool_input_key, tool_input = sub_payload(payload)
    session_value = payload.get("session_id")
    record: dict[str, Any] = {
        "schema_version": 1,
        "event": event,
        "payload_status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "top_level_keys": sorted(payload.keys()),
        "tool_input_key": tool_input_key,
        "tool_input_keys": sorted(tool_input.keys()),
        "top_session_id_present": isinstance(session_value, str) and bool(session_value),
        "top_session_id_digest": digest(session_value),
        "tool_input_session_id_present": "session_id" in tool_input,
        "top_cwd_present": isinstance(payload.get("cwd"), str) and bool(payload.get("cwd")),
        "top_cwd": payload.get("cwd") if isinstance(payload.get("cwd"), str) else None,
        "tool_input_cwd_present": isinstance(tool_input.get("cwd"), str) and bool(tool_input.get("cwd")),
        "tool_input_cwd": tool_input.get("cwd") if isinstance(tool_input.get("cwd"), str) else None,
        "top_phase_present": "phase" in payload,
        "tool_input_phase_present": "phase" in tool_input,
        "tool_name": str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or ""),
        "command_length": len(str(tool_input.get("command") or tool_input.get("cmd") or "")),
    }
    if event == "user_prompt_submit":
        record["prompt_shape"] = prompt_shape(payload)
    return record


def append_record(record: dict[str, Any]) -> None:
    path = probe_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def main() -> int:
    # Every failure path must still emit {} so the originating tool call is
    # never blocked or marked failed.
    try:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--event", default="unknown")
        args, _ = parser.parse_known_args()
        payload, status = load_payload()
        append_record(build_record(payload, status, args.event))
    except Exception:
        pass
    sys.stdout.write("{}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
