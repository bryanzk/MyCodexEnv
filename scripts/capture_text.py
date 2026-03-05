#!/usr/bin/env python3
"""Capture frequently used text snippets and classify them automatically."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


CATEGORY_COMMAND = "command"
CATEGORY_PROMPT = "prompt"
CATEGORY_DIALOGUE = "dialogue"
CATEGORY_OTHER = "other"
CATEGORY_CHOICES = {CATEGORY_COMMAND, CATEGORY_PROMPT, CATEGORY_DIALOGUE, CATEGORY_OTHER}


COMMAND_PREFIXES: Iterable[str] = {
    "ls",
    "cd",
    "cp",
    "mv",
    "rm",
    "mkdir",
    "rmdir",
    "touch",
    "cat",
    "less",
    "find",
    "grep",
    "rg",
    "sed",
    "awk",
    "xargs",
    "git",
    "go",
    "npm",
    "pnpm",
    "node",
    "python",
    "python3",
    "uv",
    "pip",
    "pip3",
    "docker",
    "docker-compose",
    "make",
    "curl",
    "wget",
    "ssh",
    "rsync",
    "tar",
    "chmod",
    "chown",
    "sudo",
    "systemctl",
    "export",
    "alias",
    "printf",
    "echo",
    "kill",
    "pkill",
    "ps",
    "top",
    "which",
    "whoami",
    "pwd",
    "uname",
}

PROMPT_KEYWORDS: Iterable[str] = {
    "你是",
    "请",
    "请你",
    "请帮",
    "请帮我",
    "帮我",
    "我想",
    "我需要",
    "可以",
    "能否",
    "你能",
    "麻烦",
    "prompt",
    "instruction",
    "act as",
    "how to",
    "please",
    "could you",
    "can you",
    "write",
    "generate",
    "explain",
    "describe",
    "summarize",
    "建议",
    "帮忙",
}


def has_non_ascii(text: str) -> bool:
    return any(ord(char) > 127 for char in text)


def looks_like_command_line(line: str) -> bool:
    line = line.strip()
    if not line:
        return False

    if re.match(r"^\s*[#$>]", line):
        return True

    tokens = re.split(r"\s+", line)
    first = tokens[0].lower()
    if first in COMMAND_PREFIXES:
        return True

    command_pattern = r"^[A-Za-z0-9._\-/]+(?::[0-9]+)?$"
    if re.match(command_pattern, first) and len(line) > 1:
        return True

    if re.search(r"[;&|]{1,2}|\\\n|\n", line):
        return False

    return False


def looks_like_command(text: str) -> bool:
    if not text.strip():
        return False

    if has_non_ascii(text):
        return False

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False

    if all(looks_like_command_line(ln) for ln in lines[:3]):
        return True

    return looks_like_command_line(lines[0])


def looks_like_prompt(text: str) -> bool:
    lower = text.lower()
    if any(keyword in lower for keyword in PROMPT_KEYWORDS):
        return True

    if re.search(r"[?？]", text):
        return True

    return False


def classify(text: str) -> str:
    if looks_like_command(text):
        return CATEGORY_COMMAND

    if looks_like_prompt(text):
        return CATEGORY_PROMPT

    if has_non_ascii(text):
        return CATEGORY_DIALOGUE

    return CATEGORY_OTHER


def parse_tags(values: List[str]) -> List[str]:
    tags: List[str] = []
    for raw in values:
        parts = [item.strip() for item in raw.split(",") if item.strip()]
        tags.extend(parts)
    return tags


def normalize_category(category: str) -> str:
    if category == "auto":
        return CATEGORY_OTHER
    if category not in CATEGORY_CHOICES:
        raise ValueError(f"Unsupported category: {category}")
    return category


def write_markdown_entry(entry_dir: Path, entry_id: str, created_at: str, category: str, source: str, tags: List[str], text: str) -> str:
    entry_dir.mkdir(parents=True, exist_ok=True)
    entry_path = entry_dir / f"{entry_id}.md"
    tag_line = ", ".join(tags) if tags else ""
    with entry_path.open("w", encoding="utf-8") as fp:
        fp.write(f"# {created_at}\n")
        fp.write(f"- category: {category}\n")
        fp.write(f"- source: {source}\n")
        if tag_line:
            fp.write(f"- tags: {tag_line}\n")
        fp.write("\n")
        fp.write("```text\n")
        fp.write(text.rstrip("\n"))
        fp.write("\n```\n")
    return str(entry_path)


def write_ledger(ledger_path: Path, record: dict) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")


def capture(
    text: str,
    out_dir: Path,
    category: str,
    source: str,
    tags: List[str],
    raw_input: bool,
) -> dict:
    text = text if raw_input else text.rstrip("\n")
    if category == "auto":
        category = classify(text)
    elif category not in CATEGORY_CHOICES:
        raise ValueError(f"Unsupported category: {category}")

    now = datetime.now().astimezone()
    ts = now.isoformat(timespec="seconds")
    date = now.strftime("%Y-%m-%d")
    short_id = uuid.uuid4().hex[:10]
    entry_dir = out_dir / "entries" / date / category
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    entry_id = f"{date}_{now.strftime('%H%M%S')}_{short_id}"

    entry_path = write_markdown_entry(
        entry_dir,
        entry_id=entry_id,
        created_at=ts,
        category=category,
        source=source,
        tags=tags,
        text=text,
    )

    record = {
        "id": entry_id,
        "timestamp": ts,
        "category": category,
        "source": source,
        "tags": tags,
        "text_checksum": checksum,
        "path": entry_path,
        "input_len": len(text),
    }

    write_ledger(out_dir / "ledger.jsonl", record)
    return record


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自动记录并分类常用文本（命令行/提示/对话）")
    parser.add_argument("text", nargs="?", help="要记录的文本；留空时从标准输入读取")
    parser.add_argument("--category", default="auto", choices=sorted(CATEGORY_CHOICES | {"auto"}))
    parser.add_argument("--source", default="manual", help="记录来源标签，例如: cli, api, convo")
    parser.add_argument("--out-dir", default="text_records", help="记录目录（默认：text_records）")
    parser.add_argument("--tag", action="append", default=[], help="标签，支持逗号分隔")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON（默认兼容友好文字）")
    parser.add_argument("--raw", action="store_true", help="保留输入中的空行，不做尾部 trim（默认会去掉末尾换行）")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    text = args.text
    if text is None:
        text = sys.stdin.read()

    if not text:
        print("No input text provided.", file=sys.stderr)
        return 1

    tags = parse_tags(args.tag)
    out_dir = Path(args.out_dir).expanduser().resolve()
    normalized_category = normalize_category(args.category)

    record = capture(
        text=text,
        out_dir=out_dir,
        category=normalized_category if args.category != "auto" else "auto",
        source=args.source,
        tags=tags,
        raw_input=args.raw,
    )

    if args.json:
        print(json.dumps(record, ensure_ascii=False))
    else:
        print(f"[{record['timestamp']}] {record['category']} -> {record['path']}")
        print(f"tags: {', '.join(tags) if tags else 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
