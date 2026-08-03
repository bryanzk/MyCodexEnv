#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def compaction_event_increment(event: Any) -> int:
    """Return one only for a decoded top-level compacted event."""
    return int(isinstance(event, dict) and event.get("type") == "compacted")
