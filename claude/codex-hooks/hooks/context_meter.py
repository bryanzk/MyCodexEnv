#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


# 描述 hook payload，不描述 rollout；rollout 侧见 scripts/harness_cost_report.py。
USAGE_FIELDS_PRESENT = False
STATE_VERSION = 1


def observed_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def payload_mappings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mappings = [payload]
    for key in ("payload", "data", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            mappings.append(value)
    return mappings


def usage_mappings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for source in payload_mappings(payload):
        for key in ("usage", "token_usage"):
            value = source.get(key)
            if isinstance(value, dict):
                mappings.append(value)
    return mappings


def first_observed(mappings: list[dict[str, Any]], keys: tuple[str, ...]) -> int | None:
    for mapping in mappings:
        for key in keys:
            observed = observed_int(mapping.get(key))
            if observed is not None:
                return observed
    return None


def atomic_write_meter(path: Path, meter: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(meter, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def ordinal_only_context(ordinal: int) -> dict[str, Any]:
    return {
        "signal": "ordinal-only",
        "compaction_ordinal": ordinal,
        "token_usage": "unknown",
        "remaining_capacity": "unknown",
        "additional_context": (
            f"compaction_ordinal={ordinal} (host-observed); context_pressure_signal=ordinal-only"
        ),
    }


def build_context(
    payload: dict[str, Any],
    *,
    ordinal: int,
    codex_home: Path,
    usage_fields_present: bool = USAGE_FIELDS_PRESENT,
) -> dict[str, Any]:
    if not usage_fields_present:
        return ordinal_only_context(ordinal)

    mappings = usage_mappings(payload)
    token_usage = {
        "input_tokens": first_observed(mappings, ("input_tokens", "prompt_tokens")),
        "output_tokens": first_observed(mappings, ("output_tokens", "completion_tokens")),
        "total_tokens": first_observed(mappings, ("total_tokens", "tokens_used")),
    }
    observed_usage = {key: value for key, value in token_usage.items() if value is not None}
    if not observed_usage:
        return ordinal_only_context(ordinal)

    context_window = first_observed(
        [*mappings, *payload_mappings(payload)],
        ("context_window", "context_window_tokens", "max_context_tokens"),
    )
    total_tokens = token_usage["total_tokens"]
    remaining_capacity: int | str = "unknown"
    if context_window is not None and total_tokens is not None:
        remaining_capacity = max(0, context_window - total_tokens)

    meter = {
        "schema_version": STATE_VERSION,
        "observed_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "token_usage": observed_usage,
        "context_window": context_window if context_window is not None else "unknown",
        "remaining_capacity": remaining_capacity,
    }
    atomic_write_meter(codex_home / "harness" / "meter.json", meter)
    return {
        "signal": "usage-observed",
        "compaction_ordinal": ordinal,
        "token_usage": observed_usage,
        "remaining_capacity": remaining_capacity,
        "additional_context": (
            f"compaction_ordinal={ordinal} (host-observed); context_pressure_signal=usage-observed; "
            f"token_usage={json.dumps(observed_usage, sort_keys=True, separators=(',', ':'))}; "
            f"remaining_capacity={remaining_capacity}"
        ),
    }
