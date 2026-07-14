#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence


def run_legacy(mode: str, argv: Sequence[str] | None = None) -> int:
    """Route one read-only status mode through its compatibility CLI."""
    forwarded = list(argv) if argv is not None else None
    if mode == "recover":
        from harness_status_recover import main as legacy_main
    elif mode == "runtime":
        from harness_status_runtime import main as legacy_main
    elif mode == "evidence":
        from harness_status_evidence import main as legacy_main
    else:
        raise ValueError(f"unknown status mode: {mode}")
    return legacy_main(forwarded)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query Harness Runtime status through one read-only entry point.")
    parser.add_argument("command", choices=["status"])
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--runtime", action="store_true", help="Show observable Codex runtime configuration.")
    modes.add_argument("--evidence", action="store_true", help="Summarize local harness evidence.")
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] != "status":
        parser.parse_args(raw)
        return 0

    forwarded = raw[1:]
    runtime_count = forwarded.count("--runtime")
    evidence_count = forwarded.count("--evidence")
    if runtime_count + evidence_count > 1:
        parser.error("argument --evidence: not allowed with argument --runtime")
    if runtime_count:
        forwarded.remove("--runtime")
        return run_legacy("runtime", forwarded)
    if evidence_count:
        forwarded.remove("--evidence")
        return run_legacy("evidence", forwarded)
    return run_legacy("recover", forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
