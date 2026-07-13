#!/usr/bin/env python3
"""Report-only ranking of old active Codex sessions.

Reads only ``CODEX_HOME/sessions/**/*.jsonl`` and
``CODEX_HOME/session_index.jsonl``. Never writes file content or explicit
metadata; filesystem atime is outside this guarantee. Nonzero exit codes mean
the scan itself could not complete or arguments were invalid, never that an
individual persisted line was malformed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

QUEUE_SCOPE = "returned-window-only"
DATA_CLASSIFICATION = "sensitive-local"
TERMINAL_ESCAPE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))"
)
BARE_URL_SCHEME = re.compile(r"\b(https?|ftp)://", flags=re.IGNORECASE)


@dataclass
class Candidate:
    primary_rank: int
    thread_id: str
    title: str
    cwd_label: str
    repo_root: str | None
    repo_root_provenance: str
    session_path: str
    started_at: str
    age_days: int
    size_bytes: int
    compaction_count: int
    handoff_required: bool
    source_kind: str


class InvalidTimestamp(ValueError):
    pass


def decoded_events(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                yield line_number, None
                continue
            yield line_number, event if isinstance(event, dict) else None


def validate_args(older_than_days: int, limit: int) -> None:
    if older_than_days < 0:
        raise ValueError("older-than-days must be at least 0")
    if not 20 <= limit <= 50:
        raise ValueError("limit must be between 20 and 50")


def parse_iso_utc(raw: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise InvalidTimestamp("timestamp is missing")
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidTimestamp(f"invalid timestamp: {raw!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidTimestamp(f"timezone offset required: {raw!r}")
    return parsed.astimezone(timezone.utc)


def canonical_utc_z(moment: datetime) -> str:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise InvalidTimestamp("timezone-aware datetime required")
    return moment.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def source_kind(payload: dict) -> str:
    if payload.get("thread_source") == "subagent":
        return "subagent"
    source = payload.get("source")
    if isinstance(source, dict) and "subagent" in source:
        return "subagent"
    if source is None and "thread_source" not in payload:
        return "unspecified"
    return "unknown"


def canonical_repo(payload: dict, index_entry: dict) -> tuple[str | None, str]:
    # Start fail-closed for the current persisted schema. Add a source field
    # only after its canonical-root semantics are verified and tested.
    return None, "unknown"


def load_index(index_path: Path) -> tuple[dict, int]:
    entries: dict = {}
    skipped = 0
    if not index_path.is_file():
        return entries, skipped
    with index_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                entries[entry["id"]] = entry
            else:
                skipped += 1
    return entries, skipped


def scan_sessions(
    codex_home: Path,
    older_than_days: int,
    limit: int,
    now: datetime,
) -> dict:
    validate_args(older_than_days, limit)
    if not codex_home.is_dir():
        raise ValueError("codex home must be an existing directory")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    now_utc = now.astimezone(timezone.utc)

    index_entries, skipped_index_lines = load_index(
        codex_home / "session_index.jsonl"
    )
    sessions_root = codex_home / "sessions"
    skipped_session_lines = 0
    invalid_or_missing_timestamp_count = 0
    excluded_subagent_count = 0
    eligible_rows: list[dict] = []

    session_paths = (
        sorted(path for path in sessions_root.rglob("*.jsonl") if path.is_file())
        if sessions_root.is_dir()
        else []
    )
    for path in session_paths:
        compaction_count = 0
        malformed = 0
        meta_event: dict | None = None
        meta_payload: dict | None = None
        for _, event in decoded_events(path):
            if event is None:
                malformed += 1
                continue
            event_type = event.get("type")
            if event_type == "compacted":
                compaction_count += 1
            elif event_type == "session_meta" and meta_payload is None:
                payload = event.get("payload")
                if isinstance(payload, dict) and isinstance(payload.get("id"), str):
                    meta_event = event
                    meta_payload = payload
        skipped_session_lines += malformed
        if meta_payload is None or meta_event is None:
            continue
        kind = source_kind(meta_payload)
        if kind == "subagent":
            excluded_subagent_count += 1
            continue
        raw_started = meta_payload.get("timestamp") or meta_event.get("timestamp")
        try:
            started = parse_iso_utc(raw_started)
        except InvalidTimestamp:
            invalid_or_missing_timestamp_count += 1
            continue
        cutoff = now_utc - timedelta(days=older_than_days)
        if started > cutoff:
            continue
        thread_id = meta_payload["id"]
        index_entry = index_entries.get(thread_id, {})
        repo_root, repo_root_provenance = canonical_repo(meta_payload, index_entry)
        title = index_entry.get("thread_name")
        eligible_rows.append({
            "thread_id": thread_id,
            "title": title if isinstance(title, str) else "",
            "cwd_label": str(meta_payload.get("cwd") or ""),
            "repo_root": repo_root,
            "repo_root_provenance": repo_root_provenance,
            "session_path": str(path),
            "started_at": canonical_utc_z(started),
            "age_days": (now_utc - started).days,
            "size_bytes": path.stat().st_size,
            "compaction_count": compaction_count,
            "handoff_required": compaction_count >= 2,
            "source_kind": kind,
        })

    eligible_rows.sort(
        key=lambda row: (-row["size_bytes"], row["started_at"], row["thread_id"])
    )
    candidates = [
        Candidate(primary_rank=rank, **row)
        for rank, row in enumerate(eligible_rows[:limit], 1)
    ]
    returned_handoff_queue = [
        {"primary_rank": item.primary_rank, "thread_id": item.thread_id,
         "compaction_count": item.compaction_count}
        for item in sorted(
            (item for item in candidates if item.handoff_required),
            key=lambda item: (-item.compaction_count, item.primary_rank),
        )
    ]
    return {
        "data_classification": DATA_CLASSIFICATION,
        "candidates": [asdict(item) for item in candidates],
        "candidate_count": len(eligible_rows),
        "returned_count": len(candidates),
        "returned_handoff_queue": returned_handoff_queue,
        "queue_scope": QUEUE_SCOPE,
        "skipped_session_lines": skipped_session_lines,
        "skipped_index_lines": skipped_index_lines,
        "invalid_or_missing_timestamp_count": invalid_or_missing_timestamp_count,
        "excluded_subagent_count": excluded_subagent_count,
    }


def markdown_cell(value: object) -> str:
    raw = TERMINAL_ESCAPE.sub("", str(value if value is not None else ""))
    text = " ".join(
        "".join(character for character in raw if not unicodedata.category(character).startswith("C")).split()
    )
    for character in ("\\", "|", "[", "]", "<", ">", "`"):
        text = text.replace(character, f"\\{character}")
    text = BARE_URL_SCHEME.sub(lambda match: f"{match.group(1)}\\:\\/\\/", text)
    return text


def render_markdown(report: dict) -> str:
    lines = [
        "# Codex Fluent Active Session Report",
        "",
        f"- data_classification: {report['data_classification']} (do not publish without review)",
        f"- candidate_count: {report['candidate_count']}",
        f"- returned_count: {report['returned_count']}",
        f"- queue_scope: {report['queue_scope']}",
        f"- skipped_session_lines: {report['skipped_session_lines']}",
        f"- skipped_index_lines: {report['skipped_index_lines']}",
        f"- invalid_or_missing_timestamp_count: "
        f"{report['invalid_or_missing_timestamp_count']}",
        f"- excluded_subagent_count: {report['excluded_subagent_count']}",
        "",
        "## Primary Size Ranking",
        "",
        "| primary_rank | size_bytes | age_days | compaction_count "
        "| handoff_required | thread_id | title | cwd_label | repo_root |",
        "|---:|---:|---:|---:|:---:|---|---|---|---|",
    ]
    for row in report["candidates"]:
        lines.append(
            "| {primary_rank} | {size_bytes} | {age_days} | {compaction_count} "
            "| {handoff_required} | {thread_id} | {title} | {cwd_label} "
            "| {repo_root} |".format(
                primary_rank=row["primary_rank"],
                size_bytes=row["size_bytes"],
                age_days=row["age_days"],
                compaction_count=row["compaction_count"],
                handoff_required="true" if row["handoff_required"] else "false",
                thread_id=markdown_cell(row["thread_id"]),
                title=markdown_cell(row["title"]),
                cwd_label=markdown_cell(row["cwd_label"]),
                repo_root=markdown_cell(
                    row["repo_root"] if row["repo_root"] is not None else "unknown"
                ),
            )
        )
    lines += [
        "",
        "## Returned Handoff Queue",
        "",
        "| primary_rank | compaction_count | thread_id |",
        "|---:|---:|---|",
    ]
    for item in report["returned_handoff_queue"]:
        lines.append(
            f"| {item['primary_rank']} | {item['compaction_count']} "
            f"| {markdown_cell(item['thread_id'])} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rank old active Codex sessions by transcript size (read-only).",
    )
    parser.add_argument("--codex-home", required=True, type=Path)
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown",
        dest="output_format",
    )
    # Hidden deterministic test seam. Ordinary user and automation
    # invocations must not depend on it.
    parser.add_argument("--now", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        validate_args(args.older_than_days, args.limit)
    except ValueError as exc:
        parser.error(str(exc))
    if args.now is None:
        now = datetime.now(timezone.utc)
    else:
        try:
            now = parse_iso_utc(args.now)
        except InvalidTimestamp as exc:
            parser.error(str(exc))
    try:
        report = scan_sessions(
            args.codex_home, args.older_than_days, args.limit, now
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.output_format == "json":
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
