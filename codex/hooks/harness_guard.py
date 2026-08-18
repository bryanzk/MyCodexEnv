#!/usr/bin/env python3

import json
import os
import sys


READ_TOOLS = {"read", "read_file", "list_dir", "list_directory"}
MUTATION_TOOLS = {"apply_patch", "write", "edit", "multi_edit", "delete", "delete_file"}
PATH_KEYS = ("path", "file", "file_path", "filename")
PATCH_PREFIXES = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
SHELL_STARTUP_FILES = {
    ".zshrc", ".zshenv", ".zprofile", ".zlogin", ".bashrc", ".bash_profile", ".bash_login", ".profile"
}
SYSTEM_SHELL_STARTUP_FILES = {"zshrc", "zshenv", "zprofile", "zlogin", "bashrc", "bash.bashrc", "profile"}
_HOME_INPUT = os.path.expanduser("~")
_HOME = os.path.realpath(_HOME_INPUT)
_CODEX_HOME_INPUT = os.path.expanduser(os.environ.get("CODEX_HOME", os.path.join(_HOME_INPUT, ".codex")))
_CODEX_HOME = os.path.realpath(
    _CODEX_HOME_INPUT
)
_ETC = os.path.realpath("/etc")
_PERSISTENCE_ROOTS = (
    os.path.join(_HOME, "Library", "LaunchAgents"),
    "/Library/LaunchAgents",
    "/Library/LaunchDaemons",
    "/System/Library/LaunchAgents",
    "/System/Library/LaunchDaemons",
)


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


def _lexical_path(raw: object, base: str | None = None) -> str | None:
    if not isinstance(raw, str) or raw == "" or "\x00" in raw:
        return None
    text = raw
    replacements = (
        ("$" + "CODEX_HOME", str(codex_home())),
        ("${" + "CODEX_HOME}", str(codex_home())),
        ("$" + "HOME", str(_HOME)),
        ("${" + "HOME}", str(_HOME)),
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
        for source, target in ((_CODEX_HOME_INPUT, _CODEX_HOME), (_HOME_INPUT, _HOME)):
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


def _payload_cwd(payload: dict[str, object]) -> str | None:
    raw = payload.get("cwd")
    return _lexical_path(raw) if isinstance(raw, str) else None


def _target_identity(raw: object, base: str | None) -> tuple[str, str, str] | None:
    lexical = _lexical_path(raw, base)
    if lexical is None:
        return None
    parent, leaf = os.path.split(lexical)
    entry = os.path.join(os.path.realpath(parent), leaf)
    return lexical, entry, os.path.realpath(lexical)


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
        patch = raw_input if isinstance(raw_input, str) else patch_values[0] if len(patch_values) == 1 else None
        if patch is None and not patch_values and not isinstance(raw_input, str) and len(payload_commands) == 1:
            # Codex code-mode host wire: the patch arrives as a top-level command
            # with no input container (observed live on 2026-08-18).
            candidate = payload_commands[0]
            patch = candidate if isinstance(candidate, str) else None
        elif patch is not None and payload_commands:
            # Dual-source payloads stay ambiguous and defer to native policy.
            patch = None
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


def _is_credential_target(path: str, *, check_inode: bool = False) -> bool:
    if _same_path(path, os.path.join(codex_home(), "auth.json")):
        return True
    if _same_path(path, os.path.join(_HOME, ".aws", "credentials")) or _same_path(
        path, os.path.join(_HOME, ".netrc")
    ):
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
        exact=(
            os.path.join(codex_home(), "auth.json"),
            os.path.join(_HOME, ".aws", "credentials"),
            os.path.join(_HOME, ".netrc"),
        ),
        roots=(os.path.join(_HOME, ".ssh"),),
        predicate=lambda candidate: os.path.basename(candidate).casefold().startswith("id_")
        and os.path.splitext(candidate)[1].casefold() != ".pub",
    )


def _is_control_plane_target(path: str, *, check_inode: bool = False) -> bool:
    home = codex_home()
    if (
        _same_path(path, os.path.join(home, "hooks.json"))
        or _within(path, os.path.join(home, "hooks"))
        or _within(path, os.path.join(home, "rules"))
    ):
        return True
    exact = (
        os.path.join(home, "runtime", "tool-policy.json"),
        os.path.join(home, "runtime", "harness-scope.json"),
        os.path.join(home, "runtime", "harness-guard-targets.json"),
        os.path.join(home, "harness", "deployed-manifest.json"),
    )
    if any(
        _same_path(path, target)
        for target in exact
    ):
        return True
    return check_inode and _hardlink_matches(path, exact=(os.path.join(home, "hooks.json"), *exact), roots=(os.path.join(home, "hooks"), os.path.join(home, "rules")))


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


def block(reason_code: str) -> dict[str, str]:
    return {"decision": "block", "reason": f"[harness] {reason_code}"}


def decision(payload: dict[str, object]) -> dict[str, str]:
    touches = structured_action(payload)
    if touches is None:
        return {}
    for touch, (lexical, entry, referent) in touches:
        if _is_credential_target(lexical) or _is_credential_target(entry):
            return block("credential_target_access")
        if touch in {"read", "write"} and _is_credential_target(referent, check_inode=True):
            return block("credential_target_access")
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_control_plane_target(referent, check_inode=True):
            return block("active_control_plane_mutation")
        if touch == "delete" and _is_control_plane_target(entry):
            return block("active_control_plane_mutation")
    for touch, (_, entry, referent) in touches:
        if touch == "write" and _is_persistence_target(referent, check_inode=True):
            return block("os_persistence_mutation")
        if touch == "delete" and _is_persistence_target(entry):
            return block("os_persistence_mutation")
    return {}


def main() -> int:
    json.dump(decision(load_payload()), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
