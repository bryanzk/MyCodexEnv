#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path


def parse_execution_identity(stderr: str) -> dict[str, str]:
    version = re.search(r"(?:OpenAI Codex v|codex-cli\s+)([0-9.]+)", stderr)
    model = re.search(r"(?m)^model:\s*(\S+)", stderr)
    reasoning = re.search(r"(?m)^reasoning effort:\s*(\S+)", stderr)
    return {
        "codex_version": f"codex-cli {version.group(1)}" if version else "",
        "model": model.group(1) if model else "",
        "reasoning_effort": reasoning.group(1) if reasoning else "",
    }


def build_codex_command(
    codex_bin: str,
    case_dir: Path,
    final_path: Path,
    prompt: str,
    model: str,
    reasoning_effort: str,
) -> list[str]:
    return [
        codex_bin,
        "exec",
        "--ephemeral",
        "-s",
        "read-only",
        "--skip-git-repo-check",
        "-C",
        str(case_dir),
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-o",
        str(final_path),
        prompt,
    ]


def run_command(command: list[str], timeout: int) -> tuple[int | None, str, str, bool]:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr, False
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate()
        return None, stdout, stderr, True


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture identity-checked fresh-session writing behavior transcripts.")
    parser.add_argument("--eval", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", required=True)
    parser.add_argument("--config", default=Path.home() / ".codex" / "config.toml", type=Path)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--timeout", default=180, type=int)
    args = parser.parse_args()

    payload = json.loads(args.eval.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise SystemExit(f"output directory already exists: {args.output_dir}")
    args.output_dir.mkdir(parents=True)
    config_sha = hashlib.sha256(args.config.read_bytes()).hexdigest()
    if config_sha != args.config_sha256:
        raise SystemExit(f"config SHA-256 mismatch: expected={args.config_sha256} actual={config_sha}")
    version = subprocess.run([args.codex_bin, "--version"], capture_output=True, text=True, check=False)
    expected_version = version.stdout.strip()
    work_root = Path(tempfile.mkdtemp(prefix="writing-behavior-eval-"))
    failed = False
    try:
        for case in payload["cases"]:
            case_dir = work_root / case["name"]
            case_dir.mkdir()
            for relative, content in case["fixture_files"].items():
                target = case_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                target.chmod(0o444)
            prompt = case["prompt"]
            final_path = args.output_dir / f"{case['name']}.final.txt"
            command = build_codex_command(
                args.codex_bin, case_dir, final_path, prompt, args.model, args.reasoning_effort
            )
            attempts = []
            for attempt in (1, 2):
                code, stdout, stderr, timed_out = run_command(command, args.timeout)
                (args.output_dir / f"{case['name']}.attempt{attempt}.stdout.txt").write_text(stdout, encoding="utf-8")
                (args.output_dir / f"{case['name']}.attempt{attempt}.stderr.txt").write_text(stderr, encoding="utf-8")
                actual = parse_execution_identity(f"{expected_version}\n{stderr}")
                identity_ok = actual == {
                    "codex_version": expected_version,
                    "model": args.model,
                    "reasoning_effort": args.reasoning_effort,
                }
                has_final = final_path.is_file() and bool(final_path.read_text(encoding="utf-8").strip())
                infrastructure_ok = code == 0 and not timed_out and has_final and identity_ok
                attempts.append(
                    {
                        "attempt": attempt,
                        "exit_code": code,
                        "timed_out": timed_out,
                        "has_final": has_final,
                        "actual_identity": actual,
                        "identity_ok": identity_ok,
                    }
                )
                if infrastructure_ok:
                    break
            receipt = {
                "name": case["name"],
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "config_sha256": config_sha,
                "attempts": attempts,
                "infrastructure_ok": infrastructure_ok,
            }
            (args.output_dir / f"{case['name']}.receipt.json").write_text(
                json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
            )
            failed |= not infrastructure_ok
    finally:
        shutil.rmtree(work_root)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
