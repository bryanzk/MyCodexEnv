"""S0 probe tests. Run with: python3 -m pytest <this file> -q"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

PROBE = Path.home() / ".codex" / "hooks" / "payload_probe.py"


def run_probe(stdin_text: str, event: str, probe_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CODEX_HARNESS_PROBE_DIR"] = str(probe_dir)
    return subprocess.run(
        [sys.executable, str(PROBE), "--event", event],
        input=stdin_text,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def read_records(probe_dir: Path) -> list[dict]:
    path = probe_dir / "pretooluse-schema.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_valid_payload_is_recorded_and_never_blocks(tmp_path):
    payload = {
        "session_id": "019fcce6-ec3a-71c3-bc4d-1236774ad56f",
        "cwd": "/Users/kezheng/Codes/CursorDeveloper/ShipQ",
        "tool_name": "exec_command",
        "tool_input": {"command": "ls -la", "cwd": "/tmp/elsewhere"},
    }
    result = run_probe(json.dumps(payload), "pre_tool_use", tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    records = read_records(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record["event"] == "pre_tool_use"
    assert record["top_session_id_present"] is True
    assert record["top_cwd_present"] is True
    assert record["tool_input_cwd_present"] is True
    # Top-level and tool_input cwd must be recorded independently.
    assert record["top_cwd"] != record["tool_input_cwd"]
    assert record["top_phase_present"] is False


def test_malformed_input_still_returns_empty_object(tmp_path):
    for bad in ["", "   ", "{not json", "[1,2,3]"]:
        result = run_probe(bad, "pre_tool_use", tmp_path)
        assert result.returncode == 0, bad
        assert result.stdout.strip() == "{}", bad
        assert "Traceback" not in result.stderr, bad


def test_sensitive_values_are_not_persisted(tmp_path):
    marker = "SHOULD-NOT-APPEAR-IN-PROBE-OUTPUT"
    payload = {
        "session_id": "abc-123",
        "cwd": "/tmp/repo",
        "tool_input": {"command": f"echo {marker}", "api_key": marker},
        "prompt": f"line one {marker}\nline two",
    }
    run_probe(json.dumps(payload), "user_prompt_submit", tmp_path)
    raw = (tmp_path / "pretooluse-schema.jsonl").read_text(encoding="utf-8")
    assert marker not in raw
    assert "abc-123" not in raw  # identity stored as digest only
    record = read_records(tmp_path)[0]
    assert record["top_session_id_digest"] and len(record["top_session_id_digest"]) == 12
    assert record["command_length"] > 0
    assert record["prompt_shape"]["field"] == "prompt"
    assert record["prompt_shape"]["line_count"] == 2
    assert "text" not in record["prompt_shape"]


def test_same_identity_yields_same_digest(tmp_path):
    payload = {"session_id": "same-id", "cwd": "/tmp/a"}
    run_probe(json.dumps(payload), "pre_tool_use", tmp_path)
    run_probe(json.dumps(payload), "pre_tool_use", tmp_path)
    records = read_records(tmp_path)
    assert len(records) == 2
    assert records[0]["top_session_id_digest"] == records[1]["top_session_id_digest"]


def test_missing_host_fields_are_reported_as_absent(tmp_path):
    run_probe(json.dumps({"tool_input": {"phase": "development"}}), "pre_tool_use", tmp_path)
    record = read_records(tmp_path)[0]
    assert record["top_session_id_present"] is False
    assert record["top_cwd_present"] is False
    assert record["tool_input_phase_present"] is True
    assert record["top_phase_present"] is False


def test_output_file_permissions_are_owner_only(tmp_path):
    run_probe(json.dumps({"session_id": "x"}), "pre_tool_use", tmp_path)
    path = tmp_path / "pretooluse-schema.jsonl"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
