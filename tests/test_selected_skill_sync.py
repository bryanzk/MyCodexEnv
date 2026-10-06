from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / 'scripts/sync_codex_home.sh'
HELPER = ROOT / 'scripts/harness_refresh_identity.py'


class SelectedSkillSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='selected-skill-test-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repo = self.base / 'fixture-repo'
        self.codex = self.base / 'fixture-codex'
        self.claude = self.base / 'fixture-claude'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Skill Sync Test Fixture')
        self.git('config', 'user.email', 'skill-sync-test@example.test')
        # Isolate Git fixture commits from any machine-level hook configuration.
        hooks = self.base / 'empty-git-fixture-hooks'
        hooks.mkdir()
        self.git('config', 'core.hooksPath', str(hooks))
        for rel, text in {
            'codex/AGENTS.md': 'Fixture rules\n',
            'codex/remote-access.md': 'Fixture, no remote access\n',
            'codex/remote-hosts.md': 'Fixture, no hosts\n',
            'codex/hooks/task_state.py': 'pass\n',
            'codex/skills/alpha/SKILL.md': '---\nname: alpha\ndescription: Fixture alpha.\n---\nNew alpha\n',
            'codex/skills/beta/SKILL.md': '---\nname: beta\ndescription: Fixture beta.\n---\nNew beta\n',
            'claude/shared-skills.txt': '# Fixture registry\nalpha\n',
            'runtime-approvals/approved-source-digests.txt': '# Fixture approvals only\n',
        }.items():
            self.write(self.repo / rel, text)
        self.git('add', '.')
        self.approve_fixture()
        self.git('add', '.')
        self.git('commit', '-qm', 'Create isolated fixture')
        for home in [self.codex, self.claude]:
            self.write(home / 'config.toml', '# Existing config\n')
            self.write(home / 'hooks/unchanged', 'Existing hook\n')
            self.write(home / 'runtime/unchanged', 'Existing runtime\n')
            self.write(home / 'skills/alpha/SKILL.md', 'Old alpha\n')
            (home / 'skills/alpha/SKILL.md').chmod(0o600)
            self.write(home / 'skills/alpha/local-note.md', 'User local note\n')
            self.write(home / 'skills/beta/SKILL.md', 'Old beta\n')

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def git(self, *arguments):
        return subprocess.check_output(['git', '-C', str(self.repo), *arguments], stderr=subprocess.STDOUT)

    def approve_fixture(self):
        spec = importlib.util.spec_from_file_location('fixture_digest', HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        digest = module.source_digest(self.repo)
        self.write(self.repo / 'runtime-approvals/approved-source-digests.txt', 'sha256:' + digest + '  isolated-test-fixture-only\n')

    def snapshot(self, home):
        return {str(p.relative_to(home)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777)
                for p in home.rglob('*') if p.is_file() and not p.is_symlink()}

    def sync(self, names='alpha', *extra):
        return subprocess.run(['bash', str(SYNC), '--repo-root', str(self.repo), '--codex-home', str(self.codex),
                               '--sync-skills-only', names, *extra], capture_output=True, text=True)

    def assert_blocked_without_writes(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)
        self.assertEqual(self.before_codex, self.snapshot(self.codex))
        self.assertEqual(self.before_claude, self.snapshot(self.claude))

    def save_before(self):
        self.before_codex = self.snapshot(self.codex)
        self.before_claude = self.snapshot(self.claude)

    def test_only_selected_skills_and_registered_claude_shared_skills_change(self):
        self.save_before()
        result = self.sync('alpha,beta', '--shared-claude-skills-home', str(self.claude))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['source_attestation'], 'existing_preflight')
        for home in [self.codex, self.claude]:
            self.assertIn('New alpha', (home / 'skills/alpha/SKILL.md').read_text())
            self.assertEqual((home / 'skills/alpha/SKILL.md').stat().st_mode & 0o777, 0o600)
            self.assertEqual((home / 'skills/alpha/local-note.md').read_text(), 'User local note\n')
            for rel in ['config.toml', 'hooks/unchanged', 'runtime/unchanged']:
                before = self.before_codex if home == self.codex else self.before_claude
                self.assertEqual(self.snapshot(home)[rel], before[rel])
        self.assertIn('New beta', (self.codex / 'skills/beta/SKILL.md').read_text())
        self.assertEqual((self.claude / 'skills/beta/SKILL.md').read_text(), 'Old beta\n')

    def test_source_dirty_blocks_before_any_runtime_write(self):
        self.save_before()
        self.write(self.repo / 'codex/skills/alpha/SKILL.md', 'Dirty alpha\n')
        self.assert_blocked_without_writes(self.sync(), 'source_dirty')

    def test_unapproved_clean_source_blocks_before_any_runtime_write(self):
        self.save_before()
        self.write(self.repo / 'codex/skills/alpha/SKILL.md', 'Changed alpha\n')
        self.git('add', 'codex/skills/alpha/SKILL.md')
        self.git('commit', '-qm', 'Unapproved fixture change')
        self.assert_blocked_without_writes(self.sync(), 'source_digest_unapproved')

    def test_dirty_approval_blocks_before_any_runtime_write(self):
        self.save_before()
        p = self.repo / 'runtime-approvals/approved-source-digests.txt'
        p.write_text(p.read_text() + '# uncommitted fixture approval\n')
        self.assert_blocked_without_writes(self.sync(), 'approved_manifest_dirty')

    def test_invalid_and_duplicate_names_block(self):
        self.save_before()
        for names in ['../escape', 'alpha,alpha', 'alpha,', 'alpha/child']:
            self.assert_blocked_without_writes(self.sync(names), 'invalid or duplicate selected skill name')

    def test_symlink_target_blocks(self):
        shutil.rmtree(self.codex / 'skills/alpha')
        outside = self.base / 'outside'
        outside.mkdir()
        (self.codex / 'skills/alpha').symlink_to(outside, target_is_directory=True)
        self.save_before()
        self.assert_blocked_without_writes(self.sync(), 'invalid selected skill destination')
        self.assertEqual(list(outside.iterdir()), [])

    def test_approved_source_symlink_blocks(self):
        (self.repo / 'codex/skills/alpha/link').symlink_to('/tmp')
        self.git('add', '.')
        self.approve_fixture()
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture with source symlink')
        self.save_before()
        self.assert_blocked_without_writes(self.sync(), 'nonregular selected skill source')

    def test_missing_source_validates_all_targets_before_writing(self):
        self.save_before()
        self.assert_blocked_without_writes(self.sync('alpha,missing'), 'invalid selected skill source')

    def test_incompatible_mode_blocks(self):
        self.save_before()
        self.assert_blocked_without_writes(self.sync('alpha', '--sync-agents-only'), 'cannot be combined')

    def test_nondirectory_nested_target_validates_before_any_write(self):
        self.write(self.repo / 'codex/skills/alpha/agents/openai.yaml', 'interface: {}\n')
        self.git('add', '.')
        self.approve_fixture()
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture nested file')
        self.write(self.codex / 'skills/alpha/agents', 'user ordinary file\n')
        self.save_before()
        self.assert_blocked_without_writes(self.sync(), 'nondirectory selected skill destination ancestor')

    def test_source_destination_overlap_blocks(self):
        result = subprocess.run(['bash', str(SYNC), '--repo-root', str(self.repo), '--codex-home', str(self.repo / 'codex'),
                                 '--sync-skills-only', 'alpha'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('source/destination overlap', result.stderr)
        self.assertEqual(self.git('status', '--porcelain').decode(), '')

    def test_source_ancestor_symlink_blocks(self):
        external = self.base / 'external-fixture-skills'
        shutil.move(str(self.repo / 'codex/skills'), str(external))
        (self.repo / 'codex/skills').symlink_to(external, target_is_directory=True)
        self.git('add', '.')
        self.approve_fixture()
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture source directory symlink')
        self.save_before()
        self.assert_blocked_without_writes(self.sync(), 'symlink selected skill source ancestor')

    def test_new_helper_keeps_source_executable_mode(self):
        helper = self.repo / 'codex/skills/alpha/helper.sh'
        self.write(helper, '#!/bin/sh\nexit 0\n')
        helper.chmod(0o755)
        self.git('add', '.')
        self.approve_fixture()
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture executable helper')
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.codex / 'skills/alpha/helper.sh').stat().st_mode & 0o777, 0o755)

    def test_nondirectory_above_claude_home_validates_before_codex_writes(self):
        bad_parent = self.base / 'ordinary-file'
        bad_parent.write_text('User file\n')
        self.save_before()
        result = self.sync('alpha', '--shared-claude-skills-home', str(bad_parent / 'new-home'))
        self.assert_blocked_without_writes(result, 'nondirectory selected skill destination ancestor')
        self.assertEqual(bad_parent.read_text(), 'User file\n')


if __name__ == '__main__':
    unittest.main()
