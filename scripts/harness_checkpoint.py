#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PHASES = {"research", "requirements", "planning", "development", "validation", "review", "ship", "handoff"}


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def run_git(repo_root: Path, args: list[str], empty_value: str = "unknown") -> str:
    proc = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or empty_value


def git_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def git_snapshot(repo_root: Path) -> dict[str, str | int]:
    status = run_git(repo_root, ["status", "--short"], empty_value="")
    dirty_lines = [] if status == "unknown" else [line for line in status.splitlines() if line.strip()]
    return {
        "branch": run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "latest_commit": run_git(repo_root, ["rev-parse", "--short", "HEAD"]),
        "dirty_status": "unknown" if status == "unknown" else ("dirty" if dirty_lines else "clean"),
        "dirty_count": len(dirty_lines),
    }


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.phase not in PHASES:
        errors.append(f"--phase must be one of {', '.join(sorted(PHASES))}")
    if not args.summary.strip():
        errors.append("--summary is required")
    if not args.next_safe_task.strip():
        errors.append("--next-safe-task is required")

    verification_values = [
        args.verification_command,
        args.verification_exit_code,
        args.verification_key_output,
    ]
    has_any_verification = any(value not in (None, "") for value in verification_values)
    has_full_verification = all(value not in (None, "") for value in verification_values)

    if args.allow_unverified:
        if args.phase != "handoff":
            errors.append("--allow-unverified is only allowed for --phase handoff")
        if not args.blocker:
            errors.append("--allow-unverified requires at least one --blocker")
        if has_any_verification and not has_full_verification:
            errors.append("partial verification is not allowed; provide all verification fields or none")
    elif not has_full_verification:
        errors.append("fresh verification requires --verification-command, --verification-exit-code, and --verification-key-output")
    return errors


def replace_snapshot_line(lines: list[str], prefix: str, value: str) -> bool:
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = f"{prefix}{value}"
            return True
    return False


def update_current_snapshot(content: str, args: argparse.Namespace, timestamp: str) -> str:
    lines = content.splitlines()
    replace_snapshot_line(lines, "- phase: ", args.phase)
    replace_snapshot_line(lines, "- next_safe_task: ", args.next_safe_task)
    replace_snapshot_line(lines, "- latest_checkpoint: ", f"{timestamp} {args.summary}")
    if args.verification_command:
        latest_verification = (
            f"{timestamp} command={args.verification_command}; "
            f"exit_code={args.verification_exit_code}; key_output={args.verification_key_output}"
        )
    else:
        latest_verification = f"{timestamp} unverified handoff; blockers={'; '.join(args.blocker)}"
    replace_snapshot_line(lines, "- latest_verification: ", latest_verification)
    return "\n".join(lines).rstrip() + "\n"


def render_checkpoint(args: argparse.Namespace, timestamp: str, git: dict[str, str | int]) -> str:
    lines = [
        f"### {timestamp}",
        f"- phase: {args.phase}",
        "- event: checkpoint",
        f"- summary: {args.summary}",
        "- git:",
        f"  - branch: {git['branch']}",
        f"  - latest_commit: {git['latest_commit']}",
        f"  - dirty_status: {git['dirty_status']}",
        f"  - dirty_count: {git['dirty_count']}",
    ]
    lines.append("- changed_surfaces:")
    if args.changed_surface:
        for surface in args.changed_surface:
            lines.append(f"  - `{surface}`")
    else:
        lines.append("  - none")
    lines.append("- verification:")
    if args.verification_command:
        lines.extend(
            [
                f"  - command: `{args.verification_command}`",
                f"  - exit_code: {args.verification_exit_code}",
                f"  - key_output: {args.verification_key_output}",
            ]
        )
    else:
        lines.append("  - unverified: true")
    lines.append("- blockers:")
    if args.blocker:
        for blocker in args.blocker:
            lines.append(f"  - {blocker}")
    else:
        lines.append("  - none")
    lines.append(f"- next_safe_task: {args.next_safe_task}")
    return "\n".join(lines) + "\n"


def append_checkpoint(args: argparse.Namespace) -> int:
    errors = validate_args(args)
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1

    repo_root = git_root(args.repo_root)
    state_file = Path(args.state_file).expanduser() if args.state_file else repo_root / "docs" / "harness-state.md"
    if not state_file.exists():
        print(f"ERROR: state file does not exist: {state_file}", file=sys.stderr)
        return 1

    timestamp = now_iso()
    git = git_snapshot(repo_root)
    try:
        content = state_file.read_text(encoding="utf-8")
        updated = update_current_snapshot(content, args, timestamp)
        if "\n## State Log\n" not in updated:
            updated += "\n## State Log\n"
        updated = updated.rstrip() + "\n\n" + render_checkpoint(args, timestamp, git)
        temp_file = state_file.with_suffix(state_file.suffix + ".tmp")
        temp_file.write_text(updated, encoding="utf-8")
        temp_file.replace(state_file)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(str(state_file))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a Harness Runtime checkpoint to docs/harness-state.md.")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    append_parser = subparsers.add_parser("append", help="Append one checkpoint entry")
    append_parser.add_argument("--repo-root")
    append_parser.add_argument("--state-file")
    append_parser.add_argument("--phase", required=True)
    append_parser.add_argument("--summary", required=True)
    append_parser.add_argument("--changed-surface", action="append", default=[])
    append_parser.add_argument("--verification-command")
    append_parser.add_argument("--verification-exit-code", type=int)
    append_parser.add_argument("--verification-key-output")
    append_parser.add_argument("--next-safe-task", required=True)
    append_parser.add_argument("--blocker", action="append", default=[])
    append_parser.add_argument("--allow-unverified", action="store_true")
    append_parser.set_defaults(func=append_checkpoint)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
