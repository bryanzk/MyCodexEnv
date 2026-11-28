#!/usr/bin/env python3
"""Preview a sync without writing to the Codex home (SHI-637).

The real sync runs against a sandbox copy of the surfaces it manages. The
preview then lists every file the sync would add, change or remove, with a
unified diff for text files. Nothing is written to the real Codex home.

Only the managed surfaces are copied: the top-level docs, config.toml,
hooks.json, and the agents, skills, hooks, runtime, zsh, harness (without
harness/evidence) and bin folders. Symlinks are copied as the files they point
to, so the sandbox sync cannot write through a link into the real home; after
the run the real managed files are compared with their state before, and any
difference fails the preview. Credentials, sessions and databases are never
read. The superpowers checkout is not previewed: the sandbox run always uses
--skip-superpowers-sync.
"""
from __future__ import annotations

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOP_FILES = (
    "AGENTS.md",
    "remote-access.md",
    "remote-hosts.md",
    "remote-hosts.local.md",
    "config.toml",
    "hooks.json",
)
TOP_DIRS = ("agents", "skills", "hooks", "runtime", "zsh", "harness", "bin")
# Paths the sync writes for its own bookkeeping; they are not runtime changes.
IGNORED_PREFIXES = ("runtime-backups/", "harness/evidence/")
IGNORED_NAMES = (".phase0-sync.lock", ".harness-guard-sync.lock")
PATH_REWRITE_FILES = ("config.toml",)
MAX_DIFF_LINES = 200


def path_forms(path: Path) -> list[str]:
    forms = {str(path), str(path.resolve())}
    return sorted(forms, key=len, reverse=True)


def rewrite(text: str, old: Path, new: Path) -> str:
    for form in path_forms(old):
        text = text.replace(form, str(new))
    return text


def copy_managed(real: Path, sandbox: Path) -> None:
    sandbox.mkdir(parents=True, exist_ok=True)
    for name in TOP_FILES:
        source = real / name
        if source.is_file():
            target = sandbox / name
            if name in PATH_REWRITE_FILES:
                target.write_text(rewrite(source.read_text(encoding="utf-8"), real, sandbox), encoding="utf-8")
                shutil.copymode(source, target)
            else:
                shutil.copyfile(source, target)
                shutil.copymode(source, target)
    for name in TOP_DIRS:
        source = real / name
        if source.is_dir():
            # symlinks=False copies link targets, so nothing in the sandbox points out of it.
            shutil.copytree(
                source,
                sandbox / name,
                symlinks=False,
                ignore_dangling_symlinks=True,
                ignore=shutil.ignore_patterns("evidence") if name == "harness" else None,
            )


def ignored(relative: str) -> bool:
    if relative.startswith(IGNORED_PREFIXES) or Path(relative).name in IGNORED_NAMES:
        return True
    return ".backup." in Path(relative).name


def snapshot(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for top in (*TOP_FILES, *TOP_DIRS):
        path = root / top
        if path.is_symlink() or path.is_file():
            files[top] = path
        elif path.is_dir():
            for item in path.rglob("*"):
                if item.is_file() or item.is_symlink():
                    relative = item.relative_to(root).as_posix()
                    if not ignored(relative):
                        files[relative] = item
    return files


def content(path: Path, relative: str, sandbox: Path, real: Path) -> bytes:
    if path.is_symlink():
        return b"symlink -> " + os.readlink(path).encode()
    data = path.read_bytes()
    if relative in PATH_REWRITE_FILES and sandbox in path.parents:
        data = rewrite(data.decode("utf-8"), sandbox, real).encode("utf-8")
    return data


def real_fingerprint(real: Path) -> dict[str, tuple[str, bytes]]:
    """Kind and content of every real managed path, to prove the preview wrote nothing."""
    result: dict[str, tuple[str, bytes]] = {}
    for top in (*TOP_FILES, *TOP_DIRS):
        path = real / top
        items = [path] if (path.is_file() or path.is_symlink()) else (list(path.rglob("*")) if path.is_dir() else [])
        for item in items:
            relative = item.relative_to(real).as_posix()
            if relative.startswith("harness/evidence/"):
                continue
            if item.is_symlink():
                result[relative] = ("link", os.readlink(item).encode())
            elif item.is_file():
                result[relative] = ("file", item.read_bytes())
    return result


def text_lines(data: bytes) -> list[str] | None:
    try:
        return data.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--codex-home", required=True, type=Path)
    parser.add_argument("--keep-sandbox", action="store_true", help="leave the sandbox for inspection")
    parser.add_argument("sync_args", nargs=argparse.REMAINDER, help="extra arguments for the sync, after --")
    args = parser.parse_args(argv)
    extra = [arg for arg in args.sync_args if arg != "--"]
    if any(arg in ("--codex-home", "--repo-root", "--dry-run", "--shared-claude-skills-home") for arg in extra):
        print("dry-run: --codex-home, --repo-root and --shared-claude-skills-home are set by the preview", file=sys.stderr)
        return 2

    real = args.codex_home.expanduser().absolute()
    repo = args.repo_root.expanduser().absolute()
    sync = Path(__file__).resolve().parent / "sync_codex_home.sh"
    workdir = Path(tempfile.mkdtemp(prefix="codex-sync-dry-run-"))
    sandbox = workdir / "codex-home"
    real_before = real_fingerprint(real)
    try:
        copy_managed(real, sandbox)
        before = {rel: content(path, rel, sandbox, real) for rel, path in snapshot(sandbox).items()}
        command = [str(sync), "--repo-root", str(repo), "--codex-home", str(sandbox), *extra]
        if "--skip-superpowers-sync" not in command:
            command.append("--skip-superpowers-sync")
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        after = {rel: content(path, rel, sandbox, real) for rel, path in snapshot(sandbox).items()}
        if real_fingerprint(real) != real_before:
            print(f"dry-run: ERROR: files under {real} changed during the preview; inspect them", file=sys.stderr)
            return 3

        print(f"dry-run: nothing was written to {real}")
        print(f"dry-run: sync_exit={proc.returncode}")
        for line in (proc.stdout + proc.stderr).replace(str(sandbox), str(real)).splitlines()[-15:]:
            print(f"  sync: {line}")
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(rel for rel in set(before) & set(after) if before[rel] != after[rel])
        for label, items in (("add", added), ("change", changed), ("remove", removed)):
            for rel in items:
                print(f"would {label}: {rel}")
        shown = 0
        for rel in changed:
            old, new = text_lines(before[rel]), text_lines(after[rel])
            if old is None or new is None:
                print(f"--- {rel}: binary, {len(before[rel])} -> {len(after[rel])} bytes")
                continue
            for line in difflib.unified_diff(old, new, f"current/{rel}", f"after-sync/{rel}"):
                if shown >= MAX_DIFF_LINES:
                    break
                sys.stdout.write(line if line.endswith("\n") else line + "\n")
                shown += 1
        if shown >= MAX_DIFF_LINES:
            print(f"... diff cut at {MAX_DIFF_LINES} lines")
        print(f"dry-run summary: add={len(added)} change={len(changed)} remove={len(removed)}")
        print("dry-run: superpowers checkout not previewed")
        if args.keep_sandbox:
            print(f"dry-run: sandbox kept at {sandbox}")
        return proc.returncode
    finally:
        if not args.keep_sandbox:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
