#!/usr/bin/env python3
"""Read DHF hook registration from Codex config.toml text.

The registration source of truth is `codex/config.template.toml`; the runtime
copy lives in `~/.codex/config.toml`. `~/.codex/hooks.json` belongs to other
tools and is never written by this repository. Parsing is line-based on purpose
so it also runs on interpreters without `tomllib`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MANAGED_HOOK_DIR = "/.codex/hooks/"
REQUIRED_EVENTS = ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse")
STATE_EVENT_NAMES = {
    "session_start": "SessionStart",
    "user_prompt_submit": "UserPromptSubmit",
    "pre_tool_use": "PreToolUse",
    "post_tool_use": "PostToolUse",
    "post_compact": "PostCompact",
}
_EVENT_HEADER = re.compile(r"^\[\[hooks\.([A-Za-z]+)\]\]\s*(?:#.*)?$")
_HOOK_HEADER = re.compile(r"^\[\[hooks\.([A-Za-z]+)\.hooks\]\]\s*(?:#.*)?$")
_COMMAND = re.compile(r'^command\s*=\s*("(?:[^"\\]|\\.)*")\s*(?:#.*)?$')
_STATE_HEADER = re.compile(r'^\[hooks\.state\."((?:[^"\\]|\\.)*)"\]\s*$')
_STATE_KEY = re.compile(r"config\.toml:([a-z_]+):(\d+):(\d+)$")


def hook_commands(config_text: str) -> dict[str, list[list[str]]]:
    """Return event -> groups -> commands in file order."""
    events: dict[str, list[list[str]]] = {}
    current: list[str] | None = None
    for raw in config_text.splitlines():
        line = raw.strip()
        event = _EVENT_HEADER.match(line)
        if event:
            events.setdefault(event.group(1), []).append([])
            current = None
            continue
        hook = _HOOK_HEADER.match(line)
        if hook:
            groups = events.setdefault(hook.group(1), [])
            if not groups:
                groups.append([])
            current = groups[-1]
            continue
        if line.startswith("["):
            current = None
            continue
        if current is not None:
            command = _COMMAND.match(line)
            if command:
                current.append(json.loads(command.group(1)))
    return events


def is_managed(command: str) -> bool:
    return MANAGED_HOOK_DIR in command


def managed_commands(events: dict[str, list[list[str]]]) -> dict[str, list[str]]:
    """Flatten to event -> managed commands, dropping events with none."""
    managed: dict[str, list[str]] = {}
    for event, groups in events.items():
        commands = [command for group in groups for command in group if is_managed(command)]
        if commands:
            managed[event] = commands
    return managed


def disabled_managed_commands(config_text: str) -> list[str]:
    """Managed commands whose `[hooks.state."...config.toml:<event>:<g>:<i>"]` says enabled = false.

    With tomllib (Python 3.11+) the state and registrations are read from parsed
    TOML, so any valid spelling counts. Older interpreters use the line scan.
    """
    try:
        import tomllib
    except ImportError:
        return _disabled_managed_commands_by_line(config_text)
    try:
        hooks = tomllib.loads(config_text).get("hooks", {})
    except tomllib.TOMLDecodeError:
        return _disabled_managed_commands_by_line(config_text)
    state = hooks.get("state", {}) if isinstance(hooks, dict) else {}
    disabled: list[str] = []
    for key, value in (state.items() if isinstance(state, dict) else []):
        if not isinstance(value, dict) or value.get("enabled") is not False:
            continue
        match = _STATE_KEY.search(key)
        if not match:
            continue
        groups = hooks.get(STATE_EVENT_NAMES.get(match.group(1), ""), [])
        group_index, hook_index = int(match.group(2)), int(match.group(3))
        try:
            command = groups[group_index]["hooks"][hook_index]["command"]
        except (IndexError, KeyError, TypeError):
            continue
        if isinstance(command, str) and is_managed(command) and command not in disabled:
            disabled.append(command)
    return disabled


def _disabled_managed_commands_by_line(config_text: str) -> list[str]:
    events = hook_commands(config_text)
    disabled: list[str] = []
    key: str | None = None
    for raw in config_text.splitlines():
        line = raw.strip()
        header = _STATE_HEADER.match(line)
        if header:
            key = header.group(1)
            continue
        if line.startswith("["):
            key = None
            continue
        if key and re.match(r"^enabled\s*=\s*false\s*(?:#.*)?$", line):
            match = _STATE_KEY.search(key)
            if not match:
                continue
            groups = events.get(STATE_EVENT_NAMES.get(match.group(1), ""), [])
            group_index, hook_index = int(match.group(2)), int(match.group(3))
            if group_index < len(groups) and hook_index < len(groups[group_index]):
                command = groups[group_index][hook_index]
                if is_managed(command) and command not in disabled:
                    disabled.append(command)
    return disabled


def hooks_json_managed_commands(hooks_json_text: str) -> list[str]:
    """Managed commands still registered in a hooks.json document (should be none)."""
    try:
        payload = json.loads(hooks_json_text)
    except json.JSONDecodeError:
        return []
    found: list[str] = []
    hooks = payload.get("hooks") if isinstance(payload, dict) else None
    for groups in (hooks.values() if isinstance(hooks, dict) else []):
        for group in groups if isinstance(groups, list) else []:
            for hook in (group.get("hooks") if isinstance(group, dict) else None) or []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if isinstance(command, str) and is_managed(command):
                    found.append(command)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check DHF hook registration.")
    sub = parser.add_subparsers(dest="command", required=True)
    source = sub.add_parser("source", help="template registers every required event")
    source.add_argument("--template", type=Path, required=True)
    compare = sub.add_parser("compare", help="runtime config registers exactly the template's managed hooks")
    compare.add_argument("--template", type=Path, required=True)
    compare.add_argument("--config", type=Path, required=True)
    foreign = sub.add_parser("no-managed", help="hooks.json carries no managed hook commands")
    foreign.add_argument("--hooks-json", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "source":
        managed = managed_commands(hook_commands(args.template.read_text(encoding="utf-8")))
        missing = [event for event in REQUIRED_EVENTS if event not in managed]
        if missing:
            print(f"template does not register: {missing}", file=sys.stderr)
            return 1
        return 0
    if args.command == "compare":
        expected = managed_commands(hook_commands(args.template.read_text(encoding="utf-8")))
        actual = managed_commands(hook_commands(args.config.read_text(encoding="utf-8")))
        if expected != actual:
            print(json.dumps({"expected": expected, "actual": actual}, sort_keys=True), file=sys.stderr)
            return 1
        return 0
    if not args.hooks_json.exists():
        return 0
    stale = hooks_json_managed_commands(args.hooks_json.read_text(encoding="utf-8"))
    if stale:
        print(f"hooks.json still registers managed hooks: {stale}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
