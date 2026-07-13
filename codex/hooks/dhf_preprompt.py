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


SHIPQ_ROOT = Path(
    os.environ.get("DHF_PREPROMPT_SHIPQ_ROOT", str(Path.home() / "Codes" / "CursorDeveloper" / "ShipQ"))
)
SHIPQ_ADAPTER = Path(
    os.environ.get("DHF_PREPROMPT_SHIPQ_ADAPTER", str(Path.home() / ".codex" / "hooks" / "shipq_dhf_preprompt.py"))
)
DHF_SKILL = Path(
    os.environ.get(
        "DHF_PREPROMPT_SKILL",
        str(Path.home() / ".codex" / "skills" / "delivery-harness-framework" / "SKILL.md"),
    )
)
TRUSTED_HOOKS_ROOT = Path.home() / ".codex" / "hooks"
ALLOW_UNTRUSTED_ADAPTER = os.environ.get("DHF_PREPROMPT_ALLOW_UNTRUSTED_TEST_PATHS") == "1"

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
    return first_text(payload, ("cwd", "workdir", "repo_root"))


def under_shipq(cwd: str) -> bool:
    if not cwd:
        return False
    try:
        path = Path(cwd).expanduser().resolve()
        shipq_root = SHIPQ_ROOT.expanduser().resolve()
    except (OSError, ValueError):
        return False
    return path == shipq_root or shipq_root in path.parents


def valid_cwd(cwd: str) -> bool:
    try:
        Path(cwd).expanduser().resolve()
    except (OSError, ValueError):
        return False
    return True


def skip_requested(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SKIP_PATTERNS)


def generic_activation_requested(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in ACTIVATION_PATTERNS)


def load_shipq_adapter() -> ModuleType:
    if not SHIPQ_ADAPTER.is_file():
        raise RuntimeError(f"cannot load ShipQ DHF adapter: {SHIPQ_ADAPTER}")
    if SHIPQ_ADAPTER.is_symlink():
        raise RuntimeError("cannot load ShipQ DHF adapter from a symlink")
    adapter_path = SHIPQ_ADAPTER.resolve()
    trusted_root = TRUSTED_HOOKS_ROOT.expanduser().resolve()
    if not ALLOW_UNTRUSTED_ADAPTER and adapter_path.parent != trusted_root:
        raise RuntimeError("cannot load ShipQ DHF adapter outside the trusted hooks root")
    spec = importlib.util.spec_from_file_location("shipq_dhf_preprompt_adapter", adapter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ShipQ DHF adapter: {SHIPQ_ADAPTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_dhf_context() -> str:
    return DHF_SKILL.read_text(encoding="utf-8")


def continue_only() -> dict[str, Any]:
    return {"continue": True}


def validate_response(response: object) -> dict[str, Any]:
    if not isinstance(response, dict) or response.get("continue") is not True:
        raise TypeError("hook response must be a continue response object")
    unexpected_keys = set(response) - {"continue", "hookSpecificOutput"}
    if unexpected_keys:
        raise TypeError("hook response contains unsupported top-level keys")
    if "hookSpecificOutput" in response and not isinstance(response["hookSpecificOutput"], dict):
        raise TypeError("hookSpecificOutput must be an object")
    json.dumps(response, ensure_ascii=False)
    return response


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


def route_response(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    cwd = cwd_text(payload)
    text = prompt_text(payload)
    if not cwd:
        return continue_only(), "missing-cwd"
    if not valid_cwd(cwd):
        return continue_only(), "invalid-cwd"
    if skip_requested(text):
        return continue_only(), "opt-out"
    if under_shipq(cwd):
        adapter = load_shipq_adapter()
        return adapter.build_response(payload), "shipq-delegated"
    if generic_activation_requested(text):
        return generic_response(), "generic-activated"
    return continue_only(), "continue-only"


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    return route_response(payload)[0]


def main() -> int:
    payload, diagnostic = load_payload()
    if diagnostic:
        response = continue_only()
        route = diagnostic
    else:
        try:
            candidate, route = route_response(payload)
            response = validate_response(candidate)
        except Exception as exc:
            response = continue_only()
            route = f"runtime-error:{type(exc).__name__}"
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stderr.write(f"diagnostic={route}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
