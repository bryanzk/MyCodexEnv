#!/usr/bin/env python3
"""Fast-forward a local main worktree only when it is safe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


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
        print(" ".join(f"{key}={value}" for key, value in payload.items()))


def fail(reason: str, as_json: bool, **extra: object) -> int:
    emit(make_payload("blocked", reason=reason, **extra), as_json)
    return 1


def parse_counts(value: str) -> tuple[int, int]:
    parts = value.split()
    if len(parts) != 2:
        raise ValueError(f"expected two rev-list counts, got: {value!r}")
    return int(parts[0]), int(parts[1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Local worktree to fast-forward if safe.")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--apply", action="store_true", help="Actually fast-forward the local main worktree.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    code, out, err = run(["git", "rev-parse", "--is-inside-work-tree"], repo_root)
    if code != 0 or out != "true":
        return fail("not_git_worktree", args.json, repo_root=str(repo_root), detail=err or out)

    code, current_branch, err = run(["git", "branch", "--show-current"], repo_root)
    if code != 0:
        return fail("branch_check_failed", args.json, repo_root=str(repo_root), detail=err or current_branch)

    base_payload = {
        "repo_root": str(repo_root),
        "remote": args.remote,
        "main_branch": args.main_branch,
        "current_branch": current_branch,
        "applied": args.apply,
    }

    if current_branch != args.main_branch:
        emit(make_payload("skipped", reason="not_on_main", **base_payload), args.json)
        return 0

    code, status, err = run(["git", "status", "--porcelain"], repo_root)
    if code != 0:
        return fail("git_status_failed", args.json, command="git status --porcelain", detail=err or status, **base_payload)
    if status:
        emit(make_payload("skipped", reason="dirty_worktree", detail=status, **base_payload), args.json)
        return 0

    code, out, err = run(["git", "fetch", args.remote, "--prune"], repo_root)
    if code != 0:
        return fail("fetch_failed", args.json, command=f"git fetch {args.remote} --prune", detail=err or out, **base_payload)

    remote_ref = f"refs/remotes/{args.remote}/{args.main_branch}"
    code, local_head, err = run(["git", "rev-parse", args.main_branch], repo_root)
    if code != 0:
        return fail("rev_parse_failed", args.json, ref=args.main_branch, detail=err or local_head, **base_payload)
    code, remote_head, err = run(["git", "rev-parse", "--verify", remote_ref], repo_root)
    if code != 0:
        return fail("missing_remote_ref", args.json, ref=remote_ref, detail=err or remote_head, **base_payload)

    code, counts_out, err = run(["git", "rev-list", "--left-right", "--count", f"{args.main_branch}...{remote_ref}"], repo_root)
    if code != 0:
        return fail("rev_list_failed", args.json, detail=err or counts_out, **base_payload)
    try:
        local_only, remote_only = parse_counts(counts_out)
    except ValueError as exc:
        return fail("rev_list_parse_failed", args.json, detail=str(exc), **base_payload)

    payload = {
        **base_payload,
        "counts": {"local_only": local_only, "remote_only": remote_only},
        "local_before": local_head,
        "remote_head": remote_head,
    }

    if local_only == 0 and remote_only == 0:
        emit(make_payload("synced", reason="already_equal", **payload), args.json)
        return 0

    if local_only != 0 or remote_only <= 0:
        emit(make_payload("skipped", reason="not_behind_only", **payload), args.json)
        return 0

    if not args.apply:
        emit(make_payload("would_update", reason="behind_only", **payload), args.json)
        return 0

    code, out, err = run(["git", "merge", "--ff-only", remote_ref], repo_root)
    if code != 0:
        return fail("ff_only_merge_failed", args.json, command=f"git merge --ff-only {remote_ref}", detail=err or out, **payload)

    code, local_after, err = run(["git", "rev-parse", args.main_branch], repo_root)
    if code != 0:
        return fail("rev_parse_failed", args.json, ref=args.main_branch, detail=err or local_after, **payload)

    emit(make_payload("updated", reason="behind_only", local_after=local_after, **payload), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
