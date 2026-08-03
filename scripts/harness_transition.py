#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_store() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    return codex_home / "harness" / "transitions.jsonl"


def valid_record(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == 1
        and isinstance(value.get("key"), str)
        and bool(value["key"])
        and isinstance(value.get("task_id"), str)
        and bool(value["task_id"])
        and isinstance(value.get("timestamp"), str)
        and bool(value["timestamp"])
    )


def read_first_records(path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    if not path.exists():
        return {}, 0
    first: dict[str, dict[str, Any]] = {}
    malformed_count = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RuntimeError(f"cannot read transition store: {exc}") from exc
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed_count += 1
            continue
        if not valid_record(record):
            malformed_count += 1
            continue
        first.setdefault(record["key"], record)
    return first, malformed_count


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def validate_identifier(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if len(value.encode("utf-8")) > 512:
        raise ValueError(f"{name} must be at most 512 bytes")


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            raise OSError(f"short append: wrote {written} of {len(encoded)} bytes")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def command_query(args: argparse.Namespace) -> int:
    try:
        validate_identifier("key", args.key)
        first, malformed_count = read_first_records(args.store)
    except (RuntimeError, ValueError) as exc:
        emit({"status": "error", "message": str(exc)})
        return 2
    record = first.get(args.key)
    if record is None:
        emit({"status": "not_found", "key": args.key, "malformed_count": malformed_count})
        return 0
    emit({"status": "found", "record": record, "malformed_count": malformed_count})
    return 0


def command_record(args: argparse.Namespace) -> int:
    try:
        validate_identifier("key", args.key)
        validate_identifier("task-id", args.task_id)
        first, malformed_count = read_first_records(args.store)
        prior = first.get(args.key)
        if prior is not None:
            if prior["task_id"] == args.task_id:
                emit({"status": "existing", "record": prior, "malformed_count": malformed_count})
                return 0
            emit({"status": "conflict", "record": prior, "malformed_count": malformed_count})
            return 1

        candidate = {
            "schema_version": 1,
            "key": args.key,
            "task_id": args.task_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        }
        append_record(args.store, candidate)
        first, malformed_count = read_first_records(args.store)
    except (OSError, RuntimeError, ValueError) as exc:
        emit({"status": "error", "message": str(exc)})
        return 2

    winner = first.get(args.key)
    if winner is None:
        emit({"status": "error", "message": "appended record missing after reread"})
        return 2
    if winner["task_id"] != args.task_id:
        emit({"status": "conflict", "record": winner, "malformed_count": malformed_count})
        return 1
    emit({"status": "recorded", "record": winner, "malformed_count": malformed_count})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append-only Harness transition idempotency store")
    subparsers = parser.add_subparsers(dest="command", required=True)

    query_parser = subparsers.add_parser("query", help="Query the first record for one transition key")
    query_parser.add_argument("--store", type=Path, default=default_store())
    query_parser.add_argument("--key", required=True)
    query_parser.set_defaults(func=command_query)

    record_parser = subparsers.add_parser("record", help="CAS-record one task id for a transition key")
    record_parser.add_argument("--store", type=Path, default=default_store())
    record_parser.add_argument("--key", required=True)
    record_parser.add_argument("--task-id", required=True)
    record_parser.set_defaults(func=command_record)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
