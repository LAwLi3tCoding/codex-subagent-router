#!/usr/bin/env python3
"""Verify the current routing contract and installed files; not runtime performance."""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

BLOCK_START = "<!-- CODEX-SUBAGENT-ROUTER:START -->"
BLOCK_END = "<!-- CODEX-SUBAGENT-ROUTER:END -->"
EXPECTED_ROLES = {
    "sol-low": ("gpt-6.1-sol", "low", None),
    "sol-medium": ("gpt-6.1-sol", "medium", None),
    "sol-high": ("gpt-6.1-sol", "high", None),
    "sol-xhigh": ("gpt-6.1-sol", "xhigh", None),
    "sol-reviewer": ("gpt-6.1-sol", "high", "read-only"),
    "astra-reviewer": ("gpt-6-astra", "xhigh", "read-only"),
}
# Obsolete installed files are errors, not supported execution roles.
RETIRED_AGENT_ROLES = (
    "default", "explorer", "mechanical", "owner", "high-risk-owner",
    "luna-low", "luna-batch", "luna-reasoner", "luna-medium", "luna-high",
    "luna-xhigh", "luna-max", "terra-explorer", "terra-researcher", "terra-low",
    "terra-medium", "terra-high", "terra-xhigh", "terra-max", "terra-ultra",
    "sol-max", "sol-ultra",
)


def scan_shareable_tree(root: Path) -> list[str]:
    findings: list[str] = []
    local_user = Path.home().name
    internal_domains = ["san" + "kuai.com", "mei" + "tuan.com"]
    home_pattern = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    token_pattern = re.compile(r"(?:sk|ghp|github_pat)-[A-Za-z0-9_]{16,}")

    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(
            part in {".git", ".omx", ".leanpowers", "__pycache__"} for part in path.parts
        ):
            continue
        if path.name in {".DS_Store", ".leanpowers.owner.json"} or path.suffix in {".pyc", ".pyo"}:
            continue
        relative = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"binary:{relative}")
            continue
        if home_pattern.search(text):
            findings.append(f"absolute-home-path:{relative}")
        if local_user and local_user in text:
            findings.append(f"local-user:{relative}")
        if any(domain in text.lower() for domain in internal_domains):
            findings.append(f"internal-domain:{relative}")
        if email_pattern.search(text):
            findings.append(f"email:{relative}")
        if token_pattern.search(text):
            findings.append(f"credential-pattern:{relative}")
    return findings


def verify_install(codex_home: Path, global_agents: Path,
                   policy_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    try:
        config = tomllib.loads((codex_home / "config.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [f"config:{error}"]
    agents = config.get("agents", {})
    if agents.get("enabled") is not True:
        errors.append("config:agents.enabled")
    for key in ("default_subagent_model", "default_subagent_reasoning_effort"):
        if key in agents:
            errors.append(f"config:agents.{key}")
    for role in RETIRED_AGENT_ROLES:
        if (codex_home / "agents" / f"{role}.toml").exists():
            errors.append(f"agent:{role}:retired")
    for role, (model, effort, sandbox) in EXPECTED_ROLES.items():
        path = codex_home / "agents" / f"{role}.toml"
        try:
            content = path.read_text(encoding="utf-8")
            parsed = tomllib.loads(content)
            if policy_path is not None:
                expected = (policy_path.parents[1] / "agents" / path.name).read_text(encoding="utf-8")
                if content != expected:
                    errors.append(f"agent:{role}:content")
        except (OSError, tomllib.TOMLDecodeError) as error:
            errors.append(f"agent:{role}:{error}")
            continue
        for key, value in (("name", role), ("model", model),
                           ("model_reasoning_effort", effort), ("sandbox_mode", sandbox)):
            if parsed.get(key) != value:
                errors.append(f"agent:{role}:{key}")
        if not str(parsed.get("description", "")).strip() or not str(parsed.get("developer_instructions", "")).strip():
            errors.append(f"agent:{role}:required-fields")
    try:
        guidance = global_agents.read_text(encoding="utf-8")
        if guidance.count(BLOCK_START) != 1 or guidance.count(BLOCK_END) != 1:
            errors.append("guidance:managed-block")
        else:
            start, end = guidance.index(BLOCK_START), guidance.index(BLOCK_END)
            if end < start:
                errors.append("guidance:managed-block")
            elif policy_path is not None:
                policy = policy_path.read_text(encoding="utf-8").rstrip()
                if guidance[start:end + len(BLOCK_END)] != f"{BLOCK_START}\n{policy}\n{BLOCK_END}":
                    errors.append("guidance:managed-block-content")
    except OSError as error:
        errors.append(f"guidance:{error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--global-agents", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    override = args.codex_home / "AGENTS.override.md"
    active = override if override.is_file() and override.read_text(encoding="utf-8").strip() else args.codex_home / "AGENTS.md"
    errors = [f"shareable:{item}" for item in scan_shareable_tree(root)]
    errors += verify_install(args.codex_home, args.global_agents or active,
                             root / "policy/subagent-routing.md")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Router source and installed configuration verified; runtime routing is not inferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
