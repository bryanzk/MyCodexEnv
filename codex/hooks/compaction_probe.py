#!/usr/bin/env python3
"""UserPromptSubmit: inject the host-observed compaction ordinal for this session.

The ordinal comes from ``compaction_recorder.py``, which the host runs on
``PostCompact`` and ``SessionStart``. This probe does not read session
transcripts. When the session has no complete record, it injects nothing,
writes no evidence, and counts one miss in
``$CODEX_HOME/harness/compaction_probe_receipt.json``.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from compaction_recorder import atomic_write, lookup, state_path
from context_meter import USAGE_FIELDS_PRESENT, build_context


RECEIPT_VERSION = 1
RECEIPT_NAME = "compaction_probe_receipt.json"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def load_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def session_ordinal(payload: dict[str, Any], home: Path) -> tuple[int | None, str]:
    """Return (ordinal, outcome). The ordinal is None unless the record is complete."""
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        return None, "no_session_id"
    entry = lookup(session_id.strip(), state_path(home))
    if entry is None:
        return None, "no_record"
    if not entry["complete"]:
        return None, "incomplete_record"
    return entry["ordinal"], "hit"


def count_outcome(home: Path, outcome: str) -> None:
    path = home / "harness" / RECEIPT_NAME
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict) or receipt.get("schema_version") != RECEIPT_VERSION:
            raise ValueError
    except (OSError, ValueError):
        receipt = {"schema_version": RECEIPT_VERSION, "outcomes": {}}
    outcomes = receipt.get("outcomes")
    if not isinstance(outcomes, dict):
        outcomes = receipt["outcomes"] = {}
    previous = outcomes.get(outcome)
    outcomes[outcome] = (previous if isinstance(previous, int) and not isinstance(previous, bool) else 0) + 1
    receipt["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    atomic_write(path, receipt)


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


def main() -> int:
    response = continue_response()
    try:
        payload = load_payload()
        home = codex_home()
        ordinal, outcome = session_ordinal(payload, home)
        if ordinal is not None:
            response = inject_response(ordinal, payload, home)
        try:
            count_outcome(home, outcome)
        except Exception:
            pass
    except Exception:
        response = continue_response()
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
