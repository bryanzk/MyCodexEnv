#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SKILL_FILENAME = "SKILL.md"
TEXT_SUFFIXES = {".jsonl", ".md", ".txt"}
REPO_REF_SUFFIXES = {".md", ".py", ".sh", ".toml", ".json", ".jsonl", ".yaml", ".yml"}
DEFAULT_EXCLUDED_REPO_REF_DIRS = {".git", "node_modules", "__pycache__", "stencils", "fixtures"}
DEFAULT_EXCLUDED_REPO_REF_FILES = {"audit_skills.py"}
DEFAULT_EXCLUDED_REPO_REF_PREFIXES = ("docs/skill-governance-",)


@dataclass
class SkillRecord:
    name: str
    sources: set[str] = field(default_factory=set)
    paths: dict[str, str] = field(default_factory=dict)
    hashes: dict[str, str] = field(default_factory=dict)
    description: str = ""
    command_loads: int = 0
    runtime_loads: int = 0
    explicit_mentions: int = 0
    first_seen: str | None = None
    last_seen: str | None = None
    repo_refs: int = 0
    repo_ref_files: list[str] = field(default_factory=list)

    @property
    def strong_signal(self) -> int:
        return self.command_loads + self.runtime_loads

    @property
    def total_signal(self) -> int:
        return self.strong_signal + self.explicit_mentions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit managed Codex skills without mutating runtime state.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing codex/skills and optional .agents/skills.")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--include-mentions", action="store_true", help="Treat [$skill] user mentions as usage signal.")
    parser.add_argument("--max-candidates", type=int, default=80, help="Maximum candidates per rendered section.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def skill_description(text: str) -> str:
    for line in text.splitlines()[:30]:
        stripped = line.strip()
        if stripped.startswith("description:"):
            return stripped.removeprefix("description:").strip().strip('"')[:220]
    for line in text.splitlines()[:8]:
        stripped = line.strip()
        if stripped and not stripped.startswith("---") and not stripped.startswith("name:"):
            return stripped[:220]
    return ""


def add_date(record: SkillRecord, path: Path) -> None:
    match = re.search(r"(20\d\d)[/-](\d\d)[/-](\d\d)|(20\d\d-\d\d-\d\d)", str(path))
    if not match:
        return
    if match.group(1):
        date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    else:
        date = match.group(4)
    if record.first_seen is None or date < record.first_seen:
        record.first_seen = date
    if record.last_seen is None or date > record.last_seen:
        record.last_seen = date


def collect_skills(repo_root: Path, codex_home: Path) -> dict[str, SkillRecord]:
    sources = {
        "repo": repo_root / "codex" / "skills",
        "global": codex_home / "skills",
        "agents": repo_root / ".agents" / "skills",
    }
    records: dict[str, SkillRecord] = {}
    for source, base in sources.items():
        if not base.exists():
            continue
        for skill_file in sorted(base.glob(f"*/{SKILL_FILENAME}")):
            name = skill_file.parent.name
            record = records.setdefault(name, SkillRecord(name=name))
            record.sources.add(source)
            record.paths[source] = str(skill_file)
            data = skill_file.read_bytes()
            record.hashes[source] = hashlib.sha256(data).hexdigest()
            if source == "repo" or not record.description:
                record.description = skill_description(data.decode("utf-8", errors="ignore"))
    return records


def iter_history_files(codex_home: Path) -> list[Path]:
    files: list[Path] = []
    for base in [
        codex_home / "sessions",
        codex_home / "archived_sessions",
        codex_home / "memories" / "rollout_summaries",
    ]:
        if not base.exists():
            continue
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix in TEXT_SUFFIXES:
                    files.append(path)
    for path in [codex_home / "session_index.jsonl", codex_home / "memories" / "MEMORY.md"]:
        if path.exists():
            files.append(path)
    return files


def apply_history_signals(records: dict[str, SkillRecord], codex_home: Path) -> int:
    command_re = re.compile(r"superpowers-codex use-skill ([A-Za-z0-9_.:-]+)")
    loading_re = re.compile(r"Loading (?:personal|system|superpowers )?skill: ([A-Za-z0-9_.:-]+)")
    mention_re = re.compile(r"\[\$([A-Za-z0-9_.:-]+)\]")
    files = iter_history_files(codex_home)
    for path in files:
        try:
            text = read_text(path)
        except OSError:
            continue
        for regex, field_name in [
            (command_re, "command_loads"),
            (loading_re, "runtime_loads"),
            (mention_re, "explicit_mentions"),
        ]:
            for match in regex.finditer(text):
                name = match.group(1).split("/")[-1]
                record = records.get(name)
                if record is None:
                    continue
                setattr(record, field_name, getattr(record, field_name) + 1)
                add_date(record, path)
    return len(files)


def apply_repo_references(records: dict[str, SkillRecord], repo_root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(repo_root):
        rel_parts = set(Path(dirpath).relative_to(repo_root).parts)
        if rel_parts & DEFAULT_EXCLUDED_REPO_REF_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if name not in DEFAULT_EXCLUDED_REPO_REF_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix not in REPO_REF_SUFFIXES:
                continue
            rel_path = str(path.relative_to(repo_root))
            if path.name in DEFAULT_EXCLUDED_REPO_REF_FILES:
                continue
            if any(rel_path.startswith(prefix) for prefix in DEFAULT_EXCLUDED_REPO_REF_PREFIXES):
                continue
            try:
                text = read_text(path)
            except OSError:
                continue
            for name, record in records.items():
                if name not in text:
                    continue
                if path.name == SKILL_FILENAME and path.parent.name == name:
                    continue
                count = text.count(name)
                record.repo_refs += count
                if count and len(record.repo_ref_files) < 3:
                    record.repo_ref_files.append(rel_path)


def record_json(record: SkillRecord) -> dict[str, Any]:
    return {
        "name": record.name,
        "sources": sorted(record.sources),
        "strong_signal": record.strong_signal,
        "command_loads": record.command_loads,
        "runtime_loads": record.runtime_loads,
        "explicit_mentions": record.explicit_mentions,
        "total_signal": record.total_signal,
        "repo_refs": record.repo_refs,
        "repo_ref_files": record.repo_ref_files,
        "first_seen": record.first_seen,
        "last_seen": record.last_seen,
        "description": record.description,
        "hashes": {key: value[:12] for key, value in sorted(record.hashes.items())},
    }


def build_summary(records: dict[str, SkillRecord], history_files_scanned: int, include_mentions: bool) -> dict[str, Any]:
    all_records = sorted(records.values(), key=lambda item: item.name)
    signal_attr = "total_signal" if include_mentions else "strong_signal"

    def signal(record: SkillRecord) -> int:
        return getattr(record, signal_attr)

    repo_unused = [record for record in all_records if "repo" in record.sources and signal(record) == 0]
    low_ref = [record for record in repo_unused if record.repo_refs <= 2]
    medium_ref = [record for record in repo_unused if 3 <= record.repo_refs <= 15]
    high_ref = [record for record in repo_unused if record.repo_refs > 15]
    global_only_unused = [record for record in all_records if record.sources == {"global"} and signal(record) == 0]
    agent_duplicates = [
        record
        for record in all_records
        if "agents" in record.sources and ("repo" in record.sources or "global" in record.sources)
    ]
    gstack_alias_pairs = []
    for record in all_records:
        if not record.name.startswith("gstack-"):
            continue
        base = records.get(record.name.removeprefix("gstack-"))
        if base:
            gstack_alias_pairs.append({"alias": record_json(record), "base": record_json(base)})

    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "history_files_scanned": history_files_scanned,
        "usage_signal_mode": signal_attr,
        "counts": {
            "unique_skills": len(records),
            "repo": sum(1 for record in all_records if "repo" in record.sources),
            "global": sum(1 for record in all_records if "global" in record.sources),
            "agents": sum(1 for record in all_records if "agents" in record.sources),
            "repo_missing_from_global": sum(1 for record in all_records if "repo" in record.sources and "global" not in record.sources),
            "global_not_repo": sum(1 for record in all_records if "global" in record.sources and "repo" not in record.sources),
        },
        "repo_missing_from_global": [
            record_json(record) for record in all_records if "repo" in record.sources and "global" not in record.sources
        ],
        "repo_unused": {
            "total": len(repo_unused),
            "low_ref": [record_json(record) for record in low_ref],
            "medium_ref": [record_json(record) for record in medium_ref],
            "high_ref": [record_json(record) for record in high_ref],
        },
        "global_only_unused": [record_json(record) for record in global_only_unused],
        "agent_duplicates": [record_json(record) for record in agent_duplicates],
        "gstack_alias_pairs": gstack_alias_pairs,
        "top_used": [
            record_json(record)
            for record in sorted(all_records, key=lambda item: (-signal(item), -item.repo_refs, item.name))[:40]
        ],
    }


def render_records(records: list[dict[str, Any]], limit: int) -> list[str]:
    if not records:
        return ["- none"]
    lines = []
    for record in records[:limit]:
        files = ", ".join(record["repo_ref_files"]) if record["repo_ref_files"] else "none"
        lines.append(
            f"- `{record['name']}`: sources={','.join(record['sources'])}; "
            f"strong={record['strong_signal']}; mentions={record['explicit_mentions']}; "
            f"repo_refs={record['repo_refs']}; refs={files}"
        )
    if len(records) > limit:
        lines.append(f"- ... {len(records) - limit} more")
    return lines


def render_markdown(summary: dict[str, Any], max_candidates: int) -> str:
    counts = summary["counts"]
    lines = [
        "# Skill Governance Audit",
        "",
        f"- timestamp: `{summary['timestamp']}`",
        f"- history_files_scanned: `{summary['history_files_scanned']}`",
        f"- usage_signal_mode: `{summary['usage_signal_mode']}`",
        f"- unique_skills: `{counts['unique_skills']}`",
        f"- repo_skills: `{counts['repo']}`",
        f"- global_skills: `{counts['global']}`",
        f"- agents_skills: `{counts['agents']}`",
        f"- repo_missing_from_global: `{counts['repo_missing_from_global']}`",
        f"- global_not_repo: `{counts['global_not_repo']}`",
        "",
        "## First-pass Decommission Candidates",
        "",
        "These repo-managed skills have no usage signal under the selected mode and at most two repo references.",
        *render_records(summary["repo_unused"]["low_ref"], max_candidates),
        "",
        "## Needs Routing Review",
        "",
        "These repo-managed skills have no usage signal but have some repo references, usually router docs, tests, or neighboring skills.",
        *render_records(summary["repo_unused"]["medium_ref"], max_candidates),
        "",
        "## Runtime-only Unused Candidates",
        "",
        "These are present only in global runtime under the selected mode. Treat gstack aliases as compatibility candidates, not immediate delete targets.",
        *render_records(summary["global_only_unused"], max_candidates),
        "",
        "## Duplicate Source Candidates",
        "",
        "These also exist under `.agents/skills`; identical hashes are source duplication rather than content drift.",
        *render_records(summary["agent_duplicates"], max_candidates),
        "",
        "## Gstack Alias Pairs",
    ]
    for pair in summary["gstack_alias_pairs"][:max_candidates]:
        alias = pair["alias"]
        base = pair["base"]
        lines.append(
            f"- `{alias['name']}` -> `{base['name']}`: "
            f"alias_strong={alias['strong_signal']}; base_strong={base['strong_signal']}; "
            f"base_sources={','.join(base['sources'])}"
        )
    if len(summary["gstack_alias_pairs"]) > max_candidates:
        lines.append(f"- ... {len(summary['gstack_alias_pairs']) - max_candidates} more")
    lines.extend(
        [
            "",
            "## Top Used",
            *render_records(summary["top_used"], max_candidates),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve(strict=False)
    codex_home = Path(args.codex_home).expanduser().resolve(strict=False)
    records = collect_skills(repo_root, codex_home)
    history_count = apply_history_signals(records, codex_home)
    apply_repo_references(records, repo_root)
    summary = build_summary(records, history_count, args.include_mentions)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary, args.max_candidates))
    return 0


if __name__ == "__main__":
    sys.exit(main())
