import importlib.util
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROLE_MATRIX = {
    **{
        f"luna-{effort}": ("gpt-5.6-luna", effort)
        for effort in ("medium", "high", "xhigh", "max")
    },
    **{
        f"terra-{effort}": ("gpt-5.6-terra", effort)
        for effort in ("low", "medium", "high", "xhigh", "max", "ultra")
    },
    **{
        f"sol-{effort}": ("gpt-5.6-sol", effort)
        for effort in ("low", "medium", "high", "xhigh", "max", "ultra")
    },
}
RETIRED_ROLES = (
    "luna-low",
    "luna-batch",
    "luna-reasoner",
    "terra-explorer",
    "terra-researcher",
)
RECEIPT_FIELDS = {
    "remaining_work",
    "delegation_benefit",
    "phase",
    "work_mode",
    "scope_closed",
    "design_closed",
    "risk",
    "complexity_signals",
    "independent_workstreams",
    "same_tier_required",
    "selected_role",
    "selected_model",
    "selected_effort",
    "rejected_lower_tier",
    "rejected_higher_tier",
    "fallback",
}


def read_role(role: str) -> dict[str, object]:
    return tomllib.loads(
        (REPO_ROOT / "agents" / f"{role}.toml").read_text(encoding="utf-8")
    )


def load_verifier():
    path = REPO_ROOT / "scripts" / "verify.py"
    spec = importlib.util.spec_from_file_location("routing_policy_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoutingPolicyContractTest(unittest.TestCase):
    def test_canonical_model_effort_matrix_matches_role_files(self):
        for role, expected in CANONICAL_ROLE_MATRIX.items():
            with self.subTest(role=role):
                config = read_role(role)
                self.assertEqual(config["name"], role)
                self.assertEqual(config.get("model"), expected[0])
                self.assertEqual(config.get("model_reasoning_effort"), expected[1])
        self.assertFalse((REPO_ROOT / "agents" / "luna-ultra.toml").exists())
        self.assertFalse((REPO_ROOT / "agents" / "luna-low.toml").exists())

    def test_retired_aliases_are_not_exposed(self):
        verifier = load_verifier()
        public_guidance = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                REPO_ROOT / "policy" / "subagent-routing.md",
                REPO_ROOT / "README.md",
                REPO_ROOT / "README.zh-CN.md",
            )
        )

        for role in RETIRED_ROLES:
            with self.subTest(role=role):
                self.assertFalse((REPO_ROOT / "agents" / f"{role}.toml").exists())
                self.assertNotIn(role, verifier.EXPECTED_ROLES)
                self.assertNotIn(f"`{role}`", public_guidance)

    def test_policy_requires_receipt_precedence_and_affirmative_default(self):
        policy = (REPO_ROOT / "policy" / "subagent-routing.md").read_text(
            encoding="utf-8"
        )
        default = read_role("default")

        self.assertIn("### Routing decision receipt", policy)
        self.assertIn("Every spawn prompt must include", policy)
        for field in RECEIPT_FIELDS:
            self.assertIn(f"`{field}`", policy)
        self.assertIn("### Conflict precedence", policy)
        self.assertIn("Split mixed-mode work into sequential assignments", policy)
        self.assertIn("A lower tier requires all downgrade conditions", policy)
        self.assertIn("Any high-risk escalation signal is sufficient", policy)
        self.assertIn("Unknown is not evidence for a cheaper route", policy)
        self.assertIn("affirmative same-tier match", policy)
        self.assertIn("affirmative same-tier match", default["developer_instructions"])

    def test_policy_uses_positive_delegation_and_family_defaults(self):
        policy = (REPO_ROOT / "policy" / "subagent-routing.md").read_text(
            encoding="utf-8"
        )
        compact_policy = " ".join(policy.split())

        self.assertIn("Split the task into ready workstreams", compact_policy)
        self.assertIn("must run them in parallel", compact_policy)
        self.assertIn("more than a trivial lookup or edit", compact_policy)
        self.assertIn("does not require `ultra`", compact_policy)
        self.assertIn("Delegate non-trivial isolated read-only evidence work to Terra by default", compact_policy)
        self.assertIn("does not need to be present in the original user request", compact_policy)
        self.assertIn("delegate non-trivial mechanical implementation", compact_policy)
        self.assertIn("Use Sol only when local judgment remains", compact_policy)

    def test_dispatch_scenarios_cover_parallel_serial_and_direct_decisions(self):
        payload = json.loads(
            (REPO_ROOT / "policy" / "routing-scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        cases = {case["id"]: case for case in payload["dispatch_cases"]}

        self.assertEqual(
            set(cases),
            {
                "direct-trivial-lookup",
                "parallel-terra-independent-readonly",
                "parallel-luna-nonoverlapping-implementation",
                "serial-terra-then-luna",
                "serial-overlapping-writes",
                "single-sol-local-judgment",
            },
        )
        self.assertEqual(cases["direct-trivial-lookup"]["expected_mode"], "direct")
        self.assertEqual(cases["direct-trivial-lookup"]["expected_roles"], [])

        for case_id in (
            "parallel-terra-independent-readonly",
            "parallel-luna-nonoverlapping-implementation",
        ):
            with self.subTest(case=case_id):
                case = cases[case_id]
                self.assertEqual(case["expected_mode"], "parallel")
                self.assertGreaterEqual(len(case["expected_roles"]), 2)
                self.assertFalse(any(role.endswith("-ultra") for role in case["expected_roles"]))

        self.assertEqual(cases["serial-terra-then-luna"]["expected_mode"], "serial")
        self.assertEqual(
            cases["serial-terra-then-luna"]["expected_roles"],
            ["terra-medium", "luna-high"],
        )
        self.assertEqual(cases["serial-overlapping-writes"]["expected_mode"], "serial")
        self.assertEqual(cases["single-sol-local-judgment"]["expected_mode"], "single")
        self.assertEqual(
            cases["single-sol-local-judgment"]["expected_roles"],
            ["sol-medium"],
        )

    def test_synthetic_scenarios_cover_every_route_and_invariant(self):
        scenario_path = REPO_ROOT / "policy" / "routing-scenarios.json"
        self.assertTrue(scenario_path.is_file())
        payload = json.loads(scenario_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        receipts = payload["cases"]
        self.assertEqual(len({case["id"] for case in receipts}), len(receipts))

        selected_roles = {case["receipt"]["selected_role"] for case in receipts}
        self.assertEqual(
            selected_roles,
            set(CANONICAL_ROLE_MATRIX) | {"default", "direct"},
        )

        for case in receipts:
            with self.subTest(case=case["id"]):
                receipt = case["receipt"]
                self.assertEqual(set(receipt), RECEIPT_FIELDS)
                role = receipt["selected_role"]
                if role == "direct":
                    self.assertFalse(receipt["delegation_benefit"])
                    self.assertIsNone(receipt["selected_model"])
                    self.assertIsNone(receipt["selected_effort"])
                    continue

                self.assertTrue(receipt["delegation_benefit"])
                if role == "default":
                    self.assertTrue(receipt["same_tier_required"])
                    self.assertTrue(receipt["rejected_lower_tier"])
                    self.assertTrue(receipt["rejected_higher_tier"])
                    continue

                model, effort = CANONICAL_ROLE_MATRIX[role]
                self.assertEqual(receipt["selected_model"], model)
                self.assertEqual(receipt["selected_effort"], effort)
                if role.startswith("luna-"):
                    self.assertTrue(receipt["scope_closed"])
                    self.assertTrue(receipt["design_closed"])
                    self.assertNotEqual(receipt["risk"], "high")
                if role.startswith("terra-"):
                    self.assertIn(receipt["work_mode"], {"read_only", "research"})
                    self.assertEqual(read_role(role)["sandbox_mode"], "read-only")
                if role.endswith("-ultra"):
                    self.assertGreaterEqual(receipt["independent_workstreams"], 2)
                    self.assertIn("exceptional", receipt["complexity_signals"])

    def test_luna_efforts_own_distinct_closed_implementation_tiers(self):
        policy = (REPO_ROOT / "policy" / "subagent-routing.md").read_text(
            encoding="utf-8"
        )
        payload = json.loads(
            (REPO_ROOT / "policy" / "routing-scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        receipts = {case["id"]: case["receipt"] for case in payload["cases"]}

        tiers = {
            "luna-medium-mechanical-implementation": (
                "luna-medium",
                "literal_mechanical_change",
            ),
            "luna-high-explicit-rule-implementation": (
                "luna-high",
                "multiple_explicit_rules",
            ),
            "luna-xhigh-interacting-implementation": (
                "luna-xhigh",
                "interacting_explicit_rules",
            ),
            "luna-max-closed-logic-heavy-implementation": (
                "luna-max",
                "logic_heavy",
            ),
        }
        for case_id, (role, distinguishing_signal) in tiers.items():
            with self.subTest(case=case_id):
                receipt = receipts[case_id]
                self.assertEqual(receipt["phase"], "implementation")
                self.assertEqual(receipt["work_mode"], "implementation")
                self.assertTrue(receipt["scope_closed"])
                self.assertTrue(receipt["design_closed"])
                self.assertNotEqual(receipt["risk"], "high")
                self.assertEqual(receipt["selected_role"], role)
                self.assertEqual(receipt["selected_model"], "gpt-5.6-luna")
                self.assertIn(distinguishing_signal, receipt["complexity_signals"])
                self.assertIn("exact_mechanical_oracle", receipt["complexity_signals"])

                config = read_role(role)
                self.assertIn("implementation", config["description"])
                self.assertIn(
                    "Implement authorized code changes",
                    config["developer_instructions"],
                )

        reopened = receipts["sol-xhigh-reopened-implementation-design"]
        self.assertEqual(reopened["phase"], "implementation")
        self.assertFalse(reopened["design_closed"])
        self.assertEqual(reopened["selected_role"], "sol-xhigh")

        self.assertIn("Luna Medium is the lowest named route", policy)
        self.assertIn("primary route for logic-heavy implementation", policy)
        self.assertIn("non-mechanical writes", policy)
        self.assertIn("`medium -> high -> xhigh -> max`", policy)

    def test_sol_implementation_scenarios_require_local_judgment(self):
        payload = json.loads(
            (REPO_ROOT / "policy" / "routing-scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        for case in payload["cases"]:
            receipt = case["receipt"]
            if receipt["selected_role"] not in {"sol-low", "sol-medium", "sol-high"}:
                continue
            if receipt["phase"] != "implementation":
                continue
            with self.subTest(case=case["id"]):
                self.assertFalse(receipt["design_closed"])
                self.assertIn("local_judgment", receipt["complexity_signals"])

        for role in ("sol-medium", "sol-high"):
            with self.subTest(role=role):
                config = read_role(role)
                self.assertIn("local judgment", config["description"])
                self.assertIn("local judgment", config["developer_instructions"])

    def test_runtime_model_cache_reports_missing_or_corrupt_efforts(self):
        verifier = load_verifier()
        models = [
            {
                "slug": f"gpt-5.6-{family}",
                "supported_reasoning_levels": [
                    {"effort": effort} for effort in efforts
                ],
            }
            for family, efforts in verifier.FAMILY_EFFORTS.items()
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "models_cache.json"
            cache_path.write_text(json.dumps({"models": models}), encoding="utf-8")
            self.assertEqual(verifier.verify_runtime_model_matrix(cache_path), [])

            models[0]["supported_reasoning_levels"] = [
                item
                for item in models[0]["supported_reasoning_levels"]
                if item["effort"] != "max"
            ]
            cache_path.write_text(json.dumps({"models": models}), encoding="utf-8")
            self.assertIn(
                "runtime-model:gpt-5.6-luna:max",
                verifier.verify_runtime_model_matrix(cache_path),
            )

            cache_path.write_text("not-json", encoding="utf-8")
            errors = verifier.verify_runtime_model_matrix(cache_path)
            self.assertEqual(len(errors), 1)
            self.assertTrue(errors[0].startswith("runtime-model-cache:"))

            cache_path.unlink()
            self.assertEqual(verifier.verify_runtime_model_matrix(cache_path), [])

    def test_runtime_model_cache_findings_warn_without_masking_install_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            codex_home.mkdir()
            cache_path = codex_home / "models_cache.json"
            efforts_by_model: dict[str, set[str]] = {}
            for model, effort in CANONICAL_ROLE_MATRIX.values():
                efforts_by_model.setdefault(model, set()).add(effort)
            efforts_by_model["gpt-5.6-luna"].remove("max")
            cache_path.write_text(
                json.dumps(
                    {
                        "models": [
                            {
                                "slug": model,
                                "supported_reasoning_levels": [
                                    {"effort": effort} for effort in sorted(efforts)
                                ],
                            }
                            for model, efforts in sorted(efforts_by_model.items())
                        ]
                    }
                ),
                encoding="utf-8",
            )

            install = subprocess.run(
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
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertIn(
                "warning:runtime-model:gpt-5.6-luna:max", install.stderr
            )
            self.assertIn(
                "Router source and installed configuration verified.", install.stdout
            )

            role_path = codex_home / "agents" / "sol-high.toml"
            cache_path.write_text("not-json", encoding="utf-8")
            role_path.write_text(
                role_path.read_text(encoding="utf-8").replace(
                    'model = "gpt-5.6-sol"', 'model = "gpt-5.6-luna"'
                ),
                encoding="utf-8",
            )
            verify = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "verify.py"),
                    "--codex-home",
                    str(codex_home),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify.returncode, 1)
            self.assertIn(
                "warning:runtime-model-cache:JSONDecodeError", verify.stderr
            )
            self.assertIn("agent:sol-high:model", verify.stderr)

    def test_runtime_incompatibility_falls_back_without_blocking_parent_work(self):
        policy = (REPO_ROOT / "policy" / "subagent-routing.md").read_text(
            encoding="utf-8"
        )
        compact_policy = " ".join(policy.split())

        self.assertIn("### Runtime compatibility fallback", policy)
        self.assertIn("advisory compatibility evidence", compact_policy)
        self.assertIn("try the configured route", compact_policy)
        self.assertIn("same family at `max`", compact_policy)
        self.assertIn("at most one alternate child start", compact_policy)
        self.assertIn("parent executes the assignment directly", compact_policy)
        self.assertIn("Never silently cross model families", compact_policy)
        self.assertIn("record the fallback in the routing receipt", compact_policy)


if __name__ == "__main__":
    unittest.main()
