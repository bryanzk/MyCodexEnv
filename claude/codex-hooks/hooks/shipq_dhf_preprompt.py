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
DHF_SKILL = os.environ.get(
    "DHF_PREPROMPT_SKILL",
    str(Path.home() / ".codex" / "skills" / "delivery-harness-framework" / "SKILL.md"),
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


def load_dhf_context() -> str:
    return Path(DHF_SKILL).read_text(encoding="utf-8")


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    text = prompt_text(payload)
    if not under_shipq(cwd_text(payload)) or skip_requested(text):
        return {"continue": True}

    context = (
        "ShipQ pre-prompt hook: DHF has been automatically invoked for this "
        "ShipQ prompt. Treat the following loaded skill output as active "
        "routing context before non-trivial work. The user can opt out only "
        "with `no dhf`, `skip dhf`, `不用 dhf`, or an equivalent opt-out in "
        "the current prompt.\n\n"
        "=== BEGIN AUTO-INVOKED delivery-harness-framework ===\n"
        f"{load_dhf_context()}\n"
        "=== END AUTO-INVOKED delivery-harness-framework ==="
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
