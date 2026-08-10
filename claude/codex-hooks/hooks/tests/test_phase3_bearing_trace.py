"""Phase 3 tests: S4 session-start bearing lines and S5 gate trace."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import harness_guard  # noqa: E402
import harness_observer  # noqa: E402

BEARING = HOOKS_DIR / "session_bearing.py"
POLICY = json.loads((HOOKS_DIR.parent / "tool-policy.json").read_text(encoding="utf-8"))


@pytest.fixture
def env(tmp_path, monkeypatch):
    codex = tmp_path / "codexhome"
    (codex / "runtime").mkdir(parents=True)
    (codex / "runtime" / "tool-policy.json").write_text(json.dumps(POLICY), encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(codex))
    monkeypatch.delenv("CODEX_HARNESS_PHASE", raising=False)
    governed = tmp_path / "Codes"
    governed.mkdir()
    outside = tmp_path / "Downloads"
    outside.mkdir()
    scope = {
        "governed_roots": [str(governed)],
        "protected_roots": [str(codex)],
        "out_of_scope_mode": "allow",
    }
    (codex / "runtime" / "harness-scope.json").write_text(json.dumps(scope), encoding="utf-8")
    return codex, governed, outside


def run_bearing(cwd: Path, codex: Path) -> str:
    import os

    env_vars = dict(os.environ, CODEX_HOME=str(codex))
    env_vars.pop("CODEX_HARNESS_PHASE", None)
    proc = subprocess.run(
        [sys.executable, str(BEARING)],
        input=json.dumps({"cwd": str(cwd)}),
        capture_output=True,
        text=True,
        env=env_vars,
    )
    return proc.stdout


def context_of(stdout: str) -> str:
    if not stdout.strip():
        return ""
    return json.loads(stdout)["hookSpecificOutput"]["additionalContext"]


# --- S4 bearing lines ---

def test_bearing_out_of_scope(env):
    codex, governed, outside = env
    context = context_of(run_bearing(outside, codex))
    assert "out-of-scope" in context and "still blocked" in context


def test_bearing_governed_unknown_suggests_declare(env):
    codex, governed, outside = env
    proj = governed / "proj"
    proj.mkdir()
    context = context_of(run_bearing(proj, codex))
    assert "phase=unknown" in context
    assert "codex-task declare" in context


def test_bearing_governed_self_declared_phase(env):
    codex, governed, outside = env
    proj = governed / "proj"
    proj.mkdir()
    cli = HOOKS_DIR.parent / "bin" / "codex-task"
    import os

    env_vars = dict(os.environ, CODEX_HOME=str(codex))
    subprocess.run(
        [sys.executable, str(cli), "declare", "implementation", "--reason", "t"],
        cwd=str(proj),
        env=env_vars,
        check=True,
        capture_output=True,
    )
    context = context_of(run_bearing(proj, codex))
    assert "phase=development" in context
    assert "source=self_declared" in context


def test_bearing_silent_without_policy(env, tmp_path):
    codex, governed, outside = env
    (codex / "runtime" / "tool-policy.json").unlink()
    assert run_bearing(outside, codex).strip() == ""


# --- S5 gate trace ---

def test_trace_env_source(env, monkeypatch):
    codex, governed, outside = env
    monkeypatch.setenv("CODEX_HARNESS_PHASE", "development")
    phase, _, trace = harness_guard.phase_with_trace({"cwd": str(governed)}, POLICY, None)
    assert phase == "development"
    assert trace["source"] == "env" and trace["env"] == "present"


def test_trace_unknown_records_gate_reasons(env):
    codex, governed, outside = env
    proj = governed / "proj"
    proj.mkdir()
    phase, reason, trace = harness_guard.phase_with_trace({"cwd": str(proj)}, POLICY, None)
    assert phase == "unknown"
    assert trace["source"] == "none"
    assert trace["transcript"] == "NO_TRANSCRIPT"
    assert trace["self_declared"] == "NO_DECLARATION"
    assert trace["snapshot"] is None


def test_trace_snapshot_source(env, tmp_path):
    codex, governed, outside = env
    repo = governed / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "harness-state.md").write_text(
        "## Current Snapshot\n- phase: development\n", encoding="utf-8"
    )
    phase, _, trace = harness_guard.phase_with_trace({"cwd": str(repo)}, POLICY, repo)
    assert phase == "development"
    assert trace["source"] == "snapshot"


def test_trace_self_declared_source(env):
    codex, governed, outside = env
    proj = governed / "proj"
    proj.mkdir()
    cli = HOOKS_DIR.parent / "bin" / "codex-task"
    import os

    env_vars = dict(os.environ, CODEX_HOME=str(codex))
    subprocess.run(
        [sys.executable, str(cli), "declare", "planning", "--reason", "t"],
        cwd=str(proj),
        env=env_vars,
        check=True,
        capture_output=True,
    )
    phase, reason, trace = harness_guard.phase_with_trace({"cwd": str(proj)}, POLICY, None)
    assert phase == "planning"
    assert reason == "SELF_DECLARED"
    assert trace["source"] == "self_declared"


def test_observer_event_includes_phase_trace(env):
    codex, governed, outside = env
    proj = governed / "proj"
    proj.mkdir()
    payload = {"tool_name": "exec_command", "tool_input": {"command": "ls"}, "cwd": str(proj)}
    event = harness_observer.build_event(payload)
    assert event["phase"] == "unknown"
    assert event["phase_trace"]["source"] == "none"
    assert event["phase_trace"]["transcript"] == "NO_TRANSCRIPT"
