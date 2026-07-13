#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKIP_PARTS = {".git", "node_modules", "__pycache__"}
GENERATED_GSTACK_DIRS = {
    ".agents",
    ".cursor",
    ".factory",
    ".gbrain",
    ".hermes",
    ".kiro",
    ".openclaw",
    ".opencode",
    ".slate",
}
FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
FIELD_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):(?P<value>.*)$")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
URL_SCHEMES = ("http:", "https:", "mailto:", "data:", "skill:", "plugin:", "app:", "file:")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    detail: str

    def as_json(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "detail": self.detail,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check local Codex skill structure, helper syntax, references, and managed runtime drift."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")),
        help="Accepted for source-stage verification command compatibility; Claude skill checks are not part of this gate.",
    )
    parser.add_argument("--plugin-root", action="append", default=[], help="Additional plugin/cache root to scan recursively.")
    parser.add_argument(
        "--strict-runtime-parity",
        action="store_true",
        default=os.environ.get("STRICT_RUNTIME_PARITY") == "1",
        help="Fail managed runtime drift even when the repo source file is currently dirty.",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def relative_display(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def skill_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    files: list[Path] = []
    for path in root.rglob("SKILL.md"):
        relative = path.relative_to(root)
        if set(path.parts) & SKIP_PARTS:
            continue
        if len(relative.parts) >= 2 and relative.parts[0] == "gstack" and relative.parts[1] in GENERATED_GSTACK_DIRS:
            continue
        files.append(path)
    return sorted(files)


def frontmatter_fields(text: str) -> tuple[dict[str, str], str | None]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, "SKILL.md must start with closed YAML frontmatter"
    lines = match.group("body").splitlines()
    fields: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        field_match = FIELD_RE.match(line)
        if not field_match:
            index += 1
            continue
        key = field_match.group("key")
        raw_value = field_match.group("value").strip()
        if raw_value in {"", "|", ">", "|-", ">-", "|+", ">+"}:
            continuation: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
                continuation.append(lines[index].strip())
                index += 1
            fields[key] = " ".join(part for part in continuation if part)
            continue
        fields[key] = raw_value.strip('"\'')
        index += 1
    return fields, None


def reference_targets(text: str) -> set[str]:
    text = FENCED_CODE_RE.sub("", text)
    targets: set[str] = set()
    for match in MARKDOWN_LINK_RE.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith("<") and ">" in raw:
            raw = raw[1 : raw.index(">")]
        else:
            raw = raw.split(maxsplit=1)[0]
        targets.add(raw)
    return targets


def local_reference(raw: str) -> str | None:
    target = raw.strip().rstrip(".,;:")
    if not target or target.startswith(("#", "/", "~")) or target.lower().startswith(URL_SCHEMES):
        return None
    if any(marker in target for marker in ("<", ">", "{", "}", "*", "$")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return target or None


def reference_exists(skill_file: Path, target: str, scan_root: Path, repo_root: Path) -> bool:
    bases = [skill_file.parent, repo_root]
    parent = skill_file.parent.parent
    while parent == scan_root or scan_root in parent.parents:
        bases.append(parent)
        if parent == scan_root:
            break
        parent = parent.parent
    return any((base / target).resolve().exists() for base in bases)


def check_frontmatter_and_references(skill_file: Path, scan_root: Path, repo_root: Path) -> list[Finding]:
    display = relative_display(skill_file, repo_root)
    findings: list[Finding] = []
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [Finding("error", "skill_unreadable", display, str(exc))]

    fields, error = frontmatter_fields(text)
    if error:
        findings.append(Finding("error", "invalid_frontmatter", display, error))
        return findings
    name = fields.get("name", "").strip()
    description = fields.get("description", "").strip()
    if not name:
        findings.append(Finding("error", "missing_skill_name", display, "frontmatter.name is required"))
    elif name != skill_file.parent.name:
        findings.append(
            Finding(
                "warning",
                "skill_name_alias",
                display,
                f"frontmatter.name={name!r} differs from parent directory {skill_file.parent.name!r}",
            )
        )
    if not description:
        findings.append(Finding("error", "missing_skill_description", display, "frontmatter.description is required"))

    for raw in sorted(reference_targets(text)):
        target = local_reference(raw)
        if target is None:
            continue
        if not reference_exists(skill_file, target, scan_root, repo_root):
            severity = "warning" if target.startswith("examples/") else "error"
            findings.append(
                Finding(
                    severity,
                    "missing_relative_reference",
                    display,
                    f"referenced path does not exist: {target}",
                )
            )
    return findings


def helper_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file() or set(path.parts) & SKIP_PARTS or path.name == "SKILL.md":
            continue
        if path.suffix.lower() in {".py", ".json", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs"}:
            files.append(path)
        elif path.stat().st_mode & 0o111:
            try:
                first_line = path.open("r", encoding="utf-8", errors="ignore").readline()
            except OSError:
                continue
            if first_line.startswith("#!"):
                files.append(path)
    return sorted(files)


def syntax_finding(path: Path, repo_root: Path) -> Finding | None:
    display = relative_display(path, repo_root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return Finding("error", "helper_unreadable", display, str(exc))
    suffix = path.suffix.lower()
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if suffix == ".py" or (not suffix and "python" in first_line):
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            return Finding("error", "python_syntax_error", display, f"line {exc.lineno}: {exc.msg}")
        return None
    if suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            return Finding("error", "json_syntax_error", display, f"line {exc.lineno}: {exc.msg}")
        return None
    if suffix in {".sh", ".bash", ".zsh"} or (not suffix and ("bash" in first_line or "zsh" in first_line)):
        shell = "/bin/zsh" if suffix == ".zsh" or "zsh" in first_line else "/bin/bash"
        proc = subprocess.run([shell, "-n", str(path)], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()[-1]
            return Finding("error", "shell_syntax_error", display, detail)
        return None
    if suffix in {".js", ".mjs", ".cjs"} or (not suffix and "node" in first_line):
        proc = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()[-1]
            return Finding("error", "javascript_syntax_error", display, detail)
    return None


def managed_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    files: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file() or set(path.parts) & SKIP_PARTS or path.name == ".DS_Store":
            continue
        relative = path.relative_to(root)
        if len(relative.parts) >= 2 and relative.parts[0] == "gstack" and relative.parts[1] in GENERATED_GSTACK_DIRS:
            continue
        files[str(relative)] = path
    return files


def managed_runtime_status(repo_skills: Path, runtime_skills: Path) -> dict[str, Any]:
    # Codex 0.144+ materializes `.system` skills while app-server is active and
    # may remove that projection when the server exits. Their compatibility is
    # therefore covered by the app-server skills/list gate, not persistent hash
    # parity against CODEX_HOME/skills.
    repo_files = {
        relative: path
        for relative, path in managed_files(repo_skills).items()
        if not relative.startswith(".system/")
    }
    runtime_files = {
        relative: path
        for relative, path in managed_files(runtime_skills).items()
        if not relative.startswith(".system/")
    }
    repo_manifests = sorted(path for path in repo_files if path.endswith("/SKILL.md"))
    runtime_manifests = sorted(path for path in runtime_files if path.endswith("/SKILL.md"))
    missing_files = sorted(set(repo_files) - set(runtime_files))
    missing_manifests = sorted(path for path in missing_files if path.endswith("/SKILL.md"))
    drifted = sorted(
        relative
        for relative in set(repo_files) & set(runtime_files)
        if hashlib.sha256(repo_files[relative].read_bytes()).digest()
        != hashlib.sha256(runtime_files[relative].read_bytes()).digest()
    )
    runtime_only = sorted(set(runtime_manifests) - set(repo_manifests))
    return {
        "checked": len(repo_manifests),
        "missing": missing_manifests,
        "missing_files": missing_files,
        "drifted": drifted,
        "runtime_only": runtime_only,
    }


def source_file_dirty(repo_root: Path, relative: str) -> bool:
    path = Path("codex") / "skills" / relative
    commands = [
        ["git", "diff", "--quiet", "--", str(path)],
        ["git", "diff", "--cached", "--quiet", "--", str(path)],
    ]
    for command in commands:
        proc = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
        if proc.returncode == 1:
            return True
        if proc.returncode not in (0, 1):
            return False
    return False


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Skill Compatibility Audit",
        "",
        f"- skill_files: {summary['skill_files']}",
        f"- helper_files: {summary['helper_files']}",
        f"- errors: {summary['errors']}",
        f"- warnings: {summary['warnings']}",
        f"- managed_missing: {len(payload['managed_runtime']['missing'])}",
        f"- managed_drifted: {len(payload['managed_runtime']['drifted'])}",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding['severity'].upper()} {finding['code']} {finding['path']}: {finding['detail']}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    codex_home = Path(args.codex_home).expanduser().resolve()
    roots: list[tuple[str, Path]] = [
        ("repo", repo_root / "codex" / "skills"),
        ("agents", repo_root / ".agents" / "skills"),
        ("runtime", codex_home / "skills"),
    ]
    roots.extend(("plugin", Path(raw).expanduser().resolve()) for raw in args.plugin_root)

    seen_skill_files: set[Path] = set()
    findings: list[Finding] = []
    helper_count = 0
    root_counts: dict[str, int] = {}
    for label, root in roots:
        files = skill_files(root)
        root_counts[str(root)] = len(files)
        for skill_file in files:
            if label == "runtime":
                relative_skill = skill_file.relative_to(root)
                if (repo_root / "codex" / "skills" / relative_skill).is_file():
                    continue
            resolved_skill = skill_file.resolve()
            if resolved_skill in seen_skill_files:
                continue
            seen_skill_files.add(resolved_skill)
            findings.extend(check_frontmatter_and_references(skill_file, root, repo_root))
            for helper in helper_files(skill_file.parent):
                helper_count += 1
                finding = syntax_finding(helper, repo_root)
                if finding is not None:
                    findings.append(finding)

    managed = managed_runtime_status(repo_root / "codex" / "skills", codex_home / "skills")
    for name in managed["missing"]:
        findings.append(Finding("error", "managed_skill_missing", str(codex_home / "skills" / name), name))
    for name in managed["missing_files"]:
        if name in managed["missing"]:
            continue
        findings.append(Finding("error", "managed_skill_file_missing", str(codex_home / "skills" / name), name))
    for name in managed["drifted"]:
        if not args.strict_runtime_parity and source_file_dirty(repo_root, name):
            findings.append(
                Finding(
                    "warning",
                    "managed_skill_source_stage_drift",
                    str(codex_home / "skills" / name),
                    f"{name} differs because the repo source is dirty; runtime sync is still required before strict verification",
                )
            )
            continue
        findings.append(Finding("error", "managed_skill_drift", str(codex_home / "skills" / name), name))

    findings.sort(key=lambda item: (item.severity != "error", item.code, item.path, item.detail))
    errors = sum(1 for item in findings if item.severity == "error")
    warnings = sum(1 for item in findings if item.severity == "warning")
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "roots": root_counts,
        "summary": {
            "skill_files": len(seen_skill_files),
            "helper_files": helper_count,
            "errors": errors,
            "warnings": warnings,
        },
        "managed_runtime": managed,
        "findings": [item.as_json() for item in findings],
    }
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
