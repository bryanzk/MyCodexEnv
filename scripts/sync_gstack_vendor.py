#!/usr/bin/env python3
"""Sync the vendored gstack skill tree from an upstream git snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_SOURCE = "https://github.com/garrytan/gstack.git"
VENDOR_PATH = Path("codex") / "skills" / "gstack"


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file())


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(path: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if ".git" in item.parts:
            continue
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            manifest[relative] = f"symlink:{item.readlink()}"
        elif item.is_file():
            manifest[relative] = f"file:{file_digest(item)}"
    return manifest


def diff_manifest_count(left: dict[str, str], right: dict[str, str]) -> int:
    keys = set(left) | set(right)
    return sum(1 for key in keys if left.get(key) != right.get(key))


def ignore_snapshot_noise(directory: str, names: list[str]) -> set[str]:
    ignored = {".git"}
    return {name for name in names if name in ignored}


def validate_snapshot(snapshot: Path) -> str:
    required = ["VERSION", "package.json", "setup"]
    for relative in required:
        path = snapshot / relative
        if not path.exists():
            fail(f"Upstream gstack snapshot is missing required file: {relative}")
    version = (snapshot / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        fail("Upstream gstack VERSION is empty")
    return version


def clone_snapshot(source: str, ref: str | None, tmp_dir: Path) -> Path:
    snapshot = tmp_dir / "gstack"
    code, out, err = run(["git", "clone", "--depth", "1", source, str(snapshot)])
    if code != 0:
        fail(f"Failed to clone gstack source: {err or out}")

    if ref:
        code, out, err = run(["git", "fetch", "--depth", "1", "origin", ref], cwd=snapshot)
        if code != 0:
            fail(f"Failed to fetch gstack ref {ref}: {err or out}")
        code, out, err = run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=snapshot)
        if code != 0:
            fail(f"Failed to checkout gstack ref {ref}: {err or out}")

    return snapshot


def stage_snapshot(snapshot: Path, parent: Path) -> Path:
    staging = Path(tempfile.mkdtemp(prefix=".gstack-sync-stage-", dir=parent))
    shutil.rmtree(staging)
    shutil.copytree(snapshot, staging, ignore=ignore_snapshot_noise, symlinks=True)
    return staging


def replace_vendor(vendor: Path, staging: Path, keep_backup: bool) -> Path | None:
    backup: Path | None = None
    if vendor.exists():
        backup = Path(tempfile.mkdtemp(prefix=".gstack-sync-backup-", dir=vendor.parent))
        shutil.rmtree(backup)
        vendor.rename(backup)

    try:
        staging.rename(vendor)
    except Exception:
        if backup and backup.exists() and not vendor.exists():
            backup.rename(vendor)
        raise

    if backup and backup.exists() and not keep_backup:
        shutil.rmtree(backup)
        return None
    return backup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync codex/skills/gstack from an upstream git snapshot.")
    parser.add_argument("--repo-root", default=".", help="Repository root that owns codex/skills/gstack.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Git URL or local git repository path for gstack.")
    parser.add_argument("--ref", default="", help="Optional branch, tag, or commit to fetch and checkout.")
    parser.add_argument("--dry-run", action="store_true", help="Clone and validate, but do not replace the vendor tree.")
    parser.add_argument("--keep-backup", action="store_true", help="Keep the previous vendor tree backup after replacement.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        fail(f"Repo root does not exist: {repo_root}")

    vendor = repo_root / VENDOR_PATH
    vendor.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="gstack-upstream-") as tmp:
        snapshot = clone_snapshot(args.source, args.ref or None, Path(tmp))
        version = validate_snapshot(snapshot)
        snapshot_files = count_files(snapshot)
        snapshot_manifest = build_manifest(snapshot)
        vendor_manifest = build_manifest(vendor) if vendor.exists() else {}
        diff_files = diff_manifest_count(snapshot_manifest, vendor_manifest)
        payload = {
            "source": args.source,
            "ref": args.ref or "default",
            "vendor": str(vendor),
            "version": version,
            "changed_files": snapshot_files,
            "diff_files": diff_files,
            "needs_update": diff_files > 0,
            "dry_run": args.dry_run,
            "backup": None,
        }

        if not args.dry_run:
            staging = stage_snapshot(snapshot, vendor.parent)
            validate_snapshot(staging)
            backup = replace_vendor(vendor, staging, args.keep_backup)
            payload["backup"] = str(backup) if backup else None

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        action = "would sync" if args.dry_run else "synced"
        print(f"gstack {action}: version={payload['version']} files={payload['changed_files']} vendor={payload['vendor']}")
        if payload["backup"]:
            print(f"backup: {payload['backup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
