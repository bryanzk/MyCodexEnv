#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time


# Guard fault rule (docs/dhf-spec.md, section 8, Restrict): when the Guard itself
# fails, write and delete calls are blocked and every other call is let through.
# This block must stay at the top and stay trivial: it is what still runs when
# anything below it raises, including at import time.
_MUTATION_TOOL_NAMES = ("apply_patch", "write", "edit", "multi_edit", "delete", "delete_file")
_FAULT = {"payload": None}


def fault_result(payload: object) -> dict[str, str]:
    names = [payload[key] for key in ("tool_name", "tool", "name") if key in payload] if isinstance(payload, dict) else []
    name = names[0].lower() if len(names) == 1 and isinstance(names[0], str) else ""
    return {"decision": "block", "reason": "[harness] guard_fault"} if name in _MUTATION_TOOL_NAMES else {}


def _fault_exit(exc_type, exc, trace) -> None:
    try:
        import traceback

        traceback.print_exception(exc_type, exc, trace)
    except Exception:
        pass
    payload = _FAULT["payload"]
    try:
        if payload is None:
            payload = json.load(sys.stdin)
        result = fault_result(payload)
    except Exception:
        payload, result = {}, {}
    try:
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        sys.stdout.flush()
        sys.stderr.flush()
        record_invocation(payload if isinstance(payload, dict) else {}, result)
    except Exception:
        pass
    # Exit 0 so the host reads the decision instead of treating the crash as allow.
    os._exit(0)


if __name__ == "__main__":
    sys.excepthook = _fault_exit


# --- BEGIN DHF GUARD CORE (generated from dhf/core/guard_core.py by scripts/build_guard_bundle.py; do not edit here) ---
SHELL_STARTUP_FILES = {
    ".zshrc", ".zshenv", ".zprofile", ".zlogin", ".bashrc", ".bash_profile", ".bash_login", ".profile"
}
SYSTEM_SHELL_STARTUP_FILES = {"zshrc", "zshenv", "zprofile", "zlogin", "bashrc", "bash.bashrc", "profile"}
RECEIPT_SCHEMA_VERSION = 1
RECEIPT_TEXT_LIMIT = 200
RECEIPT_KEY_LIMIT = 16
RECEIPT_DIRECTORY_MODE = 0o700
RECEIPT_FILE_MODE = 0o600
_HOME_INPUT = os.path.expanduser("~")
_HOME = os.path.realpath(_HOME_INPUT)
_ETC = os.path.realpath("/etc")
_PERSISTENCE_ROOTS = (
    os.path.join(_HOME, "Library", "LaunchAgents"),
    "/Library/LaunchAgents",
    "/Library/LaunchDaemons",
    "/System/Library/LaunchAgents",
    "/System/Library/LaunchDaemons",
)
# Host profile, filled once by the adapter. Credentials under the user's home
# and OS persistence locations are protected for every host and need no entry.
_PROFILE = {
    "path_variables": (),  # ((NAME, value), ...): "$NAME" or "${NAME}" at the start of a raw path
    "root_aliases": (),  # ((root as the host spells it, real root), ...)
    "credential_files": (),  # exact files that hold the host's own credentials
    "control_files": (),  # exact files of the harness control plane
    "control_roots": (),  # directories of the harness control plane
}


def configure(*, path_variables=(), root_aliases=(), credential_files=(), control_files=(), control_roots=()) -> None:
    _PROFILE["path_variables"] = tuple(path_variables)
    _PROFILE["root_aliases"] = tuple(root_aliases)
    _PROFILE["credential_files"] = tuple(credential_files)
    _PROFILE["control_files"] = tuple(control_files)
    _PROFILE["control_roots"] = tuple(control_roots)


def _lexical_path(raw: object, base: str | None = None) -> str | None:
    if not isinstance(raw, str) or raw == "" or "\x00" in raw:
        return None
    text = raw
    replacements = tuple(
        (prefix, value)
        for name, value in _PROFILE["path_variables"] + (("HOME", _HOME),)
        for prefix in ("$" + name, "${" + name + "}")
    )
    for prefix, replacement in replacements:
        if text == prefix or text.startswith(prefix + "/"):
            text = replacement + text[len(prefix) :]
            break
    try:
        path = os.path.expanduser(text)
        if not os.path.isabs(path):
            if base is None:
                return None
            path = os.path.join(base, path)
        path = os.path.normpath(path)
        for source, target in _PROFILE["root_aliases"] + ((_HOME_INPUT, _HOME),):
            if _same_path(path, source) or _within(path, source):
                path = os.path.join(target, os.path.relpath(path, source))
                break
        return path
    except (OSError, RuntimeError, ValueError):
        return None


def _same_path(left: str, right: str) -> bool:
    return left.casefold() == right.casefold()

def _within(path: str, root: str) -> bool:
    path_key = path.casefold()
    root_key = root.casefold()
    try:
        return os.path.commonpath((path_key, root_key)) == root_key
    except ValueError:
        return False

def _hardlink_key(path: str) -> tuple[int, int] | None:
    try:
        info = os.stat(path)
        if info.st_nlink < 2 or os.path.isdir(path):
            return None
        return info.st_dev, info.st_ino
    except OSError:
        return None

def _hardlink_matches(
    path: str,
    *,
    exact: tuple[str, ...] = (),
    roots: tuple[str, ...] = (),
    predicate=None,
) -> bool:
    key = _hardlink_key(path)
    if key is None:
        return False
    for candidate in exact:
        if _hardlink_key(candidate) == key:
            return True
    for root in roots:
        try:
            for directory, _, files in os.walk(root):
                for name in files:
                    candidate = os.path.join(directory, name)
                    if (predicate is None or predicate(candidate)) and _hardlink_key(candidate) == key:
                        return True
        except OSError:
            continue
    return False

def _target_identity(raw: object, base: str | None) -> tuple[str, str, str] | None:
    lexical = _lexical_path(raw, base)
    if lexical is None:
        return None
    parent, leaf = os.path.split(lexical)
    entry = os.path.join(os.path.realpath(parent), leaf)
    return lexical, entry, os.path.realpath(lexical)


def _is_credential_target(path: str, *, check_inode: bool = False) -> bool:
    exact = _PROFILE["credential_files"] + (
        os.path.join(_HOME, ".aws", "credentials"),
        os.path.join(_HOME, ".netrc"),
    )
    if any(_same_path(path, target) for target in exact):
        return True
    name = os.path.basename(path).casefold()
    if (
        _same_path(os.path.dirname(path), os.path.join(_HOME, ".ssh"))
        and name.startswith("id_")
        and os.path.splitext(name)[1] != ".pub"
    ):
        return True
    if not check_inode:
        return False
    return _hardlink_matches(
        path,
        exact=exact,
        roots=(os.path.join(_HOME, ".ssh"),),
        predicate=lambda candidate: os.path.basename(candidate).casefold().startswith("id_")
        and os.path.splitext(candidate)[1].casefold() != ".pub",
    )


def _is_control_plane_target(path: str, *, check_inode: bool = False) -> bool:
    exact = _PROFILE["control_files"]
    roots = _PROFILE["control_roots"]
    if any(_same_path(path, target) for target in exact) or any(_within(path, root) for root in roots):
        return True
    return check_inode and _hardlink_matches(path, exact=exact, roots=roots)


def _is_persistence_target(path: str, *, check_inode: bool = False) -> bool:
    parent = os.path.dirname(path)
    name = os.path.basename(path).casefold()
    if _same_path(parent, _HOME) and name in SHELL_STARTUP_FILES:
        return True
    if _same_path(parent, _ETC) and name in SYSTEM_SHELL_STARTUP_FILES:
        return True
    if any(_within(path, root) for root in _PERSISTENCE_ROOTS):
        return True
    if not check_inode:
        return False
    exact = tuple(os.path.join(_HOME, name) for name in SHELL_STARTUP_FILES) + tuple(
        os.path.join(_ETC, name) for name in SYSTEM_SHELL_STARTUP_FILES
    )
    return _hardlink_matches(path, exact=exact, roots=_PERSISTENCE_ROOTS)


def decide(touches, governance=None) -> str:
    """Return the reason code that blocks these touches, or "" to let them through.

    A touch is (kind, (lexical, entry, referent)) with kind "read", "write" or
    "delete" and the three identities produced by _target_identity().

    `governance` is None in the default profile. In the governed profile the
    adapter passes {"write_authorized": bool, "phase": str or None,
    "write_roots": (real paths, ...)}: after the always-on blocks, a write or
    delete then needs an owner-declared phase that permits writing (Position,
    Empower) and a target inside the declared roots (Contain). Reads are never
    affected.
    """
    for touch, (lexical, entry, referent) in touches:
        if _is_credential_target(lexical) or _is_credential_target(entry):
            return "credential_target_access"
        if touch in {"read", "write"} and _is_credential_target(referent, check_inode=True):
            return "credential_target_access"
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_control_plane_target(referent, check_inode=True):
            return "active_control_plane_mutation"
        if touch == "delete" and _is_control_plane_target(entry):
            return "active_control_plane_mutation"
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_persistence_target(referent, check_inode=True):
            return "os_persistence_mutation"
        if touch == "delete" and _is_persistence_target(entry):
            return "os_persistence_mutation"
    if governance is None:
        return ""
    for touch, (_, entry, referent) in touches:
        if touch not in {"write", "delete"}:
            continue
        if not governance.get("write_authorized"):
            return "governed_phase_forbids_write" if governance.get("phase") else "governed_write_without_phase"
        target = referent if touch == "write" else entry
        if not any(_within(target, root) for root in governance.get("write_roots", ())):
            return "governed_write_outside_workspace"
    return ""


def _receipt_text(value):
    return value[:RECEIPT_TEXT_LIMIT] if isinstance(value, str) else ""

def _receipt_keys(value):
    if not isinstance(value, dict):
        return []
    return sorted(_receipt_text(key) for key in value if isinstance(key, str))[:RECEIPT_KEY_LIMIT]

def _now_iso():
    local = time.localtime()
    offset = time.strftime("%z", local) or "+0000"
    return time.strftime("%Y-%m-%dT%H:%M:%S", local) + offset[:3] + ":" + offset[3:]

def _atomic_write_json(target_dir, name, data):
    temp_name = os.path.join(target_dir, ".%s.%d" % (name, os.getpid()))
    try:
        descriptor = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, RECEIPT_FILE_MODE)
        os.fchmod(descriptor, RECEIPT_FILE_MODE)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, os.path.join(target_dir, name))
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _guard_identity(previous, guard_file):
    """Return (path, [mtime_ns, size], sha256) for the Guard file that is running.

    The digest is recomputed only when path, mtime, or size differ from the
    previous receipt, so the hash module stays off the per-call path.
    """
    path = os.path.abspath(guard_file)
    info = os.stat(path)
    stamp = [info.st_mtime_ns, info.st_size]
    cached = previous.get("guard_sha256")
    if (
        previous.get("guard_path") == path
        and previous.get("guard_stat") == stamp
        and isinstance(cached, str)
        and len(cached) == 64
    ):
        return path, stamp, cached
    import hashlib

    with open(path, "rb") as handle:
        return path, stamp, hashlib.sha256(handle.read()).hexdigest()


def _append_block_evidence(timestamp, reason_code, raw_tool, *, directory, cwd=None, session=None, phase=None):
    os.makedirs(directory, mode=RECEIPT_DIRECTORY_MODE, exist_ok=True)
    event = {
        "schema_version": 1,
        "timestamp": timestamp,
        "event_type": "guardrail_decision",
        "evidence_kind": "decision",
        "cwd": _receipt_text(cwd or os.getcwd()),
        "phase": phase or "unknown",
        "tool_name": _receipt_text(raw_tool) or "unknown",
        "approval_state": "blocked",
        "failure_class": "boundary_breach",
        "message": reason_code,
    }
    if isinstance(session, str) and session:
        event["session_id"] = _receipt_text(session)
    target = os.path.join(directory, timestamp[:10] + ".jsonl")
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, RECEIPT_FILE_MODE)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def record(
    *,
    receipt_dir,
    guard_file,
    raw_tool,
    blocked,
    reason_code,
    unrecognized=False,
    diagnostic=None,
    extra=None,
    evidence=None,
):
    """Leave a host-independent trace that the Guard ran.

    Records names and counters only: never command, patch, or file content.
    Counters are best-effort under concurrent hooks; last_invoked_at and
    guard_sha256 are the authoritative liveness fields. `extra` adds the
    adapter's own receipt fields, `diagnostic` describes an unrecognized call's
    shape, and `evidence` (directory, cwd, session, phase) is given for a block.
    """
    timestamp = _now_iso()
    os.makedirs(receipt_dir, mode=RECEIPT_DIRECTORY_MODE, exist_ok=True)
    name = "guard-receipt.json"
    try:
        with open(os.path.join(receipt_dir, name), encoding="utf-8") as handle:
            previous = json.load(handle)
    except (OSError, ValueError):
        previous = {}
    if not isinstance(previous, dict):
        previous = {}

    def counter(key):
        value = previous.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    guard_path, guard_stat, guard_sha256 = _guard_identity(previous, guard_file)
    receipt = dict(extra or {})
    receipt.update(
        {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "guard_path": guard_path,
            "guard_stat": guard_stat,
            "guard_sha256": guard_sha256,
            "last_invoked_at": timestamp,
            "last_tool_name": _receipt_text(raw_tool),
            "last_decision": "block" if blocked else "allow",
            "last_reason_code": reason_code,
            "invocations": counter("invocations") + 1,
            "blocks": counter("blocks") + (1 if blocked else 0),
            "unrecognized_mutations": counter("unrecognized_mutations") + (1 if unrecognized else 0),
            "last_unrecognized": previous.get("last_unrecognized")
            if isinstance(previous.get("last_unrecognized"), dict)
            else None,
        }
    )
    if unrecognized:
        shape = {"at": timestamp, "tool_name": _receipt_text(raw_tool)}
        shape.update(diagnostic or {})
        receipt["last_unrecognized"] = shape
    _atomic_write_json(receipt_dir, name, receipt)
    if blocked and evidence is not None:
        _append_block_evidence(timestamp, reason_code, raw_tool, **evidence)
# --- END DHF GUARD CORE ---


# Codex adapter: translate a Codex PreToolUse payload into touches for the core
# and the core's reason code into Codex's hook response.
READ_TOOLS = {"read", "read_file", "list_dir", "list_directory"}
MUTATION_TOOLS = set(_MUTATION_TOOL_NAMES)
PATH_KEYS = ("path", "file", "file_path", "filename")
PATCH_PREFIXES = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
_CODEX_HOME_INPUT = os.path.expanduser(os.environ.get("CODEX_HOME", os.path.join(_HOME_INPUT, ".codex")))
_CODEX_HOME = os.path.realpath(
    _CODEX_HOME_INPUT
)
configure(
    path_variables=(("CODEX_HOME", _CODEX_HOME),),
    root_aliases=((_CODEX_HOME_INPUT, _CODEX_HOME),),
    credential_files=(os.path.join(_CODEX_HOME, "auth.json"),),
    control_files=(
        os.path.join(_CODEX_HOME, "hooks.json"),
        # DHF hooks are registered in config.toml; editing it can unregister the Guard.
        os.path.join(_CODEX_HOME, "config.toml"),
        os.path.join(_CODEX_HOME, "runtime", "tool-policy.json"),
        os.path.join(_CODEX_HOME, "runtime", "harness-scope.json"),
        os.path.join(_CODEX_HOME, "runtime", "harness-guard-targets.json"),
        os.path.join(_CODEX_HOME, "harness", "deployed-manifest.json"),
    ),
    # task-state holds the owner's profile and phase declarations.
    control_roots=(
        os.path.join(_CODEX_HOME, "hooks"),
        os.path.join(_CODEX_HOME, "rules"),
        os.path.join(_CODEX_HOME, "task-state"),
    ),
)
_PROFILE_DIR = os.path.join(_CODEX_HOME_INPUT, "task-state", "profiles")
_GOVERNED_HINTS = {
    "governed_write_without_phase": "declare a phase first: codex-task declare development --reason <CODE>, or open the session with the line 任务模式: development",
    "governed_phase_forbids_write": "the declared phase does not permit writes; declare development to write",
    "governed_write_outside_workspace": "the target is outside this workspace, the temp directories, and extra_write_roots in harness-scope.json",
    "governed_unrecognized_mutation": "the governed profile blocks write calls it cannot classify",
}
_STATE = {"profile": "light", "phase": None}


def load_payload() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}

def codex_home() -> str:
    return _CODEX_HOME

def tool_name(payload: dict[str, object]) -> str:
    values = [payload[key] for key in ("tool_name", "tool", "name") if key in payload]
    return values[0].lower() if len(values) == 1 and isinstance(values[0], str) else ""

def raw_tool_input(payload: dict[str, object]) -> object:
    keys = [key for key in ("tool_input", "input", "arguments", "params") if key in payload]
    return payload[keys[0]] if len(keys) == 1 else None

def tool_input(payload: dict[str, object]) -> dict[str, object]:
    value = raw_tool_input(payload)
    return value if isinstance(value, dict) else {}

def _payload_cwd(payload: dict[str, object]) -> str | None:
    raw = payload.get("cwd")
    return _lexical_path(raw) if isinstance(raw, str) else None

def _single_path(data: dict[str, object]) -> str | None:
    keys = [key for key in PATH_KEYS if key in data]
    return data[keys[0]] if len(keys) == 1 and isinstance(data[keys[0]], str) else None

def _replacement_pair(data: dict[str, object]) -> tuple[str, str] | None:
    pairs = (("old", "new"), ("old_string", "new_string"))
    matches = [pair for pair in pairs if all(isinstance(data.get(key), str) for key in pair)]
    mentioned = [key for pair in pairs for key in pair if key in data]
    return matches[0] if len(matches) == 1 and len(mentioned) == 2 else None

def _patch_touches(patch: str) -> list[tuple[str, str]] | None:
    touches: list[tuple[str, str]] = []
    last_update: int | None = None
    for raw_line in patch.splitlines():
        line = raw_line.strip()
        if line.startswith("*** Update File: "):
            target = line.removeprefix("*** Update File: ").strip()
            if target:
                last_update = len(touches)
                touches.extend((("read", target), ("write", target)))
        elif line.startswith("*** Move to: "):
            target = line.removeprefix("*** Move to: ").strip()
            if target and last_update is not None:
                source = touches[last_update][1]
                touches[last_update + 1] = ("delete", source)
                touches.append(("write", target))
            last_update = None
        elif line.startswith("*** Add File: "):
            target = line.removeprefix("*** Add File: ").strip()
            if target:
                touches.append(("write", target))
            last_update = None
        elif line.startswith("*** Delete File: "):
            target = line.removeprefix("*** Delete File: ").strip()
            if target:
                touches.extend((("read", target), ("delete", target)))
            last_update = None
    return touches or None

def structured_action(payload: dict[str, object]) -> list[tuple[str, tuple[str, str, str]]] | None:
    name = tool_name(payload)
    payload_commands = [payload[key] for key in ("command", "cmd") if key in payload]
    if name not in READ_TOOLS | MUTATION_TOOLS or (name != "apply_patch" and payload_commands):
        return None
    data = tool_input(payload)
    raw_touches: list[tuple[str, str]] = []
    if name == "apply_patch":
        raw_input = raw_tool_input(payload)
        patch_values = [data[key] for key in ("patch", "command") if key in data]
        # Codex host wires deliver the patch as freeform input, as
        # tool_input.patch/command, or as a top-level command that some hosts
        # mirror alongside the container copy (observed live on 2026-08-18).
        # Identical duplicates collapse to one source; genuinely conflicting
        # sources stay ambiguous and defer to native policy.
        sources = ([raw_input] if raw_input is not None and not isinstance(raw_input, dict) else []) + patch_values + payload_commands
        unique = {value for value in sources if isinstance(value, str)}
        patch = unique.pop() if sources and len(unique) == 1 and all(isinstance(value, str) for value in sources) else None
        if not isinstance(patch, str) or (raw_touches := _patch_touches(patch)) is None:
            return None
    elif name == "multi_edit":
        edits = data.get("edits")
        if not isinstance(edits, list) or not edits:
            return None
        top_path = _single_path(data)
        if top_path is not None:
            if any(not isinstance(edit, dict) or _single_path(edit) is not None or _replacement_pair(edit) is None for edit in edits):
                return None
            raw_touches.append(("write", top_path))
        else:
            if any(key in data for key in PATH_KEYS):
                return None
            for edit in edits:
                if not isinstance(edit, dict):
                    return None
                path = _single_path(edit)
                content_valid = isinstance(edit.get("content"), str)
                pair_valid = _replacement_pair(edit) is not None
                if path is None or content_valid == pair_valid:
                    return None
                raw_touches.append(("write", path))
    else:
        path = _single_path(data)
        if path is None:
            return None
        if name == "write" and not isinstance(data.get("content"), str):
            return None
        if name == "edit" and _replacement_pair(data) is None:
            return None
        touch = "read" if name in READ_TOOLS else "delete" if name in {"delete", "delete_file"} else "write"
        raw_touches.append((touch, path))

    cwd = _payload_cwd(payload)
    touches: list[tuple[str, tuple[str, str, str]]] = []
    for touch, raw in raw_touches:
        identity = _target_identity(raw, cwd)
        if identity is None:
            return None
        touches.append((touch, identity))
    return touches

def block(reason_code: str) -> dict[str, str]:
    hint = _GOVERNED_HINTS.get(reason_code)
    return {"decision": "block", "reason": f"[harness] {reason_code}" + (f" ({hint})" if hint else "")}


def governance(payload: dict[str, object]) -> dict[str, object] | None:
    """Resolve the governed profile for this call, or None for the default profile.

    The owner sets a profile per workspace with `codex-task profile`. While no
    workspace has one, this costs a single directory listing and nothing else
    is loaded. In the governed profile the phase comes from the owner's task
    marker in the session or from `codex-task declare`; both are read by the
    sibling task_state module.
    """
    try:
        if not os.listdir(_PROFILE_DIR):
            return None
    except (FileNotFoundError, NotADirectoryError):
        return None
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "dhf_task_state", os.path.join(os.path.dirname(os.path.abspath(__file__)), "task_state.py")
    )
    task_state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task_state)
    cwd = payload.get("cwd")
    profile, _ = task_state.resolve_profile(cwd)
    _STATE["profile"] = profile
    workspace = task_state.workspace_key(cwd)
    if profile != "governed" or workspace is None:
        return None
    with open(os.path.join(_CODEX_HOME_INPUT, "runtime", "tool-policy.json"), encoding="utf-8") as handle:
        policy = json.load(handle)
    phase, _ = task_state.resolve_declared_phase(payload, policy)
    if phase is None:
        phase, _ = task_state.resolve_self_declared(cwd, policy)
    _STATE["phase"] = phase
    rules = policy.get("phases", {}).get(phase, {}) if phase else {}
    extra = []
    try:
        with open(os.path.join(_CODEX_HOME_INPUT, "runtime", "harness-scope.json"), encoding="utf-8") as handle:
            extra = json.load(handle).get("extra_write_roots", [])
    except FileNotFoundError:
        pass
    roots = [str(workspace), "/tmp", os.environ.get("TMPDIR") or "/tmp", *[_lexical_path(root) or "" for root in extra if isinstance(root, str)]]
    return {
        "phase": phase,
        "write_authorized": bool(isinstance(rules, dict) and rules.get("allow_repo_write")),
        "write_roots": tuple(os.path.realpath(root) for root in roots if root),
    }


def decision(payload: dict[str, object]) -> dict[str, str]:
    touches = structured_action(payload)
    if touches is None:
        # A write call the adapter cannot parse is only recorded, except in the governed profile.
        if tool_name(payload) in MUTATION_TOOLS and governance(payload) is not None:
            return block("governed_unrecognized_mutation")
        return {}
    # Reads are never governed, so the profile is resolved only for writes and deletes.
    governed = governance(payload) if any(touch != "read" for touch, _ in touches) else None
    reason_code = decide(touches, governed)
    return block(reason_code) if reason_code else {}


def _reason_code(result):
    reason = result.get("reason", "")
    prefix = "[harness] "
    # A governed block carries a hint after the code; the code is the first word.
    return reason[len(prefix):].split(" ", 1)[0] if isinstance(reason, str) and reason.startswith(prefix) else ""


def record_invocation(payload, result):
    blocked = result.get("decision") == "block"
    tool = tool_name(payload)
    unrecognized = (not blocked) and tool in MUTATION_TOOLS and structured_action(payload) is None
    diagnostic = None
    if unrecognized:
        raw_input = raw_tool_input(payload)
        diagnostic = {
            "payload_keys": _receipt_keys(payload),
            "tool_input_type": type(raw_input).__name__,
            "tool_input_keys": _receipt_keys(raw_input),
        }
    evidence = None
    if blocked:
        evidence = {
            "directory": os.path.expanduser(
                os.environ.get("CODEX_HARNESS_EVIDENCE_DIR", os.path.join(_CODEX_HOME_INPUT, "harness", "evidence"))
            ),
            "cwd": _payload_cwd(payload),
            "session": payload.get("session_id") or os.environ.get("CODEX_SESSION_ID"),
            "phase": _STATE["phase"],
        }
    record(
        receipt_dir=os.path.join(_CODEX_HOME_INPUT, "harness"),
        guard_file=__file__,
        raw_tool=tool,
        blocked=blocked,
        reason_code=_reason_code(result) if blocked else "",
        unrecognized=unrecognized,
        diagnostic=diagnostic,
        extra={"codex_home": _CODEX_HOME_INPUT, "profile": _STATE["profile"]},
        evidence=evidence,
    )


def main() -> int:
    payload = load_payload()
    _FAULT["payload"] = payload
    result = decision(payload)
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()
    try:
        record_invocation(payload, result)
    except Exception:
        # The receipt is evidence only: a failed write must never change or
        # delay the decision already delivered to the host.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
