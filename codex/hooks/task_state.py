#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCAN_LINE_LIMIT = 50
MARKER_PATTERN = re.compile(
    r"^\s*(?:任务模式|task-mode)\s*[:：]\s*([A-Za-z-]+)\s*$",
    flags=re.IGNORECASE,
)
DECLARABLE_PHASES = {
    "planning": "planning",
    "plan": "planning",
    "development": "development",
    "implementation": "development",
    "review": "review",
    "validation": "validation",
    "handoff": "handoff",
    "report-only": "review",
}
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    flags=re.IGNORECASE,
)


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def _sessions_root() -> Path:
    return (_codex_home() / "sessions").resolve(strict=False)


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validated_transcript_path(raw_path: Any) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, "NO_TRANSCRIPT"
    try:
        sessions_root = _sessions_root()
        transcript = Path(raw_path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None, "TRANSCRIPT_PATH_OUT_OF_BOUNDS"
    if not _path_within(transcript, sessions_root):
        return None, "TRANSCRIPT_PATH_OUT_OF_BOUNDS"
    return transcript, None


def _read_events(path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= SCAN_LINE_LIMIT:
                    break
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return None, "TRANSCRIPT_INVALID"
                if not isinstance(event, dict):
                    return None, "TRANSCRIPT_INVALID"
                events.append(event)
    except OSError:
        return None, "NO_TRANSCRIPT"
    if not events:
        return None, "TRANSCRIPT_INVALID"
    return events, None


def _session_meta(events: list[dict[str, Any]], session_id: str) -> tuple[dict[str, Any] | None, str | None]:
    first = events[0]
    payload = first.get("payload")
    if first.get("type") != "session_meta" or not isinstance(payload, dict):
        return None, "TRANSCRIPT_INVALID"
    if session_id not in {payload.get("id"), payload.get("session_id")}:
        return None, "TRANSCRIPT_IDENTITY_MISMATCH"
    return payload, None


def _is_user_message(event: dict[str, Any]) -> bool:
    payload = event.get("payload")
    return (
        event.get("type") == "response_item"
        and isinstance(payload, dict)
        and payload.get("type") == "message"
        and payload.get("role") == "user"
    )


def _is_owner_confirmation(event: dict[str, Any]) -> bool:
    payload = event.get("payload")
    return (
        event.get("type") == "event_msg"
        and isinstance(payload, dict)
        and payload.get("type") == "user_message"
    )


def _first_owner_text(events: list[dict[str, Any]]) -> str | None:
    for index in range(1, len(events) - 1):
        event = events[index]
        if not _is_user_message(event) or not _is_owner_confirmation(events[index + 1]):
            continue
        payload = event["payload"]
        content = payload.get("content")
        if not isinstance(content, list):
            return None
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "input_text":
                continue
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                return text
        return None
    return None


_HOST_WRAPPER_OPEN = re.compile(r"^<([A-Za-z_][A-Za-z0-9_-]*)>$")


def _skip_host_wrappers(lines: list[str], start: int) -> int | None:
    index = start
    while True:
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            return None
        match = _HOST_WRAPPER_OPEN.fullmatch(lines[index].strip())
        if match is None:
            return index
        closing = f"</{match.group(1)}>"
        index += 1
        while index < len(lines) and lines[index].strip() != closing:
            index += 1
        if index >= len(lines):
            return None
        index += 1


def _first_instruction_line(text: str) -> str | None:
    lines = text.splitlines()
    first_index = _skip_host_wrappers(lines, 0)
    if first_index is None:
        return None
    first = lines[first_index].strip()
    if first == "# Files mentioned by the user:":
        request_index = next(
            (
                index
                for index in range(first_index + 1, len(lines))
                if lines[index].strip() == "## My request for Codex:"
            ),
            None,
        )
        if request_index is None:
            return None
        return next((line.strip() for line in lines[request_index + 1 :] if line.strip()), None)
    return first


def _declared_phase(events: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[str | None, str]:
    text = _first_owner_text(events)
    if text is None:
        return None, "MARKER_NOT_FOUND"
    first_line = _first_instruction_line(text)
    if first_line is None:
        return None, "MARKER_NOT_FOUND"
    match = MARKER_PATTERN.fullmatch(first_line)
    if match is None:
        return None, "MARKER_NOT_FOUND"
    declared = match.group(1).lower()
    if declared == "ship":
        return None, "PHASE_NOT_DECLARABLE"
    phase = DECLARABLE_PHASES.get(declared)
    if phase is None:
        return None, "MARKER_NOT_FOUND"
    phases = policy.get("phases")
    if not isinstance(phases, dict) or phase not in phases:
        return None, "PHASE_NOT_IN_POLICY"
    return phase, "alias_resolved" if declared == "report-only" else "DECLARED"


def _eligible_root_path(path: Path, session_id: str, sessions_root: Path) -> Path | None:
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError):
        return None
    if not _path_within(resolved, sessions_root):
        return None
    if not resolved.name.endswith(f"-{session_id}.jsonl"):
        return None
    return resolved if resolved.is_file() else None


def _find_root_transcript(session_id: str) -> Path | None:
    if not UUID_PATTERN.fullmatch(session_id):
        return None
    sessions_root = _sessions_root()
    try:
        paths = sessions_root.glob(f"*/*/*/rollout-*-{session_id}.jsonl")
        matches = [candidate for path in paths if (candidate := _eligible_root_path(path, session_id, sessions_root))]
    except OSError:
        return None
    return matches[0] if len(matches) == 1 else None


def _git_root_from_cwd(raw_cwd: Any) -> Path | None:
    if not isinstance(raw_cwd, str) or not raw_cwd.strip():
        return None
    try:
        cwd = Path(raw_cwd).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None
    for candidate in (cwd, *cwd.parents):
        marker = candidate / ".git"
        try:
            if marker.exists() or marker.is_symlink():
                return candidate
        except OSError:
            return None
    return None


def _canonical_cwd(raw_cwd: Any) -> Path | None:
    if not isinstance(raw_cwd, str) or not raw_cwd.strip():
        return None
    try:
        return Path(raw_cwd).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _resolve_transcript(
    transcript: Path,
    session_id: str,
    current_cwd: Any,
    policy: dict[str, Any],
) -> tuple[str | None, str]:
    events, error = _read_events(transcript)
    if events is None:
        return None, error or "TRANSCRIPT_INVALID"
    meta, error = _session_meta(events, session_id)
    if meta is None:
        return None, error or "TRANSCRIPT_INVALID"

    if meta.get("id") == session_id:
        root_events = events
        root_meta = meta
        inherited = False
    else:
        root_path = _find_root_transcript(session_id)
        if root_path is None:
            return None, "ROOT_TRANSCRIPT_NOT_FOUND"
        root_events, error = _read_events(root_path)
        if root_events is None:
            return None, error or "TRANSCRIPT_INVALID"
        root_meta, error = _session_meta(root_events, session_id)
        if root_meta is None or root_meta.get("id") != session_id:
            return None, "TRANSCRIPT_IDENTITY_MISMATCH"
        inherited = True

    if root_meta.get("thread_source") != "user":
        return None, "THREAD_SOURCE_NOT_ELIGIBLE"
    root_repo = _git_root_from_cwd(root_meta.get("cwd"))
    current_repo = _git_root_from_cwd(current_cwd)
    if root_repo is not None or current_repo is not None:
        if root_repo is None or current_repo is None or root_repo != current_repo:
            return None, "ROOT_REPO_MISMATCH"
    else:
        root_cwd = _canonical_cwd(root_meta.get("cwd"))
        active_cwd = _canonical_cwd(current_cwd)
        if root_cwd is None or active_cwd is None or root_cwd != active_cwd:
            return None, "ROOT_WORKSPACE_MISMATCH"
    phase, reason = _declared_phase(root_events, policy)
    if phase is None:
        return None, reason
    return phase, "INHERITED" if inherited else reason


def workspace_key(raw_cwd: Any) -> Path | None:
    return _git_root_from_cwd(raw_cwd) or _canonical_cwd(raw_cwd)


def declaration_path(raw_cwd: Any) -> Path | None:
    key = workspace_key(raw_cwd)
    if key is None:
        return None
    digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
    return _codex_home() / "task-state" / f"{digest}.json"


def resolve_self_declared(raw_cwd: Any, policy: dict[str, Any]) -> tuple[str | None, str]:
    try:
        path = declaration_path(raw_cwd)
        if path is None:
            return None, "NO_WORKSPACE"
        if not path.is_file():
            return None, "NO_DECLARATION"
        record = json.loads(path.read_text(encoding="utf-8"))
        expires_raw = record.get("expires_at") if isinstance(record, dict) else None
        if not isinstance(expires_raw, str):
            return None, "DECLARATION_INVALID"
        expires = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
        if expires.tzinfo is None or datetime.now(timezone.utc) >= expires:
            return None, "DECLARATION_EXPIRED" if expires.tzinfo is not None else "DECLARATION_INVALID"
        phase = record.get("phase")
        phases = policy.get("phases")
        if not isinstance(phase, str) or not isinstance(phases, dict) or phase not in phases:
            return None, "DECLARATION_INVALID"
        return phase, "SELF_DECLARED"
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None, "DECLARATION_INVALID"


def resolve_declared_phase(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[str | None, str]:
    try:
        if not isinstance(payload, dict) or not isinstance(policy, dict):
            return None, "NO_TRANSCRIPT"
        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            return None, "NO_TRANSCRIPT"
        transcript, error = _validated_transcript_path(payload.get("transcript_path"))
        if transcript is None:
            return None, error or "NO_TRANSCRIPT"
        phase, reason = _resolve_transcript(
            transcript,
            session_id,
            payload.get("cwd"),
            policy,
        )
        return phase, reason
    except Exception:
        return None, "TRANSCRIPT_INVALID"
