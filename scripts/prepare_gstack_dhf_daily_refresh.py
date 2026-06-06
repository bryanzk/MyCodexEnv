#!/usr/bin/env python3
"""Prepare a standalone repo clone and fresh dry-run evidence for the daily refresh automation."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_AUTOMATION_ID = "gstack-dhf-daily-refresh"
DEFAULT_GSTACK_SOURCE = "https://github.com/garrytan/gstack.git"
DEFAULT_AUTOMATION_BRANCH = "automation/gstack-dhf-daily-refresh"
DNS_RESOLVE_ATTEMPTS = 25
DNS_RESOLVE_RETRY_SECONDS = 5.0


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def retry_run(
    cmd: list[str],
    cwd: Path | None = None,
    attempts: int = 3,
    retry_fragments: tuple[str, ...] = ("Could not resolve host", "Temporary failure", "timed out"),
) -> tuple[int, str, str]:
    last: tuple[int, str, str] = (1, "", "command did not run")
    for attempt in range(1, attempts + 1):
        last = run(cmd, cwd=cwd)
        code, out, err = last
        if code == 0:
            return last
        combined = f"{out}\n{err}"
        if attempt == attempts or not any(fragment in combined for fragment in retry_fragments):
            return last
        time.sleep(attempt)
    return last


def extract_host(value: str) -> str | None:
    if "://" not in value:
        return None
    parsed = urlparse(value)
    return parsed.hostname


def resolve_host(
    host: str,
    attempts: int = DNS_RESOLVE_ATTEMPTS,
    base_delay_seconds: float = DNS_RESOLVE_RETRY_SECONDS,
    max_delay_seconds: float = DNS_RESOLVE_RETRY_SECONDS,
) -> dict[str, object]:
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            return {"host": host, "resolved": True, "attempts": attempt, "last_error": ""}
        except OSError as exc:
            last_error = str(exc)
            if attempt < attempts:
                time.sleep(min(base_delay_seconds * attempt, max_delay_seconds))
    return {"host": host, "resolved": False, "attempts": attempts, "last_error": last_error}


def resolve_sources(sources: list[tuple[str, str, str]]) -> list[dict[str, object]]:
    cache: dict[str, dict[str, object]] = {}
    resolution = []
    for label, source, host in sources:
        if host not in cache:
            cache[host] = resolve_host(host)
        resolution.append({"label": label, "source": source, **cache[host]})
    return resolution


def git_origin(repo_root: Path) -> str:
    code, out, err = run(["git", "config", "--get", "remote.origin.url"], cwd=repo_root)
    if code != 0 or not out:
        raise RuntimeError(f"Failed to read remote.origin.url: {err or out}")
    return out.strip()


def is_standalone_clone(path: Path) -> bool:
    return (path / ".git").is_dir()


def ref_exists(repo_root: Path, ref: str) -> bool:
    code, _, _ = run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=repo_root)
    return code == 0


def make_payload(status: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"status": status}
    payload.update(extra)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller-repo-root", default=".", help="Repo that contains this script and the automation prompt.")
    parser.add_argument("--automation-id", default=DEFAULT_AUTOMATION_ID)
    parser.add_argument("--clone-root", default="", help="Standalone clone path used by the automation. Defaults to $CODEX_HOME/automations/<id>/repo.")
    parser.add_argument("--memory-file", default="", help="Automation memory file. Defaults to $CODEX_HOME/automations/<id>/memory.md.")
    parser.add_argument("--gstack-source", default=DEFAULT_GSTACK_SOURCE)
    parser.add_argument("--automation-branch", default=DEFAULT_AUTOMATION_BRANCH, help="Dedicated branch for automation commits; main is only used as the rebase base.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    controller_repo_root = Path(args.controller_repo_root).expanduser().resolve()
    codex_home = Path.home() / ".codex"
    automation_root = codex_home / "automations" / args.automation_id
    clone_root = Path(args.clone_root).expanduser().resolve() if args.clone_root else automation_root / "repo"
    memory_file = Path(args.memory_file).expanduser().resolve() if args.memory_file else automation_root / "memory.md"

    try:
        repo_origin = git_origin(controller_repo_root)
    except RuntimeError as exc:
        payload = make_payload(
            "blocked",
            reason="missing_origin",
            detail=str(exc),
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    hosts = []
    for label, source in (("repo_origin", repo_origin), ("gstack_source", args.gstack_source)):
        host = extract_host(source)
        if host:
            hosts.append((label, source, host))

    resolution = resolve_sources(hosts)
    unresolved = [item for item in resolution if not item["resolved"]]
    if unresolved:
        payload = make_payload(
            "deferred",
            reason="dns_unreachable",
            blocked_hosts=[item["host"] for item in unresolved],
            dns_resolution=resolution,
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
            repo_origin=repo_origin,
            gstack_source=args.gstack_source,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0

    if clone_root.exists() and not is_standalone_clone(clone_root):
        payload = make_payload(
            "blocked",
            reason="clone_root_not_standalone",
            detail="automation working repo must be a standalone clone with a .git directory",
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    if not clone_root.exists():
        clone_root.parent.mkdir(parents=True, exist_ok=True)
        code, out, err = retry_run(["git", "clone", repo_origin, str(clone_root)])
        if code != 0:
            payload = make_payload(
                "blocked",
                reason="clone_failed",
                detail=err or out,
                controller_repo_root=str(controller_repo_root),
                clone_root=str(clone_root),
                memory_file=str(memory_file),
                repo_origin=repo_origin,
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 1

    commands = [["git", "fetch", "origin"]]
    for cmd in commands:
        code, out, err = retry_run(cmd, cwd=clone_root)
        if code != 0:
            payload = make_payload(
                "blocked",
                reason="git_sync_failed",
                command=" ".join(cmd),
                detail=err or out,
                controller_repo_root=str(controller_repo_root),
                clone_root=str(clone_root),
                memory_file=str(memory_file),
                repo_origin=repo_origin,
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 1

    code, out, err = run(["git", "status", "--porcelain"], cwd=clone_root)
    if code != 0:
        payload = make_payload(
            "blocked",
            reason="git_status_failed",
            command="git status --porcelain",
            detail=err or out,
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
            repo_origin=repo_origin,
            automation_branch=args.automation_branch,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    if out.strip():
        payload = make_payload(
            "blocked",
            reason="clone_dirty",
            command="git status --porcelain",
            detail=out,
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
            repo_origin=repo_origin,
            automation_branch=args.automation_branch,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    remote_branch_ref = f"refs/remotes/origin/{args.automation_branch}"
    start_point = f"origin/{args.automation_branch}" if ref_exists(clone_root, remote_branch_ref) else "origin/main"
    branch_commands = [
        ["git", "switch", "--no-track", "-C", args.automation_branch, start_point],
    ]
    if start_point != "origin/main":
        branch_commands.append(["git", "rebase", "origin/main"])

    for cmd in branch_commands:
        code, out, err = retry_run(cmd, cwd=clone_root)
        if code != 0:
            payload = make_payload(
                "blocked",
                reason="git_sync_failed",
                command=" ".join(cmd),
                detail=err or out,
                controller_repo_root=str(controller_repo_root),
                clone_root=str(clone_root),
                memory_file=str(memory_file),
                repo_origin=repo_origin,
                automation_branch=args.automation_branch,
            )
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return 1

    local_version_path = clone_root / "codex" / "skills" / "gstack" / "VERSION"
    local_version = local_version_path.read_text(encoding="utf-8").strip() if local_version_path.exists() else ""
    sync_script = controller_repo_root / "scripts" / "sync_gstack_vendor.py"
    code, out, err = retry_run(
        [
            sys.executable,
            str(sync_script),
            "--repo-root",
            str(clone_root),
            "--source",
            args.gstack_source,
            "--dry-run",
            "--json",
        ],
        cwd=clone_root,
    )
    if code != 0:
        payload = make_payload(
            "blocked",
            reason="dry_run_failed",
            detail=err or out,
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
            repo_origin=repo_origin,
            gstack_source=args.gstack_source,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    dry_run_payload = json.loads(out)
    payload = make_payload(
        "ready",
        controller_repo_root=str(controller_repo_root),
        clone_root=str(clone_root),
        memory_file=str(memory_file),
        repo_origin=repo_origin,
        gstack_source=args.gstack_source,
        automation_branch=args.automation_branch,
        local_version=local_version,
        dry_run=dry_run_payload,
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json else json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
