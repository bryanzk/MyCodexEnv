#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SKIP_DIR_NAMES = {
    ".git",
    ".worktrees",
    ".agents-backups",
    "node_modules",
    ".venv",
    "venv",
    "target",
    ".next",
    ".open-next",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage",
}

PRIMARY_DOC_FILES = ("README.md", "readme.md", "README.zh-CN.md", "README.en.md")
ROOT_AGENT_FILENAMES = ("AGENTS.md", "agents.md")
STACK_MARKERS = {
    "python": ("pyproject.toml", "requirements.txt", "requirements-dev.txt"),
    "node": ("package.json",),
    "rust": ("Cargo.toml",),
    "go": ("go.mod",),
}
REPO_MAP_HINTS = {
    "src": "核心源码目录",
    "app": "应用入口与页面目录",
    "lib": "共享逻辑与工具库",
    "cmd": "可执行入口与 CLI 命令",
    "internal": "内部实现与私有模块",
    "scripts": "脚本与运维入口",
    "tests": "回归测试与 fixture",
    "test": "测试入口",
    "docs": "说明文档与设计记录",
    "doc": "补充文档目录",
    "config": "配置与环境模板",
    "configs": "配置目录",
    "deploy": "部署与环境交付物",
    "deployments": "部署资源",
    "docker": "容器化入口",
    "contracts": "合约或契约资源",
    "features": "功能规格或 BDD 资源",
    "tasks": "任务与运行记录",
    "packages": "多包工作区目录",
    "html": "静态页面或导出产物",
}
HIGH_RISK_HINTS = {
    "deploy": "部署与环境配置变更",
    "deployments": "部署脚本与环境交付物",
    "docker": "容器镜像与运行参数",
    "contracts": "合约、链上交互或 ABI 变更",
    "config": "配置与环境变量边界",
    "configs": "配置与环境变量边界",
    "scripts": "脚本可能触发批量操作或写入",
    "local": "本地状态、缓存或手工资产",
    "skills": "本地 skill 与自动化行为",
}
REQUIRED_CODEX_HEADERS = [
    "## Purpose",
    "## Verification Gate",
    "## Layering",
    "## Repo AGENTS Expectations",
]
GENERATED_MARKER = "<!-- generated-by: manage_agents.py -->"


@dataclass
class RepoRecord:
    name: str
    path: Path
    realpath: Path
    root_agents: Path | None
    local_agents: list[Path]
    readmes: list[Path]
    manifests: list[Path]
    important_dirs: list[Path]
    docs_dirs: list[Path]
    scripts_dirs: list[Path]
    tests_dirs: list[Path]
    stack: list[str]
    package_scripts: dict[str, str]
    title: str
    summary: str


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_hash(path: Path) -> str:
    return sha256_bytes(str(path).encode("utf-8"))[:16]


def relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir() or (path / ".git").is_file()


def is_skipped_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES


def actual_root_agents(path: Path) -> Path | None:
    try:
        for entry in path.iterdir():
            if entry.is_file() and entry.name == "AGENTS.md":
                return entry
    except FileNotFoundError:
        return None
    return None


def detect_stack(path: Path) -> list[str]:
    stack: list[str] = []
    names = {item.name for item in path.iterdir()} if path.exists() else set()
    for name, markers in STACK_MARKERS.items():
        if any(marker in names for marker in markers):
            stack.append(name)
    return stack


def parse_package_scripts(path: Path) -> dict[str, str]:
    package_json = path / "package.json"
    if not package_json.exists():
        return {}
    try:
        payload = json.loads(load_text(package_json))
    except json.JSONDecodeError:
        return {}
    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def collect_actual_readmes(path: Path) -> list[Path]:
    priority = {
        "readme.md": 0,
        "README.md": 0,
        "readme.zh-cn.md": 1,
        "readme.en.md": 2,
    }
    readmes: list[Path] = []
    for entry in path.iterdir():
        if not entry.is_file():
            continue
        lowered = entry.name.lower()
        if lowered in {"readme.md", "readme.zh-cn.md", "readme.en.md"}:
            readmes.append(entry)
    return sorted(readmes, key=lambda item: (priority.get(item.name.lower(), 9), item.name.lower()))


def extract_readme_context(path: Path) -> tuple[str, str]:
    title = ""
    summary = ""
    for readme in collect_actual_readmes(path):
        lines = load_text(readme).splitlines()
        paragraph_lines: list[str] = []
        collecting = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
                continue
            if not stripped:
                if collecting:
                    break
                continue
            if stripped.startswith(("#", "```", "- ", "* ", "|", "![", "[!", "`")):
                continue
            collecting = True
            if stripped:
                paragraph_lines.append(stripped)
                if len(paragraph_lines) >= 2:
                    break
        if paragraph_lines:
            summary = " ".join(paragraph_lines)
        break
    if not title:
        title = path.name
    if not summary:
        summary = f"{path.name} 仓库。"
    return title, summary


def collect_directory_group(path: Path, names: set[str]) -> list[Path]:
    collected: list[Path] = []
    for name in names:
        candidate = path / name
        if candidate.exists():
            collected.append(candidate)
    return sorted(collected, key=lambda item: item.name.lower())


def discover_local_agents(root: Path, exclude_root: Path | None = None) -> list[Path]:
    results: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        dirnames[:] = [name for name in dirnames if not is_skipped_dir(name)]
        for filename in filenames:
            if filename != "AGENTS.md":
                continue
            candidate = current_path / filename
            if exclude_root is not None and candidate == exclude_root:
                continue
            results.append(candidate)
    return sorted(results)


def discover_nested_repos(repo_root: Path, seen: set[Path]) -> list[Path]:
    nested: list[Path] = []
    base_depth = len(repo_root.parts)
    for current_root, dirnames, _ in os.walk(repo_root):
        current_path = Path(current_root)
        dirnames[:] = [name for name in dirnames if not is_skipped_dir(name)]
        if current_path == repo_root:
            continue
        if len(current_path.parts) - base_depth > 3:
            dirnames[:] = []
            continue
        if is_git_repo(current_path):
            real = current_path.resolve()
            if real not in seen:
                seen.add(real)
                nested.append(current_path)
            dirnames[:] = []
    return nested


def build_repo_record(path: Path) -> RepoRecord:
    root_agents = actual_root_agents(path)
    local_agents = discover_local_agents(path, exclude_root=root_agents)
    readmes = collect_actual_readmes(path)
    manifests: list[Path] = []
    for marker_group in STACK_MARKERS.values():
        for marker in marker_group:
            candidate = path / marker
            if candidate.exists():
                manifests.append(candidate)
    for candidate in ("Makefile", "justfile"):
        file_path = path / candidate
        if file_path.exists():
            manifests.append(file_path)
    stack = detect_stack(path)
    package_scripts = parse_package_scripts(path)
    title, summary = extract_readme_context(path)
    important_dirs = [path / name for name in REPO_MAP_HINTS if (path / name).exists()]
    docs_dirs = collect_directory_group(path, {"docs", "doc"})
    scripts_dirs = collect_directory_group(path, {"scripts"})
    tests_dirs = collect_directory_group(path, {"tests", "test"})
    return RepoRecord(
        name=path.name,
        path=path,
        realpath=path.resolve(),
        root_agents=root_agents,
        local_agents=local_agents,
        readmes=readmes,
        manifests=sorted({item for item in manifests}, key=lambda item: item.name.lower()),
        important_dirs=important_dirs,
        docs_dirs=docs_dirs,
        scripts_dirs=scripts_dirs,
        tests_dirs=tests_dirs,
        stack=stack,
        package_scripts=package_scripts,
        title=title,
        summary=summary,
    )


def discover_repos(workspace_root: Path) -> list[RepoRecord]:
    if not workspace_root.exists():
        fail(f"Workspace root does not exist: {workspace_root}")
    seen: set[Path] = set()
    repos: list[RepoRecord] = []
    for entry in sorted(workspace_root.iterdir(), key=lambda item: item.name.lower()):
        if is_skipped_dir(entry.name):
            continue
        if not entry.is_dir():
            continue
        if is_git_repo(entry):
            real = entry.resolve()
            if real not in seen:
                seen.add(real)
                repos.append(build_repo_record(entry))
            for nested in discover_nested_repos(entry, seen):
                repos.append(build_repo_record(nested))
    repos.sort(key=lambda repo: repo.path.as_posix().lower())
    return repos


def discover_orphan_agents(workspace_root: Path, repos: list[RepoRecord]) -> list[Path]:
    owned_roots = [repo.realpath for repo in repos]
    orphans: list[Path] = []
    for agent in discover_local_agents(workspace_root):
        real = agent.resolve()
        if any(str(real).startswith(str(root)) for root in owned_roots):
            continue
        orphans.append(agent)
    return sorted(orphans)


def scan_workspace(workspace_root: Path, codex_source: Path, codex_runtime: Path, backup_root: Path) -> dict:
    repos = discover_repos(workspace_root)
    orphan_agents = discover_orphan_agents(workspace_root, repos)
    return {
        "workspace_root": workspace_root.as_posix(),
        "backup_root": backup_root.as_posix(),
        "codex_source": codex_source.as_posix(),
        "codex_runtime": codex_runtime.as_posix(),
        "repos": [
            {
                "name": repo.name,
                "path": repo.path.as_posix(),
                "realpath": repo.realpath.as_posix(),
                "root_agents": repo.root_agents.as_posix() if repo.root_agents else None,
                "local_agents": [item.as_posix() for item in repo.local_agents],
                "readmes": [item.as_posix() for item in repo.readmes],
                "manifests": [item.as_posix() for item in repo.manifests],
                "important_dirs": [item.as_posix() for item in repo.important_dirs],
                "stack": repo.stack,
                "package_scripts": repo.package_scripts,
                "title": repo.title,
                "summary": repo.summary,
            }
            for repo in repos
        ],
        "orphan_local_agents": [item.as_posix() for item in orphan_agents],
    }


def infer_workflows(repo: RepoRecord) -> list[str]:
    workflows: list[str] = []
    if repo.package_scripts:
        for key in ("dev", "build", "test", "lint", "start", "preview", "deploy"):
            if key in repo.package_scripts:
                workflows.append(f"- `npm run {key}`")
    if "python" in repo.stack:
        if (repo.path / "test_runner.py").exists():
            workflows.append("- `python3 test_runner.py`")
        elif repo.tests_dirs:
            workflows.append("- `pytest -q`")
    if "go" in repo.stack:
        workflows.append("- `go test ./...`")
    if "rust" in repo.stack:
        workflows.append("- `cargo test`")
        workflows.append("- `cargo build`")
    if (repo.path / "Makefile").exists():
        workflows.append("- `make`")
    if not workflows:
        workflows.append("- 先阅读 README 或脚本目录，再执行与本仓库匹配的最小验证命令。")
    return workflows


def infer_verification(repo: RepoRecord, workflows: list[str]) -> list[str]:
    verification: list[str] = []
    if (repo.path / "test_runner.py").exists():
        verification.append("- 优先运行 `python3 test_runner.py`。")
    elif "node" in repo.stack and "test" in repo.package_scripts:
        verification.append("- 优先运行 `npm run test`。")
    elif "python" in repo.stack and repo.tests_dirs:
        verification.append("- 优先运行 `pytest -q`。")
    elif "go" in repo.stack:
        verification.append("- 优先运行 `go test ./...`。")
    elif "rust" in repo.stack:
        verification.append("- 优先运行 `cargo test`。")
    else:
        verification.append("- 先确认 README 或脚本中声明的验证入口，再执行最小回归。")
    verification.append("- 修改文档或配置时，确认引用路径、脚本入口和说明一致。")
    return verification


def infer_high_risk(repo: RepoRecord) -> list[str]:
    risk_items: list[str] = []
    for directory in repo.important_dirs:
        hint = HIGH_RISK_HINTS.get(directory.name)
        if hint:
            risk_items.append(f"- `{directory.name}/`: {hint}")
    if repo.local_agents:
        risk_items.append("- 局部 `AGENTS.md` 对应的子目录通常有额外规则，改动前先下钻阅读。")
    if not risk_items:
        risk_items.append("- 配置、部署脚本、批量处理脚本和对外接口属于高风险改动。")
    return risk_items


def build_repo_agents(repo: RepoRecord) -> str:
    lines: list[str] = [GENERATED_MARKER, f"# {repo.title}", ""]
    lines.extend(
        [
            "## Purpose",
            f"- {repo.summary}",
            "- 本文件只描述当前仓库的导航信息；通用 Codex 规则由上层环境提供。",
            "",
            "## Read First",
        ]
    )
    if repo.readmes:
        for readme in repo.readmes:
            lines.append(f"- `{relative_posix(readme, repo.path)}`")
    else:
        lines.append("- 仓库根目录没有 README；先从源码、脚本和测试入口逆向理解。")
    if repo.docs_dirs:
        for docs_dir in repo.docs_dirs:
            lines.append(f"- `{relative_posix(docs_dir, repo.path)}/`")
    if repo.local_agents:
        lines.append("- 局部目录含专用 `AGENTS.md`，任务落入对应子目录时继续下钻。")
    lines.extend(["", "## Repo Map"])
    if repo.important_dirs:
        for directory in repo.important_dirs:
            lines.append(
                f"- `{relative_posix(directory, repo.path)}/`: {REPO_MAP_HINTS.get(directory.name, '仓库关键目录')}"
            )
    else:
        lines.append("- 目录结构较轻，优先从根目录文件和 README 理解入口。")

    lines.extend(["", "## Source Of Truth"])
    if repo.manifests:
        for manifest in repo.manifests:
            lines.append(f"- `{relative_posix(manifest, repo.path)}`")
    else:
        lines.append("- 仓库缺少标准 manifest；请以 README、脚本和测试目录为准。")
    if repo.local_agents:
        for local_agent in repo.local_agents:
            lines.append(f"- `{relative_posix(local_agent, repo.path)}`")

    workflows = infer_workflows(repo)
    lines.extend(["", "## Common Workflows", *workflows, "", "## Verification", *infer_verification(repo, workflows)])
    lines.extend(["", "## High-Risk Areas", *infer_high_risk(repo)])
    lines.extend(
        [
            "",
            "## Change Rules",
            "- 不要在本文件复制通用 Codex 规则；只保留仓库特有约束。",
            "- 变更入口命令、目录结构或对外接口时，同步更新 README、docs 和相关测试。",
            "- 若任务仅落在某个局部目录，先阅读该目录下的 `AGENTS.md` 再修改。",
            "",
            "## When To Ask",
            "- 需要改变公开接口、部署方式、配置默认值或数据格式时。",
            "- 需要删除目录、重命名关键文件或绕过现有验证入口时。",
            "",
            "## Subdirectory AGENTS",
        ]
    )
    if repo.local_agents:
        for local_agent in repo.local_agents:
            lines.append(f"- `{relative_posix(local_agent, repo.path)}`")
    else:
        lines.append("- 当前仓库没有额外的局部 `AGENTS.md`。")
    lines.append("")
    return "\n".join(lines)


def parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line.strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def extract_backticked_tokens(lines: list[str]) -> list[str]:
    tokens: list[str] = []
    for line in lines:
        tokens.extend(re.findall(r"`([^`]+)`", line))
    return tokens


def validate_generated_command(repo: RepoRecord, command: str) -> str | None:
    if command == "python3 test_runner.py":
        if (repo.path / "test_runner.py").exists():
            return None
        return "缺少 `test_runner.py`"
    if command.startswith("npm run "):
        script_name = command.removeprefix("npm run ").strip()
        if script_name in repo.package_scripts:
            return None
        return f"`package.json` 缺少脚本 `{script_name}`"
    if command == "pytest -q":
        if repo.tests_dirs:
            return None
        return "缺少测试目录，无法支持 `pytest -q`"
    if command == "go test ./...":
        if "go" in repo.stack:
            return None
        return "仓库不是 Go 项目"
    if command in {"cargo test", "cargo build"}:
        if "rust" in repo.stack:
            return None
        return "仓库不是 Rust 项目"
    if command == "make":
        if (repo.path / "Makefile").exists():
            return None
        return "缺少 `Makefile`"
    return f"未知命令来源：`{command}`"


def verify_generated_root_agents(repo: RepoRecord, root_path: Path, root_text: str) -> list[str]:
    errors: list[str] = []
    sections = parse_markdown_sections(root_text)
    required_sections = (
        "## Read First",
        "## Repo Map",
        "## Source Of Truth",
        "## Common Workflows",
        "## Verification",
        "## Subdirectory AGENTS",
    )
    for heading in required_sections:
        if heading not in sections:
            errors.append(f"{root_path} missing section {heading}")

    path_sections = ("## Read First", "## Repo Map", "## Source Of Truth", "## Subdirectory AGENTS")
    for heading in path_sections:
        for token in extract_backticked_tokens(sections.get(heading, [])):
            target = repo.path / token.rstrip("/")
            if not target.exists():
                errors.append(f"{root_path} references missing path `{token}`")

    command_sections = ("## Common Workflows", "## Verification")
    for heading in command_sections:
        for command in extract_backticked_tokens(sections.get(heading, [])):
            problem = validate_generated_command(repo, command)
            if problem is not None:
                errors.append(f"{root_path} command `{command}` has no valid source: {problem}")
    return errors


def build_backup_entries(scan_payload: dict) -> list[dict]:
    entries: list[dict] = []

    def append_entry(original_path: Path, level: str, repo_name: str | None) -> None:
        exists = original_path.exists()
        entry_id = path_hash(original_path)
        content = original_path.read_bytes() if exists else None
        entries.append(
            {
                "id": entry_id,
                "level": level,
                "repo": repo_name,
                "original_path": original_path.as_posix(),
                "sha256_before": sha256_bytes(content) if content is not None else None,
                "existed_before": exists,
                "restore_action": "restore" if exists else "delete",
            }
        )

    append_entry(Path(scan_payload["codex_source"]), "codex_source", "MyCodexEnv")
    append_entry(Path(scan_payload["codex_runtime"]), "codex_runtime", ".codex")

    for repo in scan_payload["repos"]:
        repo_path = Path(repo["path"])
        append_entry(repo_path / "AGENTS.md", "repo_root", repo["name"])
        for local_agent in repo["local_agents"]:
            append_entry(Path(local_agent), "repo_local", repo["name"])

    for orphan in scan_payload["orphan_local_agents"]:
        append_entry(Path(orphan), "repo_local", None)
    return entries


def render_backup_report(manifest: dict) -> str:
    create_count = sum(1 for entry in manifest["entries"] if not entry["existed_before"])
    restore_count = len(manifest["entries"]) - create_count
    lines = [
        "# AGENTS Backup Report",
        "",
        f"- backup_id: `{manifest['backup_id']}`",
        f"- created_at: `{manifest['created_at']}`",
        f"- restore_count: `{restore_count}`",
        f"- delete_on_restore_count: `{create_count}`",
        "",
        "## Entries",
    ]
    for entry in manifest["entries"]:
        status = "restore" if entry["existed_before"] else "delete"
        lines.append(f"- `{entry['level']}` {entry['original_path']} -> {status}")
    lines.append("")
    return "\n".join(lines)


def command_scan(args: argparse.Namespace) -> int:
    payload = scan_workspace(args.workspace_root, args.codex_source, args.codex_runtime, args.backup_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_backup(args: argparse.Namespace) -> int:
    scan_payload = scan_workspace(args.workspace_root, args.codex_source, args.codex_runtime, args.backup_root)
    backup_id = args.backup_id or datetime.now().strftime("%Y%m%d%H%M%S")
    backup_dir = args.backup_root / backup_id
    if backup_dir.exists():
        fail(f"Backup already exists: {backup_dir}")
    entries_dir = backup_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    entries = build_backup_entries(scan_payload)
    for entry in entries:
        original_path = Path(entry["original_path"])
        if not entry["existed_before"]:
            continue
        shutil.copy2(original_path, entries_dir / f"{entry['id']}.md")
    manifest = {
        "backup_id": backup_id,
        "created_at": datetime.now().isoformat(),
        "workspace_root": args.workspace_root.as_posix(),
        "backup_root": args.backup_root.as_posix(),
        "entries": entries,
    }
    write_text(backup_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    write_text(backup_dir / "report.md", render_backup_report(manifest))
    print(json.dumps({"backup_id": backup_id, "backup_dir": backup_dir.as_posix()}, ensure_ascii=False))
    return 0


def command_generate(args: argparse.Namespace) -> int:
    scan_payload = scan_workspace(args.workspace_root, args.codex_source, args.codex_runtime, args.backup_root)
    actions: list[dict] = []

    if not args.codex_source.exists():
        fail(f"Codex source does not exist: {args.codex_source}")

    args.codex_runtime.parent.mkdir(parents=True, exist_ok=True)
    if args.codex_runtime.exists():
        backup_path = args.codex_runtime.with_name(f"{args.codex_runtime.name}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(args.codex_runtime, backup_path)
    shutil.copy2(args.codex_source, args.codex_runtime)
    actions.append({"path": args.codex_runtime.as_posix(), "action": "update"})

    for repo_payload in scan_payload["repos"]:
        repo = build_repo_record(Path(repo_payload["path"]))
        root_target = repo.root_agents or (repo.path / "AGENTS.md")
        if root_target.exists() and not args.rewrite_existing:
            existing_text = load_text(root_target)
            if GENERATED_MARKER not in existing_text:
                actions.append({"path": root_target.as_posix(), "action": "keep"})
                continue
        content = build_repo_agents(repo)
        write_text(root_target, content)
        actions.append({"path": root_target.as_posix(), "action": "update" if repo.root_agents else "create"})

    if args.backup_id:
        backup_dir = args.backup_root / args.backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        report_path = backup_dir / "report.md"
        manifest_path = backup_dir / "manifest.json"
        if manifest_path.exists():
            prefix = render_backup_report(json.loads(load_text(manifest_path))).rstrip()
        else:
            prefix = load_text(report_path).rstrip() if report_path.exists() else "# AGENTS Backup Report"
        if "## Generation Actions" in prefix:
            prefix = prefix.split("## Generation Actions", 1)[0].rstrip()
        report_lines = [prefix, "", "## Generation Actions", "", f"- backup_id: `{args.backup_id}`", "", "## Actions"]
        for action in actions:
            report_lines.append(f"- `{action['action']}` {action['path']}")
        report_lines.append("")
        write_text(report_path, "\n".join(report_lines))

    print(json.dumps({"actions": actions}, ensure_ascii=False))
    return 0


def command_restore(args: argparse.Namespace) -> int:
    manifest_path = args.backup_root / args.backup_id / "manifest.json"
    if not manifest_path.exists():
        fail(f"Backup manifest not found: {manifest_path}")
    manifest = json.loads(load_text(manifest_path))
    restored = 0
    deleted = 0
    entries_dir = manifest_path.parent / "entries"
    for entry in manifest["entries"]:
        original_path = Path(entry["original_path"])
        if entry["existed_before"]:
            backup_file = entries_dir / f"{entry['id']}.md"
            if not backup_file.exists():
                fail(f"Missing backup entry file: {backup_file}")
            write_text(original_path, load_text(backup_file))
            restored += 1
        elif original_path.exists():
            original_path.unlink()
            deleted += 1
    print(json.dumps({"restored": restored, "deleted": deleted}, ensure_ascii=False))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    scan_payload = scan_workspace(args.workspace_root, args.codex_source, args.codex_runtime, args.backup_root)
    errors: list[str] = []
    if not args.codex_source.exists():
        errors.append(f"missing codex source: {args.codex_source}")
    if not args.codex_runtime.exists():
        errors.append(f"missing codex runtime: {args.codex_runtime}")
    if args.codex_source.exists() and args.codex_runtime.exists():
        if sha256_bytes(args.codex_source.read_bytes()) != sha256_bytes(args.codex_runtime.read_bytes()):
            errors.append("codex source/runtime hash mismatch")
        source_text = load_text(args.codex_source)
        for header in REQUIRED_CODEX_HEADERS:
            if header not in source_text:
                errors.append(f"codex source missing header: {header}")

    for repo_payload in scan_payload["repos"]:
        repo_path = Path(repo_payload["path"])
        root_path = actual_root_agents(repo_path) or (repo_path / "AGENTS.md")
        if not root_path.exists():
            errors.append(f"missing repo root AGENTS: {root_path}")
            continue
        root_text = load_text(root_path)
        is_generated = GENERATED_MARKER in root_text
        if repo_payload["root_agents"] is None and not is_generated:
            errors.append(f"generated repo root missing marker: {root_path}")
        for required in ("## Purpose", "## Read First", "## Verification", "## Subdirectory AGENTS"):
            if is_generated and required not in root_text:
                errors.append(f"{root_path} missing section {required}")
        if is_generated:
            errors.extend(verify_generated_root_agents(build_repo_record(repo_path), root_path, root_text))
        for local_agent in repo_payload["local_agents"]:
            if not Path(local_agent).exists():
                errors.append(f"missing local AGENTS: {local_agent}")
            elif relative_posix(Path(local_agent), repo_path) not in root_text:
                errors.append(f"root AGENTS missing local AGENTS route: {root_path} -> {local_agent}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "repo_count": len(scan_payload["repos"])}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage multi-level AGENTS.md artifacts.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("/Users/kezheng/Codes/CursorDeveloper"),
        help="Workspace root that contains target repositories.",
    )
    common.add_argument(
        "--backup-root",
        type=Path,
        default=Path("/Users/kezheng/Codes/CursorDeveloper/.agents-backups"),
        help="Backup root for AGENTS snapshots.",
    )
    common.add_argument(
        "--codex-source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "codex" / "AGENTS.md",
        help="Source of truth for the Codex-level AGENTS.md.",
    )
    common.add_argument(
        "--codex-runtime",
        type=Path,
        default=Path.home() / ".codex" / "AGENTS.md",
        help="Runtime Codex AGENTS.md target.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", parents=[common])
    scan_parser.set_defaults(handler=command_scan)

    backup_parser = subparsers.add_parser("backup", parents=[common])
    backup_parser.add_argument("--backup-id", help="Explicit backup identifier.")
    backup_parser.set_defaults(handler=command_backup)

    generate_parser = subparsers.add_parser("generate", parents=[common])
    generate_parser.add_argument("--backup-id", help="Attach generation report to an existing backup id.")
    generate_parser.add_argument(
        "--rewrite-existing",
        action="store_true",
        help="Rewrite existing root AGENTS.md files instead of keeping them.",
    )
    generate_parser.set_defaults(handler=command_generate)

    restore_parser = subparsers.add_parser("restore", parents=[common])
    restore_parser.add_argument("--backup-id", required=True, help="Backup id to restore.")
    restore_parser.set_defaults(handler=command_restore)

    verify_parser = subparsers.add_parser("verify", parents=[common])
    verify_parser.set_defaults(handler=command_verify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
