#!/usr/bin/env python3
import subprocess
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent
BOOTSTRAP = ROOT / "bootstrap.sh"
SYNC = ROOT / "scripts" / "sync_codex_home.sh"
SYNC_CLAUDE = ROOT / "scripts" / "sync_claude_home.sh"
VERIFY = ROOT / "scripts" / "verify_codex_env.sh"
MANAGE_AGENTS = ROOT / "scripts" / "manage_agents.py"


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def require(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        sys.exit(1)


def count_top_dirs(path: Path) -> int:
    return len([item for item in path.iterdir() if item.is_dir()])


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def active_toml_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").mkdir(parents=True, exist_ok=True)
    return path


def run_manage_agents(*args):
    return run([sys.executable, str(MANAGE_AGENTS), *args])


def test_bootstrap_eigenphi_argument_is_optional():
    code, out, err = run([str(BOOTSTRAP), "--help"])
    require(code == 0, "bootstrap help should render successfully")
    text = f"{out}\n{err}"
    require("[--eigenphi-backend-root <path>]" in text, "eigenphi argument should be optional in usage")
    require("默认禁用" in text, "help should explain EigenPhi MCP is disabled by default")
    print("[PASS] bootstrap optional EigenPhi argument check")


def test_sync_ignores_legacy_eigenphi_argument():
    with tempfile.TemporaryDirectory() as tmp:
        missing_backend = Path(tmp) / "missing-backend"
        codex_home = Path(tmp) / ".codex"
        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--eigenphi-backend-root",
                str(missing_backend),
                "--codex-home",
                str(codex_home),
                "--skip-superpowers-sync",
            ]
        )
        require(code == 0, f"sync should ignore legacy EigenPhi path: {err or out}")
        rendered = (codex_home / "config.toml").read_text(encoding="utf-8")
        require('[mcp_servers."eigenphi-blockchain"]' not in active_toml_lines(rendered), "EigenPhi MCP should not be active")
    print("[PASS] sync ignores legacy EigenPhi argument")


def test_sync_renders_template_and_copies_skills():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_home = tmp_path / ".codex"

        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--codex-home",
                str(codex_home),
                "--skip-superpowers-sync",
            ]
        )
        require(code == 0, f"sync failed: {err or out}")

        rendered = (codex_home / "config.toml").read_text(encoding="utf-8")
        require("${NPM_GLOBAL_BIN}" not in rendered, "npm global bin placeholder should be replaced")
        require('[mcp_servers."eigenphi-blockchain"]' not in active_toml_lines(rendered), "EigenPhi MCP should not be active")
        require('# [mcp_servers."eigenphi-blockchain"]' in rendered, "disabled EigenPhi MCP block should remain documented")
        require('[mcp_servers."chrome-devtools"]' in rendered, "chrome-devtools MCP should be rendered")
        require("--no-usage-statistics" in rendered, "chrome-devtools MCP should disable usage statistics")
        require("--no-performance-crux" in rendered, "chrome-devtools MCP should disable CrUX lookups")
        require((codex_home / "AGENTS.md").exists(), "AGENTS.md should be copied")
        require((codex_home / "remote-access.md").exists(), "remote access policy should be copied")
        require((codex_home / "remote-hosts.md").exists(), "remote hosts registry should be copied")
        require(
            (codex_home / "remote-access.md").read_text(encoding="utf-8")
            == (ROOT / "codex" / "remote-access.md").read_text(encoding="utf-8"),
            "runtime remote-access.md should match source",
        )
        require((codex_home / "workflow" / "rules" / "behaviors.md").exists(), "codex workflow rules should be copied")

        expected_skills = count_top_dirs(ROOT / "codex" / "skills")
        actual_skills = count_top_dirs(codex_home / "skills")
        require(actual_skills == expected_skills, f"skills count mismatch: {actual_skills} != {expected_skills}")
        require(
            (codex_home / "skills" / "review" / "checklist.md").exists(),
            "review checklist should be copied with the skill",
        )
        require(
            (codex_home / "skills" / "qa" / "templates" / "qa-report-template.md").exists(),
            "qa report template should be copied with the skill",
        )
        require(
            (codex_home / "skills" / "qa" / "references" / "issue-taxonomy.md").exists(),
            "qa reference docs should be copied with the skill",
        )
        require(
            (codex_home / "skills" / "browse" / "bin" / "find-browse").exists(),
            "browse helper scripts should be copied with the skill",
        )
        require(
            (codex_home / "skills" / "gstack" / "setup").exists(),
            "gstack root setup should be copied with the global skill",
        )
        require(
            (codex_home / "skills" / "gstack" / "bin" / "gstack-config").exists(),
            "gstack shared helper scripts should be copied with the global skill",
        )
        require(
            (codex_home / "skills" / "gstack" / "browse" / "src" / "cli.ts").exists(),
            "gstack browse source should be copied with the global skill",
        )
        require(
            (codex_home / "skills" / "gstack-qa" / "SKILL.md").exists(),
            "gstack namespaced qa skill should be copied",
        )
        require(
            (codex_home / "skills" / "gstack-ship" / "SKILL.md").exists(),
            "gstack namespaced ship skill should be copied",
        )
        project_lifecycle_skill = codex_home / "skills" / "project-lifecycle-harness" / "SKILL.md"
        project_lifecycle_agent = codex_home / "skills" / "project-lifecycle-harness" / "agents" / "openai.yaml"
        require(project_lifecycle_skill.exists(), "project lifecycle harness skill should be copied")
        require(project_lifecycle_agent.exists(), "project lifecycle harness OpenAI agent metadata should be copied")
        require(
            project_lifecycle_skill.read_text(encoding="utf-8")
            == (ROOT / "codex" / "skills" / "project-lifecycle-harness" / "SKILL.md").read_text(encoding="utf-8"),
            "runtime project lifecycle harness skill should match source",
        )
        require(
            project_lifecycle_agent.read_text(encoding="utf-8")
            == (ROOT / "codex" / "skills" / "project-lifecycle-harness" / "agents" / "openai.yaml").read_text(encoding="utf-8"),
            "runtime project lifecycle harness agent metadata should match source",
        )

    print("[PASS] sync render + skills copy")


def test_project_lifecycle_harness_stays_generic():
    skill_root = ROOT / "codex" / "skills" / "project-lifecycle-harness"
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    agent_text = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

    require("name: project-lifecycle-harness" in skill_text, "project lifecycle harness skill name missing")
    require(
        "Use $project-lifecycle-harness" in agent_text,
        "OpenAI agent metadata should route to the generic lifecycle harness",
    )
    forbidden_terms = [
        "ShipQ",
        "shipq",
        "workbook",
        "freight",
        "quote demo",
        "/Users/",
        "CursorDeveloper",
    ]
    combined = f"{skill_text}\n{agent_text}"
    offenders = [term for term in forbidden_terms if term in combined]
    require(not offenders, f"generic project lifecycle harness contains project-specific terms: {offenders}")

    print("[PASS] project lifecycle harness generic boundary")


def test_sync_agents_only_copies_and_backs_up_agents():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        codex_home = tmp_path / ".codex"
        codex_home.mkdir(parents=True, exist_ok=True)
        original_agents = codex_home / "AGENTS.md"
        original_agents.write_text("# old agents\n", encoding="utf-8")

        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
                "--codex-home",
                str(codex_home),
                "--sync-agents-only",
            ]
        )
        require(code == 0, f"sync agents only failed: {err or out}")
        require((codex_home / "AGENTS.md").exists(), "AGENTS.md should be copied in sync-agents-only mode")
        require((codex_home / "remote-access.md").exists(), "remote-access.md should be copied in sync-agents-only mode")
        require((codex_home / "remote-hosts.md").exists(), "remote-hosts.md should be copied in sync-agents-only mode")
        require(
            (codex_home / "AGENTS.md").read_text(encoding="utf-8")
            == (ROOT / "codex" / "AGENTS.md").read_text(encoding="utf-8"),
            "sync-agents-only should copy repo codex/AGENTS.md",
        )
        require(
            (codex_home / "remote-access.md").read_text(encoding="utf-8")
            == (ROOT / "codex" / "remote-access.md").read_text(encoding="utf-8"),
            "sync-agents-only should copy repo codex/remote-access.md",
        )
        backups = list(codex_home.glob("AGENTS.md.backup.*"))
        require(backups, "sync-agents-only should back up existing AGENTS.md")

    print("[PASS] sync agents only")


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

        code, out, err = run(
            [
                str(SYNC),
                "--repo-root",
                str(ROOT),
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


def test_manage_agents_scan_backup_generate_restore():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        backup_root = workspace_root / ".agents-backups"
        control_root = tmp_path / "control"
        codex_source = control_root / "codex" / "AGENTS.md"
        codex_runtime = tmp_path / ".codex" / "AGENTS.md"
        codex_runtime.parent.mkdir(parents=True, exist_ok=True)
        write(
            codex_source,
            "# Codex Global\n\n## Purpose\n- 通用规则。\n\n## Verification Gate\n- `command`\n- `exit_code`\n- `key_output`\n- `timestamp`\n\n## Remote Operations\n- 远程操作前读取 `~/.codex/remote-access.md`。\n\n## Layering\n- Codex level\n\n## Repo AGENTS Expectations\n- repo-specific\n",
        )
        codex_runtime.write_text("# old runtime\n", encoding="utf-8")
        write(control_root / "codex" / "remote-access.md", "# Remote Access Policy\n")
        write(control_root / "codex" / "remote-hosts.md", "# Remote Hosts Registry\n")
        write(codex_runtime.parent / "remote-access.md", "# old remote access\n")
        write(codex_runtime.parent / "remote-hosts.md", "# old remote hosts\n")

        repo_python = make_git_repo(workspace_root / "repo-python")
        write(repo_python / "README.md", "# Repo Python\n\nA Python service.\n")
        write(repo_python / "pyproject.toml", "[project]\nname = 'repo-python'\n")
        (repo_python / "src").mkdir(parents=True, exist_ok=True)
        (repo_python / "tests").mkdir(parents=True, exist_ok=True)

        repo_node = make_git_repo(workspace_root / "repo-node")
        write(repo_node / "README.md", "# Repo Node\n\nA web app.\n")
        write(
            repo_node / "package.json",
            json.dumps(
                {
                    "name": "repo-node",
                    "scripts": {"dev": "next dev", "build": "next build", "test": "vitest run"},
                }
            ),
        )
        local_agents = repo_node / "services" / "api" / "AGENTS.md"
        write(local_agents, "# Local API Rules\n")

        os.symlink(repo_node, workspace_root / "repo-node-alias")

        code, out, err = run_manage_agents(
            "scan",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
        )
        require(code == 0, f"scan failed: {err or out}")
        scan_payload = json.loads(out)
        require(len(scan_payload["repos"]) == 2, f"expected 2 deduped repos, got {len(scan_payload['repos'])}")
        require(
            any(repo["path"].endswith("repo-node") and repo["local_agents"] for repo in scan_payload["repos"]),
            "repo-node local AGENTS should be discovered",
        )

        backup_id = "test-backup"
        code, out, err = run_manage_agents(
            "backup",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
            "--backup-id",
            backup_id,
        )
        require(code == 0, f"backup failed: {err or out}")
        backup_payload = json.loads(out)
        require(backup_payload["backup_id"] == backup_id, "backup id mismatch")
        manifest_path = backup_root / backup_id / "manifest.json"
        require(manifest_path.exists(), "backup manifest should exist")
        report_path = backup_root / backup_id / "report.md"
        require(report_path.exists(), "backup report should exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(
            any(entry["level"] == "codex_runtime" for entry in manifest["entries"]),
            "manifest should include codex runtime entry",
        )
        require(
            any(entry["original_path"] == str(local_agents) for entry in manifest["entries"]),
            "manifest should include local AGENTS entry",
        )
        require(
            any(
                entry["level"] == "repo_root"
                and entry["original_path"] == str(repo_python / "AGENTS.md")
                and not entry["existed_before"]
                and entry["restore_action"] == "delete"
                for entry in manifest["entries"]
            ),
            "missing root AGENTS should be tracked for delete-on-restore",
        )

        code, out, err = run_manage_agents(
            "backup",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
            "--backup-id",
            backup_id,
        )
        require(code != 0, "backup should fail when backup_id already exists")

        code, out, err = run_manage_agents(
            "generate",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
            "--backup-id",
            backup_id,
        )
        require(code == 0, f"generate failed: {err or out}")
        require((repo_python / "AGENTS.md").exists(), "repo-python root AGENTS should be generated")
        require((repo_node / "AGENTS.md").exists(), "repo-node root AGENTS should be generated")
        require((repo_node / "services" / "api" / "AGENTS.md").read_text(encoding="utf-8") == "# Local API Rules\n", "local AGENTS should remain untouched")
        require(
            codex_runtime.read_text(encoding="utf-8") == codex_source.read_text(encoding="utf-8"),
            "codex runtime should match codex source after generate",
        )
        require(list(codex_runtime.parent.glob("AGENTS.md.backup.*")), "generate should back up existing codex runtime AGENTS")
        report_text = report_path.read_text(encoding="utf-8")
        require("## Entries" in report_text and "## Generation Actions" in report_text, "report should retain backup entries and generation actions")

        code, out, err = run_manage_agents(
            "verify",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
        )
        require(code == 0, f"verify failed: {err or out}")

        write(
            repo_python / "AGENTS.md",
            (repo_python / "AGENTS.md").read_text(encoding="utf-8").replace("README.md", "MISSING.md"),
        )
        write(
            repo_node / "AGENTS.md",
            (repo_node / "AGENTS.md").read_text(encoding="utf-8").replace("npm run test", "npm run lint"),
        )
        code, out, err = run_manage_agents(
            "verify",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
        )
        require(code != 0, "verify should fail for invalid generated path or command references")
        require("MISSING.md" in out and "npm run lint" in out, "verify should explain invalid path and command source")

        code, out, err = run_manage_agents(
            "generate",
            "--workspace-root",
            str(workspace_root),
            "--backup-root",
            str(backup_root),
            "--codex-source",
            str(codex_source),
            "--codex-runtime",
            str(codex_runtime),
            "--backup-id",
            backup_id,
        )
        require(code == 0, f"regenerate failed: {err or out}")

        code, out, err = run_manage_agents(
            "restore",
            "--backup-root",
            str(backup_root),
            "--backup-id",
            backup_id,
        )
        require(code == 0, f"restore failed: {err or out}")
        require(not (repo_python / "AGENTS.md").exists(), "repo-python AGENTS should be removed on restore")
        require(not (repo_node / "AGENTS.md").exists(), "repo-node AGENTS should be removed on restore")
        require(codex_runtime.read_text(encoding="utf-8") == "# old runtime\n", "codex runtime should be restored")

    print("[PASS] manage_agents scan/backup/generate/restore")


def main():
    require(BOOTSTRAP.exists(), f"missing bootstrap: {BOOTSTRAP}")
    require(SYNC.exists(), f"missing sync script: {SYNC}")
    require(SYNC_CLAUDE.exists(), f"missing sync script: {SYNC_CLAUDE}")
    require(VERIFY.exists(), f"missing verify script: {VERIFY}")
    require(MANAGE_AGENTS.exists(), f"missing manage_agents script: {MANAGE_AGENTS}")

    test_bootstrap_eigenphi_argument_is_optional()
    test_sync_ignores_legacy_eigenphi_argument()
    test_sync_renders_template_and_copies_skills()
    test_project_lifecycle_harness_stays_generic()
    test_sync_agents_only_copies_and_backs_up_agents()
    test_sync_claude_injects_integration_block()
    test_verify_after_full_sync()
    test_capture_text_auto_classifies_input_types()
    test_manage_agents_scan_backup_generate_restore()
    print("[PASS] all tests")


if __name__ == "__main__":
    main()
