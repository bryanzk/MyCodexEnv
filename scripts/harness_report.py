#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def codex_home(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def parse_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--since must use YYYY-MM-DD") from exc
    return value


def read_events(evidence_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    if not evidence_dir.exists():
        return events, malformed

    for path in sorted(evidence_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            malformed.append({"file": str(path), "line": 0, "error": str(exc)})
            continue
        for line_no, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed.append({"file": str(path), "line": line_no, "error": exc.msg})
                continue
            if not isinstance(event, dict):
                malformed.append({"file": str(path), "line": line_no, "error": "event is not an object"})
                continue
            event["_source_file"] = str(path)
            event["_source_line"] = line_no
            events.append(event)
    return events, malformed


def event_timestamp(event: dict[str, Any]) -> str:
    return str(event.get("timestamp", ""))


def event_matches(event: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.cwd and normalize_path(str(event.get("cwd", ""))) != normalize_path(args.cwd):
        return False
    if args.since and event_timestamp(event)[:10] < args.since:
        return False
    if args.phase and event.get("phase") != args.phase:
        return False
    if args.event_type and event.get("event_type") != args.event_type:
        return False
    return True


def compact_event(event: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "timestamp",
        "event_type",
        "phase",
        "cwd",
        "tool_name",
        "command",
        "exit_code",
        "key_output",
        "approval_state",
        "failure_class",
        "message",
    ]
    return {key: event[key] for key in keys if key in event}


def summarize(events: list[dict[str, Any]], malformed: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    filtered = [event for event in events if event_matches(event, args)]
    filtered.sort(key=event_timestamp, reverse=True)
    if args.limit is not None:
        filtered = filtered[: args.limit]

    failures = [
        event
        for event in filtered
        if event.get("event_type") in {"guardrail_decision", "sandbox_failure", "approval_request"}
        or event.get("failure_class") not in (None, "", "none")
    ]
    verifications = [event for event in filtered if event.get("event_type") == "verification_result"]

    return {
        "evidence_dir": str(args.evidence_dir),
        "filters": {
            "cwd": args.cwd,
            "since": args.since,
            "phase": args.phase,
            "event_type": args.event_type,
            "limit": args.limit,
        },
        "total_events": len(filtered),
        "scanned_events": len(events),
        "malformed_count": len(malformed),
        "malformed_lines": malformed,
        "phase_counts": dict(Counter(str(event.get("phase", "unknown")) for event in filtered)),
        "event_type_counts": dict(Counter(str(event.get("event_type", "unknown")) for event in filtered)),
        "failure_class_counts": dict(
            Counter(str(event.get("failure_class", "none")) for event in filtered if event.get("failure_class") not in (None, ""))
        ),
        "recent_verifications": [compact_event(event) for event in verifications[:5]],
        "recent_failures": [compact_event(event) for event in failures[:5]],
    }


def render_counter(title: str, values: dict[str, int]) -> list[str]:
    lines = [f"## {title}"]
    if not values:
        lines.append("- none")
        return lines
    for key, value in sorted(values.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    return lines


def render_event_list(title: str, values: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}"]
    if not values:
        lines.append("- none")
        return lines
    for event in values:
        parts = [
            str(event.get("timestamp", "unknown-time")),
            str(event.get("event_type", "unknown-event")),
            f"phase={event.get('phase', 'unknown')}",
        ]
        if "command" in event:
            parts.append(f"command={event['command']}")
        if "exit_code" in event:
            parts.append(f"exit_code={event['exit_code']}")
        if "failure_class" in event:
            parts.append(f"failure_class={event['failure_class']}")
        if "message" in event:
            parts.append(f"message={event['message']}")
        lines.append("- " + " | ".join(parts))
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Harness Evidence Report",
        "",
        f"- evidence_dir: `{summary['evidence_dir']}`",
        f"- total_events: {summary['total_events']}",
        f"- scanned_events: {summary['scanned_events']}",
        f"- malformed_count: {summary['malformed_count']}",
    ]
    if summary["total_events"] == 0:
        lines.append("- status: empty report; no evidence events matched the filters.")
    lines.append("")
    lines.extend(render_counter("Phase Distribution", summary["phase_counts"]))
    lines.append("")
    lines.extend(render_counter("Event Type Distribution", summary["event_type_counts"]))
    lines.append("")
    lines.extend(render_counter("Failure Class Summary", summary["failure_class_counts"]))
    lines.append("")
    lines.extend(render_event_list("Recent Verification", summary["recent_verifications"]))
    lines.append("")
    lines.extend(render_event_list("Recent Guardrail Or Sandbox Failure", summary["recent_failures"]))
    if summary["malformed_lines"]:
        lines.append("")
        lines.append("## Malformed Lines")
        for item in summary["malformed_lines"]:
            lines.append(f"- `{item['file']}`:{item['line']} {item['error']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize local Codex harness evidence JSONL files.")
    parser.add_argument("--codex-home", help="Codex home used when --evidence-dir is not set")
    parser.add_argument("--evidence-dir", type=Path, help="Directory containing *.jsonl evidence files")
    parser.add_argument("--cwd", help="Filter to an exact working directory")
    parser.add_argument("--since", type=parse_date, help="Filter events on or after YYYY-MM-DD")
    parser.add_argument("--phase", help="Filter to one lifecycle phase")
    parser.add_argument("--event-type", help="Filter to one evidence event_type")
    parser.add_argument("--limit", type=int, default=50, help="Maximum matching events to summarize")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit structured JSON")
    args = parser.parse_args()

    if args.limit is not None and args.limit < 0:
        print("ERROR: --limit must be >= 0", file=sys.stderr)
        return 1
    args.evidence_dir = (args.evidence_dir or codex_home(args.codex_home) / "harness" / "evidence").expanduser()

    events, malformed = read_events(args.evidence_dir)
    summary = summarize(events, malformed, args)
    if args.json_output:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
