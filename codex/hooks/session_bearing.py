#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
try:
    import harness_guard
except Exception:
    harness_guard = None


BUDGET_SECONDS = 0.18


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def find_repo_root(cwd_value: Any) -> Path | None:
    if not isinstance(cwd_value, str) or not cwd_value.strip():
        return None
    cwd = Path(cwd_value).expanduser().resolve(strict=False)
    if not cwd.is_dir():
        return None
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def run_recover(command: list[str], deadline: float) -> subprocess.CompletedProcess[str] | None:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return None
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=remaining,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def recover_payload(repo_root: Path, deadline: float) -> dict[str, Any] | None:
    recover = repo_root / "scripts" / "harness_recover.py"
    if not recover.is_file():
        return None
    base = [sys.executable, str(recover), "--repo-root", str(repo_root)]
    result = run_recover([*base, "--boundary", "--json"], deadline)
    if result is None:
        return None
    if result.returncode != 0:
        if "unrecognized arguments: --boundary" not in result.stderr:
            return None
        result = run_recover([*base, "--json"], deadline)
        if result is None or result.returncode != 0:
            return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def one_line(value: Any) -> str:
    text = str(value) if value is not None else "unknown"
    return " ".join(text.splitlines()).strip() or "unknown"


def render_context(payload: dict[str, Any]) -> str:
    bearing = {
        "phase": one_line(payload.get("phase", "unknown")),
        "next_safe_task": one_line(payload.get("next_safe_task", "unknown")),
        "boundary_verdict": one_line(payload.get("boundary_verdict", "unknown")),
        "dirty_status": one_line(payload.get("dirty_status", "unknown")),
    }
    lines = ["Harness session bearing (recovered repo state):"]
    lines.extend(f"- {key}={value}" for key, value in bearing.items())
    return "\n".join(lines)


def harness_lines(payload: dict[str, Any]) -> list[str]:
    if harness_guard is None:
        return []
    try:
        policy = harness_guard.load_policy()
        if not policy:
            return []
        cwd = str(payload.get("cwd") or os.getcwd())
        scope = harness_guard.load_scope()
        watch_status, _ = harness_guard.integrity_watch_status(scope)
        lines = ["[harness] integrity watch inactive: deployed manifest missing."] if watch_status == "inactive" else []
        if harness_guard.out_of_scope(payload, scope):
            lines.insert(
                0,
                f"[harness] workspace={cwd}: out-of-scope — low/medium writes allowed; high-risk calls still blocked.",
            )
            return lines
        root = harness_guard.git_root(cwd)
        phase, reason, trace = harness_guard.phase_with_trace(payload, policy, root)
        if phase == "unknown":
            lines.insert(
                0,
                f"[harness] workspace={cwd}: governed, phase=unknown — writes blocked. "
                f"Declare first: ~/.codex/bin/codex-task declare implementation --reason task-init "
                f"(marker_reason={reason})",
            )
        else:
            lines.insert(0, f"[harness] workspace={cwd}: governed, phase={phase} (source={trace.get('source')})")
        return lines
    except Exception:
        return []


def main() -> int:
    deadline = time.monotonic() + BUDGET_SECONDS
    try:
        payload = load_payload()
        parts: list[str] = []
        repo_root = find_repo_root(payload.get("cwd"))
        if repo_root is not None:
            recovered = recover_payload(repo_root, deadline)
            if recovered is not None:
                parts.append(render_context(recovered))
        if time.monotonic() < deadline:
            parts.extend(harness_lines(payload))
        if not parts:
            return 0
        response = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n".join(parts),
            },
        }
        json.dump(response, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
