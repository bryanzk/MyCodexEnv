#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

try:
    import task_state
except Exception:  # A guard import failure must degrade to restrictive legacy sources.
    task_state = None


def load_payload() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def load_policy() -> dict[str, Any]:
    path = codex_home() / "runtime" / "tool-policy.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


OUT_OF_SCOPE_PHASE_POLICY: dict[str, Any] = {
    "allow_repo_write": True,
    "allow_network": True,
    "allow_remote": False,
}

# Best-effort textual detection of protected targets inside shell commands
# (redirects, arguments). This is not a sandbox; the hard boundary remains
# file ownership/permissions on the protected roots themselves.
DEFAULT_PROTECTED_COMMAND_PATTERNS = [
    r"(~|\$HOME|/Users/[^/\s\"']+|/home/[^/\s\"']+)/\.codex(/|\b)",
]


def load_scope() -> dict[str, Any]:
    path = codex_home() / "runtime" / "harness-scope.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _canonical_path(raw: Any, base: Path | None = None) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        path = Path(raw).expanduser()
        if not path.is_absolute() and base is not None:
            path = base / path
        return path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _scope_roots(scope: dict[str, Any], key: str) -> list[Path]:
    value = scope.get(key)
    if not isinstance(value, list):
        return []
    roots: list[Path] = []
    for item in value:
        if isinstance(item, str):
            path = _canonical_path(item)
            if path is not None:
                roots.append(path)
    return roots


def _within_any(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def _protected_hit(payload: dict[str, Any], scope: dict[str, Any], cwd: Path | None) -> bool:
    """Best-effort detection of a protected-root target: cwd, structured
    candidate paths, or a textual mention in the command."""
    protected = _scope_roots(scope, "protected_roots")
    targets: list[Path] = [cwd] if cwd is not None else []
    for raw in candidate_paths(payload):
        path = _canonical_path(raw, cwd)
        if path is not None:
            targets.append(path)
    if protected and any(_within_any(target, protected) for target in targets):
        return True
    configured = scope.get("protected_command_patterns")
    if isinstance(configured, list):
        patterns = [p for p in configured if isinstance(p, str)]
    else:
        patterns = list(DEFAULT_PROTECTED_COMMAND_PATTERNS)
    # Always derive patterns from protected_roots too, in both raw (~/...)
    # and canonical (/home/user/...) spellings, so the textual check cannot
    # silently miss a configured protected root.
    for root in protected:
        patterns.append(re.escape(str(root)))
    raw_protected = scope.get("protected_roots")
    if isinstance(raw_protected, list):
        for item in raw_protected:
            if isinstance(item, str) and item.strip():
                patterns.append(re.escape(item.strip()))
    text = "\n".join([command_text(payload), *candidate_paths(payload)])
    return match_any(patterns, text) is not None


def out_of_scope(payload: dict[str, Any], scope: dict[str, Any]) -> bool:
    """True only when the call is confidently outside governed territory.

    Every uncertain or invalid input degrades to False (= governed,
    fail-closed, behavior identical to the pre-scope guard).
    """
    governed = _scope_roots(scope, "governed_roots")
    if not governed:
        return False
    if scope.get("out_of_scope_mode") not in {"allow", "report"}:
        return False
    cwd = _canonical_path(str(payload.get("cwd") or os.getcwd()))
    if cwd is None:
        return False
    if _within_any(cwd, governed):
        return False
    if _protected_hit(payload, scope, cwd):
        return False
    return True


TASK_ADMIN_METACHARS = re.compile(r"[;&|<>`$\r\n]")
TASK_ADMIN_PHASE = re.compile(r"^[A-Za-z-]+$")
TASK_ADMIN_TTL = re.compile(r"^\d+[hm]$")
TASK_ADMIN_SESSION = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def is_task_admin_command(cmd: str) -> bool:
    """Strict allowlist for `codex-task declare ...`.

    A prefix regex would wave through `codex-task declare x --reason y && rm
    -rf ~`, so this parses the whole command: no shell metacharacters, exact
    binary identity (bare name or the canonical $CODEX_HOME/bin path), the
    `declare` subcommand, and only the known argument shapes. Any deviation
    returns False and the command falls back to normal classification.
    """
    if not cmd or TASK_ADMIN_METACHARS.search(cmd):
        return False
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return False
    if len(tokens) < 5:  # binary, declare, phase, --reason, value
        return False
    head = tokens[0]
    if head != "codex-task":
        head_path = _canonical_path(head)
        expected = (codex_home() / "bin" / "codex-task").resolve(strict=False)
        if head_path != expected:
            return False
    if tokens[1] != "declare":
        return False
    if TASK_ADMIN_PHASE.fullmatch(tokens[2]) is None:
        return False
    index = 3
    seen_reason = False
    while index < len(tokens):
        flag = tokens[index]
        if flag == "--reason" and index + 1 < len(tokens) and tokens[index + 1].strip():
            seen_reason = True
            index += 2
            continue
        if flag == "--ttl" and index + 1 < len(tokens) and TASK_ADMIN_TTL.fullmatch(tokens[index + 1]):
            index += 2
            continue
        if flag == "--session-id" and index + 1 < len(tokens) and TASK_ADMIN_SESSION.fullmatch(tokens[index + 1]):
            index += 2
            continue
        return False
    return seen_reason


def tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


def command_text(payload: dict[str, Any]) -> str:
    data = tool_input(payload)
    for key in ("command", "cmd"):
        if key in data:
            return str(data[key])
    for key in ("command", "cmd"):
        if key in payload:
            return str(payload[key])
    return ""


def candidate_paths(payload: dict[str, Any]) -> list[str]:
    data = tool_input(payload)
    paths: list[str] = []
    for key in ("path", "file", "file_path", "filename", "cwd", "workdir"):
        value = data.get(key) or payload.get(key)
        if isinstance(value, str):
            paths.append(value)
    return paths


def phase_from_state_snapshot(root: Path | None) -> str | None:
    if root is None:
        return None
    candidates = [
        root / "docs" / "harness-state.md",
        root / "docs" / "designs" / "harness-state.md",
    ]
    present = [path for path in candidates if path.exists() or path.is_symlink()]
    if len(present) != 1:
        return None
    state = present[0]
    if state.is_symlink():
        return None
    try:
        text = state.read_text(encoding="utf-8")
    except OSError:
        return None

    in_snapshot = False
    snapshot_count = 0
    phases: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"##\s+current snapshot", stripped, flags=re.IGNORECASE):
            snapshot_count += 1
            in_snapshot = True
            continue
        if in_snapshot and re.match(r"##(?:\s|$)", stripped):
            in_snapshot = False
            continue
        if not in_snapshot:
            continue
        match = re.fullmatch(r"\s*-\s*phase\s*:\s*([A-Za-z_]+)\s*", line, flags=re.IGNORECASE)
        if match:
            phases.append(match.group(1))
    if snapshot_count != 1 or len(phases) != 1:
        return None
    return phases[0]


def phase_with_trace(
    payload: dict[str, Any],
    policy: dict[str, Any],
    root: Path | None,
) -> tuple[str, str, dict[str, Any]]:
    """Resolve the phase and record every gate's verdict (S5 gate trace).

    Gates in priority order: env/payload injection > transcript marker >
    self-declared (codex-task declare) > repo state snapshot > unknown."""
    trace: dict[str, Any] = {}
    env_value = payload.get("phase") or os.environ.get("CODEX_HARNESS_PHASE")
    trace["env"] = "present" if env_value else "absent"
    marker_reason = "NOT_EVALUATED"
    value = env_value
    source = "env" if env_value else "none"
    if not value:
        if task_state is None:
            marker_phase, marker_reason = None, "TASK_STATE_UNAVAILABLE"
        else:
            try:
                marker_phase, marker_reason = task_state.resolve_declared_phase(payload, policy)
            except Exception:
                marker_phase, marker_reason = None, "TRANSCRIPT_INVALID"
        trace["transcript"] = marker_reason
        self_phase = None
        self_reason = "NOT_EVALUATED"
        if not marker_phase and task_state is not None:
            try:
                self_phase, self_reason = task_state.resolve_self_declared(
                    payload.get("cwd") or os.getcwd(), policy
                )
            except Exception:
                self_phase, self_reason = None, "DECLARATION_INVALID"
            if self_phase:
                marker_reason = "SELF_DECLARED"
        trace["self_declared"] = "SELF_DECLARED" if self_phase else self_reason
        snapshot_phase = None
        if not marker_phase and not self_phase:
            snapshot_phase = phase_from_state_snapshot(root)
        trace["snapshot"] = snapshot_phase
        value = marker_phase or self_phase or snapshot_phase or "unknown"
        if marker_phase:
            source = "transcript"
        elif self_phase:
            source = "self_declared"
        elif snapshot_phase:
            source = "snapshot"
        else:
            source = "none"
    phase = str(value)
    resolved = phase if phase in policy.get("phases", {}) else "unknown"
    trace["source"] = source
    trace["resolved"] = resolved
    return resolved, marker_reason, trace


def _phase_resolution(
    payload: dict[str, Any],
    policy: dict[str, Any],
    root: Path | None,
) -> tuple[str, str]:
    phase, marker_reason, _ = phase_with_trace(payload, policy, root)
    return phase, marker_reason


def current_phase(payload: dict[str, Any], policy: dict[str, Any], root: Path | None) -> str:
    phase, _ = _phase_resolution(payload, policy, root)
    return phase


def unknown_phase_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("unknown_phase_behavior") == "default_phase":
        default_phase = str(policy.get("default_phase") or "")
        default_policy = policy.get("phases", {}).get(default_phase)
        if isinstance(default_policy, dict):
            return default_policy
    return {
        "allow_repo_write": False,
        "allow_network": False,
        "allow_remote": False,
    }


def match_any(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return pattern
    return None


def configured_evidence_dir(policy: dict[str, Any]) -> Path:
    override = os.environ.get("CODEX_HARNESS_EVIDENCE_DIR")
    if override:
        return Path(override).expanduser()
    raw = str(policy.get("evidence_dir") or "")
    if raw == "~/.codex":
        return codex_home()
    if raw.startswith("~/.codex/"):
        return codex_home() / raw.removeprefix("~/.codex/")
    if raw:
        return Path(raw).expanduser()
    return codex_home() / "harness" / "evidence"


def payload_value(payload: dict[str, Any], key: str) -> Any:
    data = tool_input(payload)
    if key in data:
        return data[key]
    return payload.get(key)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def receipt_is_fresh(event: dict[str, Any], now: datetime) -> bool:
    timestamp = parse_timestamp(event.get("timestamp"))
    if timestamp is None:
        return False
    age = now - timestamp.astimezone(timezone.utc)
    return timedelta(0) <= age <= timedelta(minutes=10)


def has_fresh_validation_receipt(payload: dict[str, Any], policy: dict[str, Any], root: Path | None) -> bool:
    plan_hash = payload_value(payload, "plan_sha256")
    if not isinstance(plan_hash, str) or not plan_hash.strip() or root is None:
        return False
    expected_root = root.resolve(strict=False)
    expected_worker_count = int_or_none(payload_value(payload, "worker_count"))
    evidence_dir = configured_evidence_dir(policy)
    if not evidence_dir.exists() or not evidence_dir.is_dir():
        return False

    now = datetime.now(timezone.utc)
    try:
        paths = sorted(evidence_dir.glob("*.jsonl"))
    except OSError:
        return False

    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event_type") != "agent_team_validated" or event.get("evidence_kind") != "decision":
                continue
            metadata = event.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if metadata.get("plan_sha256") != plan_hash.strip():
                continue
            receipt_root = metadata.get("repo_root")
            if not isinstance(receipt_root, str):
                continue
            if Path(receipt_root).expanduser().resolve(strict=False) != expected_root:
                continue
            if expected_worker_count is not None and int_or_none(metadata.get("worker_count")) != expected_worker_count:
                continue
            if receipt_is_fresh(event, now):
                return True
    return False


def classify(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str | None]:
    cmd = command_text(payload)
    name = tool_name(payload).lower()
    path_text = "\n".join(candidate_paths(payload))
    if match_any(policy.get("secret_path_patterns", []), path_text):
        return "secret", "secret path"
    if match_any(policy.get("secret_command_patterns", []), cmd):
        return "secret", "credential-shaped literal in command"
    if match_any(policy.get("destructive_command_patterns", []), cmd):
        return "destructive", "destructive command pattern"
    if match_any(policy.get("dynamic_exec_patterns", []), cmd):
        return "dynamic_exec", "dynamic download or execution pattern"
    if match_any(policy.get("remote_command_patterns", []), cmd):
        return "remote", "remote or infrastructure command"
    if match_any(policy.get("network_command_patterns", []), cmd):
        return "network", "network command pattern"
    agent_dispatch_names = {str(item).lower() for item in policy.get("agent_dispatch_tool_names", [])}
    if name in agent_dispatch_names or match_any(policy.get("agent_dispatch_command_patterns", []), cmd):
        return "agent_dispatch", "multi-agent dispatch"
    if name in {"apply_patch", "write", "edit", "multi_edit"} or match_any(policy.get("repo_write_command_patterns", []), cmd):
        return "repo_write", "repo write pattern"
    return "read", None


def category_risk_tier(policy: dict[str, Any], category: str) -> str:
    category_policy = policy.get("categories", {}).get(category, {})
    tier = category_policy.get("risk_tier") if isinstance(category_policy, dict) else None
    return tier if tier in {"low", "medium", "high"} else "high"


def git_root(cwd: str) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd or os.getcwd(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def block(reason: str, risk_tier: str) -> dict[str, Any]:
    # Codex-supported PreToolUse legacy block shape. Isolated probe on
    # 2026-07-28 (codex-cli 0.144.1) proved: this shape and the
    # hookSpecificOutput deny shape intercept; the previous top-level
    # {"permissionDecision": ...} shape and every "ask" variant are parsed
    # as invalid/unsupported, the hook run is marked failed, and the tool
    # call continues (fail-open). Former ask categories are therefore
    # upgraded to block until the host supports a real ask.
    return {"decision": "block", "reason": f"{reason} [risk_tier={risk_tier}]"}


def decision(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy:
        return {}
    if is_task_admin_command(command_text(payload)):
        # `codex-task declare` only writes $CODEX_HOME/task-state and must be
        # runnable from any phase, otherwise the agent cannot self-remediate.
        return {}
    cwd = payload.get("cwd") or os.getcwd()
    root = git_root(str(cwd))
    scope = load_scope()
    scoped_out = out_of_scope(payload, scope)
    if scoped_out:
        # Out-of-scope workspace: phase declaration is waived, but classify()
        # still runs — secret/destructive/dynamic_exec/remote keep blocking.
        phase, marker_reason = "out_of_scope", "OUT_OF_SCOPE"
        phase_policy: dict[str, Any] | None = dict(OUT_OF_SCOPE_PHASE_POLICY)
    else:
        phase, marker_reason = _phase_resolution(payload, policy, root)
        phase_policy = policy.get("phases", {}).get(phase)
    if phase_policy is None:
        phase_policy = unknown_phase_policy(policy)

    category, reason = classify(payload, policy)
    risk_tier = category_risk_tier(policy, category)
    if marker_reason == "SELF_DECLARED" and category != "read":
        # Protected roots outrank self declarations: an agent-declared phase
        # must never unlock writes to the guard's own configuration.
        if _protected_hit(payload, scope, _canonical_path(str(cwd))):
            return block(
                "[harness] protected roots stay locked under a self-declared phase.",
                "high",
            )
    if category == "agent_dispatch":
        if phase_policy.get("allow_subagents") is False:
            return block(f"[harness] subagent dispatch is disabled during phase '{phase}'.", risk_tier)
        if has_fresh_validation_receipt(payload, policy, root):
            return {}
        return block(
            "[harness] validate the worker plan with scripts/harness_agent_team.py validate --emit-evidence before dispatch.",
            risk_tier,
        )
    if category == "read":
        return {}

    if category == "repo_write" and phase_policy.get("allow_repo_write") is True:
        return {}
    if category == "network" and phase_policy.get("allow_network") is True:
        return {}
    if category == "remote" and phase_policy.get("allow_remote") is True:
        return {}

    guidance = ""
    if not scoped_out and risk_tier in {"low", "medium"}:
        guidance = (
            " To proceed: run ~/.codex/bin/codex-task declare implementation"
            ' --reason "why" and retry.'
        )
    return block(
        f"[harness] {category} is restricted during phase '{phase}': {reason or category}. "
        f"[marker_reason={marker_reason}]{guidance}",
        risk_tier,
    )


def main() -> int:
    payload = load_payload()
    result = decision(payload, load_policy())
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
