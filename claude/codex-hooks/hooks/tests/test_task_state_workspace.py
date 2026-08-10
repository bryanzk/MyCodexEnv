"""S1 regression tests: eligibility semantics for git and non-git workspaces."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import task_state  # noqa: E402

SESSION_ID = "12345678-1234-1234-1234-123456789abc"
POLICY = {
    "phases": {
        "planning": {},
        "development": {"allow_repo_write": True},
        "review": {},
        "validation": {},
        "handoff": {},
    }
}


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    home = tmp_path / "codexhome"
    (home / "sessions").mkdir(parents=True)
    monkeypatch.setenv("CODEX_HOME", str(home))
    return home


def write_transcript(codex_home: Path, root_cwd: Path, first_line: str | None) -> Path:
    day_dir = codex_home / "sessions" / "2026" / "08" / "10"
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / f"rollout-2026-08-10-{SESSION_ID}.jsonl"
    text = "please do things" if first_line is None else f"{first_line}\n\nplease do things"
    events = [
        {
            "type": "session_meta",
            "payload": {"id": SESSION_ID, "cwd": str(root_cwd), "thread_source": "user"},
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        },
        {"type": "event_msg", "payload": {"type": "user_message"}},
    ]
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    return path


def resolve(codex_home: Path, root_cwd: Path, current_cwd: Path, first_line="task-mode: implementation"):
    transcript = write_transcript(codex_home, root_cwd, first_line)
    payload = {
        "session_id": SESSION_ID,
        "transcript_path": str(transcript),
        "cwd": str(current_cwd),
    }
    return task_state.resolve_declared_phase(payload, POLICY)


def make_repo(base: Path, name: str) -> Path:
    repo = base / name
    (repo / ".git").mkdir(parents=True)
    return repo


def test_same_repo_different_subdirs(codex_home, tmp_path):
    repo = make_repo(tmp_path, "repo")
    (repo / "a").mkdir()
    (repo / "b").mkdir()
    assert resolve(codex_home, repo / "a", repo / "b") == ("development", "DECLARED")


def test_two_different_repos(codex_home, tmp_path):
    repo_a = make_repo(tmp_path, "repo_a")
    repo_b = make_repo(tmp_path, "repo_b")
    assert resolve(codex_home, repo_a, repo_b) == (None, "ROOT_REPO_MISMATCH")


def test_root_repo_current_non_git(codex_home, tmp_path):
    repo = make_repo(tmp_path, "repo")
    plain = tmp_path / "plain"
    plain.mkdir()
    assert resolve(codex_home, repo, plain) == (None, "ROOT_REPO_MISMATCH")


def test_root_non_git_current_repo(codex_home, tmp_path):
    repo = make_repo(tmp_path, "repo")
    plain = tmp_path / "plain"
    plain.mkdir()
    assert resolve(codex_home, plain, repo) == (None, "ROOT_REPO_MISMATCH")


def test_same_non_git_dir_declares(codex_home, tmp_path):
    plain = tmp_path / "Job Application"
    plain.mkdir()
    assert resolve(codex_home, plain, plain) == ("development", "DECLARED")


def test_two_different_non_git_dirs(codex_home, tmp_path):
    a = tmp_path / "docs_a"
    b = tmp_path / "docs_b"
    a.mkdir()
    b.mkdir()
    assert resolve(codex_home, a, b) == (None, "ROOT_WORKSPACE_MISMATCH")


def test_non_git_symlink_matches_real_path(codex_home, tmp_path):
    real = tmp_path / "docs"
    real.mkdir()
    link = tmp_path / "docs_link"
    link.symlink_to(real, target_is_directory=True)
    assert resolve(codex_home, real, link) == ("development", "DECLARED")


def test_non_git_implementation_maps_to_development(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    phase, _ = resolve(codex_home, plain, plain, first_line="task-mode: implementation")
    assert phase == "development"


def test_non_git_without_marker_stays_fail_closed(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert resolve(codex_home, plain, plain, first_line=None) == (None, "MARKER_NOT_FOUND")


# --- host wrapper blocks prepended to the user's first message ---

WRAPPER = "<recommended_plugins>\nplugin-a: does things\nplugin-b: other\n</recommended_plugins>"


def test_marker_after_host_wrapper_is_parsed(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = f"{WRAPPER}\n\ntask-mode: implementation"
    assert resolve(codex_home, plain, plain, first_line=first) == ("development", "DECLARED")


def test_review_marker_after_host_wrapper(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = f"{WRAPPER}\n\ntask-mode: review"
    assert resolve(codex_home, plain, plain, first_line=first) == ("review", "DECLARED")


def test_marker_after_two_wrappers(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = f"{WRAPPER}\n<host_meta>\nx\n</host_meta>\n\ntask-mode: implementation"
    assert resolve(codex_home, plain, plain, first_line=first) == ("development", "DECLARED")


def test_unclosed_wrapper_fails_closed(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = "<recommended_plugins>\nstuff\n\ntask-mode: implementation"
    assert resolve(codex_home, plain, plain, first_line=first) == (None, "MARKER_NOT_FOUND")


def test_marker_inside_wrapper_is_not_a_declaration(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = "<recommended_plugins>\ntask-mode: implementation\n</recommended_plugins>\n\ndo work"
    assert resolve(codex_home, plain, plain, first_line=first) == (None, "MARKER_NOT_FOUND")


def test_wrapper_then_files_mentioned_block(codex_home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    first = (
        f"{WRAPPER}\n\n# Files mentioned by the user:\n- a.md\n\n"
        "## My request for Codex:\ntask-mode: implementation"
    )
    assert resolve(codex_home, plain, plain, first_line=first) == ("development", "DECLARED")
