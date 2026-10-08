import importlib.util
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROLES = {
    "sol-low": ("gpt-6.1-sol", "low", None),
    "sol-medium": ("gpt-6.1-sol", "medium", None),
    "sol-high": ("gpt-6.1-sol", "high", None),
    "sol-xhigh": ("gpt-6.1-sol", "xhigh", None),
    "astra-reviewer": ("gpt-6-astra", "xhigh", "read-only"),
}
RETIRED_ROLES = (
    "default", "explorer", "mechanical", "owner", "high-risk-owner",
    "luna-low", "luna-batch", "luna-reasoner", "luna-medium", "luna-high",
    "luna-xhigh", "luna-max", "terra-explorer", "terra-researcher", "terra-low",
    "terra-medium", "terra-high", "terra-xhigh", "terra-max", "terra-ultra",
    "sol-max", "sol-ultra",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_snapshot(root: Path):
    return {
        str(path.relative_to(root)): (
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mode & 0o777,
        )
        for path in root.rglob("*")
    }


class InstallerContractTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_module("router_install", REPO_ROOT / "scripts" / "install.py")
        self.verifier = load_module("router_verify", REPO_ROOT / "scripts" / "verify.py")
        self.policy_path = REPO_ROOT / "policy" / "subagent-routing.md"

    def test_one_command_installer_activates_router_without_hook(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            result = subprocess.run(
                ["sh", str(REPO_ROOT / "install.sh"), "--codex-home", str(codex_home)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Router source and installed configuration verified", result.stdout)
            self.assertEqual(
                {path.stem for path in (codex_home / "agents").glob("*.toml")},
                set(EXPECTED_ROLES),
            )
            self.assertFalse((codex_home / "hooks.json").exists())
            self.assertFalse((codex_home / "hooks").exists())
            config = tomllib.loads((codex_home / "config.toml").read_text(encoding="utf-8"))
            self.assertTrue(config["agents"]["enabled"])
            self.assertNotIn("features", config)

    def test_install_preserves_primary_permissions_mcp_limits_and_existing_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            config_path = codex_home / "config.toml"
            initial = (
                'model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"\n'
                'sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n'
                '[agents]\nenabled = false\nmax_concurrent_threads_per_session = 3\n'
                'max_threads = 2\ninterrupt_message = false\n'
                'default_subagent_model = "old-model"\n'
                'default_subagent_reasoning_effort = "low"\n'
                '[features]\n# Keep feature choices.\nhooks = false\nweb_search = true\n'
                '[sandbox_workspace_write]\nnetwork_access = false\n'
                '[mcp_servers.example]\ncommand = "example-server"\nargs = ["--stdio"]\n'
            )
            config_path.write_text(initial, encoding="utf-8")
            config_path.chmod(0o600)
            old_config = tomllib.loads(initial)
            hooks_path = codex_home / "hooks.json"
            hooks_content = '{"hooks": {"SubagentStart": []}, "description": "Existing hooks"}\n'
            hooks_path.write_text(hooks_content, encoding="utf-8")
            old_hook = codex_home / "hooks" / "existing_hook.py"
            old_hook.parent.mkdir()
            old_hook.write_text("# Existing hook definition\n", encoding="utf-8")
            guidance_path = codex_home / "AGENTS.md"
            guidance_path.write_text("# Existing guidance\n\nKeep this line.\n", encoding="utf-8")
            unrelated_role = codex_home / "agents" / "custom.toml"
            unrelated_role.parent.mkdir()
            unrelated_role.write_text('name = "custom"\n', encoding="utf-8")

            self.installer.install(REPO_ROOT, codex_home, guidance_path)
            installed_config = config_path.read_text(encoding="utf-8")
            parsed = tomllib.loads(installed_config)
            self.assertIn("[features]\n# Keep feature choices.\nhooks = false\nweb_search = true\n", installed_config)
            expected = tomllib.loads(initial)
            expected["agents"]["enabled"] = True
            del expected["agents"]["default_subagent_model"]
            del expected["agents"]["default_subagent_reasoning_effort"]
            self.assertEqual(parsed, expected)
            self.assertEqual(parsed["model"], old_config["model"])
            self.assertEqual(parsed["model_reasoning_effort"], old_config["model_reasoning_effort"])
            self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(hooks_path.read_text(encoding="utf-8"), hooks_content)
            self.assertEqual(old_hook.read_text(encoding="utf-8"), "# Existing hook definition\n")
            self.assertEqual(unrelated_role.read_text(encoding="utf-8"), 'name = "custom"\n')
            installed_guidance = guidance_path.read_text(encoding="utf-8")
            self.assertIn("Keep this line.", installed_guidance)
            self.assertEqual(installed_guidance.count(self.installer.BLOCK_START), 1)
            self.assertEqual(installed_guidance.count(self.installer.BLOCK_END), 1)
            self.assertEqual(self.verifier.verify_install(codex_home, guidance_path, self.policy_path), [])
            first = profile_snapshot(codex_home)
            self.assertEqual(self.installer.install(REPO_ROOT, codex_home, guidance_path), [])
            self.assertEqual(profile_snapshot(codex_home), first)

    def test_migration_backs_up_retired_and_replaced_roles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            target_agents = codex_home / "agents"
            target_agents.mkdir(parents=True)
            original_roles = {}
            for role in RETIRED_ROLES + tuple(EXPECTED_ROLES):
                original = f'name = "{role}"\nmarker = "previous-definition"\n'
                (target_agents / f"{role}.toml").write_text(original, encoding="utf-8")
                original_roles[role] = original
            guidance = codex_home / "AGENTS.md"
            self.installer.install(REPO_ROOT, codex_home, guidance)
            for role, original in original_roles.items():
                with self.subTest(role=role):
                    backups = list((codex_home / "subagent-router-backups").glob(f"*/agents/{role}.toml"))
                    self.assertEqual(len(backups), 1)
                    self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
                    target = target_agents / f"{role}.toml"
                    if role in RETIRED_ROLES:
                        self.assertFalse(target.exists())
                    else:
                        parsed = tomllib.loads(target.read_text(encoding="utf-8"))
                        model, effort, sandbox = EXPECTED_ROLES[role]
                        self.assertEqual(parsed["model"], model)
                        self.assertEqual(parsed["model_reasoning_effort"], effort)
                        self.assertEqual(parsed.get("sandbox_mode"), sandbox)
            self.assertEqual(self.verifier.verify_install(codex_home, guidance, self.policy_path), [])

    def test_quoted_and_dotted_limits_survive_default_removal(self):
        cases = {
            "quoted": (
                '["agents"]\n"max_concurrent_threads_per_session" = 5\n'
                "'max_threads' = 4\n"
                '"default_subagent_model" = "old-model"\n'
                "'default_subagent_reasoning_effort' = 'low'\n"
                'interrupt_message = false\n'
            ),
            "dotted": (
                'model = "gpt-6-astra"\n'
                'agents.max_concurrent_threads_per_session = 5\n'
                'agents.max_threads = 4\n'
                'agents.default_subagent_model = "old-model"\n'
                'agents.default_subagent_reasoning_effort = "low"\n'
            ),
        }
        for name, initial in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                codex_home = Path(temp_dir) / ".codex"
                codex_home.mkdir()
                config_path = codex_home / "config.toml"
                config_path.write_text(initial, encoding="utf-8")
                self.installer.install(REPO_ROOT, codex_home, codex_home / "AGENTS.md")
                parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
                expected = tomllib.loads(initial)
                expected["agents"]["enabled"] = True
                del expected["agents"]["default_subagent_model"]
                del expected["agents"]["default_subagent_reasoning_effort"]
                self.assertEqual(parsed, expected)

    def test_invalid_inputs_are_rejected_before_any_profile_change(self):
        cases = ("config", "guidance", "missing-role", "malformed-role", "wrong-role")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "source"
                for directory in ("agents", "policy"):
                    shutil.copytree(REPO_ROOT / directory, source / directory)
                codex_home = root / ".codex"
                codex_home.mkdir()
                config = codex_home / "config.toml"
                config.write_text('model = "gpt-6-astra"\n', encoding="utf-8")
                guidance = codex_home / "AGENTS.md"
                guidance.write_text("Keep this line.\n", encoding="utf-8")
                old_role = codex_home / "agents" / "owner.toml"
                old_role.parent.mkdir()
                old_role.write_text('name = "owner"\n', encoding="utf-8")
                candidate = source / "agents" / "sol-high.toml"
                if case == "config":
                    config.write_text('model = [\n', encoding="utf-8")
                elif case == "guidance":
                    guidance.write_text(self.installer.BLOCK_START + "\n", encoding="utf-8")
                elif case == "missing-role":
                    candidate.unlink()
                elif case == "malformed-role":
                    candidate.write_text('model = [\n', encoding="utf-8")
                elif case == "wrong-role":
                    candidate.write_text(candidate.read_text(encoding="utf-8").replace(
                        'model = "gpt-6.1-sol"', 'model = "wrong-model"'
                    ), encoding="utf-8")
                before = profile_snapshot(codex_home)
                with self.assertRaises((ValueError, OSError)):
                    self.installer.install(source, codex_home, guidance)
                self.assertEqual(profile_snapshot(codex_home), before)

    def test_verifier_rejects_retired_roles_and_stale_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            guidance = codex_home / "AGENTS.md"
            self.installer.install(REPO_ROOT, codex_home, guidance)
            stale_role = codex_home / "agents" / "owner.toml"
            stale_role.write_text('name = "owner"\n', encoding="utf-8")
            self.assertIn("agent:owner:retired", self.verifier.verify_install(codex_home, guidance, self.policy_path))
            stale_role.unlink()
            original = guidance.read_text(encoding="utf-8")
            guidance.write_text(original.replace(self.installer.BLOCK_START,
                self.installer.BLOCK_START + "\nStale policy."), encoding="utf-8")
            self.assertIn("guidance:managed-block-content", self.verifier.verify_install(codex_home, guidance, self.policy_path))

    def test_first_role_write_failure_restores_profile_and_keeps_backups(self):
        for existing_agents in (False, True):
            for write_before_failure in (False, True):
                with self.subTest(existing_agents=existing_agents, write_before_failure=write_before_failure), tempfile.TemporaryDirectory() as temp_dir:
                    codex_home = Path(temp_dir) / ".codex"
                    codex_home.mkdir()
                    config = codex_home / "config.toml"
                    config.write_text('model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"\n', encoding="utf-8")
                    config.chmod(0o640)
                    guidance = codex_home / "AGENTS.md"
                    guidance.write_text("Keep existing guidance.\n", encoding="utf-8")
                    guidance.chmod(0o600)
                    if existing_agents:
                        agents = codex_home / "agents"
                        agents.mkdir()
                        (agents / "sol-high.toml").write_text('name = "previous-sol-high"\n', encoding="utf-8")
                        (agents / "sol-high.toml").chmod(0o600)
                        (agents / "owner.toml").write_text('name = "owner"\n', encoding="utf-8")
                        (agents / "owner.toml").chmod(0o644)
                    before = profile_snapshot(codex_home)
                    original_write = self.installer._atomic_write
                    attempted = []

                    def fail_first_role(path, content):
                        attempted.append(path.name)
                        if path.name == "sol-low.toml":
                            if write_before_failure:
                                original_write(path, content)
                            raise OSError("Simulated role write failure")
                        original_write(path, content)

                    with mock.patch.object(self.installer, "_atomic_write", side_effect=fail_first_role):
                        with self.assertRaisesRegex(OSError, "Simulated role write failure"):
                            self.installer.install(REPO_ROOT, codex_home, guidance)
                    self.assertEqual(attempted, ["config.toml", "AGENTS.md", "sol-low.toml"])
                    after = {
                        name: value for name, value in profile_snapshot(codex_home).items()
                        if name.split("/")[0] != "subagent-router-backups"
                    }
                    self.assertEqual(after, before)
                    for role in EXPECTED_ROLES:
                        if not (existing_agents and role == "sol-high"):
                            self.assertFalse((codex_home / "agents" / f"{role}.toml").exists())
                    backup_dirs = list((codex_home / "subagent-router-backups").iterdir())
                    self.assertEqual(len(backup_dirs), 1)
                    self.assertEqual(profile_snapshot(backup_dirs[0]), before)

    def test_last_role_write_failure_restores_read_only_config_and_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_text('model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"\n', encoding="utf-8")
            guidance = codex_home / "AGENTS.md"
            guidance.write_text("Keep existing guidance.\n", encoding="utf-8")
            config.chmod(0o444)
            guidance.chmod(0o444)
            before = profile_snapshot(codex_home)
            original_write = self.installer._atomic_write

            def fail_after_last_role(path, content):
                original_write(path, content)
                if path.name == "astra-reviewer.toml":
                    raise OSError("Simulated last role write failure")

            with mock.patch.object(self.installer, "_atomic_write", side_effect=fail_after_last_role):
                with self.assertRaisesRegex(OSError, "Simulated last role write failure"):
                    self.installer.install(REPO_ROOT, codex_home, guidance)
            after = {
                name: value for name, value in profile_snapshot(codex_home).items()
                if name.split("/")[0] != "subagent-router-backups"
            }
            self.assertEqual(after, before)
            self.assertFalse((codex_home / "agents").exists())
            backup_dirs = list((codex_home / "subagent-router-backups").iterdir())
            self.assertEqual(len(backup_dirs), 1)
            self.assertEqual(profile_snapshot(backup_dirs[0]), before)

    def test_failed_first_restore_still_restores_guidance_and_cleans_roles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            original_config = 'model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"\n'
            config.write_text(original_config, encoding="utf-8")
            config.chmod(0o640)
            guidance = codex_home / "AGENTS.md"
            original_guidance = "Keep existing guidance.\n"
            guidance.write_text(original_guidance, encoding="utf-8")
            guidance.chmod(0o444)
            original_write = self.installer._atomic_write
            original_restore = self.installer._restore_backup
            restores = []

            def fail_after_last_role(path, content):
                original_write(path, content)
                if path.name == "astra-reviewer.toml":
                    raise OSError("Simulated last role write failure")

            def fail_first_restore(source, destination):
                restores.append(destination.name)
                if len(restores) == 1:
                    raise OSError("Simulated first restore failure")
                original_restore(source, destination)

            with mock.patch.object(self.installer, "_atomic_write", side_effect=fail_after_last_role), mock.patch.object(self.installer, "_restore_backup", side_effect=fail_first_restore):
                with self.assertRaises(RuntimeError) as raised:
                    self.installer.install(REPO_ROOT, codex_home, guidance)
            self.assertEqual(restores, ["config.toml", "AGENTS.md"])
            self.assertEqual(guidance.read_text(encoding="utf-8"), original_guidance)
            self.assertEqual(guidance.stat().st_mode & 0o777, 0o444)
            self.assertFalse((codex_home / "agents").exists())
            self.assertNotEqual(config.read_text(encoding="utf-8"), original_config)
            backup_dirs = list((codex_home / "subagent-router-backups").iterdir())
            self.assertEqual(len(backup_dirs), 1)
            backup_config = backup_dirs[0] / "config.toml"
            self.assertEqual(backup_config.read_text(encoding="utf-8"), original_config)
            self.assertEqual(backup_config.stat().st_mode & 0o777, 0o640)
            self.assertIn("incomplete recovery", str(raised.exception))
            self.assertIn("config.toml", str(raised.exception))
            self.assertIn(str(backup_dirs[0]), str(raised.exception))
            self.assertIsInstance(raised.exception.__cause__, OSError)

    def test_regular_file_at_agents_directory_rejects_before_profile_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text('model = "gpt-6-astra"\n', encoding="utf-8")
            guidance = codex_home / "AGENTS.md"
            guidance.write_text("Keep existing guidance.\n", encoding="utf-8")
            (codex_home / "agents").write_text("This is a file.\n", encoding="utf-8")
            before = profile_snapshot(codex_home)
            with self.assertRaises((OSError, ValueError)):
                self.installer.install(REPO_ROOT, codex_home, guidance)
            self.assertEqual(profile_snapshot(codex_home), before)

    def test_managed_config_and_role_symlinks_preserve_link_and_target(self):
        for destination in ("config.toml", "agents/sol-low.toml"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                codex_home = root / ".codex"
                codex_home.mkdir()
                target = root / "external.toml"
                target.write_text('model = "gpt-6-astra"\n', encoding="utf-8")
                target.chmod(0o640)
                link = codex_home / destination
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)
                before = profile_snapshot(codex_home)
                target_before = (target.read_bytes(), target.stat().st_mode & 0o777)
                link_before = link.readlink()
                with self.assertRaisesRegex(ValueError, "symbolic link"):
                    self.installer.install(REPO_ROOT, codex_home, codex_home / "AGENTS.md")
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.readlink(), link_before)
                self.assertEqual((target.read_bytes(), target.stat().st_mode & 0o777), target_before)
                self.assertEqual(profile_snapshot(codex_home), before)

    def test_agents_config_without_trailing_newline_installs(self):
        for initial in ('[agents]', '[agents]\nmax_threads = 3'):
            with self.subTest(initial=initial), tempfile.TemporaryDirectory() as temp_dir:
                codex_home = Path(temp_dir) / ".codex"
                codex_home.mkdir()
                config = codex_home / "config.toml"
                config.write_text(initial, encoding="utf-8")
                guidance = codex_home / "AGENTS.md"
                self.installer.install(REPO_ROOT, codex_home, guidance)
                expected = tomllib.loads(initial)
                expected["agents"]["enabled"] = True
                self.assertEqual(tomllib.loads(config.read_text(encoding="utf-8")), expected)
                self.assertEqual(self.verifier.verify_install(codex_home, guidance, self.policy_path), [])

    def test_inline_agents_table_rejects_without_profile_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_text('model = "gpt-6-astra"\nagents = { enabled = false, max_threads = 3 }\n', encoding="utf-8")
            guidance = codex_home / "AGENTS.md"
            guidance.write_text("Keep existing guidance.\n", encoding="utf-8")
            before = profile_snapshot(codex_home)
            with self.assertRaisesRegex(ValueError, "Inline agents table"):
                self.installer.install(REPO_ROOT, codex_home, guidance)
            self.assertEqual(profile_snapshot(codex_home), before)

    def test_shareable_tree_contains_no_machine_or_company_identifiers(self):
        self.assertEqual(self.verifier.scan_shareable_tree(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
