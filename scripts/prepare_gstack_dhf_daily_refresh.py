#!/usr/bin/env python3
"""Prepare standalone reproduction and live parity audit commands for report-only daily refresh."""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_AUTOMATION_ID = "gstack-dhf-daily-refresh"
DEFAULT_REPORT_ONLY_DEFINITION_DIGEST = "sha256:68acbfc89311a085661cfd9e73f4f0aa26538f5ca9235c73856a06fc21b20226"
DEFINITION_DENYLIST_RELATIVE_PATH = Path("codex/runtime/daily-refresh-definition-denylist.json")
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


def make_payload(status: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"status": status}
    payload.update(extra)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller-repo-root", default=".", help="Repo that contains this script and the automation prompt.")
    parser.add_argument("--automation-id", default=DEFAULT_AUTOMATION_ID)
    parser.add_argument("--clone-root", default="", help="Standalone report-only clone path; defaults under the system temp directory.")
    parser.add_argument("--memory-file", default="", help="Report-only evidence note path; the helper does not write it.")
    parser.add_argument("--definition-digest", default=DEFAULT_REPORT_ONLY_DEFINITION_DIGEST)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def validate_definition_digest(controller_repo_root: Path, definition_digest: str) -> tuple[bool, str]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", definition_digest):
        return False, "definition_digest_invalid"
    denylist_path = controller_repo_root / DEFINITION_DENYLIST_RELATIVE_PATH
    try:
        payload = json.loads(denylist_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "definition_denylist_invalid"
    if set(payload) != {"schema_version", "digest_algorithm", "denied_definition_digests"}:
        return False, "definition_denylist_invalid"
    denied = payload.get("denied_definition_digests")
    if payload.get("schema_version") != 1 or payload.get("digest_algorithm") != "sha256" or not isinstance(denied, list):
        return False, "definition_denylist_invalid"
    if len(denied) != len(set(denied)) or any(not isinstance(item, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", item) for item in denied):
        return False, "definition_denylist_invalid"
    if definition_digest in denied:
        return False, "definition_digest_denylisted"
    return True, ""


def main() -> int:
    args = parse_args()
    controller_repo_root = Path(args.controller_repo_root).expanduser().resolve()
    codex_home = Path.home() / ".codex"
    automation_root = Path(tempfile.gettempdir()) / "mycodexenv-automations" / args.automation_id
    clone_root = Path(args.clone_root).expanduser().resolve() if args.clone_root else automation_root / "repo"
    memory_file = Path(args.memory_file).expanduser().resolve() if args.memory_file else automation_root / "memory.md"

    definition_valid, definition_reason = validate_definition_digest(controller_repo_root, args.definition_digest)
    if not definition_valid:
        payload = make_payload(
            "blocked",
            reason=definition_reason,
            definition_digest=args.definition_digest,
            denylist_path=str(controller_repo_root / DEFINITION_DENYLIST_RELATIVE_PATH),
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

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
    for label, source in (("repo_origin", repo_origin),):
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
            definition_digest=args.definition_digest,
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
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    code, out, err = retry_run(["git", "switch", "--detach", "origin/main"], cwd=clone_root)
    if code != 0:
        payload = make_payload(
            "blocked",
            reason="git_sync_failed",
            command="git switch --detach origin/main",
            detail=err or out,
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            memory_file=str(memory_file),
            repo_origin=repo_origin,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    reproduction_gate = clone_root / "test_runner.py"
    parity_gate = clone_root / "scripts" / "verify_codex_env.sh"
    if not reproduction_gate.is_file() or not parity_gate.is_file():
        payload = make_payload(
            "blocked",
            reason="report_only_gate_missing",
            controller_repo_root=str(controller_repo_root),
            clone_root=str(clone_root),
            reproduction_gate=str(reproduction_gate),
            parity_gate=str(parity_gate),
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1

    temporary_home = Path(tempfile.mkdtemp(prefix="mce-daily-refresh-home-"))
    payload = make_payload(
        "report_only_ready",
        controller_repo_root=str(controller_repo_root),
        clone_root=str(clone_root),
        memory_file=str(memory_file),
        repo_origin=repo_origin,
        definition_digest=args.definition_digest,
        temporary_home=str(temporary_home),
        reproduction_verification={
            "command": [sys.executable, str(reproduction_gate)],
            "cwd": str(clone_root),
            "env": {"HOME": str(temporary_home), "PYTHONDONTWRITEBYTECODE": "1"},
        },
        live_parity_audit={
            "command": [
                str(parity_gate),
                "--repo-root",
                str(clone_root),
                "--codex-home",
                str(codex_home),
                "--claude-home",
                str(Path.home() / ".claude"),
            ],
            "cwd": str(clone_root),
            "codex_home": str(codex_home),
            "read_only": True,
        },
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json else json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
