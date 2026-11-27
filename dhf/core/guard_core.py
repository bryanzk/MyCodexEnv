"""Host-neutral DHF Guard core.

This module decides whether a normalized action may proceed and leaves the
invocation receipt. It must not name any host, host tool, or host payload
field: an adapter translates a host's tool call into touches, fills the
profile with configure(), and translates the reason code back into the host's
response format. Contract: docs/dhf-spec.md, sections 7 to 9.

Everything below the "core body" marker is inlined verbatim into each host
adapter by scripts/build_guard_bundle.py, so a hook stays one file with no
import that could be missing at runtime. Edit here, then run
`python3 scripts/build_guard_bundle.py --write`.
"""
from __future__ import annotations

import json
import os
import time

# --- core body: inlined into each host adapter; standard library of Python 3.9 only ---

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
