#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Codex app-server skills/list loader gate without network access.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--codex-bin", help="Functional Codex CLI path; defaults to the repo runtime resolver.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def resolve_codex(repo_root: Path, explicit: str | None) -> str:
    if explicit:
        candidate = Path(explicit).expanduser()
        proc = subprocess.run([str(candidate), "--version"], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return str(candidate)
        raise RuntimeError(f"configured Codex CLI failed --version: {candidate}")
    resolver = repo_root / "codex" / "runtime" / "resolve_codex_cli.sh"
    proc = subprocess.run([str(resolver)], capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError((proc.stderr or proc.stdout).strip() or "Codex CLI resolver failed")
    return proc.stdout.strip()


def expected_paths(repo_root: Path, codex_home: Path) -> set[Path]:
    expected: set[Path] = set()
    for skill_file in (repo_root / "codex" / "skills").glob("*/SKILL.md"):
        expected.add((codex_home / "skills" / skill_file.parent.name / "SKILL.md").resolve())
    for skill_file in (repo_root / "codex" / "skills" / ".system").glob("*/SKILL.md"):
        expected.add((codex_home / "skills" / ".system" / skill_file.parent.name / "SKILL.md").resolve())
    for skill_file in (repo_root / ".agents" / "skills").glob("*/SKILL.md"):
        expected.add(skill_file.resolve())
    return expected


def app_server_command(codex_bin: str) -> list[str]:
    command = [codex_bin, "app-server", "--listen", "stdio://"]
    sandbox_exec = Path("/usr/bin/sandbox-exec")
    if sandbox_exec.is_file():
        return [str(sandbox_exec), "-p", "(version 1)(allow default)(deny network*)", *command]
    return command


def send(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    process.stdin.flush()


def wait_for(process: subprocess.Popen[str], request_id: int, timeout: float) -> dict[str, Any]:
    assert process.stdout is not None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        ready, _, _ = select.select([process.stdout], [], [], min(1.0, remaining))
        if not ready:
            continue
        line = process.stdout.readline()
        if not line:
            break
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") == request_id:
            return message
    raise RuntimeError(f"timed out waiting for Codex app-server JSON-RPC id={request_id}")


def run_loader(repo_root: Path, codex_home: Path, codex_bin: str, timeout: float) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(codex_home)
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr_file:
        process = subprocess.Popen(
            app_server_command(codex_bin),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
            env=environment,
            bufsize=1,
        )
        try:
            send(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"clientInfo": {"name": "mycodexenv-skill-gate", "version": "1"}, "capabilities": {}},
                },
            )
            initialize = wait_for(process, 1, timeout)
            if "error" in initialize:
                raise RuntimeError(f"Codex app-server initialize failed: {initialize['error']}")
            send(process, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
            send(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "skills/list",
                    "params": {"cwds": [str(repo_root)], "forceReload": True},
                },
            )
            response = wait_for(process, 2, timeout)
            if "error" in response:
                raise RuntimeError(f"Codex app-server skills/list failed: {response['error']}")
        except Exception as exc:
            stderr_file.seek(0)
            diagnostic = stderr_file.read().strip()
            if diagnostic:
                raise RuntimeError(f"{exc}; app-server stderr: {diagnostic[-1200:]}") from exc
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    entries = response["result"]["data"]
    skills = [skill for entry in entries for skill in entry.get("skills", [])]
    errors = [error for entry in entries for error in entry.get("errors", [])]
    paths = {Path(skill["path"]).resolve() for skill in skills}
    enabled_paths = {Path(skill["path"]).resolve() for skill in skills if skill.get("enabled")}
    expected = expected_paths(repo_root, codex_home)
    return {
        "codex_bin": codex_bin,
        "skill_records": len(skills),
        "unique_names": len({skill.get("name") for skill in skills}),
        "loader_errors": len(errors),
        "errors": errors,
        "expected_paths": len(expected),
        "missing_expected_paths": sorted(str(path) for path in expected - paths),
        "disabled_expected_paths": sorted(str(path) for path in expected - enabled_paths if path in paths),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Codex Skill Loader Gate",
            "",
            f"- codex_bin: `{payload['codex_bin']}`",
            f"- skill_records: {payload['skill_records']}",
            f"- unique_names: {payload['unique_names']}",
            f"- loader_errors: {payload['loader_errors']}",
            f"- expected_paths: {payload['expected_paths']}",
            f"- missing_expected_paths: {len(payload['missing_expected_paths'])}",
            f"- disabled_expected_paths: {len(payload['disabled_expected_paths'])}",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    codex_home = Path(args.codex_home).expanduser().resolve()
    try:
        codex_bin = resolve_codex(repo_root, args.codex_bin)
        payload = run_loader(repo_root, codex_home, codex_bin, args.timeout)
    except (OSError, RuntimeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload))
    return 1 if payload["loader_errors"] or payload["missing_expected_paths"] or payload["disabled_expected_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
