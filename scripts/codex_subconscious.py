#!/usr/bin/env python3
"""Build a lightweight background memory layer for Codex from archived sessions."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


TIMESTAMP_FORMATS = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ")
BLOCKER_PATTERNS = (
    "operation not permitted",
    "permission denied",
    "connection refused",
    "timed out",
    "traceback",
    "error:",
    "failed",
    "blocked",
    "阻塞",
    "失败",
    "报错",
)


@dataclass
class SessionSummary:
    session_id: str
    thread_name: str
    session_path: str
    cwd: str
    project_name: str
    started_at: str
    updated_at: str
    first_user_message: str
    recent_user_messages: List[str]
    commentary_messages: List[str]
    tool_names: List[str]
    blockers: List[str]


def parse_timestamp(raw: Optional[str]) -> datetime:
    if not raw:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.fromtimestamp(0, tz=timezone.utc)


def slugify_project(cwd: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", cwd.strip("/"))
    return cleaned or "unknown-project"


def canonical_project_key(cwd: str) -> str:
    path = Path(cwd)
    parts = path.parts
    try:
        worktrees_index = parts.index("worktrees")
    except ValueError:
        return path.name or cwd
    if worktrees_index + 2 < len(parts):
        return parts[worktrees_index + 2]
    return path.name or cwd


def trim_text(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def first_text_content(content: object) -> str:
    if isinstance(content, str):
        return trim_text(content)
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "output_text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return trim_text(" ".join(parts))
    return ""


def detect_blockers(*texts: str) -> List[str]:
    hits: List[str] = []
    for text in texts:
        if not text:
            continue
        normalized = trim_text(text, limit=280)
        if "Command:" in normalized and "Process exited with code 0" in normalized:
            continue
        lower = normalized.lower()
        if any(pattern in lower for pattern in BLOCKER_PATTERNS):
            hits.append(normalized)
    return hits


def load_thread_names(session_index_path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not session_index_path.exists():
        return mapping
    with session_index_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = obj.get("id")
            thread_name = obj.get("thread_name")
            if session_id and thread_name:
                mapping[session_id] = thread_name
    return mapping


def extract_user_message(payload: dict) -> str:
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return trim_text(message)
    text_elements = payload.get("text_elements")
    if isinstance(text_elements, list):
        parts = [item for item in text_elements if isinstance(item, str) and item.strip()]
        if parts:
            return trim_text(" ".join(parts))
    return ""


def summarize_session(path: Path, thread_names: Dict[str, str]) -> Optional[SessionSummary]:
    session_meta = None
    user_messages: List[str] = []
    commentary_messages: List[str] = []
    tool_names: List[str] = []
    blockers: List[str] = []
    updated_at = ""

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            updated_at = event.get("timestamp") or updated_at
            event_type = event.get("type")
            payload = event.get("payload") or {}
            if event_type == "session_meta":
                session_meta = payload
                continue

            if event_type == "event_msg" and payload.get("type") == "user_message":
                message = extract_user_message(payload)
                if message:
                    user_messages.append(message)
                    blockers.extend(detect_blockers(message))
                continue

            if event_type == "event_msg" and payload.get("type") == "agent_message":
                message = payload.get("message")
                if isinstance(message, str) and message.strip():
                    commentary_messages.append(trim_text(message))
                    blockers.extend(detect_blockers(message))
                continue

            if event_type == "response_item" and payload.get("type") == "message":
                text = first_text_content(payload.get("content"))
                blockers.extend(detect_blockers(text))
                continue

            if event_type == "response_item" and payload.get("type") == "function_call":
                name = payload.get("name")
                if isinstance(name, str) and name:
                    tool_names.append(name)
                continue

    if not session_meta:
        return None

    session_id = session_meta.get("id")
    cwd = session_meta.get("cwd")
    started_at = session_meta.get("timestamp")
    if not session_id or not cwd or not started_at:
        return None

    project_name = Path(cwd).name or cwd
    thread_name = thread_names.get(session_id, project_name)
    first_user_message = user_messages[0] if user_messages else ""

    unique_blockers: List[str] = []
    seen = set()
    for blocker in blockers:
        if blocker not in seen:
            seen.add(blocker)
            unique_blockers.append(blocker)

    return SessionSummary(
        session_id=session_id,
        thread_name=thread_name,
        session_path=str(path),
        cwd=cwd,
        project_name=project_name,
        started_at=started_at,
        updated_at=updated_at or started_at,
        first_user_message=first_user_message,
        recent_user_messages=user_messages[:5],
        commentary_messages=commentary_messages[:5],
        tool_names=tool_names,
        blockers=unique_blockers[:5],
    )


def iter_archived_sessions(archived_sessions_dir: Path) -> Iterable[Path]:
    if not archived_sessions_dir.exists():
        return []
    return sorted(archived_sessions_dir.glob("*.jsonl"))


def build_index(codex_home: Path, state_dir: Path, max_sessions_per_project: int, emit_briefs: bool) -> dict:
    thread_names = load_thread_names(codex_home / "session_index.jsonl")
    sessions: List[SessionSummary] = []

    for session_path in iter_archived_sessions(codex_home / "archived_sessions"):
        summary = summarize_session(session_path, thread_names)
        if summary:
            sessions.append(summary)

    sessions.sort(key=lambda item: parse_timestamp(item.updated_at), reverse=True)

    grouped: Dict[str, List[SessionSummary]] = defaultdict(list)
    for session in sessions:
        grouped[canonical_project_key(session.cwd)].append(session)

    projects = []
    briefs_dir = state_dir / "briefs"
    if emit_briefs:
        briefs_dir.mkdir(parents=True, exist_ok=True)

    for project_key, project_sessions in sorted(
        grouped.items(),
        key=lambda item: parse_timestamp(item[1][0].updated_at),
        reverse=True,
    ):
        recent = project_sessions[:max_sessions_per_project]
        tool_counter = Counter(tool for session in recent for tool in session.tool_names)
        blocker_pool = []
        for session in recent:
            blocker_pool.extend(session.blockers)
        unique_blockers = []
        seen_blockers = set()
        for blocker in blocker_pool:
            if blocker not in seen_blockers:
                seen_blockers.add(blocker)
                unique_blockers.append(blocker)

        project_entry = {
            "cwd": recent[0].cwd,
            "project_name": project_key,
            "slug": slugify_project(project_key),
            "last_updated_at": recent[0].updated_at,
            "session_count": len(project_sessions),
            "related_cwds": list(dict.fromkeys(session.cwd for session in project_sessions))[:8],
            "recent_threads": [session.thread_name for session in recent],
            "recent_goals": [session.first_user_message for session in recent if session.first_user_message][:5],
            "top_tools": [{"name": name, "count": count} for name, count in tool_counter.most_common(8)],
            "recent_blockers": unique_blockers[:5],
            "sessions": [
                {
                    "session_id": session.session_id,
                    "thread_name": session.thread_name,
                    "started_at": session.started_at,
                    "updated_at": session.updated_at,
                    "first_user_message": session.first_user_message,
                    "commentary_messages": session.commentary_messages,
                    "tool_names": session.tool_names[:12],
                    "blockers": session.blockers,
                }
                for session in recent
            ],
        }
        projects.append(project_entry)

        if emit_briefs:
            brief_text = render_brief(project_entry)
            (briefs_dir / f"{project_entry['slug']}.md").write_text(brief_text, encoding="utf-8")

    index = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "codex_home": str(codex_home),
        "project_count": len(projects),
        "session_count": len(sessions),
        "projects": projects,
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (state_dir / "memory.md").write_text(render_memory(index), encoding="utf-8")
    return index


def render_brief(project: dict) -> str:
    lines = [f"# Codex Subconscious Brief: {project['project_name']}", ""]
    lines.append(f"- cwd: `{project['cwd']}`")
    lines.append(f"- last_updated_at: `{project['last_updated_at']}`")
    lines.append(f"- session_count: {project['session_count']}")
    related_cwds = project.get("related_cwds") or []
    if len(related_cwds) > 1:
        lines.append(f"- related_cwds: {len(related_cwds)}")
    lines.append("")

    goals = project.get("recent_goals") or []
    if goals:
        lines.append("## Recent Goals")
        for goal in goals:
            lines.append(f"- {goal}")
        lines.append("")

    blockers = project.get("recent_blockers") or []
    if blockers:
        lines.append("## Recurring Blockers")
        for blocker in blockers:
            lines.append(f"- {blocker}")
        lines.append("")

    tools = project.get("top_tools") or []
    if tools:
        lines.append("## Tool Pattern")
        for tool in tools[:5]:
            lines.append(f"- `{tool['name']}` x {tool['count']}")
        lines.append("")

    sessions = project.get("sessions") or []
    if sessions:
        lines.append("## Recent Sessions")
        for session in sessions[:3]:
            title = session.get("thread_name") or session.get("session_id")
            lines.append(f"- `{title}`")
            first_user_message = session.get("first_user_message")
            if first_user_message:
                lines.append(f"  first ask: {first_user_message}")
            commentary_messages = session.get("commentary_messages") or []
            if commentary_messages:
                lines.append(f"  agent note: {commentary_messages[0]}")
        lines.append("")

    lines.append("## Suggested Use")
    lines.append("- 开新会话前先读这份 brief，再决定要不要继续旧线程。")
    lines.append("- 若最近 blocker 重复出现，优先处理环境或 workflow 问题，而不是再次重复执行。")
    lines.append("")
    return "\n".join(lines)


def render_memory(index: dict) -> str:
    lines = ["# Codex Subconscious Memory", ""]
    lines.append(f"- generated_at: `{index['generated_at']}`")
    lines.append(f"- project_count: {index['project_count']}")
    lines.append(f"- session_count: {index['session_count']}")
    lines.append("")
    lines.append("## Active Projects")
    for project in index.get("projects", [])[:12]:
        lines.append(f"- `{project['project_name']}`")
        lines.append(f"  cwd: `{project['cwd']}`")
        lines.append(f"  recent_threads: {', '.join(project.get('recent_threads', [])[:3]) or 'none'}")
        blockers = project.get("recent_blockers") or []
        if blockers:
            lines.append(f"  blockers: {blockers[0]}")
    lines.append("")
    return "\n".join(lines)


def pick_project(index: dict, cwd: Optional[str]) -> dict:
    projects = index.get("projects", [])
    if not projects:
        raise SystemExit("No indexed projects found. Run the build command first.")
    if cwd:
        for project in projects:
            if project.get("cwd") == cwd or cwd in (project.get("related_cwds") or []):
                return project
        raise SystemExit(f"Project not found for cwd: {cwd}")
    return projects[0]


def pick_projects(index: dict, cwd: Optional[str], limit: int) -> List[dict]:
    projects = index.get("projects", [])
    if not projects:
        raise SystemExit("No indexed projects found. Run build first.")
    if cwd:
        return [pick_project(index, cwd)]
    return projects[: max(limit, 1)]


def load_index(state_dir: Path) -> dict:
    index_path = state_dir / "index.json"
    if not index_path.exists():
        raise SystemExit(f"Missing index file: {index_path}. Run build first.")
    return json.loads(index_path.read_text(encoding="utf-8"))


def command_build(args: argparse.Namespace) -> int:
    index = build_index(
        codex_home=args.codex_home,
        state_dir=args.state_dir,
        max_sessions_per_project=args.max_sessions_per_project,
        emit_briefs=args.emit_briefs,
    )
    print(
        json.dumps(
            {
                "generated_at": index["generated_at"],
                "project_count": index["project_count"],
                "session_count": index["session_count"],
                "state_dir": str(args.state_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


def command_brief(args: argparse.Namespace) -> int:
    index = load_index(args.state_dir)
    project = pick_project(index, args.cwd)
    brief = render_brief(project)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(brief, encoding="utf-8")
    print(brief)
    return 0


def command_publish_inbox(args: argparse.Namespace) -> int:
    index = load_index(args.state_dir)
    db_path = args.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    selected_projects = pick_projects(index, args.cwd, args.limit)
    created_items = []
    skipped_items = []
    with sqlite3.connect(db_path) as conn:
        for project in selected_projects:
            brief = render_brief(project)
            created_at_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
            item_id = f"subconscious-{uuid.uuid4().hex[:12]}"
            title = args.title or f"Codex Subconscious: {project['project_name']}"
            dedupe_cutoff_ms = created_at_ms - (args.dedupe_hours * 60 * 60 * 1000)
            existing = conn.execute(
                """
                SELECT id, created_at
                FROM inbox_items
                WHERE title = ? AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (title, dedupe_cutoff_ms),
            ).fetchone()
            if existing:
                skipped_items.append(
                    {
                        "title": title,
                        "project_name": project["project_name"],
                        "existing_id": existing[0],
                        "existing_created_at": existing[1],
                    }
                )
                continue
            conn.execute(
                """
                INSERT INTO inbox_items (id, title, description, thread_id, read_at, created_at)
                VALUES (?, ?, ?, NULL, NULL, ?)
                """,
                (item_id, title, brief, created_at_ms),
            )
            created_items.append(
                {
                    "id": item_id,
                    "title": title,
                    "created_at": created_at_ms,
                    "project_name": project["project_name"],
                    "cwd": project["cwd"],
                }
            )
        conn.commit()

    print(
        json.dumps(
            {
                "items": created_items,
                "skipped": skipped_items,
                "db_path": str(db_path),
                "dedupe_hours": args.dedupe_hours,
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    default_codex_home = Path.home() / ".codex"
    default_state_dir = default_codex_home / "subconscious"

    parser = argparse.ArgumentParser(
        description="Generate lightweight Codex subconscious memory from archived sessions."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build", help="Scan archived sessions and update memory")
    build_parser_.add_argument("--codex-home", type=Path, default=default_codex_home)
    build_parser_.add_argument("--state-dir", type=Path, default=default_state_dir)
    build_parser_.add_argument("--max-sessions-per-project", type=int, default=5)
    build_parser_.add_argument(
        "--emit-briefs",
        action="store_true",
        help="Also write per-project brief files under the state directory.",
    )
    build_parser_.set_defaults(func=command_build)

    brief_parser = subparsers.add_parser("brief", help="Render a briefing for one project")
    brief_parser.add_argument("--state-dir", type=Path, default=default_state_dir)
    brief_parser.add_argument("--cwd", type=str, default=None, help="Target project cwd")
    brief_parser.add_argument("--output", type=Path, default=None)
    brief_parser.set_defaults(func=command_brief)

    inbox_parser = subparsers.add_parser("publish-inbox", help="Publish a project brief into Codex inbox")
    inbox_parser.add_argument("--state-dir", type=Path, default=default_state_dir)
    inbox_parser.add_argument("--cwd", type=str, default=None, help="Target project cwd")
    inbox_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_codex_home / "sqlite" / "codex-dev.db",
        help="Path to the Codex inbox sqlite database.",
    )
    inbox_parser.add_argument("--title", type=str, default=None)
    inbox_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of most recently active projects to publish when --cwd is omitted.",
    )
    inbox_parser.add_argument(
        "--dedupe-hours",
        type=int,
        default=8,
        help="Skip publishing if an inbox item with the same title already exists within this many hours.",
    )
    inbox_parser.set_defaults(func=command_publish_inbox)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
