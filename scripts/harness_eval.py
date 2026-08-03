#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


def tier2_command(
    fixtures: Path,
    transition_script: Path,
    probe_script: Path,
    scanner_script: Path,
) -> str:
    return shlex.join(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "tier2",
            "--fixtures",
            str(fixtures),
            "--transition-script",
            str(transition_script),
            "--probe-script",
            str(probe_script),
            "--scanner-script",
            str(scanner_script),
        ]
    )


def transition_idempotency_eval(
    fixtures: Path,
    transition_script: Path,
    eval_command: str,
) -> dict[str, Any]:
    try:
        fixture = load_object(fixtures / "transition-idempotency-tier2.json")
        required = ("transition_key", "first_task_id", "second_task_id", "expected_task_id")
        if any(not isinstance(fixture.get(key), str) or not fixture[key].strip() for key in required):
            raise ValueError("transition idempotency fixture requires non-empty string fields")

        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "harness" / "transitions.jsonl"
            base = [sys.executable, str(transition_script), "record", "--store", str(store), "--key",
                    fixture["transition_key"], "--task-id"]
            first = subprocess.run([*base, fixture["first_task_id"]], capture_output=True, text=True, check=False)
            if first.returncode != 0:
                return receipt("transition_idempotency", "FAIL", eval_command, first.returncode,
                               first.stderr.strip() or first.stdout.strip())
            conflict = subprocess.run([*base, fixture["second_task_id"]], capture_output=True, text=True, check=False)
            if conflict.returncode == 0:
                return receipt("transition_idempotency", "FAIL", eval_command, 1,
                               "second task unexpectedly created another successor")
            query = subprocess.run(
                [sys.executable, str(transition_script), "query", "--store", str(store), "--key",
                 fixture["transition_key"]],
                capture_output=True,
                text=True,
                check=False,
            )
            try:
                first_payload = json.loads(first.stdout)
                conflict_payload = json.loads(conflict.stdout)
                query_payload = json.loads(query.stdout)
            except json.JSONDecodeError as exc:
                return receipt("transition_idempotency", "FAIL", eval_command, 1,
                               f"transition output is not JSON: {exc}")
            winners = [
                first_payload.get("record", {}).get("task_id"),
                conflict_payload.get("record", {}).get("task_id"),
                query_payload.get("record", {}).get("task_id"),
            ]
            records = [
                json.loads(line)
                for line in store.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            matching = [record for record in records if record.get("key") == fixture["transition_key"]]
            if query.returncode != 0 or winners != [fixture["expected_task_id"]] * 3 or len(matching) != 1:
                return receipt(
                    "transition_idempotency",
                    "FAIL",
                    eval_command,
                    1,
                    f"winner mismatch winners={winners} matching_records={len(matching)}",
                )
        return receipt(
            "transition_idempotency",
            "PASS",
            eval_command,
            0,
            f"single successor task_id={fixture['expected_task_id']} transition_key={fixture['transition_key']}",
        )
    except (OSError, ValueError) as exc:
        return receipt("transition_idempotency", "FAIL", eval_command, 1, str(exc))


def probe_agreement_eval(
    fixtures: Path,
    probe_script: Path,
    scanner_script: Path,
    eval_command: str,
) -> dict[str, Any]:
    try:
        fixture = load_object(fixtures / "probe-agreement-tier2.json")
        session_id = fixture.get("session_id")
        started_at = fixture.get("started_at")
        now = fixture.get("now")
        events = fixture.get("events")
        expected = fixture.get("expected_ordinal")
        if (
            not isinstance(session_id, str)
            or not session_id
            or not isinstance(started_at, str)
            or not isinstance(now, str)
            or not isinstance(events, list)
            or not all(isinstance(event, dict) for event in events)
            or isinstance(expected, bool)
            or not isinstance(expected, int)
            or expected < 0
        ):
            raise ValueError("probe agreement fixture has invalid fields")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "codex-home"
            repo_root = root / "repo"
            sessions = codex_home / "sessions" / "2026" / "07" / "01"
            sessions.mkdir(parents=True)
            repo_root.mkdir()
            session_file = sessions / f"rollout-{session_id}.jsonl"
            rows = [
                {
                    "timestamp": started_at,
                    "type": "session_meta",
                    "payload": {
                        "id": session_id,
                        "cwd": str(repo_root),
                        "timestamp": started_at,
                    },
                },
                *events,
            ]
            session_file.write_text(
                "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            probe = subprocess.run(
                [sys.executable, str(probe_script)],
                input=json.dumps({"session_id": session_id, "cwd": str(repo_root)}),
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            if probe.returncode != 0:
                return receipt("probe_agreement", "FAIL", eval_command, probe.returncode,
                               probe.stderr.strip() or probe.stdout.strip())
            try:
                probe_payload = json.loads(probe.stdout)
                context = probe_payload["hookSpecificOutput"]["additionalContext"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                return receipt("probe_agreement", "FAIL", eval_command, 1,
                               f"probe injection missing: {exc}")
            ordinal_match = re.search(r"\bcompaction_ordinal=(\d+)\b", context)
            if ordinal_match is None:
                return receipt("probe_agreement", "FAIL", eval_command, 1,
                               "probe context has no compaction ordinal")
            probe_ordinal = int(ordinal_match.group(1))

            scanner = subprocess.run(
                [
                    sys.executable,
                    str(scanner_script),
                    "--codex-home",
                    str(codex_home),
                    "--older-than-days",
                    "0",
                    "--limit",
                    "20",
                    "--format",
                    "json",
                    "--now",
                    now,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if scanner.returncode != 0:
                return receipt("probe_agreement", "FAIL", eval_command, scanner.returncode,
                               scanner.stderr.strip() or scanner.stdout.strip())
            try:
                report = json.loads(scanner.stdout)
                candidate = next(item for item in report["candidates"] if item["thread_id"] == session_id)
                scanner_ordinal = candidate["compaction_count"]
            except (json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
                return receipt("probe_agreement", "FAIL", eval_command, 1,
                               f"scanner candidate missing: {exc}")
            if probe_ordinal != expected or scanner_ordinal != expected or probe_ordinal != scanner_ordinal:
                return receipt(
                    "probe_agreement",
                    "FAIL",
                    eval_command,
                    1,
                    f"ordinal mismatch probe={probe_ordinal} scanner={scanner_ordinal} expected={expected}",
                )
        return receipt(
            "probe_agreement",
            "PASS",
            eval_command,
            0,
            f"probe ordinal={expected} scanner ordinal={expected} for session={session_id}",
        )
    except (OSError, ValueError) as exc:
        return receipt("probe_agreement", "FAIL", eval_command, 1, str(exc))


def command_tier1(args: argparse.Namespace) -> int:
    receipts = [recovery_eval(args.fixtures, args.recover_script), handoff_fixture_eval(args.fixtures)]
    for item in receipts:
        print(json.dumps(item, ensure_ascii=False, sort_keys=False))
    return 0 if all(item["status"] == "PASS" for item in receipts) else 1


def command_tier2(args: argparse.Namespace) -> int:
    eval_command = tier2_command(
        args.fixtures,
        args.transition_script,
        args.probe_script,
        args.scanner_script,
    )
    receipts = [
        transition_idempotency_eval(args.fixtures, args.transition_script, eval_command),
        probe_agreement_eval(args.fixtures, args.probe_script, args.scanner_script, eval_command),
    ]
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

    tier2_parser = subparsers.add_parser("tier2", help="Run transition idempotency and probe agreement evals")
    tier2_parser.add_argument("--fixtures", type=Path, default=Path("docs/evals"))
    tier2_parser.add_argument("--transition-script", type=Path, default=Path("scripts/harness_transition.py"))
    tier2_parser.add_argument("--probe-script", type=Path, default=Path("codex/hooks/compaction_probe.py"))
    tier2_parser.add_argument(
        "--scanner-script",
        type=Path,
        default=Path("codex/skills/codex-fluent/scripts/report_active_sessions.py"),
    )
    tier2_parser.set_defaults(func=command_tier2)

    lint_parser = subparsers.add_parser("handoff-lint", help="Lint one handoff document")
    lint_parser.add_argument("--path", type=Path, required=True)
    lint_parser.set_defaults(func=command_handoff_lint)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
