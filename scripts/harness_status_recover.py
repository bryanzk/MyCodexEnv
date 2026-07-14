#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from harness_checkpoint_contract import validate_checkpoint_artifact
from harness_feedback import compute_conversion_health, with_malformed_evidence_signal
from harness_requirements import TASK_DEMAND_FIELDS, meaningful_lines, parse_sections, validate_requirements


UNKNOWN_TASK_DEMAND = {"estimated_level": "unknown", "S_state": "unknown"}


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


def positive_hours(value: str) -> float:
    try:
        hours = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number of hours") from exc
    if hours <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return hours


def normalize_path(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def parse_state_value(text: str, key: str) -> str:
    prefix = f"- {key}: "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return "unknown"


def parse_state_json_value(text: str, key: str, expected_type: type) -> Any:
    raw = parse_state_value(text, key)
    if raw == "unknown":
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, expected_type) else None


def latest_checkpoint_data(text: str) -> tuple[str, dict[str, Any] | None]:
    prefix = "- checkpoint_data: "
    for line in reversed(text.splitlines()):
        if not line.startswith(prefix):
            continue
        try:
            value = json.loads(line[len(prefix) :])
        except json.JSONDecodeError:
            return "malformed", None
        if isinstance(value, dict) and not validate_checkpoint_artifact(value):
            return "valid", value
        return "schema-invalid", None
    return "absent", None


def compact_decision_event(event: dict[str, Any]) -> dict[str, Any]:
    keys = ["timestamp", "event_type", "phase", "message", "key_output", "failure_class"]
    return {key: event[key] for key in keys if key in event}


def latest_validated_task_demand(repo_root: Path) -> dict[str, str]:
    plans_dir = repo_root / "docs" / "plans"
    if not plans_dir.is_dir():
        return dict(UNKNOWN_TASK_DEMAND)

    candidates: list[tuple[int, str, Path]] = []
    for path in plans_dir.rglob("*.md"):
        try:
            candidates.append((path.stat().st_mtime_ns, str(path), path))
        except OSError:
            continue

    for _, _, path in sorted(candidates, reverse=True):
        if validate_requirements(path):
            continue
        try:
            sections = parse_sections(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        values: dict[str, str] = {}
        for raw_line in meaningful_lines(sections.get("Task Demand (D_task)", [])):
            line = raw_line.removeprefix("- ").strip()
            if ":" not in line:
                continue
            label, value = line.split(":", 1)
            field = TASK_DEMAND_FIELDS.get(label.strip())
            if field in {"estimated_level", "S_state"}:
                values[field] = value.strip()
        if values.get("estimated_level") and values.get("S_state"):
            return {"estimated_level": values["estimated_level"], "S_state": values["S_state"]}
    return dict(UNKNOWN_TASK_DEMAND)


def parse_aware_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def evaluate_boundary(
    repo_root: Path,
    dirty_status: str,
    latest_verification: dict[str, Any] | None,
    max_verification_age_hours: float,
) -> tuple[str, str]:
    if dirty_status == "dirty":
        return "unsafe", "dirty_worktree"
    if dirty_status != "clean":
        return "unknown", "dirty_status_unavailable"
    if not latest_verification:
        return "unknown", "verification_evidence_unavailable"

    exit_code = latest_verification.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        return "unknown", "verification_exit_code_unavailable"
    if exit_code != 0:
        return "unsafe", "latest_verification_failed"

    verification_time = parse_aware_timestamp(latest_verification.get("timestamp"))
    if verification_time is None:
        return "unknown", "verification_timestamp_unavailable"
    current_time = datetime.now().astimezone()
    if verification_time > current_time:
        return "unknown", "verification_timestamp_in_future"
    if current_time - verification_time > timedelta(hours=max_verification_age_hours):
        return "unknown", "verification_too_old"

    latest_commit_time = parse_aware_timestamp(run_git(repo_root, ["log", "-1", "--format=%cI"]))
    if latest_commit_time is None:
        return "unknown", "latest_commit_timestamp_unavailable"
    if verification_time < latest_commit_time:
        return "unknown", "verification_predates_latest_commit"
    return (
        "safe",
        "clean_worktree;latest_verification_exit_zero;verification_is_fresh;"
        "verification_not_older_than_latest_commit",
    )


def latest_evidence(codex: Path, repo_root: Path) -> tuple[str, dict[str, Any] | None, int, list[dict[str, Any]]]:
    evidence_dir = codex / "harness" / "evidence"
    if not evidence_dir.exists():
        return "empty", None, 0, []

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
            if "evidence_kind" not in event:
                event["evidence_kind"] = "unknown"
            if normalize_path(str(event.get("cwd", ""))) == repo_cwd:
                events.append(event)

    if not events:
        return "empty", None, malformed_count, []
    events.sort(key=lambda event: str(event.get("timestamp", "")), reverse=True)
    verifications = [event for event in events if event.get("event_type") == "verification_result"]
    return "present", (verifications[0] if verifications else None), malformed_count, events


def build_recovery(args: argparse.Namespace) -> tuple[int, dict[str, Any] | None, str | None]:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path.cwd().resolve()
    repo_index = repo_root / "docs" / "repo-index.md"
    state_file = repo_root / "docs" / "harness-state.md"
    if not repo_index.exists():
        return 1, None, f"missing repo index: {repo_index}"
    if not state_file.exists():
        return 1, None, f"missing state file: {state_file}"

    state_text = state_file.read_text(encoding="utf-8")
    checkpoint_status, checkpoint = latest_checkpoint_data(state_text)
    if checkpoint_status in {"malformed", "schema-invalid"}:
        return 1, None, f"{checkpoint_status} checkpoint_data recovery blocker"
    git_status = run_git(repo_root, ["status", "--short"], empty_value="")
    dirty_lines = [line for line in git_status.splitlines() if line.strip()] if git_status != "unknown" else []
    evidence_status, latest, malformed_count, evidence_events = latest_evidence(codex_home(args.codex_home), repo_root)
    conversion_health = with_malformed_evidence_signal(
        compute_conversion_health(evidence_events),
        malformed_count,
    )
    evidence_kind_counter = Counter(str(event.get("evidence_kind", "unknown")) for event in evidence_events)
    evidence_kind_counts = {
        "decision": evidence_kind_counter.get("decision", 0),
        "routine": evidence_kind_counter.get("routine", 0),
        "unknown": evidence_kind_counter.get("unknown", 0),
    }
    decision_events = [event for event in evidence_events if event.get("evidence_kind") == "decision"]
    next_safe_task = parse_state_value(state_text, "next_safe_task")
    dirty_status = "unknown" if git_status == "unknown" else ("dirty" if dirty_lines else "clean")
    checkpoint_evidence = checkpoint.get("verification_evidence") if checkpoint else None
    payload = {
        "repo_root": str(repo_root),
        "checkpoint_status": checkpoint_status,
        "phase": checkpoint.get("phase") if checkpoint else parse_state_value(state_text, "phase"),
        "blocked_sources": parse_state_value(state_text, "blocked_sources"),
        "constraints": checkpoint.get("constraints") if checkpoint else parse_state_json_value(state_text, "constraints", list),
        "ownership": checkpoint.get("ownership") if checkpoint else parse_state_json_value(state_text, "ownership", dict),
        "next_safe_task": next_safe_task,
        "next_action": checkpoint.get("next_action") if checkpoint else parse_state_json_value(state_text, "next_safe_task", dict),
        "verification_evidence": checkpoint_evidence or {},
        "latest_verification_state": parse_state_value(state_text, "latest_verification"),
        "dirty_status": dirty_status,
        "dirty_count": len(dirty_lines),
        "latest_commit": run_git(repo_root, ["log", "--max-count=1", "--pretty=format:%h %ad %s", "--date=short"]),
        "evidence_status": evidence_status,
        "evidence_malformed_count": malformed_count,
        "conversion_health": conversion_health,
        "task_demand": latest_validated_task_demand(repo_root),
        "latest_verification": latest or {},
        "evidence_kind_counts": evidence_kind_counts,
        "latest_decision_evidence": compact_decision_event(decision_events[0]) if decision_events else {},
    }
    if args.boundary:
        boundary_verdict, boundary_reason = evaluate_boundary(
            repo_root,
            dirty_status,
            latest,
            args.max_verification_age,
        )
        payload["boundary_verdict"] = boundary_verdict
        payload["boundary_reason"] = boundary_reason
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
        "- evidence_kind_counts: "
        + ", ".join(f"{kind}={count}" for kind, count in payload["evidence_kind_counts"].items()),
        f"- conversion_health: `{payload['conversion_health']['status']}` - {payload['conversion_health']['reason']}",
        f"- task_demand.estimated_level: `{payload['task_demand']['estimated_level']}`",
        f"- task_demand.S_state: {payload['task_demand']['S_state']}",
        f"- blocked_sources: {payload['blocked_sources']}",
        f"- next_safe_task: {payload['next_safe_task']}",
        f"- latest_verification_state: {payload['latest_verification_state']}",
    ]
    if "boundary_verdict" in payload:
        lines.extend(
            [
                f"- boundary_verdict: `{payload['boundary_verdict']}`",
                f"- boundary_reason: {payload['boundary_reason']}",
            ]
        )
    decision = payload.get("latest_decision_evidence") or {}
    if decision:
        lines.extend(
            [
                "",
                "## Latest Decision Evidence",
                f"- event_type: `{decision.get('event_type', 'unknown')}`",
                f"- phase: `{decision.get('phase', 'unknown')}`",
                f"- timestamp: {decision.get('timestamp', 'unknown')}",
            ]
        )
        if "message" in decision:
            lines.append(f"- message: {decision['message']}")
        if "failure_class" in decision:
            lines.append(f"- failure_class: {decision['failure_class']}")
        if "key_output" in decision:
            lines.append(f"- key_output: {decision['key_output']}")
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover Harness Runtime state for a fresh Codex session.")
    parser.add_argument("--repo-root")
    parser.add_argument("--codex-home")
    parser.add_argument("--boundary", action="store_true")
    parser.add_argument("--max-verification-age", type=positive_hours, default=24.0, metavar="HOURS")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

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
