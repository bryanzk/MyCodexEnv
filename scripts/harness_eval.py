#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANCHOR_FIELDS = ("repo_anchor", "mode_anchor", "compaction_ordinal", "automatic_transition_count")
VERIFICATION_FIELDS = ("command", "exit_code", "key_output", "timestamp")


def timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def receipt(eval_name: str, status: str, command: str, exit_code: int, key_output: str) -> dict[str, Any]:
    return {
        "eval": eval_name,
        "status": status,
        "command": command,
        "exit_code": exit_code,
        "key_output": key_output,
        "timestamp": timestamp(),
    }


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load fixture {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"fixture must be an object: {path}")
    return value


def section(text: str, title: str) -> str | None:
    match = re.search(
        rf"^## {re.escape(title)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else None


def lint_handoff(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unreadable handoff: {exc}"]

    errors: list[str] = []
    if "THREAD_DISCIPLINE_SUMMARY_V1" not in text:
        errors.append("missing THREAD_DISCIPLINE_SUMMARY_V1")
    for field in ANCHOR_FIELDS:
        matches = re.findall(rf"^\s*-\s*{re.escape(field)}:\s*(\S.*?)\s*$", text, flags=re.MULTILINE)
        if len(matches) != 1:
            errors.append(f"{field} must appear exactly once")

    artifacts = section(text, "Artifacts")
    if artifacts is None or not re.search(r"^\s*-\s+\S", artifacts, flags=re.MULTILINE):
        errors.append("missing non-empty artifacts section")

    verification = section(text, "Verification Evidence")
    if verification is None:
        errors.append("missing verification section")
    else:
        for field in VERIFICATION_FIELDS:
            matches = re.findall(rf"^\s*-\s*{re.escape(field)}:\s*(\S.*?)\s*$", verification, flags=re.MULTILINE)
            if len(matches) != 1:
                errors.append(f"verification {field} must appear exactly once")

    next_tasks = re.findall(r"^\s*-\s*next_safe_task:\s*(\S.*?)\s*$", text, flags=re.MULTILINE)
    if len(next_tasks) != 1:
        errors.append("next_safe_task must appear exactly once")
    return errors


def state_markdown(values: dict[str, Any]) -> str:
    required = ("phase", "blocked_sources", "next_safe_task", "latest_verification")
    missing = [key for key in required if not isinstance(values.get(key), str) or not values[key].strip()]
    if missing:
        raise ValueError("recovery state fixture missing: " + ", ".join(missing))
    return (
        "# Harness State\n\n"
        "## Current Snapshot\n"
        + "".join(f"- {key}: {values[key]}\n" for key in required)
    )


def matches_expected(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                failures.append(f"{key} is not an object")
                continue
            for nested_key, nested_expected in expected_value.items():
                if actual_value.get(nested_key) != nested_expected:
                    failures.append(f"{key}.{nested_key} mismatch")
        elif actual_value != expected_value:
            failures.append(f"{key} mismatch")
    return failures


def recovery_eval(fixtures: Path, recover_script: Path) -> dict[str, Any]:
    fixture_path = fixtures / "recovery-tier1.json"
    eval_command = shlex.join(
        [sys.executable, str(Path(__file__).resolve()), "tier1", "--fixtures", str(fixtures),
         "--recover-script", str(recover_script)]
    )
    try:
        fixture = load_object(fixture_path)
        state = fixture.get("state")
        evidence = fixture.get("evidence")
        expected = fixture.get("expected")
        if not isinstance(state, dict) or not isinstance(evidence, dict) or not isinstance(expected, dict):
            raise ValueError("recovery fixture requires state, evidence, and expected objects")

        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            repo_root = temp_root / "repo"
            codex_home = temp_root / "codex-home"
            (repo_root / "docs").mkdir(parents=True)
            (codex_home / "harness" / "evidence").mkdir(parents=True)
            (repo_root / "docs" / "repo-index.md").write_text("# Fixture Repo Index\n", encoding="utf-8")
            (repo_root / "docs" / "harness-state.md").write_text(state_markdown(state), encoding="utf-8")
            evidence_event = dict(evidence)
            evidence_event["cwd"] = str(repo_root.resolve())
            (codex_home / "harness" / "evidence" / "fixture.jsonl").write_text(
                json.dumps(evidence_event, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(recover_script),
                "--repo-root",
                str(repo_root),
                "--codex-home",
                str(codex_home),
                "--json",
            ]
            proc = subprocess.run(command, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                return receipt("recovery", "FAIL", eval_command, proc.returncode, proc.stderr.strip() or proc.stdout.strip())
            try:
                actual = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                return receipt("recovery", "FAIL", eval_command, 1, f"recover output is not JSON: {exc}")
            failures = matches_expected(actual, expected)
            if failures:
                return receipt("recovery", "FAIL", eval_command, 1, "; ".join(failures))
        return receipt("recovery", "PASS", eval_command, 0, "phase, next_safe_task, and latest_verification recovered")
    except (OSError, ValueError) as exc:
        return receipt("recovery", "FAIL", eval_command, 1, str(exc))


def handoff_fixture_eval(fixtures: Path) -> dict[str, Any]:
    fixture_path = fixtures / "handoff-lint-tier1.json"
    eval_command = shlex.join(
        [sys.executable, str(Path(__file__).resolve()), "tier1", "--fixtures", str(fixtures)]
    )
    try:
        fixture = load_object(fixture_path)
        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError("handoff lint fixture requires non-empty cases")
        mismatches: list[str] = []
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("path"), str) or not isinstance(
                case.get("expected_valid"), bool
            ):
                raise ValueError("handoff lint case requires path and expected_valid")
            case_path = fixtures / case["path"]
            actual_valid = not lint_handoff(case_path)
            if actual_valid != case["expected_valid"]:
                mismatches.append(case["path"])
        if mismatches:
            return receipt("handoff_lint", "FAIL", eval_command, 1, "unexpected lint result: " + ", ".join(mismatches))
        return receipt("handoff_lint", "PASS", eval_command, 0, f"{len(cases)} fixture cases matched")
    except (OSError, ValueError) as exc:
        return receipt("handoff_lint", "FAIL", eval_command, 1, str(exc))


def command_tier1(args: argparse.Namespace) -> int:
    receipts = [recovery_eval(args.fixtures, args.recover_script), handoff_fixture_eval(args.fixtures)]
    for item in receipts:
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))
    return 0 if all(item["status"] == "PASS" for item in receipts) else 1


def command_handoff_lint(args: argparse.Namespace) -> int:
    errors = lint_handoff(args.path)
    status = "PASS" if not errors else "FAIL"
    code = 0 if not errors else 1
    command = shlex.join([sys.executable, str(Path(__file__).resolve()), "handoff-lint", "--path", str(args.path)])
    key_output = "handoff contract complete" if not errors else "; ".join(errors)
    print(json.dumps(receipt("handoff_lint", status, command, code, key_output), ensure_ascii=False))
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixture-driven Harness behavior evaluator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tier1_parser = subparsers.add_parser("tier1", help="Run recovery and handoff lint evals")
    tier1_parser.add_argument("--fixtures", type=Path, default=Path("docs/evals"))
    tier1_parser.add_argument("--recover-script", type=Path, default=Path("scripts/harness_recover.py"))
    tier1_parser.set_defaults(func=command_tier1)

    lint_parser = subparsers.add_parser("handoff-lint", help="Lint one handoff document")
    lint_parser.add_argument("--path", type=Path, required=True)
    lint_parser.set_defaults(func=command_handoff_lint)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
