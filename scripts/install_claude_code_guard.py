#!/usr/bin/env python3
"""Install the DHF Guard for Claude Code into one repository.

The Guard travels with the repository: the adapter is copied to
`.claude/hooks/dhf_guard.py` and registered in `.claude/settings.json`, so a
local session and a single-repository cloud session both load it from the clone.

Default is `--check`: report what differs and change nothing. `--write` applies
it. Entries that other tools registered are kept; only the entries whose command
runs `.claude/hooks/dhf_guard.py` are replaced.

A repository's `.claude/settings.json` is a control file. Run `--write` only
with the owner's authorization for that repository.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "dhf" / "adapters" / "claude_code" / "dhf_guard.py"
FRAGMENT = ROOT / "dhf" / "adapters" / "claude_code" / "settings.fragment.json"
GUARD_RELATIVE = Path(".claude") / "hooks" / "dhf_guard.py"
SETTINGS_RELATIVE = Path(".claude") / "settings.json"
MANAGED_MARK = ".claude/hooks/dhf_guard.py"


def is_managed(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    hooks = group.get("hooks")
    return isinstance(hooks, list) and any(
        isinstance(hook, dict) and MANAGED_MARK in str(hook.get("command", "")) for hook in hooks
    )


def merged_settings(current: dict, fragment: dict) -> dict:
    """Return settings with the managed PreToolUse entries replaced by the fragment's."""
    result = json.loads(json.dumps(current))
    hooks = result.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings key 'hooks' must be an object")
    existing = hooks.get("PreToolUse", [])
    if not isinstance(existing, list):
        raise ValueError("settings key 'hooks.PreToolUse' must be a list")
    kept = [group for group in existing if not is_managed(group)]
    hooks["PreToolUse"] = kept + fragment["hooks"]["PreToolUse"]
    return result


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="repository to install into")
    parser.add_argument("--write", action="store_true", help="apply the changes (default: report only)")
    parser.add_argument("--check", action="store_true", help="report only and exit 1 when something differs (default)")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"ERROR:{repo} is not a directory", file=sys.stderr)
        return 2
    guard_target = repo / GUARD_RELATIVE
    settings_target = repo / SETTINGS_RELATIVE
    try:
        adapter_text = ADAPTER.read_text(encoding="utf-8")
        fragment = json.loads(FRAGMENT.read_text(encoding="utf-8"))
        current = load_settings(settings_target)
        wanted = merged_settings(current, fragment)
    except (OSError, ValueError) as error:
        print(f"ERROR:{error}", file=sys.stderr)
        return 2

    guard_state = (
        "missing" if not guard_target.exists()
        else "current" if guard_target.read_text(encoding="utf-8") == adapter_text
        else "stale"
    )
    settings_state = "current" if wanted == current else ("missing" if not settings_target.exists() else "stale")

    if args.write:
        if guard_state != "current":
            guard_target.parent.mkdir(parents=True, exist_ok=True)
            guard_target.write_text(adapter_text, encoding="utf-8")
            guard_target.chmod(0o755)
            guard_state = "current"
        if settings_state != "current":
            settings_target.parent.mkdir(parents=True, exist_ok=True)
            settings_target.write_text(json.dumps(wanted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            settings_state = "current"

    print(f"GUARD:{guard_state}:{guard_target}")
    print(f"SETTINGS:{settings_state}:{settings_target}")
    if guard_state == "current" and settings_state == "current":
        print("claude code guard installed and current")
        return 0
    print("run with --write to install (owner authorization required for the target repository)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
