#!/usr/bin/env python3
"""Inline the host-neutral Guard core into each host adapter.

A hook is promoted and run as a single file, so the core is not imported at
runtime: its body is copied between the BEGIN/END markers of every adapter.
`--check` (default) fails when an adapter's copy differs from the core;
`--write` refreshes the copies. Changing a copy under `codex/` changes the
source digest, which only the owner may approve.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = Path("dhf/core/guard_core.py")
ADAPTERS = (
    Path("codex/hooks/harness_guard.py"),
    Path("dhf/adapters/claude_code/dhf_guard.py"),
)
BODY_MARKER = "# --- core body:"
BEGIN_MARKER = "# --- BEGIN DHF GUARD CORE "
END_MARKER = "# --- END DHF GUARD CORE ---"


def core_body(core_text: str) -> str:
    lines = core_text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith(BODY_MARKER)]
    if len(starts) != 1:
        raise ValueError(f"{CORE} must contain exactly one line starting with {BODY_MARKER!r}")
    return "\n".join(lines[starts[0] + 1 :]).strip("\n")


def render(adapter_text: str, body: str) -> str:
    lines = adapter_text.splitlines()
    begins = [index for index, line in enumerate(lines) if line.startswith(BEGIN_MARKER)]
    ends = [index for index, line in enumerate(lines) if line == END_MARKER]
    if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0]:
        raise ValueError("adapter must contain exactly one BEGIN marker followed by one END marker")
    merged = lines[: begins[0] + 1] + body.splitlines() + lines[ends[0] :]
    return "\n".join(merged) + "\n"


def stale_adapters(root: Path = ROOT) -> list[Path]:
    body = core_body((root / CORE).read_text(encoding="utf-8"))
    stale = []
    for adapter in ADAPTERS:
        text = (root / adapter).read_text(encoding="utf-8")
        if render(text, body) != text:
            stale.append(adapter)
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh the inlined core in every adapter")
    parser.add_argument("--check", action="store_true", help="fail when an adapter's copy is stale (default)")
    args = parser.parse_args()
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    try:
        stale = stale_adapters()
        if args.write:
            body = core_body((ROOT / CORE).read_text(encoding="utf-8"))
            for adapter in stale:
                path = ROOT / adapter
                path.write_text(render(path.read_text(encoding="utf-8"), body), encoding="utf-8")
                print(f"UPDATED:{adapter}")
            stale = stale_adapters()
    except (OSError, ValueError) as error:
        print(f"ERROR:{error}", file=sys.stderr)
        return 2
    for adapter in stale:
        print(f"STALE:{adapter}")
    if stale:
        print(f"run: python3 scripts/build_guard_bundle.py --write", file=sys.stderr)
        return 1
    print("guard bundle consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
