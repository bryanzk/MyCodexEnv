#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple


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
# Final governed under-routing review gate is green in repo source. Explicit
# rollback values remain fail-closed because only exact value 1 enables profiles.
SIMPLIFIED_PROFILES_ENABLED = os.environ.get("DHF_PREPROMPT_SIMPLIFIED_PROFILES", "1") == "1"

PROFILE_RANK = {"light": 0, "standard": 1, "governed": 2}


class ProfileSelection(NamedTuple):
    profile: str
    escalation_signal: str | None
    escalation_signals: tuple[str, ...] = ()

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
    r"\buse\s+dhf\b",
    r"\buse\s+(?:the\s+)?delivery[-\s]+harness(?:\s+framework)?\b",
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
    r"(?:使用|启用|调用)\s*(?:dhf|交付(?:治理)?框架|交付(?:治理)?流程)",
]

GOVERNED_SIGNAL_PATTERNS = [
    (
        "durable_architecture_source_conflict",
        [r"\barchitecture\b.*\b(?:source|state)[-\s]+conflict\b", r"架构.*(?:来源|状态)冲突"],
    ),
    (
        "unknown_or_overlapping_worktree_ownership",
        [r"\b(?:dirty|worktree|ownership)\b.*\b(?:conflict|overlap|unknown)\b", r"\bstate[-\s]+conflict\b"],
    ),
    (
        "external_capture_or_private_data",
        [
            r"\bexternal\s+capture\b",
            r"\b(?:private|customer|credential|secret)\s+(?:data|capture|content)\b",
            r"\b(?:rotate|update|change|write|revoke|delete)\b.*\b(?:credential|token|api[-\s]+key|secret)\b",
            r"\b(?:credential|token|api[-\s]+key|secret)\b.*\b(?:rotate|update|change|write|revoke|delete|stored\s+value)\b",
            r"\b(?:show|print|log|dump|expose|disclose|share|reveal)\b.*\b(?:credential|token|api[-\s]+key|secret|private\s+data)\b",
            r"\b(?:private|secret|confidential|customer)\s+(?:record|records|information|data|content)\b",
        ],
    ),
    (
        "remote_or_deployment_action",
        [r"\bremote\b", r"\bssh\b", r"\bdeploy(?:ment|ed|ing)?\b", r"\bproduction\b", r"\brelease\b"],
    ),
    (
        "destructive_or_irreversible_action",
        [
            r"\b(?:destructive|irreversible)\b",
            r"\b(?:delete|drop|truncate|purge|erase)\b.*\b(?:data|rows?|records?|table|database)\b",
            r"\b(?:data|database|schema)\s+migration\b.*\b(?:delete|drop|truncate|irreversible)\b",
            r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?|-f)(?:\s|$)",
            r"\bgit\s+reset\b[^\n]*--hard(?:\s|$)",
            r"\brm\s+-[a-z]*r[a-z]*f\b|\brm\s+-[a-z]*f[a-z]*r\b",
            r"\b(?:drop|truncate)\s+(?:table|database|schema)\b",
        ],
    ),
    (
        "multiple_agents_or_overlapping_write_sets",
        [r"\bmulti(?:ple)?[-\s]+agent", r"\bmultiple\s+agents\b", r"\boverlapping\s+write\s+sets?\b"],
    ),
    (
        "resume_or_handoff",
        [r"\bresume(?:d)?\b", r"\bhandoff\b", r"\btake\s*over\b", r"\btakeover\b", r"接手", r"恢复", r"交接"],
    ),
]

STANDARD_PATTERNS = [
    r"\bimplement\b",
    r"\b(?:local|parser)\s+(?:feature|option|change)\b",
    r"\bfailing\s+(?:unit\s+)?test\b",
    r"\binvestigat(?:e|ion)\b",
    r"\bdebug(?:ging)?\b",
    r"\brefactor\b",
    r"\bcli\s+(?:flag|change|option)\b",
    r"\bui\s+(?:behavior|change|empty[-\s]+state)\b",
]

MANDATORY_HELPERS_BY_SIGNAL = {
    "resume_or_handoff": [
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_report.py",
        "harness_checkpoint.py",
    ],
    "unknown_or_overlapping_worktree_ownership": ["harness_recover.py", "harness_checkpoint.py"],
    "external_capture_or_private_data": ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
    "remote_or_deployment_action": ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
    "multiple_agents_or_overlapping_write_sets": ["harness_agent_team.py", "harness_checkpoint.py"],
    "durable_architecture_source_conflict": [
        "harness_recover.py",
        "harness_requirements.py",
        "harness_checkpoint.py",
    ],
    "malformed_profile_state": [
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_report.py",
        "harness_checkpoint.py",
    ],
    "destructive_or_irreversible_action": [
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_report.py",
        "harness_checkpoint.py",
    ],
    "retained_higher_active_profile": [
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_report.py",
        "harness_checkpoint.py",
    ],
}

REQUIRED_OUTPUT_FIELDS_BY_SIGNAL = {
    "resume_or_handoff": ["phase", "ownership", "freshness_state"],
    "unknown_or_overlapping_worktree_ownership": ["ownership"],
    "external_capture_or_private_data": ["data_boundary"],
    "remote_or_deployment_action": ["authorization_state", "rollback"],
    "multiple_agents_or_overlapping_write_sets": ["agent_write_sets"],
    "durable_architecture_source_conflict": ["source_conflict", "decision_state"],
    "malformed_profile_state": ["profile_state", "freshness_state"],
    "destructive_or_irreversible_action": ["authorization_state", "rollback"],
    "retained_higher_active_profile": ["active_profile", "escalation_signal"],
}

AUTHORITATIVE_GATES_BY_SIGNAL = {
    "resume_or_handoff": ["Startup Sequence", "State Snapshot Gate", "Checkpoint Gate"],
    "unknown_or_overlapping_worktree_ownership": ["Dirty Worktree Gate", "Checkpoint Gate"],
    "external_capture_or_private_data": [
        "External Capture Promotion Gate",
        "Evidence And Report Gate",
        "Checkpoint Gate",
    ],
    "remote_or_deployment_action": [
        "Execution Lane Gate",
        "Deployment Readiness Gate",
        "Checkpoint Gate",
    ],
    "multiple_agents_or_overlapping_write_sets": ["Agent Team Gate", "Checkpoint Gate"],
    "durable_architecture_source_conflict": [
        "Source Of Truth Order",
        "Architecture Alignment Checkpoint Gate",
        "Checkpoint Gate",
    ],
    "malformed_profile_state": ["Startup Sequence", "State Snapshot Gate", "Checkpoint Gate"],
    "destructive_or_irreversible_action": [
        "Execution Lane Gate",
        "Deployment Readiness Gate",
        "Checkpoint Gate",
    ],
    "retained_higher_active_profile": ["Startup Sequence", "Evidence And Report Gate", "Checkpoint Gate"],
}


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


def select_governance_profile(text: str, active_profile: str | None = None) -> ProfileSelection:
    signals = tuple(
        candidate_signal
        for candidate_signal, patterns in GOVERNED_SIGNAL_PATTERNS
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)
    )
    selected = "governed" if signals else "light"
    if not signals and any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in STANDARD_PATTERNS):
        selected = "standard"

    if active_profile in PROFILE_RANK and PROFILE_RANK[active_profile] > PROFILE_RANK[selected]:
        selected = active_profile
        if active_profile == "governed":
            signals = (*signals, "retained_higher_active_profile")
    return ProfileSelection(selected, signals[0] if signals else None, signals)


def profile_state_from_payload(payload: dict[str, Any]) -> tuple[str | None, bool]:
    if "dhf_profile_state" not in payload:
        return None, False
    state = payload["dhf_profile_state"]
    if not isinstance(state, dict):
        return None, True
    active = state.get("active_profile")
    if active not in PROFILE_RANK:
        return None, True
    return active, False


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


def profile_context(selection: ProfileSelection) -> str:
    signals = selection.escalation_signals or (
        (selection.escalation_signal,)
        if selection.escalation_signal
        else (("retained_higher_active_profile",) if selection.profile == "governed" else ())
    )
    mandatory_helpers = list(
        dict.fromkeys(helper for signal in signals for helper in MANDATORY_HELPERS_BY_SIGNAL.get(signal, []))
    )
    required_output_fields = list(
        dict.fromkeys(field for signal in signals for field in REQUIRED_OUTPUT_FIELDS_BY_SIGNAL.get(signal, []))
    )
    authoritative_gates = list(
        dict.fromkeys(gate for signal in signals for gate in AUTHORITATIVE_GATES_BY_SIGNAL.get(signal, []))
    )
    contract = json.dumps(
        {
            "escalation_signals": list(signals),
            "mandatory_helpers": mandatory_helpers,
            "required_output_fields": required_output_fields,
            "authoritative_gates": authoritative_gates,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )
    common = (
        "Activated generic DHF governance profile. "
        f"profile={selection.profile}. Preserve result, scope_and_constraints, verification_receipt, "
        "and remaining_risk_or_next_action. Classify completion as implemented_or_fixed, "
        "documented_or_configured, diagnosed_or_blocked, or verification_not_applicable; "
        "artifact claims need fresh command/exit_code/key_output/timestamp evidence, while pure "
        f"explanation uses verification_not_applicable without an invented command.\nDHF_PROFILE_CONTRACT={contract}\n"
    )
    if selection.profile == "light":
        return common + " Execute directly and use only the narrowest useful verification; no lifecycle helpers are required."
    if selection.profile == "standard":
        return common + " Define done, preserve dirty-worktree ownership, use a runnable focused feedback loop, and verify fresh."
    return (
        common
        + f" escalation_signal={signals[0]}; escalation_signals={','.join(signals)}. "
        "Retain the union of relevant recovery, ownership, permission, evidence, "
        "checkpoint, deployment-readiness, and agent-team gates before risky action."
    )


def simplified_generic_response(selection: ProfileSelection) -> dict[str, Any]:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": profile_context(selection),
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
    active_profile, malformed_state = profile_state_from_payload(payload)
    if generic_activation_requested(text) or active_profile is not None or malformed_state:
        if not SIMPLIFIED_PROFILES_ENABLED:
            return generic_response(), "generic-activated:legacy"
        selection = (
            ProfileSelection("governed", "malformed_profile_state")
            if malformed_state
            else select_governance_profile(text, active_profile)
        )
        return simplified_generic_response(selection), f"generic-activated:{selection.profile}"
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
