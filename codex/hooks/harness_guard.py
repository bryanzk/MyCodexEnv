#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import os
import re
import shlex
import stat
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
DEFAULT_PROTECTED_COMMAND_PATTERNS = [
    r"(~|\$HOME|/Users/[^/\s\"']+|/home/[^/\s\"']+)/\.codex(/|\b)",
]
DEFAULT_PERSISTENCE_PATH_PATTERNS = [
    r"/Library/LaunchAgents(?:/|$)",
    r"/(?:\.zshrc|\.zshenv|\.zprofile|\.bashrc|\.profile)$",
    r"\bcrontab\b.*(?:-|<|\bwrite\b)",
]
PATCH_TARGET = re.compile(r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+?)\s*$")
_DIGEST_CACHE: dict[tuple[str, int, int, int], str] = {}
RECOVERY_COMMANDS = (
    './scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" '
    '--claude-home "$HOME/.claude"; ./scripts/sync_codex_home.sh'
)


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
    return [path for item in value if (path := _canonical_path(item)) is not None]


def _within_any(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            pass
    return False


def structured_targets(payload: dict[str, Any]) -> list[str]:
    name = tool_name(payload).lower()
    data = tool_input(payload)
    if name == "apply_patch":
        patch = data.get("patch")
        if not isinstance(patch, str):
            return []
        return [match.group(1) for line in patch.splitlines() if (match := PATCH_TARGET.fullmatch(line))]
    if name not in {"write", "edit", "multi_edit"}:
        return []
    targets: list[str] = []
    for key in ("file_path", "path", "file", "filename"):
        value = data.get(key)
        if isinstance(value, str):
            targets.append(value)
    if name == "multi_edit" and isinstance(data.get("edits"), list):
        for edit in data["edits"]:
            if not isinstance(edit, dict):
                continue
            for key in ("file_path", "path", "file", "filename"):
                value = edit.get(key)
                if isinstance(value, str):
                    targets.append(value)
    return targets


def _pattern_list(scope: dict[str, Any], key: str, defaults: list[str]) -> list[str]:
    configured = scope.get(key)
    return [item for item in configured if isinstance(item, str)] if isinstance(configured, list) else list(defaults)


def _screening_hit(
    payload: dict[str, Any], scope: dict[str, Any], cwd: Path | None, *, roots_key: str | None, patterns_key: str,
    defaults: list[str],
) -> bool:
    targets = [_canonical_path(raw, cwd) for raw in structured_targets(payload)]
    if roots_key and any(
        target is not None and _within_any(target, _scope_roots(scope, roots_key)) for target in targets
    ):
        return True
    patterns = _pattern_list(scope, patterns_key, defaults)
    if roots_key:
        patterns.extend(re.escape(str(root)) for root in _scope_roots(scope, roots_key))
        raw_roots = scope.get(roots_key)
        if isinstance(raw_roots, list):
            patterns.extend(re.escape(item.strip()) for item in raw_roots if isinstance(item, str) and item.strip())
    text = "\n".join([command_text(payload), *candidate_paths(payload)])
    return match_any(patterns, text) is not None


def _protected_hit(payload: dict[str, Any], scope: dict[str, Any], cwd: Path | None) -> bool:
    targets = [_canonical_path(raw, cwd) for raw in candidate_paths(payload)]
    if any(target is not None and _within_any(target, _scope_roots(scope, "protected_roots")) for target in targets):
        return True
    text = "\n".join([command_text(payload), *candidate_paths(payload)])
    if re.search(r"\$(?:CODEX_HOME|\{CODEX_HOME\})(?:/|\b)", text, flags=re.IGNORECASE):
        return True
    return _screening_hit(
        payload, scope, cwd, roots_key="protected_roots", patterns_key="protected_command_patterns",
        defaults=DEFAULT_PROTECTED_COMMAND_PATTERNS,
    )


def _protected_skill_read_allowed(payload: dict[str, Any], cwd: Path | None) -> bool:
    home = codex_home().resolve(strict=False)
    skills = (home / "skills").resolve(strict=False)

    def is_skill_doc(raw: Any) -> bool:
        if not isinstance(raw, str):
            return False
        for prefix in ("$CODEX_HOME/", "${CODEX_HOME}/"):
            if raw.startswith(prefix):
                raw = str(home / raw.removeprefix(prefix))
                break
        path = _canonical_path(raw, cwd)
        if path is None or path.name != "SKILL.md":
            return False
        try:
            return len(path.relative_to(skills).parts) >= 2
        except ValueError:
            return False

    cmd = command_text(payload)
    if cmd:
        if re.search(r"[;&|<>`\r\n]", cmd):
            return False
        try:
            tokens = shlex.split(cmd)
        except ValueError:
            return False
        return len(tokens) >= 2 and tokens[0] in {"cat", "/bin/cat"} and all(is_skill_doc(token) for token in tokens[1:])

    if tool_name(payload).lower() not in {"read", "read_file"}:
        return False
    data = tool_input(payload)
    paths = [data[key] for key in ("path", "file", "file_path", "filename") if key in data]
    return bool(paths) and all(is_skill_doc(path) for path in paths)


def _persistence_hit(payload: dict[str, Any], scope: dict[str, Any], cwd: Path | None) -> bool:
    return _screening_hit(
        payload, scope, cwd, roots_key=None, patterns_key="persistence_path_patterns",
        defaults=DEFAULT_PERSISTENCE_PATH_PATTERNS,
    )


def out_of_scope(payload: dict[str, Any], scope: dict[str, Any]) -> bool:
    governed = _scope_roots(scope, "governed_roots")
    if not governed or scope.get("out_of_scope_mode") not in {"allow", "report"}:
        return False
    cwd = _canonical_path(str(payload.get("cwd") or os.getcwd()))
    return cwd is not None and not _within_any(cwd, governed)


TASK_ADMIN_METACHARS = re.compile(r"[;&|<>`$\r\n]")
TASK_ADMIN_PHASE = re.compile(r"^[A-Za-z-]+$")
TASK_ADMIN_REASON = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
TASK_ADMIN_TTL = re.compile(r"^\d+[hm]$")
TASK_ADMIN_SESSION = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def is_task_admin_command(cmd: str) -> bool:
    if not cmd or TASK_ADMIN_METACHARS.search(cmd):
        return False
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return False
    if len(tokens) < 4:
        return False
    head = tokens[0]
    if head != "codex-task" and _canonical_path(head) != (codex_home() / "bin" / "codex-task").resolve(strict=False):
        return False
    command = tokens[1]
    if command == "revoke":
        return len(tokens) == 4 and tokens[2] == "--reason" and TASK_ADMIN_REASON.fullmatch(tokens[3]) is not None
    if command != "declare" or len(tokens) < 5 or TASK_ADMIN_PHASE.fullmatch(tokens[2]) is None:
        return False
    seen: set[str] = set()
    validators = {"--reason": TASK_ADMIN_REASON, "--ttl": TASK_ADMIN_TTL, "--session-id": TASK_ADMIN_SESSION}
    index = 3
    while index < len(tokens):
        flag = tokens[index]
        if flag in seen or flag not in validators or index + 1 >= len(tokens):
            return False
        if validators[flag].fullmatch(tokens[index + 1]) is None:
            return False
        seen.add(flag)
        index += 2
    return "--reason" in seen


def _cached_sha256(path: Path, info: os.stat_result) -> str:
    key = (str(path), info.st_size, info.st_mtime_ns, info.st_ino)
    digest = _DIGEST_CACHE.get(key)
    if digest is None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for stale in [cached for cached in _DIGEST_CACHE if cached[0] == str(path)]:
            _DIGEST_CACHE.pop(stale, None)
        _DIGEST_CACHE[key] = digest
    return digest


def integrity_watch_status(scope: dict[str, Any]) -> tuple[str, str]:
    manifest_path = codex_home() / "harness" / "deployed-manifest.json"
    if not manifest_path.exists():
        return "inactive", "deployed manifest missing"
    limits = scope.get("integrity_watch")
    limits = limits if isinstance(limits, dict) else {}
    max_files = int(limits.get("max_files", 32))
    max_file_bytes = int(limits.get("max_file_bytes", 1024 * 1024))
    max_total_bytes = int(limits.get("max_total_bytes", 4 * 1024 * 1024))
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(files, list):
            return "frozen", "manifest files are invalid"
        if len(files) > max_files:
            return "frozen", f"manifest file count exceeds {max_files}"
        total = 0
        home = codex_home().resolve(strict=False)
        for entry in files:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                return "frozen", "manifest entry is invalid"
            raw_path = Path(entry["path"])
            if raw_path.is_absolute():
                return "frozen", "manifest path must be relative"
            path = (home / raw_path).resolve(strict=False)
            if not _within_any(path, [home]):
                return "frozen", "manifest path escapes CODEX_HOME"
            info = path.stat()
            if not stat.S_ISREG(info.st_mode) or entry.get("type") != "file":
                return "frozen", f"deployed type mismatch: {entry['path']}"
            if stat.S_IMODE(info.st_mode) != entry.get("mode"):
                return "frozen", f"deployed mode mismatch: {entry['path']}"
            if info.st_size > max_file_bytes:
                return "frozen", f"deployed file exceeds {max_file_bytes} bytes: {entry['path']}"
            total += info.st_size
            if total > max_total_bytes:
                return "frozen", f"deployed total exceeds {max_total_bytes} bytes"
            if _cached_sha256(path, info) != entry.get("sha256"):
                return "frozen", f"deployed digest mismatch: {entry['path']}"
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return "frozen", f"integrity watch error: {exc}"
    return "ok", "manifest matches"


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
    paths.extend(structured_targets(payload))
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


def _phase_resolution(
    payload: dict[str, Any],
    policy: dict[str, Any],
    root: Path | None,
) -> tuple[str, str]:
    phase, marker_reason, _ = phase_with_trace(payload, policy, root)
    return phase, marker_reason


def phase_with_trace(
    payload: dict[str, Any],
    policy: dict[str, Any],
    root: Path | None,
) -> tuple[str, str, dict[str, Any]]:
    env_value = payload.get("phase") or os.environ.get("CODEX_HARNESS_PHASE")
    scope = load_scope()
    cwd = _canonical_path(str(payload.get("cwd") or os.getcwd()))
    adopted = bool(env_value and root is not None and cwd is not None and _within_any(cwd, _scope_roots(scope, "governed_roots")))
    trace: dict[str, Any] = {"env": {"present": bool(env_value), "adopted": adopted}}
    marker_reason = "NOT_EVALUATED"
    if adopted:
        value = env_value
        trace.update({"transcript": "NOT_EVALUATED", "self_declared": "NOT_EVALUATED", "snapshot": None, "source": "env"})
    else:
        if task_state is None:
            marker_phase, marker_reason = None, "TASK_STATE_UNAVAILABLE"
        else:
            try:
                marker_phase, marker_reason = task_state.resolve_declared_phase(payload, policy)
            except Exception:
                marker_phase, marker_reason = None, "TRANSCRIPT_INVALID"
        trace["transcript"] = marker_reason
        self_phase, self_reason = None, "NOT_EVALUATED"
        if not marker_phase and task_state is not None:
            try:
                self_phase, self_reason = task_state.resolve_self_declared(payload.get("cwd") or os.getcwd(), policy)
            except Exception:
                self_phase, self_reason = None, "DECLARATION_INVALID"
        trace["self_declared"] = "SELF_DECLARED" if self_phase else self_reason
        snapshot_phase = phase_from_state_snapshot(root) if not marker_phase and not self_phase else None
        trace["snapshot"] = snapshot_phase
        value = marker_phase or self_phase or snapshot_phase or "unknown"
        if marker_phase:
            trace["source"] = "transcript"
        elif self_phase:
            marker_reason = "SELF_DECLARED"
            trace["source"] = "self_declared"
        elif snapshot_phase:
            trace["source"] = "snapshot"
        else:
            trace["source"] = "none"
    phase = str(value)
    resolved = phase if phase in policy.get("phases", {}) else "unknown"
    trace["resolved"] = resolved
    return resolved, marker_reason, trace


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
        return {}
    cwd = payload.get("cwd") or os.getcwd()
    root = git_root(str(cwd))
    scope = load_scope()
    watch_status, watch_reason = integrity_watch_status(scope)
    if watch_status == "frozen":
        category, _ = classify(payload, policy)
        if category != "read":
            return block(
                f"[harness] integrity watch frozen: {watch_reason}. Recover in a terminal: {RECOVERY_COMMANDS}",
                "high",
            )
    scoped_out = out_of_scope(payload, scope)
    if scoped_out:
        phase, marker_reason = "out_of_scope", "OUT_OF_SCOPE"
        phase_policy = dict(OUT_OF_SCOPE_PHASE_POLICY)
    else:
        phase, marker_reason = _phase_resolution(payload, policy, root)
        phase_policy = policy.get("phases", {}).get(phase)
    if phase_policy is None:
        phase_policy = unknown_phase_policy(policy)

    category, reason = classify(payload, policy)
    risk_tier = category_risk_tier(policy, category)
    canonical_cwd = _canonical_path(str(cwd))
    if scoped_out and _protected_hit(payload, scope, canonical_cwd) and not _protected_skill_read_allowed(payload, canonical_cwd):
        return block("[harness] protected-root screening blocked this call.", "high")
    if scoped_out and _persistence_hit(payload, scope, canonical_cwd):
        return block("[harness] persistence screening blocked this call.", "high")
    if marker_reason == "SELF_DECLARED" and category != "read" and _protected_hit(payload, scope, canonical_cwd):
        return block("[harness] protected roots stay locked under a self-declared phase.", "high")
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

    denial_reason = (
        f"[harness] {category} is restricted during phase '{phase}': {reason or category}. "
        f"[marker_reason={marker_reason}]"
    )
    if not scoped_out and risk_tier in {"low", "medium"}:
        denial_reason += (
            " To proceed: run ~/.codex/bin/codex-task declare implementation "
            "--reason task-unblock and retry."
        )
    return block(denial_reason, risk_tier)


def main() -> int:
    payload = load_payload()
    result = decision(payload, load_policy())
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
