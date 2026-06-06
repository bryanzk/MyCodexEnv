#!/usr/bin/env python3
"""Fast-forward main from the gstack daily refresh branch only when it is safe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_AUTOMATION_BRANCH = "automation/gstack-dhf-daily-refresh"


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def make_payload(status: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"status": status}
    payload.update(extra)
    return payload


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        details = " ".join(f"{key}={value}" for key, value in payload.items())
        print(details)


def fail(message: str, as_json: bool, **extra: object) -> int:
    payload = make_payload("blocked", reason=message, **extra)
    emit(payload, as_json)
    return 1


def parse_counts(value: str) -> tuple[int, int]:
    parts = value.split()
    if len(parts) != 2:
        raise ValueError(f"expected two rev-list counts, got: {value!r}")
    return int(parts[0]), int(parts[1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Standalone clone used by the daily refresh automation.")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--automation-branch", default=DEFAULT_AUTOMATION_BRANCH)
    parser.add_argument("--apply", action="store_true", help="Push the fast-forwarded result to the remote main branch.")
    parser.add_argument("--verified", action="store_true", help="Required with --apply after caller completed the verification gate.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / ".git").is_dir():
        return fail(
            "repo_root_not_standalone_clone",
            args.json,
            repo_root=str(repo_root),
            detail="repo root must be a standalone clone with a .git directory",
        )

    if args.apply and not args.verified:
        return fail(
            "verification_not_confirmed",
            args.json,
            repo_root=str(repo_root),
            detail="--apply requires --verified so unattended runs cannot merge before their verification gate",
        )

    code, out, err = run(["git", "status", "--porcelain"], repo_root)
    if code != 0:
        return fail("git_status_failed", args.json, command="git status --porcelain", detail=err or out)
    if out:
        return fail("clone_dirty", args.json, command="git status --porcelain", detail=out)

    code, out, err = run(["git", "fetch", args.remote, "--prune"], repo_root)
    if code != 0:
        return fail("fetch_failed", args.json, command=f"git fetch {args.remote} --prune", detail=err or out)

    main_ref = f"refs/remotes/{args.remote}/{args.main_branch}"
    automation_ref = f"refs/remotes/{args.remote}/{args.automation_branch}"
    for ref in (main_ref, automation_ref):
        code, out, err = run(["git", "rev-parse", "--verify", ref], repo_root)
        if code != 0:
            return fail("missing_remote_ref", args.json, ref=ref, detail=err or out)

    code, main_before, err = run(["git", "rev-parse", main_ref], repo_root)
    if code != 0:
        return fail("rev_parse_failed", args.json, ref=main_ref, detail=err or main_before)
    code, automation_head, err = run(["git", "rev-parse", automation_ref], repo_root)
    if code != 0:
        return fail("rev_parse_failed", args.json, ref=automation_ref, detail=err or automation_head)

    code, counts_out, err = run(["git", "rev-list", "--left-right", "--count", f"{main_ref}...{automation_ref}"], repo_root)
    if code != 0:
        return fail("rev_list_failed", args.json, detail=err or counts_out)
    try:
        main_only, automation_only = parse_counts(counts_out)
    except ValueError as exc:
        return fail("rev_list_parse_failed", args.json, detail=str(exc))

    base_payload = {
        "repo_root": str(repo_root),
        "remote": args.remote,
        "main_branch": args.main_branch,
        "automation_branch": args.automation_branch,
        "counts": {"main_only": main_only, "automation_only": automation_only},
        "main_before": main_before,
        "automation_head": automation_head,
        "applied": args.apply,
    }

    if main_only == 0 and automation_only == 0:
        emit(make_payload("synced", reason="already_equal", pushed=False, **base_payload), args.json)
        return 0

    if main_only != 0 or automation_only <= 0:
        emit(make_payload("skipped", reason="not_ahead_only", pushed=False, **base_payload), args.json)
        return 0

    if not args.apply:
        emit(make_payload("would_merge", reason="ahead_only", pushed=False, **base_payload), args.json)
        return 0

    commands = [
        ["git", "switch", "--detach", main_ref],
        ["git", "merge", "--ff-only", automation_ref],
        ["git", "push", args.remote, f"HEAD:refs/heads/{args.main_branch}"],
        ["git", "fetch", args.remote, "--prune"],
        ["git", "switch", "--no-track", "-C", args.automation_branch, automation_ref],
    ]
    for cmd in commands:
        code, out, err = run(cmd, repo_root)
        if code != 0:
            return fail("merge_command_failed", args.json, command=" ".join(cmd), detail=err or out, **base_payload)

    code, main_after, err = run(["git", "rev-parse", main_ref], repo_root)
    if code != 0:
        return fail("rev_parse_failed", args.json, ref=main_ref, detail=err or main_after, **base_payload)

    emit(make_payload("merged", reason="ahead_only", pushed=True, main_after=main_after, **base_payload), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
