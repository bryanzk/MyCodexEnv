#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BOOTSTRAP = ROOT / "bootstrap.sh"
SYNC = ROOT / "scripts" / "sync_codex_home.sh"
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

        expected_skills = count_top_dirs(ROOT / "codex" / "skills")
        actual_skills = count_top_dirs(codex_home / "skills")
        require(actual_skills == expected_skills, f"skills count mismatch: {actual_skills} != {expected_skills}")

    print("[PASS] sync render + skills copy")


def test_verify_after_full_sync():
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
            ]
        )
        require(code == 0, f"full sync failed: {err or out}")

        code, out, err = run([str(VERIFY), "--repo-root", str(ROOT), "--codex-home", str(codex_home)])
        require(code == 0, f"verify failed: {err or out}")
        require("Verification passed." in out, "verify success message missing")

    print("[PASS] full sync + verify")


def main():
    require(BOOTSTRAP.exists(), f"missing bootstrap: {BOOTSTRAP}")
    require(SYNC.exists(), f"missing sync script: {SYNC}")
    require(VERIFY.exists(), f"missing verify script: {VERIFY}")

    test_bootstrap_requires_argument()
    test_sync_requires_entrypoint_file()
    test_sync_renders_template_and_copies_skills()
    test_verify_after_full_sync()
    print("[PASS] all tests")


if __name__ == "__main__":
    main()
