#!/usr/bin/env python3
"""Compare a pinned DHF core snapshot with a source checkout and consumer copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RELEASE_RE = re.compile(r"^dhf-core-v\d{4}\.\d{2}\.\d{2}\.\d+$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


class ManifestError(ValueError):
    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.path = path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError("invalid_manifest", "path must be a non-empty string", path)
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or ".." in value.split("/")
        or "." in value.split("/")
        or "\\" in value
        or value != candidate.as_posix()
    ):
        raise ManifestError("unsafe_path", "path must be a normalized relative POSIX path", path)
    return value


def resolves_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError("manifest_read_failed", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ManifestError("manifest_json_invalid", f"line {exc.lineno} column {exc.colno}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ManifestError("invalid_manifest", "manifest must be a JSON object")
    if data.get("manifest_version") != 1:
        raise ManifestError("invalid_manifest", "manifest_version must be 1", "$.manifest_version")
    if not isinstance(data.get("consumer"), str) or not data["consumer"].strip():
        raise ManifestError("invalid_manifest", "consumer must be a non-empty string", "$.consumer")

    pin = data.get("pin")
    if not isinstance(pin, dict):
        raise ManifestError("invalid_manifest", "pin must be an object", "$.pin")
    kind = pin.get("kind")
    if kind not in {"bootstrap_snapshot", "release"}:
        raise ManifestError("invalid_manifest", "pin.kind must be bootstrap_snapshot or release", "$.pin.kind")
    if not isinstance(pin.get("packet_schema_version"), int) or isinstance(pin.get("packet_schema_version"), bool) or pin["packet_schema_version"] < 1:
        raise ManifestError("invalid_manifest", "packet_schema_version must be a positive integer", "$.pin.packet_schema_version")
    if kind == "release":
        if not isinstance(pin.get("release"), str) or not RELEASE_RE.fullmatch(pin["release"]):
            raise ManifestError("invalid_manifest", "release pin must match dhf-core-vYYYY.MM.DD.N", "$.pin.release")
        if not isinstance(pin.get("source_revision"), str) or not REVISION_RE.fullmatch(pin["source_revision"]):
            raise ManifestError("invalid_manifest", "release source_revision must be a 40-character lowercase Git hash", "$.pin.source_revision")
    elif pin.get("release") is not None or pin.get("source_revision") is not None:
        raise ManifestError("invalid_manifest", "bootstrap snapshot release and source_revision must be null", "$.pin")

    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestError("invalid_manifest", "files must be a non-empty list", "$.files")
    source_paths: set[str] = set()
    consumer_paths: set[str] = set()
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(files):
        item_path = f"$.files[{index}]"
        if not isinstance(item, dict) or set(item) != {"source", "consumer", "sha256"}:
            raise ManifestError("invalid_manifest", "each file must contain only source, consumer, and sha256", item_path)
        source = safe_relative_path(item["source"], f"{item_path}.source")
        consumer = safe_relative_path(item["consumer"], f"{item_path}.consumer")
        expected = item["sha256"]
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            raise ManifestError("invalid_manifest", "sha256 must be 64 lowercase hexadecimal characters", f"{item_path}.sha256")
        if source in source_paths:
            raise ManifestError("duplicate_path", "source path is duplicated", f"{item_path}.source")
        if consumer in consumer_paths:
            raise ManifestError("duplicate_path", "consumer path is duplicated", f"{item_path}.consumer")
        source_paths.add(source)
        consumer_paths.add(consumer)
        normalized.append({"source": source, "consumer": consumer, "sha256": expected})
    data["files"] = normalized
    return data


def compare(source_root: Path, consumer_root: Path, manifest: dict[str, Any], manifest_path: Path) -> tuple[int, dict[str, Any]]:
    errors: list[dict[str, str]] = []
    drift: list[dict[str, str]] = []
    matched = 0
    if not source_root.is_dir():
        errors.append({"code": "source_root_unavailable", "path": str(source_root), "message": "source root is not a directory"})
    if not consumer_root.is_dir():
        errors.append({"code": "consumer_root_unavailable", "path": str(consumer_root), "message": "consumer root is not a directory"})
    if errors:
        return 2, result_payload("error", manifest, manifest_path, matched, drift, errors)

    for item in manifest["files"]:
        source_path = source_root / item["source"]
        consumer_path = consumer_root / item["consumer"]
        missing = False
        if not resolves_within(source_path, source_root):
            errors.append({"code": "unsafe_source_path", "path": item["source"], "message": "source path resolves outside source root"})
            missing = True
        if not resolves_within(consumer_path, consumer_root):
            errors.append({"code": "unsafe_consumer_path", "path": item["consumer"], "message": "consumer path resolves outside consumer root"})
            missing = True
        if missing:
            continue
        if not source_path.is_file():
            errors.append({"code": "missing_source", "path": item["source"], "message": "pinned source file is missing"})
            missing = True
        if not consumer_path.is_file():
            errors.append({"code": "missing_consumer", "path": item["consumer"], "message": "pinned consumer file is missing"})
            missing = True
        if missing:
            continue

        expected = item["sha256"]
        source_hash = sha256(source_path)
        consumer_hash = sha256(consumer_path)
        item_drift = False
        if source_hash != expected:
            drift.append({"code": "source_hash_mismatch", "path": item["source"], "expected_sha256": expected, "actual_sha256": source_hash})
            item_drift = True
        if consumer_hash != expected:
            drift.append({"code": "consumer_hash_mismatch", "path": item["consumer"], "expected_sha256": expected, "actual_sha256": consumer_hash})
            item_drift = True
        if not item_drift:
            matched += 1

    if errors:
        return 2, result_payload("error", manifest, manifest_path, matched, drift, errors)
    if drift:
        return 1, result_payload("drift", manifest, manifest_path, matched, drift, errors)
    return 0, result_payload("match", manifest, manifest_path, matched, drift, errors)


def result_payload(
    status: str,
    manifest: dict[str, Any] | None,
    manifest_path: Path,
    matched: int,
    drift: list[dict[str, str]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    total = len(manifest.get("files", [])) if manifest else 0
    return {
        "ok": status == "match",
        "status": status,
        "manifest": str(manifest_path),
        "consumer": manifest.get("consumer") if manifest else None,
        "pin": manifest.get("pin") if manifest else None,
        "summary": {"total": total, "matched": matched, "drifted": len(drift), "errors": len(errors)},
        "drift": drift,
        "errors": errors,
    }


def print_human(payload: dict[str, Any]) -> None:
    print(f"DHF core snapshot: {payload['status']}")
    summary = payload["summary"]
    print(f"files: total={summary['total']} matched={summary['matched']} drifted={summary['drifted']} errors={summary['errors']}")
    for item in payload["drift"]:
        print(f"drift: {item['code']} {item['path']}")
    for item in payload["errors"]:
        print(f"error: {item['code']} {item['path']}: {item['message']}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only pinned DHF core snapshot comparator.")
    parser.add_argument("--source", required=True, help="Independent DHF source checkout root.")
    parser.add_argument("--consumer", required=True, help="Pinned consumer checkout root.")
    parser.add_argument("--manifest", required=True, help="DHF core pin manifest.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        manifest = load_manifest(manifest_path)
        code, payload = compare(
            Path(args.source).expanduser().resolve(),
            Path(args.consumer).expanduser().resolve(),
            manifest,
            manifest_path,
        )
    except ManifestError as exc:
        code = 2
        payload = result_payload(
            "error",
            None,
            manifest_path,
            0,
            [],
            [{"code": exc.code, "path": exc.path, "message": str(exc)}],
        )
    except OSError as exc:
        code = 2
        payload = result_payload(
            "error",
            None,
            manifest_path,
            0,
            [],
            [{"code": "io_error", "path": "$", "message": str(exc)}],
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print_human(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
