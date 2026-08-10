#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def git_root(cwd: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return cwd
    root = result.stdout.strip()
    return Path(root) if root else cwd


def split_words(name: str) -> list[str]:
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", name)
    parts: list[str] = []
    for chunk in normalized.split():
        parts.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", chunk))
    return [part for part in parts if part]


def infer_project_code(repo_name: str) -> str:
    words = split_words(repo_name)
    if len(words) >= 2:
        return "".join(word[0] for word in words[:6]).upper()
    if words:
        token = words[0].upper()
        return token[: min(max(len(token), 2), 6)]
    compact = re.sub(r"[^A-Za-z0-9]", "", repo_name).upper()
    return compact[:6] or "PROJ"


def build_message(cwd_value: str) -> str:
    cwd = Path(cwd_value or ".").resolve()
    root = git_root(cwd)
    project_code = infer_project_code(root.name)
    date_str = datetime.now().strftime("%Y%m%d")
    example = f"{project_code}-{date_str}-summary"
    return (
        "新建会话命名规则：所有项目的新会话标题统一使用 "
        f"`<项目缩写>-<YYYYMMDD>-<概要>`。当前工作区建议项目缩写为 "
        f"`{project_code}`，示例：`{example}`。如果当前会话尚未命名或标题不符合规范，"
        "请立即按此格式命名。"
    )


def main() -> int:
    payload = load_payload()
    message = build_message(str(payload.get("cwd", ".")))
    response = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": message,
        },
    }
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
