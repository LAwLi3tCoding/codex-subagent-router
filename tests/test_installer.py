import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(root):
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode & 0o777)
        for p in root.rglob('*') if p.is_file()
        and 'subagent-router-backups' not in p.relative_to(root).parts
    }


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_module('router_install', REPO_ROOT / 'scripts/install.py')
        self.verifier = load_module('router_verify', REPO_ROOT / 'scripts/verify.py')
        self.policy = REPO_ROOT / 'policy/subagent-routing.md'

    def test_fresh_install_creates_only_guidance_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'profile'
            guidance = home / 'AGENTS.md'
            self.assertEqual(self.installer.install(REPO_ROOT, home, guidance), [guidance.resolve()])
            self.assertEqual(set(snapshot(home)), {'AGENTS.md'})
            self.assertEqual(self.verifier.verify_install(home, guidance, self.policy), [])
            paths = set(home.rglob('*'))
            self.assertEqual(self.installer.install(REPO_ROOT, home, guidance), [])
            self.assertEqual(set(home.rglob('*')), paths)

    def test_existing_configuration_roles_hooks_and_unrelated_guidance_are_preserved(self):
        cases = (
            '[agents]\nenabled = false\ndefault_subagent_model = "existing"\n',
            'agents = { enabled = false, max_threads = 3 }\n',
            'agents.enabled = false\nagents.default_subagent_reasoning_effort = "low"\n',
            'model = [\n',  # Router does not own or parse configuration.
        )
        for config in cases:
            with self.subTest(config=config), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                (home / 'config.toml').write_text(config)
                (home / 'config.toml').chmod(0o640)
                (home / 'agents').mkdir()
                for name in ('reviewer', 'risk-reviewer', 'worker-low', 'owner', 'custom'):
                    (home / 'agents' / f'{name}.toml').write_text(
                        f'name = "{name}"\ndeveloper_instructions = "Existing workflow"\n')
                (home / 'hooks.json').write_text('{"existing": true}\n')
                start, end = self.installer.BLOCK_START, self.installer.BLOCK_END
                guidance = home / 'AGENTS.md'
                old = f'Before.\n{start}\nOld delegation and review rules.\n{end}\nAfter.\n'
                guidance.write_text(old)
                guidance.chmod(0o640)
                before = snapshot(home)
                self.installer.install(REPO_ROOT, home, guidance)
                after = snapshot(home)
                self.assertEqual({k: v for k, v in before.items() if k != 'AGENTS.md'},
                                 {k: v for k, v in after.items() if k != 'AGENTS.md'})
                expected = f'Before.\n{start}\n{self.policy.read_text().rstrip()}\n{end}\nAfter.\n'
                self.assertEqual(guidance.read_text(), expected)
                self.assertEqual(guidance.stat().st_mode & 0o777, 0o640)
                backups = list((home / 'subagent-router-backups').glob('*/AGENTS.md'))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_text(), old)
                self.assertEqual(self.verifier.verify_install(home, guidance, self.policy), [])

    def test_configuration_and_role_symlinks_remain_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / 'profile'
            (home / 'agents').mkdir(parents=True)
            target = root / 'external.toml'
            target.write_text('Existing contents.\n')
            links = (home / 'config.toml', home / 'agents/reviewer.toml')
            for link in links:
                link.symlink_to(target)
            self.installer.install(REPO_ROOT, home, home / 'AGENTS.md')
            for link in links:
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.readlink(), target)
            self.assertEqual(target.read_text(), 'Existing contents.\n')

    def test_guidance_symlink_updates_target_and_preserves_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / 'profile'
            home.mkdir()
            target = root / 'shared.md'
            target.write_text('Shared guidance.\n')
            link = home / 'AGENTS.md'
            link.symlink_to(target)
            self.installer.install(REPO_ROOT, home, link)
            self.assertTrue(link.is_symlink())
            self.assertTrue(target.read_text().startswith('Shared guidance.\n'))
            self.assertEqual(self.verifier.verify_install(home, link, self.policy), [])

    def test_invalid_markers_and_policy_fail_before_profile_changes(self):
        start, end = self.installer.BLOCK_START, self.installer.BLOCK_END
        for content in (start, end, end + start, start + end + start + end):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                guidance = home / 'AGENTS.md'
                guidance.write_text(content)
                before = snapshot(home)
                with self.assertRaises(ValueError):
                    self.installer.install(REPO_ROOT, home, guidance)
                self.assertEqual(snapshot(home), before)
                self.assertFalse((home / 'subagent-router-backups').exists())
        for policy in ('', start, end):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'source'
                (source / 'policy').mkdir(parents=True)
                (source / 'policy/subagent-routing.md').write_text(policy)
                home = root / 'profile'
                with self.assertRaises(ValueError):
                    self.installer.install(source, home, home / 'AGENTS.md')
                self.assertFalse(home.exists())

    def test_failed_write_restores_existing_or_removes_new_guidance(self):
        for existing in (False, True):
            for after_write in (False, True):
                with self.subTest(existing=existing, after_write=after_write), tempfile.TemporaryDirectory() as directory:
                    home = Path(directory)
                    guidance = home / 'AGENTS.md'
                    if existing:
                        guidance.write_text('Keep existing guidance.\n')
                        guidance.chmod(0o444)
                    (home / 'config.toml').write_text('Unchanged configuration.\n')
                    before = snapshot(home)
                    write = self.installer._atomic_write

                    def fail(path, content):
                        if after_write:
                            write(path, content)
                        raise OSError('Simulated write failure')

                    with mock.patch.object(self.installer, '_atomic_write', side_effect=fail):
                        with self.assertRaisesRegex(OSError, 'Simulated write failure'):
                            self.installer.install(REPO_ROOT, home, guidance)
                    self.assertEqual(snapshot(home), before)
                    self.assertEqual(len(list((home / 'subagent-router-backups').iterdir())), 1)

    def test_incomplete_recovery_keeps_original_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            guidance = home / 'AGENTS.md'
            guidance.write_text('Original guidance.\n')
            write = self.installer._atomic_write

            def fail(path, content):
                write(path, content)
                raise OSError('Simulated failure')

            with mock.patch.object(self.installer, '_atomic_write', side_effect=fail), \
                    mock.patch.object(self.installer, '_restore_backup', side_effect=OSError('Restore failure')):
                with self.assertRaisesRegex(RuntimeError, 'incomplete recovery'):
                    self.installer.install(REPO_ROOT, home, guidance)
            backup = next((home / 'subagent-router-backups').glob('*/AGENTS.md'))
            self.assertEqual(backup.read_text(), 'Original guidance.\n')

    def test_verifier_rejects_stale_missing_or_reversed_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            guidance = home / 'AGENTS.md'
            self.assertTrue(self.verifier.verify_install(home, guidance, self.policy))
            self.installer.install(REPO_ROOT, home, guidance)
            for text in ('', self.installer.BLOCK_END + self.installer.BLOCK_START,
                         self.installer.BLOCK_START + '\nStale policy.\n' + self.installer.BLOCK_END):
                with self.subTest(text=text):
                    guidance.write_text(text)
                    self.assertTrue(self.verifier.verify_install(home, guidance, self.policy))

    def test_cli_honors_active_override_and_explicit_destination(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                normal = home / 'AGENTS.md'
                normal.write_text('Normal guidance.\n')
                override = home / 'AGENTS.override.md'
                override.write_text('Override guidance.\n')
                custom = home / 'custom.md'
                args = ['sh', str(REPO_ROOT / 'install.sh'), '--codex-home', str(home)]
                if explicit:
                    args += ['--global-agents', str(custom)]
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('installed guidance verified', result.stdout)
                self.assertEqual(normal.read_text(), 'Normal guidance.\n')
                target = custom if explicit else override
                self.assertIn(self.installer.BLOCK_START, target.read_text())
                if explicit:
                    self.assertEqual(override.read_text(), 'Override guidance.\n')

    def test_shareable_source(self):
        self.assertEqual(self.verifier.scan_shareable_tree(REPO_ROOT), [])


if __name__ == '__main__':
    unittest.main()
