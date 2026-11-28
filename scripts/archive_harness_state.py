#!/usr/bin/env python3
"""Plan or apply harness-state State Log archive moves with sha256/count parity.

Default mode (``--dry-run --verify-only``) only reports the plan. ``--apply``
moves the oldest entries verbatim into ``docs/harness-state-archive/YYYY-MM.md`` (appending when a month file already exists), removes them from the active
file, and refreshes the ``Archived State Log Entries`` pointer table, creating it
before ``## State Log`` on the first move.

Ported from ShipQ ``scripts/archive_harness_state.py``. MyCodexEnv entry headings
are a bare timestamp (``### 2026-05-11T15:07:21-04:00``), so the `` - summary``
suffix is optional here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


STATE_LOG_MARKER = "## State Log"
POINTER_SECTION_MARKER = "## Archived State Log Entries"
ENTRY_HEADING_RE = re.compile(
    r"^###\s+(?P<year>\d{4})-(?P<month>\d{2})-\d{2}(?:[T\s]\S*)?(?:\s+-\s+.+)?\s*$"
)
ENTRY_START_RE = re.compile(r"(?m)^###\s+")
POINTER_ROW_RE = re.compile(r"^\|\s*(?P<month>\d{4}-\d{2})\s*\|.*\|\s*$")


class ArchivePlanError(RuntimeError):
    """Raised when harness-state cannot be safely planned for archive."""


@dataclass(frozen=True)
class StateEntry:
    heading: str
    text: str
    month: str
    start: int


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_state_path(repo_root: Path, state_path: Path) -> tuple[Path, Path]:
    repo_root = repo_root.resolve()
    resolved_state = state_path if state_path.is_absolute() else repo_root / state_path
    resolved_state = resolved_state.resolve()
    try:
        resolved_state.relative_to(repo_root)
    except ValueError as exc:
        raise ArchivePlanError(f"state path must stay within repo root: {resolved_state}") from exc
    if not resolved_state.exists():
        raise ArchivePlanError(f"missing state path: {resolved_state}")
    if not resolved_state.is_file():
        raise ArchivePlanError(f"state path must be a file: {resolved_state}")
    return repo_root, resolved_state


def _normalize_entry_text(segment: str) -> str:
    return segment.strip("\n") + "\n"


def _parse_entries(state_text: str) -> tuple[int, list[StateEntry]]:
    """Return the log-body offset and parsed entries (start offsets are relative to state_text)."""
    marker_index = state_text.find(STATE_LOG_MARKER)
    if marker_index == -1:
        raise ArchivePlanError(f"state file is missing {STATE_LOG_MARKER} marker")
    body_offset = marker_index + len(STATE_LOG_MARKER)
    log_body = state_text[body_offset:]
    starts = [match.start() for match in ENTRY_START_RE.finditer(log_body)]
    if not starts:
        raise ArchivePlanError("State Log has no entries")
    preamble = log_body[: starts[0]]
    if preamble.strip():
        raise ArchivePlanError("unexpected text before first State Log entry")

    entries: list[StateEntry] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(log_body)
        text = _normalize_entry_text(log_body[start:end])
        heading = text.splitlines()[0]
        match = ENTRY_HEADING_RE.match(heading)
        if match is None:
            raise ArchivePlanError(f"malformed State Log entry heading: {heading}")
        month = f"{match.group('year')}-{match.group('month')}"
        entries.append(
            StateEntry(heading=heading, text=text, month=month, start=body_offset + start)
        )
    return body_offset, entries


def _archive_path(repo_root: Path, archive_dir: Path, month: str) -> Path:
    resolved_dir = archive_dir if archive_dir.is_absolute() else repo_root / archive_dir
    return (resolved_dir / f"{month}.md").resolve()


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def build_archive_plan(
    repo_root: Path,
    state_path: Path,
    *,
    archive_dir: Path,
    keep_latest: int,
) -> dict:
    if keep_latest < 1:
        raise ArchivePlanError("keep-latest must be at least 1")
    repo_root, state_path = _resolve_state_path(repo_root, state_path)
    state_text = state_path.read_text(encoding="utf-8")
    _, entries = _parse_entries(state_text)
    entries_to_move = entries[:-keep_latest] if len(entries) > keep_latest else []
    entries_to_keep = entries[-keep_latest:] if len(entries) > keep_latest else entries

    grouped: OrderedDict[str, list[StateEntry]] = OrderedDict()
    for entry in entries_to_move:
        grouped.setdefault(entry.month, []).append(entry)

    archive_plan = []
    archive_text_parts: list[str] = []
    for month, month_entries in grouped.items():
        content = "".join(entry.text for entry in month_entries)
        archive_text_parts.append(content)
        path = _archive_path(repo_root, archive_dir, month)
        archive_plan.append(
            {
                "month": month,
                "archive_path": _relative(path, repo_root),
                "archive_exists": path.exists(),
                "entry_count": len(month_entries),
                "source_sha256": _sha256_text(content),
                "archive_sha256": _sha256_text(content),
                "first_heading": month_entries[0].heading,
                "last_heading": month_entries[-1].heading,
            }
        )

    moved_text = "".join(entry.text for entry in entries_to_move)
    archive_text = "".join(archive_text_parts)
    latest_heading = entries_to_keep[-1].heading if entries_to_keep else ""

    return {
        "schema_version": 1,
        "status": "ok",
        "dry_run": True,
        "verify_only": True,
        "repo_root": str(repo_root),
        "state_path": str(state_path),
        "state_line_count": len(state_text.splitlines()),
        "entry_count": len(entries),
        "entries_to_move_count": len(entries_to_move),
        "entries_to_keep_count": len(entries_to_keep),
        "archive_plan": archive_plan,
        "pointer_line_count": len(archive_plan),
        "source_sha256": _sha256_text(moved_text) if moved_text else "",
        "archive_sha256": _sha256_text(archive_text) if archive_text else "",
        "latest_entry_heading": latest_heading,
        "timestamp": _timestamp(),
    }


def _atomic_write(path: Path, text: str, *, mode: int | None) -> None:
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(text, encoding="utf-8")
        if tmp_path.read_text(encoding="utf-8") != text:
            raise ArchivePlanError(f"temp file readback mismatch: {tmp_path}")
        if mode is not None:
            os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def _pointer_row(month: str, archive_path: Path, entry_count: int, sha256: str, state_path: Path) -> str:
    # Both paths absolute: a repo-relative path would be resolved against the cwd.
    link = Path(os.path.relpath(archive_path, start=state_path.parent)).as_posix()
    return f"| {month} | [{link}]({link}) | {entry_count} | `{sha256}` |"


def _update_pointer_table(head_text: str, rows: dict[str, str]) -> str:
    """Replace or insert month rows in the Archived State Log Entries table, keeping months sorted."""
    section_index = head_text.find(POINTER_SECTION_MARKER)
    if section_index == -1:
        table = "".join(rows[month] + "\n" for month in sorted(rows))
        return (
            head_text.rstrip("\n")
            + "\n\n"
            + POINTER_SECTION_MARKER
            + "\n\n"
            + "Older entries were moved verbatim by `scripts/archive_harness_state.py`.\n\n"
            + "| Month | Archive | Entries | sha256 |\n"
            + "| --- | --- | --- | --- |\n"
            + table
        )
    lines = head_text.splitlines(keepends=True)
    table_rows: list[int] = []
    in_section = False
    for index, line in enumerate(lines):
        if line.startswith(POINTER_SECTION_MARKER):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and POINTER_ROW_RE.match(line.rstrip("\n")):
            table_rows.append(index)
    if not table_rows:
        raise ArchivePlanError("Archived State Log Entries table has no month rows")

    existing: dict[str, str] = {}
    for index in table_rows:
        month = POINTER_ROW_RE.match(lines[index].rstrip("\n")).group("month")
        existing[month] = lines[index].rstrip("\n")
    existing.update(rows)
    ordered = [existing[month] + "\n" for month in sorted(existing)]
    first, last = table_rows[0], table_rows[-1]
    return "".join(lines[:first]) + "".join(ordered) + "".join(lines[last + 1 :])


def apply_archive_plan(
    repo_root: Path,
    state_path: Path,
    *,
    archive_dir: Path,
    keep_latest: int,
) -> dict:
    plan = build_archive_plan(repo_root, state_path, archive_dir=archive_dir, keep_latest=keep_latest)
    repo_root, state_path = _resolve_state_path(repo_root, state_path)
    state_text = state_path.read_text(encoding="utf-8")
    state_sha_before = _sha256_text(state_text)
    body_offset, entries = _parse_entries(state_text)
    entries_to_move = entries[:-keep_latest] if len(entries) > keep_latest else []
    if not entries_to_move:
        plan.update(
            {
                "dry_run": False,
                "verify_only": False,
                "applied": False,
                "state_sha256_before": state_sha_before,
                "state_sha256_after": state_sha_before,
            }
        )
        return plan

    grouped: OrderedDict[str, list[StateEntry]] = OrderedDict()
    for entry in entries_to_move:
        grouped.setdefault(entry.month, []).append(entry)

    # Validate every archive target before writing anything.
    pending: list[tuple[Path, str, int | None, str]] = []
    for month, month_entries in grouped.items():
        path = _archive_path(repo_root, archive_dir, month)
        content = "".join(entry.text for entry in month_entries)
        mode: int | None = None
        if path.exists():
            if not path.is_file():
                raise ArchivePlanError(f"archive path must be a file: {path}")
            existing_text = path.read_text(encoding="utf-8")
            if existing_text and not existing_text.endswith("\n"):
                raise ArchivePlanError(f"archive file does not end with newline: {path}")
            for entry in month_entries:
                if entry.heading + "\n" in existing_text:
                    raise ArchivePlanError(
                        f"archive already contains entry, refusing duplicate move: {entry.heading}"
                    )
            mode = stat.S_IMODE(path.stat().st_mode)
            new_text = existing_text + content
        else:
            new_text = content
        pending.append((path, new_text, mode, month))

    first_kept = entries[-keep_latest]
    marker_index = state_text.find(STATE_LOG_MARKER)
    head_text = state_text[:marker_index]
    kept_body = state_text[first_kept.start :]
    rows: dict[str, str] = {}
    applied_archives = []
    for path, new_text, _, month in pending:
        entry_count = len(ENTRY_START_RE.findall(new_text))
        sha = _sha256_text(new_text)
        rows[month] = _pointer_row(month, path, entry_count, sha, state_path)
        applied_archives.append(
            {
                "month": month,
                "archive_path": _relative(path, repo_root),
                "appended_entries": len(grouped[month]),
                "archive_entry_count_after": entry_count,
                "archive_file_sha256_after": sha,
            }
        )
    new_head = _update_pointer_table(head_text, rows)
    new_state_text = new_head.rstrip("\n") + "\n\n" + STATE_LOG_MARKER + "\n\n" + kept_body.lstrip("\n")

    # Parity: kept entries must be byte-identical to the original tail.
    _, new_entries = _parse_entries(new_state_text)
    if [entry.text for entry in new_entries] != [entry.text for entry in entries[-keep_latest:]]:
        raise ArchivePlanError("kept State Log entries would change during archive move")

    state_mode = stat.S_IMODE(state_path.stat().st_mode)
    archive_root = _archive_path(repo_root, archive_dir, "x").parent
    archive_root.mkdir(parents=True, exist_ok=True)
    # Roll back on any failure, so a retry starts from the original files instead
    # of meeting archive copies of entries that are still in the active log.
    originals: list[tuple[Path, str | None, int | None]] = [
        (path, path.read_text(encoding="utf-8") if path.exists() else None, mode)
        for path, _, mode, _ in pending
    ]
    written: list[tuple[Path, str | None, int | None]] = []
    try:
        for (path, new_text, mode, _), original in zip(pending, originals):
            _atomic_write(path, new_text, mode=mode)
            written.append(original)
        _atomic_write(state_path, new_state_text, mode=state_mode)
    except Exception:
        for path, original_text, mode in reversed(written):
            if original_text is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, original_text, mode=mode)
        raise

    plan.update(
        {
            "dry_run": False,
            "verify_only": False,
            "applied": True,
            "applied_archives": applied_archives,
            "state_sha256_before": state_sha_before,
            "state_sha256_after": _sha256_text(new_state_text),
            "state_line_count_after": len(new_state_text.splitlines()),
        }
    )
    return plan


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--state-path",
        type=Path,
        default=Path("docs") / "harness-state.md",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=Path("docs") / "harness-state-archive",
    )
    parser.add_argument("--keep-latest", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="move entries verbatim into monthly archive files and refresh the pointer table",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    return parser.parse_args(argv)


def _emit_failure(error: str, *, as_json: bool) -> int:
    if as_json:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "failed",
                    "error": error,
                    "timestamp": _timestamp(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(error, file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply and (args.dry_run or args.verify_only):
        return _emit_failure("--apply cannot be combined with --dry-run/--verify-only", as_json=args.json)
    if not args.apply and not (args.dry_run and args.verify_only):
        return _emit_failure("only dry-run verify-only mode is supported", as_json=args.json)
    try:
        if args.apply:
            result = apply_archive_plan(
                args.repo_root,
                args.state_path,
                archive_dir=args.archive_dir,
                keep_latest=args.keep_latest,
            )
        else:
            result = build_archive_plan(
                args.repo_root,
                args.state_path,
                archive_dir=args.archive_dir,
                keep_latest=args.keep_latest,
            )
    except ArchivePlanError as exc:
        return _emit_failure(str(exc), as_json=args.json)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("status=ok")
        print("mode=apply" if args.apply else "mode=dry-run verify-only")
        print(f"entries={result['entry_count']}")
        print(f"entries_to_move={result['entries_to_move_count']}")
        print(f"entries_to_keep={result['entries_to_keep_count']}")
        print(f"pointer_line_count={result['pointer_line_count']}")
        print(f"source_sha256={result['source_sha256']}")
        print(f"archive_sha256={result['archive_sha256']}")
        for archive in result["archive_plan"]:
            print(
                "archive_plan="
                f"{archive['month']} "
                f"entries={archive['entry_count']} "
                f"path={archive['archive_path']} "
                f"sha256={archive['archive_sha256']}"
            )
        for archive in result.get("applied_archives", []):
            print(
                "applied="
                f"{archive['month']} "
                f"appended={archive['appended_entries']} "
                f"total={archive['archive_entry_count_after']} "
                f"file_sha256={archive['archive_file_sha256_after']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
