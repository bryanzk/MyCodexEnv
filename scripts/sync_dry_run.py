#!/usr/bin/env python3
"""Preview a sync without writing to the Codex home (SHI-637).

The real sync runs against a sandbox copy of the surfaces it manages. The
preview then lists every file the sync would add, change or remove, with a
unified diff for text files. Nothing is written to the real Codex home.

Only the managed surfaces are copied: the top-level docs, config.toml,
hooks.json, and the agents, skills, hooks, runtime, zsh, harness (without
harness/evidence) and bin folders. A symlink stays a symlink, so the sync's own
target checks behave as in a real run, but it is repointed at a sandbox copy of
its target, so nothing written through it reaches the real home. After the run
the real managed files are compared with their state before, and any
difference fails the preview. Permission changes count as changes. Credentials, sessions and databases are never
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


LINK_TARGETS = ".dry-run-link-targets"


def copy_managed(real: Path, sandbox: Path) -> None:
    sandbox.mkdir(parents=True, exist_ok=True)
    for name in TOP_FILES:
        source = real / name
        target = sandbox / name
        if source.is_symlink():
            os.symlink(os.readlink(source), target)
        elif source.is_file():
            if name in PATH_REWRITE_FILES:
                target.write_text(rewrite(source.read_text(encoding="utf-8"), real, sandbox), encoding="utf-8")
                shutil.copymode(source, target)
            else:
                shutil.copy2(source, target)
    for name in TOP_DIRS:
        source = real / name
        if source.is_symlink() or source.is_dir():
            if source.is_symlink():
                os.symlink(os.readlink(source), sandbox / name)
            else:
                shutil.copytree(
                    source,
                    sandbox / name,
                    symlinks=True,
                    ignore=shutil.ignore_patterns("evidence") if name == "harness" else None,
                )
    contain_links(real, sandbox)


def contain_links(real: Path, sandbox: Path) -> None:
    """Repoint every copied symlink at a sandbox copy of what it points to."""
    store = sandbox / LINK_TARGETS
    links = [path for top in (*TOP_FILES, *TOP_DIRS) for path in walk(sandbox / top) if path.is_symlink()]
    for index, link in enumerate(links):
        original = real / link.relative_to(sandbox)
        try:
            resolved = original.resolve(strict=True)
        except (OSError, RuntimeError):
            resolved = None
        replacement = store / str(index) / (resolved.name if resolved else "missing")
        replacement.parent.mkdir(parents=True, exist_ok=True)
        if resolved is not None and resolved.is_dir():
            shutil.copytree(resolved, replacement, symlinks=False, ignore_dangling_symlinks=True)
        elif resolved is not None:
            shutil.copy2(resolved, replacement)
        link.unlink()
        os.symlink(replacement, link)


def walk(path: Path) -> list[Path]:
    if path.is_symlink() or path.is_file():
        return [path]
    if not path.is_dir():
        return []
    found: list[Path] = []
    for root, dirs, files in os.walk(path):
        for name in [*dirs, *files]:
            found.append(Path(root) / name)
    return found


def ignored(relative: str) -> bool:
    if relative.startswith(IGNORED_PREFIXES) or Path(relative).name in IGNORED_NAMES:
        return True
    return ".backup." in Path(relative).name


def snapshot(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for top in (*TOP_FILES, *TOP_DIRS):
        for item in walk(root / top):
            if item.is_symlink() or item.is_file():
                relative = item.relative_to(root).as_posix()
                if not ignored(relative):
                    files[relative] = item
    return files


def content(path: Path, relative: str, sandbox: Path, real: Path) -> tuple[str, bytes]:
    """Kind, permission bits and bytes of one path; a link is compared by being a link."""
    if path.is_symlink():
        # Bytes of the sandbox copy of the target, so a write through the link shows up.
        target = path.resolve()
        return ("link", target.read_bytes() if target.is_file() else b"")
    data = path.read_bytes()
    if relative in PATH_REWRITE_FILES:
        data = rewrite(data.decode("utf-8"), sandbox, real).encode("utf-8")
    return (oct(path.stat().st_mode & 0o7777), data)


def real_fingerprint(real: Path) -> dict[str, tuple[str, bytes]]:
    """Kind, mode and content of every real managed path and link target, to prove the preview wrote nothing."""
    result: dict[str, tuple[str, bytes]] = {}
    for top in (*TOP_FILES, *TOP_DIRS):
        for item in walk(real / top):
            relative = item.relative_to(real).as_posix()
            if relative.startswith("harness/evidence/"):
                continue
            if item.is_symlink():
                target = item.resolve()
                data = target.read_bytes() if target.is_file() else b""
                result[relative] = ("link:" + os.readlink(item), data)
            elif item.is_file():
                result[relative] = (oct(item.stat().st_mode & 0o7777), item.read_bytes())
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
            (old_kind, old_data), (new_kind, new_data) = before[rel], after[rel]
            if old_kind != new_kind:
                print(f"--- {rel}: {old_kind} -> {new_kind}")
            if old_data == new_data:
                continue
            old, new = text_lines(old_data), text_lines(new_data)
            if old is None or new is None:
                print(f"--- {rel}: binary, {len(old_data)} -> {len(new_data)} bytes")
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
