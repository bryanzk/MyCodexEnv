#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from harness_requirements import parse_sections, validate_requirements


CHECKLIST_RE = re.compile(r"^- \[[ xX]\]\s+(.+?)\s*$")
STEP_RE = re.compile(r"^\s+-\s+(.+?)\s*$")


def canonical_bodies(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bodies: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        description = entry.get("description")
        steps = entry.get("steps")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"entry {index} description must be non-empty")
        if not isinstance(steps, list) or not all(isinstance(step, str) and step.strip() for step in steps):
            raise ValueError(f"entry {index} steps must be a list of non-empty strings")
        bodies.append({"description": description, "steps": steps})
    return bodies


def content_sha256(entries: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        canonical_bodies(entries),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def acceptance_entries(path: Path) -> list[dict[str, Any]]:
    sections = parse_sections(path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in sections.get("Acceptance Criteria", []):
        criterion = CHECKLIST_RE.match(line)
        if criterion:
            current = {
                "id": f"AC{len(entries) + 1:03d}",
                "description": criterion.group(1),
                "steps": [],
                "passes": False,
                "verification": None,
            }
            entries.append(current)
            continue
        step = STEP_RE.match(line)
        if current is not None and step:
            current["steps"].append(step.group(1))
    if not entries:
        raise ValueError("requirements artifact has no checklist acceptance criteria")
    return entries


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"ledger not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"ledger read failed: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("ledger root must be an object")
    return data


def validate_ledger(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("ledger schema_version must be 1")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("ledger entries must be a non-empty list")
    expected_ids = [f"AC{index:03d}" for index in range(1, len(entries) + 1)]
    actual_ids = [entry.get("id") if isinstance(entry, dict) else None for entry in entries]
    if actual_ids != expected_ids:
        raise ValueError("ledger entry ids must be contiguous and ordered")
    actual_hash = data.get("content_sha256")
    expected_hash = content_sha256(entries)
    if actual_hash != expected_hash:
        raise ValueError("content hash mismatch")
    for entry in entries:
        if not isinstance(entry.get("passes"), bool):
            raise ValueError(f"entry {entry['id']} passes must be boolean")
        verification = entry.get("verification")
        if entry["passes"]:
            if not isinstance(verification, dict):
                raise ValueError(f"entry {entry['id']} passed without verification")
            if set(verification) != {"command", "exit_code", "key_output", "timestamp"}:
                raise ValueError(f"entry {entry['id']} verification fields are incomplete")


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def cmd_init(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    errors = validate_requirements(source)
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1
    try:
        entries = acceptance_entries(source)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    source_bytes = source.read_bytes()
    ledger = {
        "schema_version": 1,
        "source": str(source),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "content_sha256": content_sha256(entries),
        "entries": entries,
    }
    target = Path(args.ledger).expanduser()
    if target.exists():
        try:
            existing = load_ledger(target)
            validate_ledger(existing)
        except ValueError as exc:
            print(f"ERROR: existing ledger is invalid: {exc}", file=sys.stderr)
            return 1
        if existing == ledger:
            print(f"unchanged {target}")
            return 0
        print(f"ERROR: existing ledger differs: {target}", file=sys.stderr)
        return 1
    try:
        atomic_write(target, ledger)
    except OSError as exc:
        print(f"ERROR: ledger write failed: {exc}", file=sys.stderr)
        return 1
    print(target)
    return 0


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def cmd_pass(args: argparse.Namespace) -> int:
    required = {
        "verification-command": args.verification_command,
        "exit-code": args.exit_code,
        "key-output": args.key_output,
        "timestamp": args.timestamp,
    }
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        print("ERROR: missing verification fields: " + ", ".join(missing), file=sys.stderr)
        return 1
    if args.exit_code != 0:
        print("ERROR: pass requires exit-code 0", file=sys.stderr)
        return 1
    if not valid_timestamp(args.timestamp):
        print("ERROR: timestamp must be ISO-8601", file=sys.stderr)
        return 1
    target = Path(args.ledger).expanduser()
    try:
        ledger = load_ledger(target)
        validate_ledger(ledger)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    entry = next((item for item in ledger["entries"] if item["id"] == args.entry_id), None)
    if entry is None:
        print(f"ERROR: ledger entry not found: {args.entry_id}", file=sys.stderr)
        return 1
    receipt = {
        "command": args.verification_command,
        "exit_code": args.exit_code,
        "key_output": args.key_output,
        "timestamp": args.timestamp,
    }
    if entry["passes"]:
        if entry.get("verification") == receipt:
            print(f"unchanged {args.entry_id}")
            return 0
        print(f"ERROR: ledger entry already passed: {args.entry_id}", file=sys.stderr)
        return 1
    entry["passes"] = True
    entry["verification"] = receipt
    try:
        atomic_write(target, ledger)
    except OSError as exc:
        print(f"ERROR: ledger write failed: {exc}", file=sys.stderr)
        return 1
    print(f"passed {args.entry_id}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    target = Path(args.ledger).expanduser()
    try:
        ledger = load_ledger(target)
        validate_ledger(ledger)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"valid entries={len(ledger['entries'])} hash={ledger['content_sha256']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Tamper-evident Harness task ledger")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    init_parser = subparsers.add_parser("init", help="Create a ledger from validated requirements")
    init_parser.add_argument("--from", dest="source", required=True)
    init_parser.add_argument("--ledger", default="ledger.json")
    init_parser.set_defaults(func=cmd_init)

    pass_parser = subparsers.add_parser("pass", help="Mark exactly one ledger entry passed")
    pass_parser.add_argument("--ledger", default="ledger.json")
    pass_parser.add_argument("--id", dest="entry_id", required=True)
    pass_parser.add_argument("--verification-command")
    pass_parser.add_argument("--exit-code", type=int)
    pass_parser.add_argument("--key-output")
    pass_parser.add_argument("--timestamp")
    pass_parser.set_defaults(func=cmd_pass)

    verify_parser = subparsers.add_parser("verify", help="Verify immutable entry bodies")
    verify_parser.add_argument("--ledger", default="ledger.json")
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
