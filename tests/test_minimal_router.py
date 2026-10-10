import importlib.util
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROLES = {
    "sol-low": ("gpt-6.1-sol", "low", None),
    "sol-medium": ("gpt-6.1-sol", "medium", None),
    "sol-high": ("gpt-6.1-sol", "high", None),
    "sol-xhigh": ("gpt-6.1-sol", "xhigh", None),
    "sol-reviewer": ("gpt-6.1-sol", "high", "read-only"),
    "astra-reviewer": ("gpt-6-astra", "xhigh", "read-only"),
}


class MinimalRouterContractTest(unittest.TestCase):
    def test_four_execution_roles_and_two_independent_reviewers_are_shipped(self):
        role_files = sorted((REPO_ROOT / "agents").glob("*.toml"))
        self.assertEqual({path.stem for path in role_files}, set(EXPECTED_ROLES))
        for path in role_files:
            with self.subTest(role=path.stem):
                config = tomllib.loads(path.read_text(encoding="utf-8"))
                model, effort, sandbox = EXPECTED_ROLES[path.stem]
                self.assertEqual(config["name"], path.stem)
                self.assertEqual(config.get("model"), model)
                self.assertEqual(config.get("model_reasoning_effort"), effort)
                self.assertEqual(config.get("sandbox_mode"), sandbox)
                self.assertTrue(config.get("description"))
                self.assertTrue(config.get("developer_instructions"))

    def test_roles_do_not_expand_permissions_or_set_global_defaults(self):
        allowed_keys = {
            "name", "description", "model", "model_reasoning_effort",
            "developer_instructions",
        }
        for role in EXPECTED_ROLES:
            with self.subTest(role=role):
                config = tomllib.loads(
                    (REPO_ROOT / "agents" / f"{role}.toml").read_text(encoding="utf-8")
                )
                expected_keys = allowed_keys | (
                    {"sandbox_mode"} if role.endswith("-reviewer") else set()
                )
                self.assertEqual(set(config), expected_keys)

    def test_migration_retires_legacy_roles_but_keeps_current_sol_roles(self):
        path = REPO_ROOT / "scripts" / "install.py"
        spec = importlib.util.spec_from_file_location("minimal_router_install", path)
        self.assertIsNotNone(spec)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        self.assertEqual(set(installer.EXPECTED_AGENT_ROLES), set(EXPECTED_ROLES))
        self.assertTrue(set(EXPECTED_ROLES).isdisjoint(installer.RETIRED_AGENT_ROLES))
        for role in (
            "default", "explorer", "mechanical", "owner", "high-risk-owner",
            "luna-low", "luna-medium", "luna-high", "luna-xhigh", "luna-max",
            "terra-low", "terra-medium", "terra-high", "terra-xhigh",
            "terra-max", "terra-ultra", "sol-max", "sol-ultra",
        ):
            with self.subTest(role=role):
                self.assertIn(role, installer.RETIRED_AGENT_ROLES)


if __name__ == "__main__":
    unittest.main()
