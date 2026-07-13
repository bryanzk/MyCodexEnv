#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


SHIPQ_ROOT = Path(os.environ.get("DHF_PREPROMPT_SHIPQ_ROOT", "/Users/kezheng/Codes/CursorDeveloper/ShipQ"))
SHIPQ_ADAPTER = Path(
    os.environ.get("DHF_PREPROMPT_SHIPQ_ADAPTER", "/Users/kezheng/.codex/hooks/shipq_dhf_preprompt.py")
)
DHF_SKILL = Path(os.environ.get("DHF_PREPROMPT_SKILL", "/Users/kezheng/.codex/skills/delivery-harness-framework/SKILL.md"))

SKIP_PATTERNS = [
    r"\bno\s+dhf\b",
    r"\bskip\s+dhf\b",
    r"\bwithout\s+dhf\b",
    r"\bno\s+delivery[-\s]+harness\b",
    r"\bskip\s+delivery[-\s]+harness\b",
    r"不用\s*(dhf|delivery[-\s]*harness)",
    r"不要\s*(dhf|delivery[-\s]*harness)",
    r"跳过\s*(dhf|delivery[-\s]*harness)",
    r"不调用\s*(dhf|delivery[-\s]*harness)",
]

ACTIVATION_PATTERNS = [
    r"\bcomplex\b",
    r"\bresume\b",
    r"\btake\s*over\b",
    r"\btakeover\b",
    r"\bhandoff\b",
    r"\bstate[-\s]+conflict\b",
    r"接手",
    r"恢复",
    r"交接",
    r"状态冲突",
]


def load_payload() -> tuple[dict[str, Any], str]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        return {}, f"malformed-json:{exc.__class__.__name__}"
    if not isinstance(payload, dict):
        return {}, "non-dict-payload"
    return payload, ""


def nested_dict(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    data = nested_dict(payload)
    for source in (payload, data):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def prompt_text(payload: dict[str, Any]) -> str:
    return first_text(payload, ("prompt", "user_prompt", "message", "task", "input_text"))


def cwd_text(payload: dict[str, Any]) -> str:
    return first_text(payload, ("cwd", "workdir", "repo_root"))


def under_shipq(cwd: str) -> bool:
    if not cwd:
        return False
    try:
        path = Path(cwd).expanduser().resolve()
        shipq_root = SHIPQ_ROOT.expanduser().resolve()
    except OSError:
        return False
    return path == shipq_root or shipq_root in path.parents


def skip_requested(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SKIP_PATTERNS)


def generic_activation_requested(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in ACTIVATION_PATTERNS)


def load_shipq_adapter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("shipq_dhf_preprompt_adapter", SHIPQ_ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ShipQ DHF adapter: {SHIPQ_ADAPTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_dhf_context() -> str:
    return DHF_SKILL.read_text(encoding="utf-8")


def continue_only() -> dict[str, Any]:
    return {"continue": True}


def generic_response() -> dict[str, Any]:
    context = (
        "Generic DHF pre-prompt dispatcher: delivery-harness-framework has "
        "been activated for this non-project-specific prompt. Treat the "
        "following generic lifecycle router as active context before complex "
        "or resumed work.\n\n"
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


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    cwd = cwd_text(payload)
    text = prompt_text(payload)
    if not cwd:
        return continue_only()
    if skip_requested(text):
        return continue_only()
    if under_shipq(cwd):
        adapter = load_shipq_adapter()
        return adapter.build_response(payload)
    if generic_activation_requested(text):
        return generic_response()
    return continue_only()


def main() -> int:
    payload, diagnostic = load_payload()
    if diagnostic:
        response = continue_only()
        route = diagnostic
    else:
        response = build_response(payload)
        route = "continue-only"
        if "hookSpecificOutput" in response:
            route = "generic-activated" if not under_shipq(cwd_text(payload)) else "shipq-delegated"
        elif not cwd_text(payload):
            route = "missing-cwd"
        elif skip_requested(prompt_text(payload)):
            route = "opt-out"
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stderr.write(f"diagnostic={route}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
