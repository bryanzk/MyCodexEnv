#!/usr/bin/env python3
import subprocess
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BOOTSTRAP = ROOT / "bootstrap.sh"
SYNC = ROOT / "scripts" / "sync_codex_home.sh"
SYNC_CLAUDE = ROOT / "scripts" / "sync_claude_home.sh"
VERIFY = ROOT / "scripts" / "verify_codex_env.sh"


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def require(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        sys.exit(1)


def count_top_dirs(path: Path) -> int:
    return len([item for item in path.iterdir() if item.is_dir()])


def make_fake_eigenphi(root: Path) -> Path:
    backend = root / "eigenphi-backend-go"
    entry = backend / "cmd" / "mcp-server"
    entry.mkdir(parents=True, exist_ok=True)
    (entry / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
    return backend


def test_bootstrap_requires_argument():
    code, out, err = run([str(BOOTSTRAP)])
    require(code != 0, "bootstrap should fail when required argument is missing")
    text = f"{out}\n{err}"
    require("--eigenphi-backend-root is required" in text, "missing required-argument error message")
    print("[PASS] bootstrap required argument check")


def test_sync_requires_entrypoint_file():
    with tempfile.TemporaryDirectory() as tmp:
        missing_backend = Path(tmp) / "missing-backend"
        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--eigenphi-backend-root",
                str(missing_backend),
                "--codex-home",
                str(Path(tmp) / ".codex"),
                "--skip-superpowers-sync",
            ]
        )
        require(code != 0, "sync should fail when backend root is invalid")
        require("Invalid eigenphi backend root" in f"{out}\n{err}", "expected invalid root error")
    print("[PASS] sync invalid backend root check")


def test_sync_renders_template_and_copies_skills():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_home = tmp_path / ".codex"
        backend = make_fake_eigenphi(tmp_path)

        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--eigenphi-backend-root",
                str(backend),
                "--codex-home",
                str(codex_home),
                "--skip-superpowers-sync",
            ]
        )
        require(code == 0, f"sync failed: {err or out}")

        rendered = (codex_home / "config.toml").read_text(encoding="utf-8")
        require("${EIGENPHI_BACKEND_ROOT}" not in rendered, "template placeholder should be replaced")
        require(str(backend / "cmd" / "mcp-server" / "main.go") in rendered, "rendered MCP path mismatch")
        require((codex_home / "AGENTS.md").exists(), "AGENTS.md should be copied")
        require((codex_home / "workflow" / "rules" / "behaviors.md").exists(), "codex workflow rules should be copied")

        expected_skills = count_top_dirs(ROOT / "codex" / "skills")
        actual_skills = count_top_dirs(codex_home / "skills")
        require(actual_skills == expected_skills, f"skills count mismatch: {actual_skills} != {expected_skills}")

    print("[PASS] sync render + skills copy")


def test_sync_claude_injects_integration_block():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        claude_home = tmp_path / ".claude"
        claude_home.mkdir(parents=True, exist_ok=True)
        # 模拟用户已有自定义内容，验证不会被覆盖丢失。
        (claude_home / "CLAUDE.md").write_text("# Existing Profile\n\ncustom=true\n", encoding="utf-8")

        code, out, err = run(
            [
                str(SYNC_CLAUDE),
                "--repo-root",
                str(ROOT),
                "--claude-home",
                str(claude_home),
            ]
        )
        require(code == 0, f"sync_claude failed: {err or out}")

        main_file = claude_home / "CLAUDE.md"
        content = main_file.read_text(encoding="utf-8")
        require("custom=true" in content, "existing CLAUDE.md content should be preserved")
        require("ccwf:integration:start" in content, "integration block start marker missing")
        require((claude_home / "workflow" / "rules" / "behaviors.md").exists(), "workflow rules should be synced")
        require((claude_home / "workflow" / "scripts" / "scan_skill_security.sh").exists(), "security scan script should be synced")

    print("[PASS] sync claude workflow + integration block")


def test_verify_after_full_sync():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_home = tmp_path / ".codex"
        claude_home = tmp_path / ".claude"
        backend = make_fake_eigenphi(tmp_path)

        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--eigenphi-backend-root",
                str(backend),
                "--codex-home",
                str(codex_home),
            ]
        )
        require(code == 0, f"full sync failed: {err or out}")

        code, out, err = run(
            [
                str(SYNC_CLAUDE),
                "--repo-root",
                str(ROOT),
                "--claude-home",
                str(claude_home),
            ]
        )
        require(code == 0, f"claude sync failed: {err or out}")

        code, out, err = run(
            [
                str(VERIFY),
                "--repo-root",
                str(ROOT),
                "--codex-home",
                str(codex_home),
                "--claude-home",
                str(claude_home),
            ]
        )
        require(code == 0, f"verify failed: {err or out}")
        require("Verification passed." in out, "verify success message missing")

    print("[PASS] full sync + verify")


def run_capture_script(capture_args):
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "capture_text.py"),
        "--json",
    ] + capture_args
    code, out, err = run(cmd)
    if code != 0:
        raise RuntimeError(f"capture script failed: {out or err}")
    try:
        payload = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"capture output is not JSON: {out}") from exc
    return payload


def test_capture_text_auto_classifies_input_types():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "text_records"

        command_record = run_capture_script(
            [
                "--out-dir",
                str(out_dir),
                "git status --short",
            ]
        )
        today = datetime.now().strftime("%Y-%m-%d")
        require(
            command_record["category"] == "command",
            f"expected command category, got {command_record['category']}",
        )
        require(
            (out_dir / command_record["path"]).exists(),
            "command record markdown file should exist",
        )
        require(
            (out_dir / "entries" / today / "command").exists(),
            "command category directory should exist",
        )
        require((out_dir / "ledger.jsonl").exists(), "ledger file should exist")

        prompt_record = run_capture_script(
            [
                "--out-dir",
                str(out_dir),
                "请帮我写一段用于复盘的 prompt。",
            ]
        )
        require(
            prompt_record["category"] == "prompt",
            f"expected prompt category, got {prompt_record['category']}",
        )

        dialogue_record = run_capture_script(
            [
                "--out-dir",
                str(out_dir),
                "我们今天下午复查下任务进度吧。",
            ]
        )
        require(
            dialogue_record["category"] == "dialogue",
            f"expected dialogue category, got {dialogue_record['category']}",
        )

        forced_dialogue = run_capture_script(
            [
                "--out-dir",
                str(out_dir),
                "--category",
                "dialogue",
                "git add .",
            ]
        )
        require(
            forced_dialogue["category"] == "dialogue",
            f"expected forced dialogue category, got {forced_dialogue['category']}",
        )

        ledger = (out_dir / "ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
        require(len(ledger) == 4, f"expected 4 ledger entries, got {len(ledger)}")

    print("[PASS] capture_text auto classification and persistence")


def main():
    require(BOOTSTRAP.exists(), f"missing bootstrap: {BOOTSTRAP}")
    require(SYNC.exists(), f"missing sync script: {SYNC}")
    require(SYNC_CLAUDE.exists(), f"missing sync script: {SYNC_CLAUDE}")
    require(VERIFY.exists(), f"missing verify script: {VERIFY}")

    test_bootstrap_requires_argument()
    test_sync_requires_entrypoint_file()
    test_sync_renders_template_and_copies_skills()
    test_sync_claude_injects_integration_block()
    test_verify_after_full_sync()
    test_capture_text_auto_classifies_input_types()
    print("[PASS] all tests")


if __name__ == "__main__":
    main()
