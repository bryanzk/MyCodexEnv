#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def run_git(repo_root: Path, args: list[str], empty_value: str = "unknown") -> str:
    proc = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or empty_value


def normalize_path(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def parse_state_value(text: str, key: str) -> str:
    prefix = f"- {key}: "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return "unknown"


def latest_evidence(codex: Path, repo_root: Path) -> tuple[str, dict[str, Any] | None, int]:
    evidence_dir = codex / "harness" / "evidence"
    if not evidence_dir.exists():
        return "empty", None, 0

    events: list[dict[str, Any]] = []
    malformed_count = 0
    repo_cwd = normalize_path(repo_root)
    for path in sorted(evidence_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            malformed_count += 1
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                continue
            if not isinstance(event, dict):
                malformed_count += 1
                continue
            if normalize_path(str(event.get("cwd", ""))) == repo_cwd:
                events.append(event)

    if not events:
        return "empty", None, malformed_count
    events.sort(key=lambda event: str(event.get("timestamp", "")), reverse=True)
    verifications = [event for event in events if event.get("event_type") == "verification_result"]
    return "present", (verifications[0] if verifications else events[0]), malformed_count


def build_recovery(args: argparse.Namespace) -> tuple[int, dict[str, Any] | None, str | None]:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path.cwd().resolve()
    repo_index = repo_root / "docs" / "repo-index.md"
    state_file = repo_root / "docs" / "harness-state.md"
    if not repo_index.exists():
        return 1, None, f"missing repo index: {repo_index}"
    if not state_file.exists():
        return 1, None, f"missing state file: {state_file}"

    state_text = state_file.read_text(encoding="utf-8")
    git_status = run_git(repo_root, ["status", "--short"], empty_value="")
    dirty_lines = [line for line in git_status.splitlines() if line.strip()] if git_status != "unknown" else []
    evidence_status, latest, malformed_count = latest_evidence(codex_home(args.codex_home), repo_root)
    payload = {
        "repo_root": str(repo_root),
        "phase": parse_state_value(state_text, "phase"),
        "blocked_sources": parse_state_value(state_text, "blocked_sources"),
        "next_safe_task": parse_state_value(state_text, "next_safe_task"),
        "latest_verification_state": parse_state_value(state_text, "latest_verification"),
        "dirty_status": "unknown" if git_status == "unknown" else ("dirty" if dirty_lines else "clean"),
        "dirty_count": len(dirty_lines),
        "latest_commit": run_git(repo_root, ["log", "--max-count=1", "--pretty=format:%h %ad %s", "--date=short"]),
        "evidence_status": evidence_status,
        "evidence_malformed_count": malformed_count,
        "latest_verification": latest or {},
    }
    return 0, payload, None


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Harness Recovery Smoke",
        "",
        f"- repo_root: `{payload['repo_root']}`",
        f"- phase: `{payload['phase']}`",
        f"- dirty_status: `{payload['dirty_status']}`",
        f"- dirty_count: {payload['dirty_count']}",
        f"- latest_commit: `{payload['latest_commit']}`",
        f"- evidence_status: `{payload['evidence_status']}`",
        f"- evidence_malformed_count: {payload['evidence_malformed_count']}",
        f"- blocked_sources: {payload['blocked_sources']}",
        f"- next_safe_task: {payload['next_safe_task']}",
        f"- latest_verification_state: {payload['latest_verification_state']}",
    ]
    latest = payload.get("latest_verification") or {}
    if latest:
        lines.extend(
            [
                "",
                "## Latest Evidence Verification",
                f"- command: `{latest.get('command', 'unknown')}`",
                f"- exit_code: {latest.get('exit_code', 'unknown')}",
                f"- key_output: {latest.get('key_output', 'unknown')}",
                f"- timestamp: {latest.get('timestamp', 'unknown')}",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover Harness Runtime state for a fresh Codex session.")
    parser.add_argument("--repo-root")
    parser.add_argument("--codex-home")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    code, payload, error = build_recovery(args)
    if code != 0:
        print(f"ERROR: {error}", file=sys.stderr)
        return code
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
