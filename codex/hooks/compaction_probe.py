#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from compaction_counter import compaction_event_increment
from context_meter import USAGE_FIELDS_PRESENT, build_context


STATE_VERSION = 1
META_READ_LIMIT = 64 * 1024
DEFAULT_MTIME_WINDOW_SECONDS = 120.0
DEFAULT_BUDGET_MS = 90.0


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def load_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def payload_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [payload]
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            sources.append(value)
    return sources


def first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for source in payload_sources(payload):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def normalized_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def check_deadline(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise TimeoutError("compaction probe budget exhausted")


def session_metadata(path: Path) -> tuple[str, Path] | None:
    try:
        with path.open("rb") as handle:
            prefix = handle.read(META_READ_LIMIT)
    except OSError:
        return None
    for raw_line in prefix.splitlines():
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(event, dict) or event.get("type") != "session_meta":
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        session_id = payload.get("id")
        cwd = payload.get("cwd")
        if isinstance(session_id, str) and session_id and isinstance(cwd, str) and cwd:
            return session_id, normalized_path(cwd)
    return None


def session_paths(sessions_root: Path, deadline: float) -> list[Path]:
    if not sessions_root.is_dir():
        return []
    paths: list[Path] = []
    for path in sessions_root.rglob("*.jsonl"):
        check_deadline(deadline)
        if path.is_file():
            paths.append(path)
    return sorted(paths)


def under_root(path: Path, root: Path) -> bool:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def resolve_explicit_session(
    payload: dict[str, Any], sessions_root: Path, session_id: str, deadline: float
) -> Path | None:
    transcript_path = first_text(payload, ("transcript_path", "session_path"))
    if transcript_path:
        candidate = Path(transcript_path).expanduser()
        if candidate.is_file() and under_root(candidate, sessions_root):
            metadata = session_metadata(candidate)
            if metadata is not None and metadata[0] == session_id:
                return candidate.resolve()

    candidates: list[Path] = []
    for path in session_paths(sessions_root, deadline):
        if session_id not in path.name:
            continue
        metadata = session_metadata(path)
        if metadata is not None and metadata[0] == session_id:
            candidates.append(path.resolve())
    return candidates[0] if len(candidates) == 1 else None


def resolve_heuristic_session(
    payload: dict[str, Any], sessions_root: Path, deadline: float, now: float, mtime_window: float
) -> Path | None:
    cwd = first_text(payload, ("cwd", "workdir", "repo_root"))
    if not cwd:
        return None
    expected_cwd = normalized_path(cwd)
    candidates: list[Path] = []
    for path in session_paths(sessions_root, deadline):
        check_deadline(deadline)
        try:
            age = now - path.stat().st_mtime
        except OSError:
            continue
        if age < 0 or age > mtime_window:
            continue
        metadata = session_metadata(path)
        if metadata is not None and metadata[1] == expected_cwd:
            candidates.append(path.resolve())
            if len(candidates) > 1:
                return None
    return candidates[0] if len(candidates) == 1 else None


def resolve_session_file(
    payload: dict[str, Any], sessions_root: Path, deadline: float, *, now: float | None = None
) -> tuple[Path | None, str]:
    session_id = first_text(payload, ("session_id", "thread_id", "conversation_id"))
    if session_id:
        path = resolve_explicit_session(payload, sessions_root, session_id, deadline)
        return (path, "session_id_hit" if path is not None else "session_id_not_found")
    try:
        mtime_window = float(os.environ.get("COMPACTION_PROBE_MTIME_WINDOW_SECONDS", DEFAULT_MTIME_WINDOW_SECONDS))
    except ValueError:
        mtime_window = DEFAULT_MTIME_WINDOW_SECONDS
    path = resolve_heuristic_session(
        payload,
        sessions_root,
        deadline,
        time.time() if now is None else now,
        max(0.0, mtime_window),
    )
    return (path, "heuristic_unique" if path is not None else "heuristic_inconclusive")


def empty_state() -> dict[str, Any]:
    return {"schema_version": STATE_VERSION, "sessions": {}}


def load_probe_state(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return empty_state(), "missing_state"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_state(), "corrupt_state"
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != STATE_VERSION
        or not isinstance(value.get("sessions"), dict)
    ):
        return empty_state(), "corrupt_state"
    return value, "valid"


def valid_state_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("offset"), int)
        and not isinstance(value.get("offset"), bool)
        and value["offset"] >= 0
        and isinstance(value.get("compaction_ordinal"), int)
        and not isinstance(value.get("compaction_ordinal"), bool)
        and value["compaction_ordinal"] >= 0
        and isinstance(value.get("device"), int)
        and isinstance(value.get("inode"), int)
    )


def read_from_offset(session_file: Path, offset: int) -> bytes:
    with session_file.open("rb") as handle:
        handle.seek(offset)
        return handle.read()


def decoded_increment(chunk: bytes) -> tuple[int, int, int]:
    last_newline = chunk.rfind(b"\n")
    if last_newline < 0:
        return 0, 0, 0
    consumed = last_newline + 1
    count = 0
    malformed = 0
    for raw_line in chunk[:consumed].splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            malformed += 1
            continue
        count += compaction_event_increment(event)
    return count, consumed, malformed


def atomic_write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def scan_session_incremental(session_file: Path, state_file: Path) -> dict[str, Any]:
    session_file = session_file.resolve()
    stat = session_file.stat()
    state, state_status = load_probe_state(state_file)
    state_key = str(session_file)
    entry = state["sessions"].get(state_key)

    if state_status == "missing_state":
        scan_mode = "full_missing_state"
        offset = 0
        ordinal = 0
    elif state_status == "corrupt_state":
        scan_mode = "full_corrupt_state"
        offset = 0
        ordinal = 0
    elif not valid_state_entry(entry):
        scan_mode = "full_missing_entry"
        offset = 0
        ordinal = 0
    elif entry["device"] != stat.st_dev or entry["inode"] != stat.st_ino:
        scan_mode = "full_replaced"
        offset = 0
        ordinal = 0
    elif entry["offset"] > stat.st_size:
        scan_mode = "full_shrunk"
        offset = 0
        ordinal = 0
    else:
        scan_mode = "incremental"
        offset = entry["offset"]
        ordinal = entry["compaction_ordinal"]

    chunk = read_from_offset(session_file, offset)
    increment, consumed, malformed_count = decoded_increment(chunk)
    ordinal += increment
    new_offset = offset + consumed
    state["sessions"][state_key] = {
        "offset": new_offset,
        "compaction_ordinal": ordinal,
        "device": stat.st_dev,
        "inode": stat.st_ino,
    }
    atomic_write_state(state_file, state)
    return {
        "compaction_ordinal": ordinal,
        "scan_mode": scan_mode,
        "bytes_read": len(chunk),
        "malformed_count": malformed_count,
        "offset": new_offset,
    }


def continue_response() -> dict[str, Any]:
    return {"continue": True}


def inject_response(
    ordinal: int,
    payload: dict[str, Any] | None = None,
    home: Path | None = None,
) -> dict[str, Any]:
    meter = build_context(
        payload or {},
        ordinal=ordinal,
        codex_home=home or codex_home(),
        usage_fields_present=USAGE_FIELDS_PRESENT,
    )
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": meter["additional_context"],
        },
    }


def append_inconclusive_evidence(payload: dict[str, Any], reason: str) -> None:
    evidence_dir = Path(
        os.environ.get(
            "CODEX_HARNESS_EVIDENCE_DIR",
            str(codex_home() / "harness" / "evidence"),
        )
    ).expanduser()
    timestamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
    event = {
        "schema_version": 1,
        "timestamp": timestamp,
        "session_id": "",
        "event_type": "startup_probe",
        "evidence_kind": "routine",
        "cwd": first_text(payload, ("cwd", "workdir", "repo_root")) or os.getcwd(),
        "phase": "unknown",
        "tool_name": "compaction_probe",
        "command": "compaction_probe.py",
        "exit_code": 0,
        "key_output": f"probe_inconclusive reason={reason}",
        "approval_state": "unknown",
        "failure_class": "missing_source",
        "message": "probe_inconclusive",
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target = evidence_dir / f"{timestamp[:10]}.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    response = continue_response()
    try:
        payload = load_payload()
        try:
            budget_ms = float(os.environ.get("COMPACTION_PROBE_BUDGET_MS", DEFAULT_BUDGET_MS))
        except ValueError:
            budget_ms = DEFAULT_BUDGET_MS
        deadline = time.monotonic() + max(1.0, budget_ms) / 1000.0
        sessions_root = codex_home() / "sessions"
        session_file, resolution = resolve_session_file(payload, sessions_root, deadline)
        if session_file is None:
            try:
                append_inconclusive_evidence(payload, resolution)
            except Exception:
                pass
        else:
            check_deadline(deadline)
            result = scan_session_incremental(
                session_file,
                codex_home() / "harness" / "probe_state.json",
            )
            check_deadline(deadline)
            response = inject_response(result["compaction_ordinal"], payload, codex_home())
    except Exception:
        response = continue_response()
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
