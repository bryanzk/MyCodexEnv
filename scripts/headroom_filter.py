#!/usr/bin/env python3
"""Compress command output before pasting it into an agent context."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Literal


Mode = Literal["auto", "search", "log", "diff", "json"]


@dataclass(frozen=True)
class CompressionStats:
    mode: str
    original_chars: int
    compressed_chars: int
    saved_percent: float
    detail: dict[str, Any]


def detect_mode(text: str) -> str:
    stripped = text.lstrip()
    first_lines = [line for line in text.splitlines()[:50] if line.strip()]

    if stripped.startswith(("diff --git ", "--- ")) or "\n@@ " in text:
        return "diff"

    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
        except json.JSONDecodeError:
            pass
        else:
            return "json"

    search_like = 0
    for line in first_lines:
        if re.match(r"^[^:\n]+:\d+:", line):
            search_like += 1
    if first_lines and search_like >= max(2, len(first_lines) // 3):
        return "search"

    return "log"


def install_hint() -> str:
    return (
        "headroom-ai is not installed for this Python interpreter.\n"
        "Recommended isolated install on this machine:\n"
        "  /opt/homebrew/bin/python3.12 -m venv /tmp/headroom\n"
        "  /tmp/headroom/bin/pip install headroom-ai\n"
        "Then run:\n"
        "  command-producing-output | /tmp/headroom/bin/python scripts/headroom_filter.py --mode auto --stats\n"
    )


def _load_headroom():
    os.environ.setdefault("HEADROOM_TELEMETRY", "off")
    try:
        from headroom import SmartCrusher
        from headroom.transforms import DiffCompressor, LogCompressor, SearchCompressor
    except ModuleNotFoundError as exc:
        if exc.name == "headroom":
            raise RuntimeError(install_hint()) from exc
        raise
    return SmartCrusher, DiffCompressor, LogCompressor, SearchCompressor


def compress_text(text: str, mode: Mode, context: str) -> tuple[str, CompressionStats]:
    selected = detect_mode(text) if mode == "auto" else mode
    SmartCrusher, DiffCompressor, LogCompressor, SearchCompressor = _load_headroom()

    if selected == "search":
        result = SearchCompressor().compress(text, context=context)
        compressed = result.compressed
        detail = {
            "original_matches": result.original_match_count,
            "compressed_matches": result.compressed_match_count,
            "files_affected": result.files_affected,
        }
    elif selected == "diff":
        result = DiffCompressor().compress(text, context=context)
        compressed = result.compressed
        detail = {
            "original_lines": result.original_line_count,
            "compressed_lines": result.compressed_line_count,
            "files_affected": result.files_affected,
        }
    elif selected == "json":
        result = SmartCrusher().crush(text, query=context)
        compressed = result.compressed
        detail = {
            "strategy": str(getattr(result, "strategy", "")),
            "was_modified": bool(getattr(result, "was_modified", False)),
        }
    else:
        result = LogCompressor().compress(text, context=context)
        compressed = result.compressed
        detail = {
            "original_lines": result.original_line_count,
            "compressed_lines": result.compressed_line_count,
            "format": str(result.format_detected),
            "stats": result.stats,
        }

    original_chars = len(text)
    compressed_chars = len(compressed)
    saved_percent = 0.0
    if original_chars:
        saved_percent = round((1 - (compressed_chars / original_chars)) * 100, 1)
    stats = CompressionStats(
        mode=selected,
        original_chars=original_chars,
        compressed_chars=compressed_chars,
        saved_percent=saved_percent,
        detail=detail,
    )
    return compressed, stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress stdin with Headroom before sending command output to an agent."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "search", "log", "diff", "json"],
        default="auto",
        help="Compression mode. auto detects common command-output shapes.",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Optional query/context string used by relevance-aware compressors.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Write compact JSON stats to stderr after compressed stdout.",
    )
    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="Print detected mode for stdin and exit without importing Headroom.",
    )
    parser.add_argument(
        "--install-hint",
        action="store_true",
        help="Print the recommended isolated install commands and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.install_hint:
        print(install_hint(), end="")
        return 0

    text = sys.stdin.read()
    if args.detect_only:
        print(detect_mode(text))
        return 0

    try:
        compressed, stats = compress_text(text, args.mode, args.context)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    sys.stdout.write(compressed)
    if compressed and not compressed.endswith("\n"):
        sys.stdout.write("\n")

    if args.stats:
        print(json.dumps(stats.__dict__, ensure_ascii=False), file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
