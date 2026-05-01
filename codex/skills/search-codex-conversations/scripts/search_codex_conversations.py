#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Iterable


LOCAL_TZ = datetime.now().astimezone().tzinfo
CODEX_HOME = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
STATE_DB = CODEX_HOME / "state_5.sqlite"
SESSIONS_DIR = CODEX_HOME / "sessions"
ARCHIVED_DIR = CODEX_HOME / "archived_sessions"


@dataclass(frozen=True)
class ThreadMeta:
    thread_id: str
    title: str
    rollout_path: Path
    created_at: int
    updated_at: int
    archived: bool
    cwd: str


@dataclass(frozen=True)
class MatchHit:
    kind: str
    text: str
    role: str | None = None
    line_no: int | None = None
    timestamp: str | None = None


@dataclass(frozen=True)
class ThreadResult:
    meta: ThreadMeta
    hits: tuple[MatchHit, ...]
    score: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search local Codex conversation history by keyword. "
            "Reads thread metadata from ~/.codex/state_5.sqlite and message "
            "content from rollout JSONL files."
        )
    )
    parser.add_argument(
        "terms",
        nargs="+",
        help="One or more keywords or quoted phrases. Default is AND matching.",
    )
    parser.add_argument(
        "--any",
        action="store_true",
        help="Use OR matching instead of the default AND matching.",
    )
    parser.add_argument(
        "--scope",
        choices=("title", "message", "both"),
        default="both",
        help="Search thread titles, message bodies, or both. Default: both.",
    )
    parser.add_argument(
        "--role",
        default="user,assistant",
        help=(
            "Comma-separated message roles for message search. "
            "Use 'all' for every role. Default: user,assistant."
        ),
    )
    parser.add_argument(
        "--archived",
        choices=("include", "only", "exclude"),
        default="include",
        help="Whether to include archived threads. Default: include.",
    )
    parser.add_argument(
        "--after",
        help="Only include threads updated on or after this date/time (YYYY-MM-DD or ISO datetime).",
    )
    parser.add_argument(
        "--before",
        help="Only include threads updated on or before this date/time (YYYY-MM-DD or ISO datetime).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of threads to show. Default: 10.",
    )
    parser.add_argument(
        "--snippets",
        type=int,
        default=2,
        help="Maximum message hits to keep per thread. Default: 2.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of human-readable text.",
    )
    return parser.parse_args()


def parse_roles(raw: str) -> set[str] | None:
    if raw.strip().lower() == "all":
        return None
    roles = {part.strip() for part in raw.split(",") if part.strip()}
    if not roles:
        raise SystemExit("--role must contain at least one role or 'all'.")
    return roles


def parse_when(raw: str, *, end_of_day: bool) -> int:
    raw = raw.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
        is_date_only = "T" not in raw and " " not in raw
    except ValueError as exc:
        raise SystemExit(f"Invalid date/time: {raw}") from exc

    if is_date_only:
        day = dt.date()
        dt = datetime.combine(day, time.max if end_of_day else time.min)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return int(dt.timestamp())


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def match_text(text: str, terms: list[str], any_mode: bool) -> bool:
    haystack = text.casefold()
    checks = [term.casefold() in haystack for term in terms]
    return any(checks) if any_mode else all(checks)


def snippet_for(text: str, terms: list[str], width: int = 180) -> str:
    compact = normalize_space(text)
    if not compact:
        return ""

    lowered = compact.casefold()
    positions = [lowered.find(term.casefold()) for term in terms]
    positions = [pos for pos in positions if pos >= 0]
    if not positions:
        return compact[:width]

    start = max(min(positions) - width // 3, 0)
    end = min(start + width, len(compact))
    piece = compact[start:end]
    if start > 0:
        piece = "..." + piece
    if end < len(compact):
        piece = piece + "..."
    return piece


def clip_text(text: str, width: int = 140) -> str:
    compact = normalize_space(text)
    if len(compact) <= width:
        return compact
    return compact[: width - 3] + "..."


def load_threads(after_ts: int | None, before_ts: int | None, archived_mode: str) -> list[ThreadMeta]:
    if not STATE_DB.exists():
        raise SystemExit(f"Missing state database: {STATE_DB}")

    query = """
        SELECT id, title, rollout_path, created_at, updated_at, archived, cwd
        FROM threads
        ORDER BY updated_at DESC
    """
    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query).fetchall()
    finally:
        conn.close()

    threads: list[ThreadMeta] = []
    for row in rows:
        archived = bool(row["archived"])
        if archived_mode == "only" and not archived:
            continue
        if archived_mode == "exclude" and archived:
            continue
        updated_at = int(row["updated_at"])
        if after_ts is not None and updated_at < after_ts:
            continue
        if before_ts is not None and updated_at > before_ts:
            continue

        rollout_path = Path(row["rollout_path"])
        if not rollout_path.exists():
            continue
        threads.append(
            ThreadMeta(
                thread_id=row["id"],
                title=row["title"] or "",
                rollout_path=rollout_path,
                created_at=int(row["created_at"]),
                updated_at=updated_at,
                archived=archived,
                cwd=row["cwd"] or "",
            )
        )
    return threads


def rg_candidates(
    threads: Iterable[ThreadMeta],
    terms: list[str],
    any_mode: bool,
) -> set[Path] | None:
    if shutil.which("rg") is None:
        return None

    allowed = {thread.rollout_path.resolve() for thread in threads}
    if not allowed:
        return set()

    search_roots = [str(SESSIONS_DIR), str(ARCHIVED_DIR)]
    matched: set[Path] | None = None

    for term in terms:
        cmd = [
            "rg",
            "-i",
            "-F",
            "-l",
            "--max-count",
            "1",
            "--glob",
            "*.jsonl",
            "--",
            term,
            *search_roots,
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        paths = {
            Path(line).resolve()
            for line in completed.stdout.splitlines()
            if line.strip()
        }
        paths &= allowed

        if any_mode:
            matched = (matched or set()) | paths
        else:
            matched = paths if matched is None else matched & paths

    return matched or set()


def extract_text(content: list[dict[str, object]]) -> str:
    parts: list[str] = []
    for item in content:
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n".join(parts)


def message_hits(
    thread: ThreadMeta,
    terms: list[str],
    any_mode: bool,
    roles: set[str] | None,
    limit: int,
) -> list[MatchHit]:
    hits: list[MatchHit] = []
    with thread.rollout_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") != "response_item":
                continue

            payload = obj.get("payload") or {}
            if payload.get("type") != "message":
                continue

            role = payload.get("role")
            if roles is not None and role not in roles:
                continue

            content = payload.get("content")
            if not isinstance(content, list):
                continue

            text = extract_text(content)
            if not text or not match_text(text, terms, any_mode):
                continue

            hits.append(
                MatchHit(
                    kind="message",
                    role=str(role) if role is not None else None,
                    line_no=line_no,
                    timestamp=obj.get("timestamp"),
                    text=snippet_for(text, terms),
                )
            )
            if len(hits) >= limit:
                break
    return hits


def search_threads(args: argparse.Namespace) -> list[ThreadResult]:
    after_ts = parse_when(args.after, end_of_day=False) if args.after else None
    before_ts = parse_when(args.before, end_of_day=True) if args.before else None
    roles = parse_roles(args.role)
    threads = load_threads(after_ts, before_ts, args.archived)

    title_hits: dict[str, list[MatchHit]] = {}
    if args.scope in ("title", "both"):
        for thread in threads:
            if match_text(thread.title, args.terms, args.any):
                title_hits[thread.thread_id] = [MatchHit(kind="title", text=normalize_space(thread.title))]

    message_candidates: set[Path] | None = set()
    if args.scope in ("message", "both"):
        message_candidates = rg_candidates(threads, args.terms, args.any)
        if message_candidates is None:
            message_candidates = {thread.rollout_path.resolve() for thread in threads}

    results: list[ThreadResult] = []
    for thread in threads:
        hits = list(title_hits.get(thread.thread_id, []))
        if (
            args.scope in ("message", "both")
            and message_candidates is not None
            and thread.rollout_path.resolve() in message_candidates
        ):
            hits.extend(message_hits(thread, args.terms, args.any, roles, args.snippets))

        if not hits:
            continue

        score = sum(5 if hit.kind == "title" else 1 for hit in hits)
        results.append(ThreadResult(meta=thread, hits=tuple(hits), score=score))

    results.sort(key=lambda item: (item.score, item.meta.updated_at), reverse=True)
    return results[: args.limit]


def format_ts(epoch_seconds: int) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=LOCAL_TZ).isoformat(timespec="seconds")


def to_json(results: list[ThreadResult], args: argparse.Namespace) -> str:
    payload = {
        "query": args.terms,
        "match_mode": "any" if args.any else "all",
        "scope": args.scope,
        "role": args.role,
        "archived": args.archived,
        "results": [
            {
                "thread_id": result.meta.thread_id,
                "title": result.meta.title,
                "updated_at": format_ts(result.meta.updated_at),
                "archived": result.meta.archived,
                "cwd": result.meta.cwd,
                "rollout_path": str(result.meta.rollout_path),
                "score": result.score,
                "hits": [
                    {
                        "kind": hit.kind,
                        "role": hit.role,
                        "timestamp": hit.timestamp,
                        "line_no": hit.line_no,
                        "text": hit.text,
                    }
                    for hit in result.hits
                ],
            }
            for result in results
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def to_text(results: list[ThreadResult], args: argparse.Namespace) -> str:
    if not results:
        return "No matching local Codex conversations found."

    lines = [
        (
            f"Found {len(results)} matching thread(s) for "
            f"{' OR '.join(args.terms) if args.any else ' AND '.join(args.terms)}."
        )
    ]
    for index, result in enumerate(results, 1):
        meta = result.meta
        title_preview = clip_text(meta.title)
        lines.append("")
        lines.append(
            f"[{index}] {title_preview} "
            f"(updated {format_ts(meta.updated_at)}, archived={'yes' if meta.archived else 'no'})"
        )
        lines.append(f"id: {meta.thread_id}")
        lines.append(f"cwd: {meta.cwd}")
        lines.append(f"path: {meta.rollout_path}")
        for hit in result.hits:
            if hit.kind == "title":
                lines.append(f"- title: {snippet_for(hit.text, args.terms)}")
            else:
                prefix = f"- {hit.role or 'unknown'}"
                if hit.timestamp:
                    prefix += f" @ {hit.timestamp}"
                if hit.line_no is not None:
                    prefix += f" (line {hit.line_no})"
                lines.append(f"{prefix}: {hit.text}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    results = search_threads(args)
    output = to_json(results, args) if args.json else to_text(results, args)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
