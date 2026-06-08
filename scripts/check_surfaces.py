#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PATH_PREFIXES = ("docs/", "codex/", "scripts/")


def normalize_path(value: str) -> str:
    value = value.strip().strip("`").strip()
    value = re.sub(r"^\./", "", value)
    return value.rstrip("/")


def is_repo_surface_path(value: str) -> bool:
    return value.startswith(PATH_PREFIXES)


def repo_index_surface_paths(repo_root: Path) -> set[str]:
    text = (repo_root / "docs" / "repo-index.md").read_text(encoding="utf-8")
    paths: set[str] = set()
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## runtime surfaces"
            continue
        if not in_section or not line.startswith("- "):
            continue
        for token in re.findall(r"`([^`]+)`", line):
            path = normalize_path(token)
            if is_repo_surface_path(path):
                paths.add(path)
                break
    return paths


def load_manifest(repo_root: Path) -> list[dict[str, Any]]:
    raw = json.loads((repo_root / "docs" / "surfaces.json").read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("docs/surfaces.json version must be 1")
    surfaces = raw.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("docs/surfaces.json surfaces must be a non-empty list")
    return surfaces


def href_for_docs_surface(path: str) -> str | None:
    if not path.startswith("docs/"):
        return None
    return "./" + path.removeprefix("docs/")


def validate_public_nav(repo_root: Path, surfaces: list[dict[str, Any]], manifest: set[str]) -> tuple[list[str], int]:
    errors: list[str] = []
    nav_count = 0
    for item in surfaces:
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue
        path = normalize_path(path_value)
        nav_pages = item.get("public_nav", [])
        if nav_pages is None:
            continue
        if not isinstance(nav_pages, list):
            errors.append(f"ERROR[public_nav_type] {path}")
            continue

        href = href_for_docs_surface(path)
        if href is None and nav_pages:
            errors.append(f"ERROR[public_nav_non_docs_surface] {path}")
            continue

        for raw_nav_page in nav_pages:
            if not isinstance(raw_nav_page, str) or not raw_nav_page.strip():
                errors.append(f"ERROR[public_nav_page_type] {path}")
                continue
            nav_path = normalize_path(raw_nav_page)
            nav_count += 1
            if nav_path not in manifest:
                errors.append(f"ERROR[public_nav_page_not_manifest] {nav_path} -> {path}")
                continue
            try:
                text = (repo_root / nav_path).read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"ERROR[public_nav_page_unreadable] {nav_path}: {exc}")
                continue
            if href not in text:
                errors.append(f"ERROR[public_nav_missing] {nav_path} -> {path}")
    return errors, nav_count


def validate(repo_root: Path, *, check_public_nav: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    manifest: set[str] = set()
    duplicates: set[str] = set()
    surfaces = load_manifest(repo_root)
    for index, item in enumerate(surfaces):
        if not isinstance(item, dict):
            errors.append(f"ERROR[manifest_item_type] index={index}")
            continue
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            errors.append(f"ERROR[manifest_path_missing] index={index}")
            continue
        path = normalize_path(path_value)
        if path != path_value:
            errors.append(f"ERROR[path_not_normalized] {path_value}")
        if not is_repo_surface_path(path):
            errors.append(f"ERROR[path_not_repo_surface] {path}")
        if path in manifest:
            duplicates.add(path)
        manifest.add(path)
        if not item.get("role"):
            errors.append(f"ERROR[role_missing] {path}")
        audience = item.get("audience")
        if not isinstance(audience, list) or not audience:
            errors.append(f"ERROR[audience_missing] {path}")

    for path in sorted(duplicates):
        errors.append(f"ERROR[duplicate_path] {path}")
    for path in sorted(manifest):
        if not (repo_root / path).exists():
            errors.append(f"ERROR[missing_on_disk] {path}")

    index_paths = repo_index_surface_paths(repo_root)
    for path in sorted(index_paths - manifest):
        errors.append(f"ERROR[in_index_not_manifest] {path}")
    for path in sorted(manifest - index_paths):
        errors.append(f"ERROR[in_manifest_not_index] {path}")

    public_nav_count = 0
    if check_public_nav:
        public_nav_errors, public_nav_count = validate_public_nav(repo_root, surfaces, manifest)
        errors.extend(public_nav_errors)

    return {
        "ok": not errors,
        "errors": errors,
        "manifest_count": len(manifest),
        "repo_index_count": len(index_paths),
        "public_nav_count": public_nav_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate docs/surfaces.json against files on disk, the first "
            "backticked repo-relative path in each docs/repo-index.md Runtime Surfaces bullet, "
            "and optionally public landing-page nav links."
        )
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check-public-nav", action="store_true")
    args = parser.parse_args()

    try:
        result = validate(Path(args.repo_root).resolve(), check_public_nav=args.check_public_nav)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "ok": False,
            "errors": [f"ERROR[load] {exc}"],
            "manifest_count": 0,
            "repo_index_count": 0,
            "public_nav_count": 0,
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["ok"]:
        print("surfaces manifest consistent")
    else:
        print("\n".join(result["errors"]), file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
