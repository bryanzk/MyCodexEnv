#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


PRODUCTIVE_EVENT_TYPES = {"checkpoint", "handoff", "subagent_report"}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _is_productive(event: dict[str, Any]) -> bool:
    event_type = _text(event.get("event_type"))
    if event_type == "verification_result":
        return _present(event.get("command")) and _present(event.get("exit_code")) and _present(event.get("key_output"))
    if event_type == "browser_smoke":
        return _present(event.get("key_output"))
    if event_type in PRODUCTIVE_EVENT_TYPES:
        return _present(event.get("message")) or _present(event.get("key_output"))
    return False


def _max_repeated_command_count(events: list[dict[str, Any]]) -> int:
    sorted_events = sorted(events, key=lambda event: _text(event.get("timestamp")))
    max_count = 0
    current_command = ""
    current_count = 0

    for event in sorted_events:
        if _is_productive(event):
            current_command = ""
            current_count = 0
            continue

        command = _text(event.get("command"))
        if not command:
            current_command = ""
            current_count = 0
            continue
        if command == current_command:
            current_count += 1
        else:
            current_command = command
            current_count = 1
        max_count = max(max_count, current_count)

    return max_count


def compute_conversion_health(events: list[dict[str, Any]]) -> dict[str, Any]:
    window_event_count = len(events)
    tool_call_count = sum(1 for event in events if _text(event.get("event_type")) == "tool_call")
    productive_events = [event for event in events if _is_productive(event)]
    productive_event_count = len(productive_events)
    repeated_command_count = _max_repeated_command_count(events)
    latest_productive_timestamp = max((_text(event.get("timestamp")) for event in productive_events), default="")
    low_conversion_signals: list[str] = []

    if tool_call_count >= 5 and productive_event_count == 0:
        low_conversion_signals.append("many_tool_calls_without_productive_feedback")
    if repeated_command_count >= 3:
        low_conversion_signals.append("repeated_same_command")

    if window_event_count < 3:
        status = "insufficient_evidence"
        reason = "fewer than three evidence events"
    elif low_conversion_signals and productive_event_count == 0:
        status = "stalled"
        reason = "low-conversion signals without productive feedback"
    elif low_conversion_signals:
        status = "watch"
        reason = "low-conversion signals with productive feedback"
    else:
        status = "healthy"
        reason = "productive feedback present without low-conversion signals"

    return {
        "status": status,
        "reason": reason,
        "window_event_count": window_event_count,
        "tool_call_count": tool_call_count,
        "productive_event_count": productive_event_count,
        "repeated_command_count": repeated_command_count,
        "latest_productive_timestamp": latest_productive_timestamp,
        "low_conversion_signals": low_conversion_signals,
    }


def with_malformed_evidence_signal(health: dict[str, Any], malformed_count: int) -> dict[str, Any]:
    normalized = dict(health)
    signals = list(normalized.get("low_conversion_signals", []))
    if malformed_count <= 0:
        normalized["low_conversion_signals"] = signals
        return normalized

    if "malformed_evidence_present" not in signals:
        signals.append("malformed_evidence_present")
    normalized["low_conversion_signals"] = signals
    if normalized.get("status") in {"healthy", "insufficient_evidence"}:
        normalized["status"] = "watch"
        normalized["reason"] = "malformed evidence present"
    return normalized
