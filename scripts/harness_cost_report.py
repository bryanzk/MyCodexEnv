#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


TOKEN_FIELDS = {
    "input": "input_tokens",
    "cached_input": "cached_input_tokens",
    "output": "output_tokens",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only token and tool-cost report for one Codex rollout.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--session", help="Session id or unique rollout filename suffix")
    source.add_argument("--rollout", type=Path, help="Exact rollout JSONL path (primarily for fixtures)")
    parser.add_argument("--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--git-head")
    parser.add_argument("--codex-config-sha256")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def resolve_rollout(args: argparse.Namespace) -> Path:
    if args.rollout:
        path = args.rollout.expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"rollout not found: {path}")
        return path
    root = args.sessions_root.expanduser().resolve()
    matches = sorted(root.glob(f"**/rollout-*{args.session}*.jsonl"))
    if len(matches) != 1:
        raise ValueError(f"session must resolve to exactly one rollout, found {len(matches)}: {args.session}")
    return matches[0]


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def usage_view(raw: dict[str, Any]) -> dict[str, int]:
    values = {output: int(raw.get(source, 0) or 0) for output, source in TOKEN_FIELDS.items()}
    values["uncached_input"] = max(0, values["input"] - values["cached_input"])
    return values


def report(path: Path) -> dict[str, Any]:
    tools: Counter[str] = Counter()
    turn_requests: Counter[str] = Counter()
    turn_input_sum: Counter[str] = Counter()
    malformed = 0
    first_time: datetime | None = None
    last_time: datetime | None = None
    session_id: str | None = None
    parent_id: str | None = None
    compaction_ordinal = 0
    current_turn: str | None = None
    turn_order: list[str] = []
    seen_turns: set[str] = set()
    turn_latest: dict[str, tuple[str | None, dict[str, Any], int]] = {}
    last_total: dict[str, Any] | None = None
    last_total_signature: tuple[tuple[str, int], ...] | None = None
    previous_input_total = 0
    requests_total = 0

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        timestamp = parse_timestamp(event.get("timestamp"))
        if timestamp:
            first_time = timestamp if first_time is None else min(first_time, timestamp)
            last_time = timestamp if last_time is None else max(last_time, timestamp)
        event_type = event.get("type")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if event_type == "session_meta":
            session_id = payload.get("session_id") or payload.get("id") or session_id
            parent_id = payload.get("parent_session_id") or payload.get("parent_thread_id") or parent_id
        elif event_type == "turn_context":
            current_turn = str(payload.get("turn_id") or f"turn-{len(turn_order) + 1}")
            if current_turn not in seen_turns:
                turn_order.append(current_turn)
                seen_turns.add(current_turn)
        elif event_type == "compacted":
            compaction_ordinal += 1
        elif event_type == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
            name = payload.get("name")
            if isinstance(name, str) and name:
                tools[name] += 1
        elif event_type == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
            total = info.get("total_token_usage")
            latest = info.get("last_token_usage")
            if not isinstance(total, dict) or not isinstance(latest, dict):
                continue
            last_total = total
            signature = tuple(sorted(
                (key, int(value or 0)) for key, value in total.items()
                if isinstance(value, (int, float))
            ))
            if signature == last_total_signature:
                continue
            input_total = int(total.get("input_tokens", 0) or 0)
            if input_total < previous_input_total:
                raise ValueError("cumulative input token total decreased within one rollout")
            row = (event.get("timestamp"), latest, compaction_ordinal)
            turn_key = current_turn or "turn-1"
            if turn_key not in seen_turns:
                turn_order.append(turn_key)
                seen_turns.add(turn_key)
            turn_latest[turn_key] = row
            turn_requests[turn_key] += 1
            turn_input_sum[turn_key] += input_total - previous_input_total
            previous_input_total = input_total
            last_total_signature = signature
            requests_total += 1

    if last_total is None:
        raise ValueError(f"no token_count events found: {path.name}")

    turns = []
    for turn_id in turn_order:
        if turn_id not in turn_latest:
            turns.append({"index": len(turns) + 1, "turn_id": turn_id, "status": "no_usage_event"})
            continue
        timestamp, raw_usage, ordinal = turn_latest[turn_id]
        turns.append({"index": len(turns) + 1, "turn_id": turn_id, "timestamp": timestamp,
                      **usage_view(raw_usage), "requests": turn_requests[turn_id],
                      "input_sum": turn_input_sum[turn_id], "compaction_ordinal": ordinal})
    totals = usage_view(last_total)
    totals["cache_hit_rate"] = (totals["cached_input"] / totals["input"] if totals["input"] else 0.0)
    totals["requests_total"] = requests_total
    if sum(turn.get("input_sum", 0) for turn in turns) != totals["input"]:
        raise ValueError("turn input sums do not reconcile to the final cumulative input total")
    wall_seconds = ((last_time - first_time).total_seconds() if first_time and last_time else 0.0)
    return {
        "session_id": session_id or path.stem.removeprefix("rollout-"),
        "rollout": path.name,
        "subagent_attribution": ({"parent_session_id": parent_id} if parent_id else "not_available"),
        "subagent_attribution_reason": "No independent child rollout can be linked from the parent rollout metadata.",
        "totals": totals,
        "turns": turns,
        "tool_calls": dict(sorted(tools.items())),
        "wall_seconds": wall_seconds,
        "malformed_lines": malformed,
    }


def main() -> int:
    args = parse_args()
    try:
        result = report(resolve_rollout(args))
        identity_args = (args.baseline_dir, args.git_head, args.codex_config_sha256)
        if any(identity_args):
            if not all(identity_args):
                raise ValueError("--baseline-dir, --git-head, and --codex-config-sha256 must be used together")
            baseline_dir = args.baseline_dir.expanduser().resolve()
            if not baseline_dir.is_dir():
                raise ValueError(f"baseline directory not found: {baseline_dir}")
            old_hashes = sorted({
                existing.get("codex_config_sha256")
                for path in baseline_dir.glob("*.json")
                if (existing := json.loads(path.read_text(encoding="utf-8"))).get("git_head") == args.git_head
                and existing.get("codex_config_sha256") != args.codex_config_sha256
            })
            result.update({"git_head": args.git_head,
                           "codex_config_sha256": args.codex_config_sha256,
                           "identity_drift": bool(old_hashes)})
            if old_hashes:
                print(f"WARN identity drift: {old_hashes[0][:8]} -> {args.codex_config_sha256[:8]}",
                      file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        totals = result["totals"]
        print(f"session={result['session_id']} turns={len(result['turns'])} wall_seconds={result['wall_seconds']:.3f}")
        print(f"input={totals['input']} cached={totals['cached_input']} "
              f"uncached={totals['uncached_input']} output={totals['output']}")
        print("tool_calls=" + json.dumps(result["tool_calls"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
