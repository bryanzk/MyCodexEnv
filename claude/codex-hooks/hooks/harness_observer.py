#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from harness_guard import current_phase, git_root, load_policy
except Exception:  # Observer must keep logging best-effort if guard imports fail.
    current_phase = None
    git_root = None
    load_policy = None

try:  # Separate import: an older deployed guard without gate tracing must not
    from harness_guard import phase_with_trace  # disable the imports above.
except Exception:
    phase_with_trace = None


COMMAND_HEAD_LIMIT = 200
KEY_OUTPUT_LIMIT = 500
TEXT_FIELD_LIMIT = 500
MAX_RECORD_BYTES = 8 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
DIRECTORY_MODE = 0o700
FILE_MODE = 0o600


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


def cwd_text(payload: dict[str, Any]) -> str:
    return str(payload.get("cwd") or tool_input(payload).get("cwd") or os.getcwd())


def fallback_phase(payload: dict[str, Any]) -> str:
    return str(payload.get("phase") or tool_input(payload).get("phase") or os.environ.get("CODEX_HARNESS_PHASE") or "unknown")


def resolved_phase(payload: dict[str, Any], cwd: str) -> str:
    if current_phase is None or git_root is None or load_policy is None:
        return fallback_phase(payload)
    try:
        policy = load_policy()
        if not policy:
            return fallback_phase(payload)
        return current_phase(payload, policy, git_root(cwd))
    except Exception:
        return fallback_phase(payload)


def resolved_phase_and_trace(payload: dict[str, Any], cwd: str) -> tuple[str, dict[str, Any] | None]:
    """S5: phase plus the per-gate verdicts, degrading to the legacy
    phase-only resolution when tracing is unavailable."""
    if phase_with_trace is None or git_root is None or load_policy is None:
        return resolved_phase(payload, cwd), None
    try:
        policy = load_policy()
        if not policy:
            return fallback_phase(payload), None
        phase, _, trace = phase_with_trace(payload, policy, git_root(cwd))
        return phase, trace
    except Exception:
        return resolved_phase(payload, cwd), None


def sha256_prefix(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def serialize_event(event: dict[str, Any]) -> str:
    serialized = json.dumps(event, ensure_ascii=False, sort_keys=True)
    if len(serialized.encode("utf-8")) <= MAX_RECORD_BYTES:
        return serialized

    shortened = {
        key: value[:64] if isinstance(value, str) else value
        for key, value in event.items()
    }
    shortened["truncated"] = True
    serialized = json.dumps(shortened, ensure_ascii=False, sort_keys=True)
    if len(serialized.encode("utf-8")) > MAX_RECORD_BYTES:
        raise ValueError("evidence record exceeds hard limit after truncation")
    return serialized


def writable_target(target_dir: Path, date: str, record_size: int) -> Path:
    sequence = 0
    while True:
        suffix = "" if sequence == 0 else f".{sequence}"
        target = target_dir / f"{date}{suffix}.jsonl"
        if not target.exists() or target.stat().st_size + record_size <= MAX_FILE_BYTES:
            return target
        sequence += 1


def append_event(event: dict[str, Any]) -> None:
    target_dir = Path(os.environ.get("CODEX_HARNESS_EVIDENCE_DIR", str(codex_home() / "harness" / "evidence"))).expanduser()
    target_dir.mkdir(parents=True, mode=DIRECTORY_MODE, exist_ok=True)
    target_dir.chmod(DIRECTORY_MODE)
    record = serialize_event(event) + "\n"
    target = writable_target(target_dir, str(event["timestamp"])[:10], len(record.encode("utf-8")))
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, FILE_MODE)
    os.fchmod(descriptor, FILE_MODE)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(record)


def refresh_loaded_receipt(payload: dict[str, Any]) -> None:
    target_dir = codex_home() / "harness"
    target_dir.mkdir(parents=True, mode=DIRECTORY_MODE, exist_ok=True)
    target_dir.chmod(DIRECTORY_MODE)
    hook_path = Path(__file__).resolve()
    session_id = payload.get("session_id") or os.environ.get("CODEX_SESSION_ID")
    receipt = {
        "schema_version": 1,
        "hook_path": str(hook_path),
        "self_digest": hashlib.sha256(hook_path.read_bytes()).hexdigest(),
        "session_id": str(session_id)[:TEXT_FIELD_LIMIT] if session_id else None,
        "event_kind": str(
            payload.get("hook_event_name")
            or payload.get("event_kind")
            or payload.get("event_type")
            or "unknown"
        ),
        "written_at": now_iso(),
    }
    target = target_dir / "loaded-receipt.json"
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target_dir)
    try:
        os.fchmod(descriptor, FILE_MODE)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
        parent_descriptor = os.open(target_dir, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def build_event(payload: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    cwd = cwd_text(payload)
    command = command_text(payload) or ""
    output = str(payload.get("key_output") or payload.get("result") or payload.get("output") or "")
    raw_capture = os.environ.get("CODEX_HARNESS_EVIDENCE_RAW") == "1"
    phase, phase_trace = resolved_phase_and_trace(payload, cwd)
    event = {
        "schema_version": 1,
        "timestamp": timestamp,
        "session_id": str(payload.get("session_id") or os.environ.get("CODEX_SESSION_ID") or "")[:TEXT_FIELD_LIMIT],
        "event_type": "tool_call",
        "cwd": cwd[:TEXT_FIELD_LIMIT],
        "phase": phase[:TEXT_FIELD_LIMIT],
        "tool_name": str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "unknown")[:TEXT_FIELD_LIMIT],
        "command_present": bool(command),
        "command_length": len(command),
        "command_sha256_prefix": sha256_prefix(command),
        "raw_capture": raw_capture,
        "exit_code": int(payload.get("exit_code")) if isinstance(payload.get("exit_code"), int) else 0,
        "key_output": output[:KEY_OUTPUT_LIMIT],
        "output_length": len(output),
        "output_sha256_prefix": sha256_prefix(output),
        "approval_state": "unknown",
        "failure_class": "none",
    }
    if phase_trace is not None:
        event["phase_trace"] = phase_trace
    if raw_capture:
        event["command_head"] = command[:COMMAND_HEAD_LIMIT]
    if len(command.encode("utf-8")) > MAX_RECORD_BYTES or len(output) > KEY_OUTPUT_LIMIT:
        event["truncated"] = True
    return event


def main() -> int:
    payload = load_payload()
    try:
        refresh_loaded_receipt(payload)
    except Exception as exc:  # Loaded evidence is best-effort; sync fails closed later.
        print(f"[harness_observer] loaded receipt warning: {exc}", file=sys.stderr)
    try:
        append_event(build_event(payload))
    except Exception as exc:  # Observer must not block the originating tool call.
        print(f"[harness_observer] warning: {exc}", file=sys.stderr)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
