#!/usr/bin/env python3
"""Record host-reported compactions per Codex session.

Registered on two host events:

- ``PostCompact``: the host finished a compaction. The session's ordinal goes up by one.
- ``SessionStart``: the session was seen. ``startup`` creates a complete record at
  ordinal 0. ``resume``, ``fork``, and ``compact`` only make sure a record exists; a
  record first created by them is marked incomplete, because compactions before it
  were not observed.

``compaction_probe.py`` reads this state at ``UserPromptSubmit``. The state lives in
``$CODEX_HOME/harness/compaction_ordinals.json``. This hook never blocks the host,
never reads session transcripts, and prints nothing.
"""
from __future__ import annotations

import fcntl
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


STATE_VERSION = 1
STATE_NAME = "compaction_ordinals.json"
RETENTION_SECONDS = 30 * 24 * 3600
COMPLETE_SOURCES = {"startup"}
SEEN_SOURCES = {"resume", "fork", "compact", "clear"}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def state_path(home: Path | None = None) -> Path:
    return (home or codex_home()) / "harness" / STATE_NAME


def empty_state() -> dict[str, Any]:
    return {"schema_version": STATE_VERSION, "sessions": {}}


def valid_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("ordinal"), int)
        and not isinstance(value.get("ordinal"), bool)
        and value["ordinal"] >= 0
        and isinstance(value.get("complete"), bool)
        and isinstance(value.get("updated_at"), (int, float))
        and not isinstance(value.get("updated_at"), bool)
    )


def load_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return empty_state()
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != STATE_VERSION
        or not isinstance(value.get("sessions"), dict)
    ):
        return empty_state()
    value["sessions"] = {
        key: entry for key, entry in value["sessions"].items() if isinstance(key, str) and valid_entry(entry)
    }
    return value


def atomic_write(path: Path, state: dict[str, Any]) -> None:
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


def apply_event(state: dict[str, Any], payload: dict[str, Any], now: float) -> bool:
    """Apply one host event to the state. Return True when the state changed."""
    session_id = payload.get("session_id")
    event = payload.get("hook_event_name")
    if not isinstance(session_id, str) or not session_id.strip() or not isinstance(event, str):
        return False
    session_id = session_id.strip()
    sessions = state["sessions"]
    entry = sessions.get(session_id)
    if event == "PostCompact":
        if entry is None:
            entry = {"ordinal": 0, "complete": False}
        entry["ordinal"] += 1
        trigger = payload.get("trigger")
        if isinstance(trigger, str) and trigger:
            entry["last_trigger"] = trigger[:32]
    elif event == "SessionStart":
        source = payload.get("source")
        if entry is None:
            entry = {"ordinal": 0, "complete": source in COMPLETE_SOURCES}
        elif source not in COMPLETE_SOURCES | SEEN_SOURCES:
            return False
    else:
        return False
    entry["updated_at"] = now
    sessions[session_id] = entry
    cutoff = now - RETENTION_SECONDS
    for key in [key for key, value in sessions.items() if value["updated_at"] < cutoff]:
        del sessions[key]
    return True


@contextmanager
def locked(path: Path) -> Iterator[None]:
    """Hold an exclusive lock for a read-modify-write of ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(path.with_name(f"{path.name}.lock"), "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield


def record(payload: dict[str, Any], path: Path, now: float | None = None) -> bool:
    with locked(path):
        state = load_state(path)
        changed = apply_event(state, payload, time.time() if now is None else now)
        if changed:
            atomic_write(path, state)
        return changed


def lookup(session_id: str, path: Path) -> dict[str, Any] | None:
    """Return the session's record, or None when there is none."""
    entry = load_state(path)["sessions"].get(session_id)
    return dict(entry) if entry is not None else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if isinstance(payload, dict):
            record(payload, state_path())
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
