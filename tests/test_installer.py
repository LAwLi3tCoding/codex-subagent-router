import importlib.util
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerContractTest(unittest.TestCase):
    def test_model_roles_enforce_capability_boundaries(self):
        policy = (REPO_ROOT / "policy" / "subagent-routing.md").read_text(
            encoding="utf-8"
        )
        luna = tomllib.loads(
            (REPO_ROOT / "agents" / "luna-reasoner.toml").read_text(
                encoding="utf-8"
            )
        )
        terra_explorer = tomllib.loads(
            (REPO_ROOT / "agents" / "terra-explorer.toml").read_text(
                encoding="utf-8"
            )
        )
        terra_researcher = tomllib.loads(
            (REPO_ROOT / "agents" / "terra-researcher.toml").read_text(
                encoding="utf-8"
            )
        )
        ultra = tomllib.loads(
            (REPO_ROOT / "agents" / "sol-ultra.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(luna["model_reasoning_effort"], "max")
        self.assertIn("strictly bounded", luna["developer_instructions"])
        self.assertIn("independently and mechanically verified", policy)
        self.assertIn("Never route open-ended", policy)

        self.assertEqual(terra_explorer["sandbox_mode"], "read-only")
        self.assertEqual(terra_researcher["sandbox_mode"], "read-only")
        self.assertIn("must not make the final decision", policy)
        self.assertIn("high-risk", terra_explorer["developer_instructions"])
        self.assertIn("high-risk", terra_researcher["developer_instructions"])

        self.assertEqual(ultra["model"], "gpt-5.6-sol")
        self.assertEqual(ultra["model_reasoning_effort"], "max")
        self.assertIn("orchestration role", ultra["description"])
        self.assertIn("Ultra is an orchestration pattern", policy)

    def test_one_command_installer_activates_router(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            result = subprocess.run(
                [
                    "sh",
                    str(REPO_ROOT / "install.sh"),
                    "--codex-home",
                    str(codex_home),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Router source and installed configuration verified.", result.stdout)
            guidance = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- CODEX-SUBAGENT-ROUTER:START -->", guidance)
            self.assertTrue((codex_home / "agents" / "luna-reasoner.toml").is_file())
            self.assertTrue((codex_home / "agents" / "sol-ultra.toml").is_file())

    def test_install_preserves_unrelated_config_and_enforces_routing_contract(self):
        installer = load_module("router_install", REPO_ROOT / "scripts" / "install.py")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / ".codex"
            codex_home.mkdir()
            global_agents = codex_home / "AGENTS.md"
            config = codex_home / "config.toml"

            global_agents.write_text(
                "# Existing guidance\n\n"
                "- Never exceed six children; inherit model defaults absent a concrete reason.\n\n"
                "Keep this line.\n",
                encoding="utf-8",
            )
            config.write_text(
                'model = "session-selected-model"\n'
                'model_reasoning_effort = "high"\n\n'
                '[agents]\n'
                'max_concurrent_threads_per_session = 3\n'
                'max_threads = 2\n'
                'default_subagent_model = "old-model"\n'
                'default_subagent_reasoning_effort = "low"\n'
                'interrupt_message = false\n\n'
                '[mcp_servers]\n',
                encoding="utf-8",
            )
            config.chmod(0o600)

            installer.install(REPO_ROOT, codex_home, global_agents)

            parsed_config = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(parsed_config["model"], "session-selected-model")
            self.assertEqual(parsed_config["model_reasoning_effort"], "high")
            self.assertTrue(parsed_config["agents"]["enabled"])
            self.assertFalse(parsed_config["agents"]["interrupt_message"])
            self.assertNotIn("max_concurrent_threads_per_session", parsed_config["agents"])
            self.assertNotIn("max_threads", parsed_config["agents"])
            self.assertNotIn("default_subagent_model", parsed_config["agents"])
            self.assertNotIn("default_subagent_reasoning_effort", parsed_config["agents"])

            expected_roles = {
                "default": (None, None),
                "luna-batch": ("gpt-5.6-luna", "medium"),
                "luna-reasoner": ("gpt-5.6-luna", "max"),
                "terra-explorer": ("gpt-5.6-terra", "medium"),
                "terra-researcher": ("gpt-5.6-terra", "high"),
                "sol-high": ("gpt-5.6-sol", "high"),
                "sol-xhigh": ("gpt-5.6-sol", "xhigh"),
                "sol-max": ("gpt-5.6-sol", "max"),
                "sol-ultra": ("gpt-5.6-sol", "max"),
            }
            for role, expected in expected_roles.items():
                role_file = codex_home / "agents" / f"{role}.toml"
                self.assertTrue(role_file.is_file(), role)
                role_config = tomllib.loads(role_file.read_text(encoding="utf-8"))
                self.assertEqual(role_config.get("model"), expected[0], role)
                self.assertEqual(role_config.get("model_reasoning_effort"), expected[1], role)

            installed_guidance = global_agents.read_text(encoding="utf-8")
            self.assertIn("Keep this line.", installed_guidance)
            self.assertIn("decides how many children to run", installed_guidance)
            self.assertNotIn("no more than three", installed_guidance.lower())
            self.assertNotIn("never exceed six children", installed_guidance.lower())
            self.assertEqual(installed_guidance.count(installer.BLOCK_START), 1)
            self.assertEqual(installed_guidance.count(installer.BLOCK_END), 1)

            verifier = load_module("router_verify_install", REPO_ROOT / "scripts" / "verify.py")
            policy_path = REPO_ROOT / "policy" / "subagent-routing.md"
            self.assertEqual(
                verifier.verify_install(codex_home, global_agents, policy_path), []
            )
            stale_guidance = installed_guidance.replace(
                "The parent agent decides how many children to run",
                "The parent agent runs no more than three children",
            )
            global_agents.write_text(stale_guidance, encoding="utf-8")
            verification_errors = verifier.verify_install(
                codex_home, global_agents, policy_path
            )
            self.assertIn("guidance:managed-block-content", verification_errors)
            for fixed_preference in (
                "Use up to four children for normal work.",
                "Use a maximum of 4 subagents.",
                "Limit parallel agents to 3.",
                "Prefer two children for routine tasks.",
            ):
                global_agents.write_text(
                    fixed_preference + "\n" + installed_guidance,
                    encoding="utf-8",
                )
                preference_errors = verifier.verify_install(
                    codex_home, global_agents, policy_path
                )
                self.assertIn(
                    "guidance:fixed-concurrency-cap",
                    preference_errors,
                    fixed_preference,
                )
            global_agents.write_text(installed_guidance, encoding="utf-8")

            first_config = config.read_text(encoding="utf-8")
            first_guidance = installed_guidance
            installer.install(REPO_ROOT, codex_home, global_agents)
            self.assertEqual(config.read_text(encoding="utf-8"), first_config)
            self.assertEqual(global_agents.read_text(encoding="utf-8"), first_guidance)

    def test_quoted_and_dotted_concurrency_keys_are_removed(self):
        installer = load_module("router_install_key_forms", REPO_ROOT / "scripts" / "install.py")
        cases = {
            "quoted": (
                '[agents]\n'
                '"max_concurrent_threads_per_session" = 5\n'
                "'max_threads' = 4\n"
                'interrupt_message = false\n'
            ),
            "dotted": (
                'model = "session-selected-model"\n'
                'agents.max_concurrent_threads_per_session = 5\n'
                'agents.max_threads = 4\n'
            ),
        }

        for name, initial_config in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                codex_home = root / ".codex"
                codex_home.mkdir()
                config = codex_home / "config.toml"
                config.write_text(initial_config, encoding="utf-8")
                global_agents = codex_home / "AGENTS.md"
                installer.install(REPO_ROOT, codex_home, global_agents)
                parsed = tomllib.loads(config.read_text(encoding="utf-8"))
                self.assertTrue(parsed["agents"]["enabled"])
                self.assertNotIn("max_concurrent_threads_per_session", parsed["agents"])
                self.assertNotIn("max_threads", parsed["agents"])

    def test_shareable_tree_contains_no_machine_or_company_identifiers(self):
        verifier = load_module("router_verify", REPO_ROOT / "scripts" / "verify.py")
        self.assertEqual(verifier.scan_shareable_tree(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
