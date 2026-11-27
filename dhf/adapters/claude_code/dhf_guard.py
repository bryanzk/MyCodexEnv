#!/usr/bin/env python3
"""DHF Guard for Claude Code: a PreToolUse command hook.

Installed as one file at <project>/.claude/hooks/dhf_guard.py by
scripts/install_claude_code_guard.py. Python 3.9 standard library only.
"""
from __future__ import annotations

import json
import os
import sys
import time


# Guard fault rule (docs/dhf-spec.md, section 8, Restrict): when the Guard itself
# fails, write calls are blocked and every other call is let through. This block
# must stay at the top and stay trivial: it is what still runs when anything
# below it raises, including at import time. A Guard that cannot start at all,
# or that times out, is covered by "onFailure": "block" on its registration.
_MUTATION_TOOL_NAMES = ("Write", "Edit", "MultiEdit", "NotebookEdit")
_FAULT = {"payload": None}


def deny(reason_code: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[harness] {reason_code}",
        }
    }


def fault_result(payload: object) -> dict[str, object]:
    name = payload.get("tool_name") if isinstance(payload, dict) else None
    return deny("guard_fault") if isinstance(name, str) and name in _MUTATION_TOOL_NAMES else {}


def _emit(result: dict[str, object]) -> None:
    # No output means "no decision": the host's own permission flow continues.
    if result:
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    sys.stdout.flush()


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
        _emit(result)
        sys.stderr.flush()
        record_invocation(payload if isinstance(payload, dict) else {}, result)
    except Exception:
        pass
    # Exit 0 so the host reads the decision instead of treating the crash as a hook failure.
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


def _resolved_too(paths) -> tuple[str, ...]:
    """Each path and, where it differs, what it resolves to.

    A protected file or directory may be a symlink into another location. A
    write is compared against the resolved target, so the destination has to be
    protected under its own name as well.
    """
    result: list[str] = []
    for path in paths:
        for candidate in (path, os.path.realpath(path)):
            if candidate not in result:
                result.append(candidate)
    return tuple(result)


def configure(*, path_variables=(), root_aliases=(), credential_files=(), control_files=(), control_roots=()) -> None:
    _PROFILE["path_variables"] = tuple(path_variables)
    _PROFILE["root_aliases"] = tuple(root_aliases)
    _PROFILE["credential_files"] = _resolved_too(credential_files)
    _PROFILE["control_files"] = _resolved_too(control_files)
    _PROFILE["control_roots"] = _resolved_too(control_roots)


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
    # A write is judged twice: by what it resolves to, and by the name it is
    # written through. The second check covers a protected name that is itself
    # a symlink to somewhere unprotected.
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_control_plane_target(referent, check_inode=True):
            return "active_control_plane_mutation"
        if touch in {"write", "delete"} and _is_control_plane_target(entry):
            return "active_control_plane_mutation"
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_persistence_target(referent, check_inode=True):
            return "os_persistence_mutation"
        if touch in {"write", "delete"} and _is_persistence_target(entry):
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


# Claude Code adapter: translate a Claude Code PreToolUse payload into touches
# for the core and the core's reason code into Claude Code's hook response.
# Tool names are case-sensitive in this host. Shell calls (Bash) are not parsed:
# write targets inside a command are a known gap (docs/dhf-spec.md, section 8).
READ_TOOLS = {"Read", "Glob", "Grep"}
MUTATION_TOOLS = set(_MUTATION_TOOL_NAMES)
_CLAUDE_HOME_INPUT = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", os.path.join(_HOME_INPUT, ".claude")))
_CLAUDE_HOME = os.path.realpath(_CLAUDE_HOME_INPUT)
_RECEIPT_DIR = os.path.join(_CLAUDE_HOME_INPUT, "dhf")
_STATE = {"project": None}


def load_payload() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def tool_name(payload: dict[str, object]) -> str:
    value = payload.get("tool_name")
    return value if isinstance(value, str) else ""


def tool_input(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("tool_input")
    return value if isinstance(value, dict) else {}


def project_dir(payload: dict[str, object]) -> str | None:
    """The project root the session started in; the payload's cwd when the host does not export it."""
    raw = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    return os.path.expanduser(raw) if isinstance(raw, str) and raw.strip() else None


def configure_host(payload: dict[str, object]) -> None:
    """Protected locations on this host (owner decision 2026-11-26, SHI-627).

    Protected: the settings files that register hooks, the hook directories, and
    this adapter's receipt directory, for the user and for the project.
    Not protected: CLAUDE.md, .claude/skills, .claude/agents. They change in
    ordinary work and stay under written rules and review.
    """
    project_input = project_dir(payload)
    _STATE["project"] = project_input
    path_variables = [("CLAUDE_CONFIG_DIR", _CLAUDE_HOME)]
    root_aliases = [(_CLAUDE_HOME_INPUT, _CLAUDE_HOME)]
    control_files = [
        os.path.join(_CLAUDE_HOME, "settings.json"),
        os.path.join(_CLAUDE_HOME, "settings.local.json"),
    ]
    control_roots = [os.path.join(_CLAUDE_HOME, "hooks"), os.path.join(_CLAUDE_HOME, "dhf")]
    if project_input:
        project = os.path.realpath(project_input)
        path_variables.append(("CLAUDE_PROJECT_DIR", project))
        root_aliases.append((project_input, project))
        control_files.extend(
            [
                os.path.join(project, ".claude", "settings.json"),
                os.path.join(project, ".claude", "settings.local.json"),
            ]
        )
        control_roots.append(os.path.join(project, ".claude", "hooks"))
    configure(
        path_variables=tuple(path_variables),
        root_aliases=tuple(root_aliases),
        # The core protects the cloud and netrc credential files under their own
        # names; listing them here adds what they resolve to when they are symlinks.
        credential_files=_with_resolved(
            [
                os.path.join(_CLAUDE_HOME, ".credentials.json"),
                os.path.join(_HOME, ".aws", "credentials"),
                os.path.join(_HOME, ".netrc"),
            ]
        ),
        control_files=_with_resolved(control_files),
        control_roots=_with_resolved(control_roots),
    )


def _with_resolved(paths: list[str]) -> tuple[str, ...]:
    """Each path and, where it differs, what it resolves to.

    A settings file or hook directory may be a symlink into a shared location.
    The core compares a write against the resolved target, so the destination
    must be protected under its own name as well.
    """
    result: list[str] = []
    for path in paths:
        for candidate in (path, os.path.realpath(path)):
            if candidate not in result:
                result.append(candidate)
    return tuple(result)


def _payload_cwd(payload: dict[str, object]) -> str | None:
    raw = payload.get("cwd")
    return _lexical_path(raw) if isinstance(raw, str) else None


def structured_action(payload: dict[str, object]) -> list[tuple[str, tuple[str, str, str]]] | None:
    """Touches of a file tool call, or None when the call is not one the adapter can classify."""
    name = tool_name(payload)
    if name not in READ_TOOLS | MUTATION_TOOLS:
        return None
    data = tool_input(payload)
    raw_touches: list[tuple[str, str]] = []
    if name == "Read":
        path = data.get("file_path")
        if not isinstance(path, str):
            return None
        raw_touches.append(("read", path))
    elif name in {"Glob", "Grep"}:
        # The search root is optional; without it the host searches the cwd.
        path = data.get("path")
        if path is not None and not isinstance(path, str):
            return None
        if isinstance(path, str) and path:
            raw_touches.append(("read", path))
    elif name == "Write":
        path = data.get("file_path")
        if not isinstance(path, str) or not isinstance(data.get("content"), str):
            return None
        raw_touches.append(("write", path))
    elif name == "Edit":
        path = data.get("file_path")
        if not isinstance(path, str) or not all(isinstance(data.get(key), str) for key in ("old_string", "new_string")):
            return None
        raw_touches.append(("write", path))
    elif name == "MultiEdit":
        path = data.get("file_path")
        edits = data.get("edits")
        if not isinstance(path, str) or not isinstance(edits, list) or not edits:
            return None
        raw_touches.append(("write", path))
    else:  # NotebookEdit
        path = data.get("notebook_path")
        if not isinstance(path, str):
            return None
        raw_touches.append(("write", path))

    cwd = _payload_cwd(payload)
    touches: list[tuple[str, tuple[str, str, str]]] = []
    for touch, raw in raw_touches:
        identity = _target_identity(raw, cwd)
        if identity is None:
            return None
        touches.append((touch, identity))
    return touches


def grep_reaches_credentials(payload: dict[str, object]) -> bool:
    """A content search prints matching lines of every file under its root.

    The core judges single files. So the adapter blocks a Grep whose root is a
    credential location or contains one: the user's .ssh directory, the cloud
    and netrc credential files, and this host's own credential file.
    """
    if tool_name(payload) != "Grep":
        return False
    raw = tool_input(payload).get("path")
    cwd = _payload_cwd(payload)
    identity = _target_identity(raw if isinstance(raw, str) and raw else ".", cwd)
    if identity is None:
        return False
    # A credential location may itself be a symlink; a search rooted at its
    # destination reaches the same files.
    anchors = _with_resolved(
        [
            os.path.join(_HOME, ".ssh"),
            os.path.join(_HOME, ".aws", "credentials"),
            os.path.join(_HOME, ".netrc"),
            *_PROFILE["credential_files"],
        ]
    )
    return any(_within(anchor, root) for root in set(identity) for anchor in anchors)


def touches_resolved_private_key(touches: list[tuple[str, tuple[str, str, str]]]) -> bool:
    """A private key reached through the destination of a symlinked .ssh directory.

    The core recognizes private keys by their place under the user's .ssh
    directory as written. When that directory is a symlink, the same key has a
    second pathname under the destination, which the core does not know.
    """
    ssh_dir = os.path.join(_HOME, ".ssh")
    resolved = os.path.realpath(ssh_dir)
    if resolved == ssh_dir:
        return False
    for _, identity in touches:
        for path in identity:
            name = os.path.basename(path).casefold()
            if (
                _same_path(os.path.dirname(path), resolved)
                and name.startswith("id_")
                and os.path.splitext(name)[1] != ".pub"
            ):
                return True
    return False


def decision(payload: dict[str, object]) -> dict[str, object]:
    configure_host(payload)
    touches = structured_action(payload)
    if touches is None:
        # A write call the adapter cannot parse is recorded, not blocked (default profile).
        return {}
    if grep_reaches_credentials(payload) or touches_resolved_private_key(touches):
        return deny("credential_target_access")
    # Only the default profile exists on this host: Position, Empower, and Contain are not wired.
    reason_code = decide(touches, None)
    return deny(reason_code) if reason_code else {}


def _reason_code(result: dict[str, object]) -> str:
    output = result.get("hookSpecificOutput")
    reason = output.get("permissionDecisionReason", "") if isinstance(output, dict) else ""
    prefix = "[harness] "
    return reason[len(prefix):].split(" ", 1)[0] if isinstance(reason, str) and reason.startswith(prefix) else ""


def record_invocation(payload: dict[str, object], result: dict[str, object]) -> None:
    output = result.get("hookSpecificOutput")
    blocked = isinstance(output, dict) and output.get("permissionDecision") == "deny"
    tool = tool_name(payload)
    unrecognized = (not blocked) and tool in MUTATION_TOOLS and structured_action(payload) is None
    diagnostic = None
    if unrecognized:
        raw_input = payload.get("tool_input")
        diagnostic = {
            "payload_keys": _receipt_keys(payload),
            "tool_input_type": type(raw_input).__name__,
            "tool_input_keys": _receipt_keys(raw_input),
        }
    evidence = None
    if blocked:
        evidence = {
            "directory": os.path.join(_RECEIPT_DIR, "evidence"),
            "cwd": _payload_cwd(payload),
            "session": payload.get("session_id"),
            "phase": None,
        }
    record(
        receipt_dir=_RECEIPT_DIR,
        guard_file=__file__,
        raw_tool=tool,
        blocked=blocked,
        reason_code=_reason_code(result) if blocked else "",
        unrecognized=unrecognized,
        diagnostic=diagnostic,
        extra={
            "host": "claude-code",
            "remote": os.environ.get("CLAUDE_CODE_REMOTE") == "true",
            "project_dir": _STATE["project"],
            "profile": "light",
        },
        evidence=evidence,
    )


def main() -> int:
    payload = load_payload()
    _FAULT["payload"] = payload
    result = decision(payload)
    _emit(result)
    try:
        record_invocation(payload, result)
    except Exception:
        # The receipt is evidence only: a failed write must never change or
        # delay the decision already delivered to the host.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
