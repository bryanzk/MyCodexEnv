#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


BUDGET_SECONDS = 0.18
RECEIPT_NAME = "bearing-receipt.json"
RECEIPT_LOCK_SECONDS = 0.05
# Tried in order. A repository whose recovery helper does not know a flag
# answers "unrecognized arguments", and only that answer moves to the next one.
RECOVER_FLAG_CHAIN = (("--bearing", "--json"), ("--boundary", "--json"), ("--json",))


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


def recover_bearing(repo_root: Path, deadline: float) -> tuple[dict[str, Any] | None, str]:
    """Return the recovered payload and an outcome word for the receipt."""
    recover = repo_root / "scripts" / "harness_recover.py"
    if not recover.is_file():
        return None, "no_recover_helper"
    base = [sys.executable, str(recover), "--repo-root", str(repo_root)]
    result = None
    for index, flags in enumerate(RECOVER_FLAG_CHAIN):
        result = run_recover([*base, *flags], deadline)
        if result is None:
            return None, "timeout"
        if result.returncode == 0:
            break
        last = index == len(RECOVER_FLAG_CHAIN) - 1
        if last or f"unrecognized arguments: {flags[0]}" not in result.stderr:
            return None, "recover_failed"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, "recover_output_invalid"
    if not isinstance(payload, dict):
        return None, "recover_output_invalid"
    return payload, "delivered"


def recover_payload(repo_root: Path, deadline: float) -> dict[str, Any] | None:
    return recover_bearing(repo_root, deadline)[0]


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


def codex_home() -> Path:
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def write_receipt(outcome: str, repo_root: Path | None, elapsed: float) -> None:
    """Leave a trace of every run inside a repository, so a bearing that never
    arrives can be seen. Writes only into an existing harness directory and
    never raises."""
    try:
        target_dir = codex_home() / "harness"
        if not target_dir.is_dir():
            return
        target = target_dir / RECEIPT_NAME
        # Two sessions can start at once. The lock covers the whole
        # read-modify-write so neither run, nor a miss, is lost.
        with (target_dir / f".{RECEIPT_NAME}.lock").open("a") as lock:
            if not _lock_within(lock, RECEIPT_LOCK_SECONDS):
                # The receipt is evidence only. A lock that another session holds
                # too long must not keep this session start waiting.
                return
            _update_receipt(target_dir, target, outcome, repo_root, elapsed)
    except Exception:
        return


def _lock_within(lock, seconds: float) -> bool:
    """Take the advisory lock, waiting at most `seconds`. True on a platform without flock."""
    try:
        import fcntl
    except ImportError:
        return True
    deadline = time.monotonic() + seconds
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.002)


def _update_receipt(target_dir: Path, target: Path, outcome: str, repo_root: Path | None, elapsed: float) -> None:
    try:
        receipt = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            receipt = {}
    except (OSError, json.JSONDecodeError):
        receipt = {}
    now = datetime.now().astimezone().replace(microsecond=0).isoformat()
    delivered = outcome == "delivered"
    counts = receipt.get("outcomes") if isinstance(receipt.get("outcomes"), dict) else {}
    counts[outcome] = int(counts.get(outcome, 0) or 0) + 1
    receipt.update(
        {
            "schema_version": 1,
            "budget_seconds": BUDGET_SECONDS,
            "last_run_at": now,
            "last_outcome": outcome,
            "last_elapsed_seconds": round(elapsed, 4),
            "last_repo_root": str(repo_root) if repo_root is not None else None,
            "runs": int(receipt.get("runs", 0) or 0) + 1,
            "delivered": int(receipt.get("delivered", 0) or 0) + (1 if delivered else 0),
            "misses": int(receipt.get("misses", 0) or 0) + (0 if delivered else 1),
            "outcomes": counts,
        }
    )
    if delivered:
        receipt["last_delivered_at"] = now
    else:
        receipt["last_miss_at"] = now
        receipt["last_miss_outcome"] = outcome
        receipt["last_miss_repo_root"] = str(repo_root) if repo_root is not None else None
    temporary = target_dir / f".{RECEIPT_NAME}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def main() -> int:
    started = time.monotonic()
    deadline = started + BUDGET_SECONDS
    repo_root: Path | None = None
    outcome = "error"
    try:
        payload = load_payload()
        repo_root = find_repo_root(payload.get("cwd"))
        if repo_root is None:
            return 0
        recovered, outcome = recover_bearing(repo_root, deadline)
        if recovered is None:
            return 0
        response = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": render_context(recovered),
            },
        }
        json.dump(response, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except Exception:
        outcome = "error"
        return 0
    finally:
        # A cwd outside any repository is the ordinary case and leaves no trace.
        # A repository without the recovery helper is not governed: no trace either.
        if repo_root is not None and outcome != "no_recover_helper":
            write_receipt(outcome, repo_root, time.monotonic() - started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
