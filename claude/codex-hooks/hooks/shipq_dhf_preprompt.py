#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SHIPQ_ROOT = Path(
    os.environ.get("DHF_PREPROMPT_SHIPQ_ROOT", str(Path.home() / "Codes" / "CursorDeveloper" / "ShipQ"))
)

SKIP_PATTERNS = [
    r"\bno\s+dhf\b",
    r"\bskip\s+dhf\b",
    r"\bwithout\s+dhf\b",
    r"\bno\s+delivery[-\s]+harness\b",
    r"\bskip\s+delivery[-\s]+harness\b",
    r"\b(?:do\s+not|don't)\s+use\s+(?:dhf|delivery[-\s]+harness)\b",
    r"\bdisable\s+(?:dhf|delivery[-\s]+harness)\b",
    r"不用\s*(dhf|delivery[-\s]*harness)",
    r"不要\s*(dhf|delivery[-\s]*harness)",
    r"跳过\s*(dhf|delivery[-\s]*harness)",
    r"不调用\s*(dhf|delivery[-\s]*harness)",
]


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def payload_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [payload]
    sources.extend(
        value
        for key in ("tool_input", "input", "arguments", "params")
        if isinstance((value := payload.get(key)), dict)
    )
    return sources


def first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for source in payload_sources(payload):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def prompt_text(payload: dict[str, Any]) -> str:
    values = []
    for source in payload_sources(payload):
        for key in ("prompt", "user_prompt", "message", "task", "input_text"):
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
    return "\n".join(values)


def cwd_text(payload: dict[str, Any]) -> str:
    return first_text(payload, ("cwd", "workdir", "repo_root")) or os.getcwd()


def under_shipq(cwd: str) -> bool:
    try:
        path = Path(cwd).expanduser().resolve()
        shipq_root = SHIPQ_ROOT.expanduser().resolve()
    except (OSError, ValueError):
        return False
    return path == shipq_root or shipq_root in path.parents


def skip_requested(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SKIP_PATTERNS)


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    text = prompt_text(payload)
    if not under_shipq(cwd_text(payload)) or skip_requested(text):
        return {"continue": True}

    context = (
        "ShipQ: use AGENTS.md already in context; reread only if missing or changed. "
        "Choose context by the requested action, not keywords. Ordinary questions, "
        "wording edits and read-only instruction audits need only their targets and "
        "direct references, not full DHF or fixed State Log reads. "
        "For all other work, follow AGENTS.md Read First: when it requires "
        "lifecycle routing (including quote changes, browser QA and code review), "
        "load shipq-lifecycle-harness and the applicable delivery-harness-framework "
        "gates, state and policy before acting. "
        "Preserve AGENTS.md Authorization Levels, ownership, recovery and "
        "verification requirements. This routing grants no authority. "
        "Use AGENTS.md Test Commands as the sole verification entry point."
    )
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
    }


def main() -> int:
    json.dump(build_response(load_payload()), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
