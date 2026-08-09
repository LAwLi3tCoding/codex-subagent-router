#!/usr/bin/env python3
"""Verify repository safety and an installed Codex subagent router."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path


BLOCK_START = "<!-- CODEX-SUBAGENT-ROUTER:START -->"
BLOCK_END = "<!-- CODEX-SUBAGENT-ROUTER:END -->"
HOOK_FILENAME = "codex_subagent_router_disclosure.py"
HOOK_STATUS = "Showing subagent model and reasoning"
RETIRED_AGENT_ROLES = (
    "luna-batch",
    "luna-reasoner",
    "terra-explorer",
    "terra-researcher",
)
FAMILY_EFFORTS = {
    "luna": ("low", "medium", "high", "xhigh", "max"),
    "terra": ("low", "medium", "high", "xhigh", "max", "ultra"),
    "sol": ("low", "medium", "high", "xhigh", "max", "ultra"),
}
EXPECTED_ROLES = {"default": (None, None)}
for family, efforts in FAMILY_EFFORTS.items():
    EXPECTED_ROLES.update(
        {
            f"{family}-{effort}": (f"gpt-5.6-{family}", effort)
            for effort in efforts
        }
    )
COUNT = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
AGENT_GROUP = r"(?:children|subagents|agents)"
AGENT_MODIFIERS = r"(?:(?:concurrent|parallel|spawned)\s+)?"
FIXED_CHILD_CAP_PATTERNS = (
    re.compile(
        rf"(?i)\b(?:never exceed|no more than|at most|up to|maximum of)\s+"
        rf"{COUNT}\s+{AGENT_MODIFIERS}{AGENT_GROUP}\b"
    ),
    re.compile(
        rf"(?i)\blimit\s+(?:the\s+number\s+of\s+)?"
        rf"{AGENT_MODIFIERS}{AGENT_GROUP}\s+to\s+{COUNT}\b"
    ),
    re.compile(
        rf"(?i)\bcap\s+(?:the\s+number\s+of\s+)?"
        rf"{AGENT_MODIFIERS}{AGENT_GROUP}\s+at\s+{COUNT}\b"
    ),
    re.compile(
        rf"(?i)\b(?:prefer|default to|normally use|usually use|start with)\s+"
        rf"{COUNT}\s+{AGENT_MODIFIERS}{AGENT_GROUP}\b"
    ),
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
            part in {".git", ".omx", "__pycache__"} for part in path.parts
        ):
            continue
        if path.suffix in {".pyc", ".pyo"}:
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


def verify_runtime_model_matrix(models_cache_path: Path) -> list[str]:
    if not models_cache_path.exists():
        return []
    try:
        payload = json.loads(models_cache_path.read_text(encoding="utf-8"))
        models = payload["models"]
        if not isinstance(models, list):
            raise TypeError("models must be a list")
        supported = {
            str(model["slug"]): {
                str(level["effort"])
                for level in model["supported_reasoning_levels"]
                if isinstance(level, dict) and "effort" in level
            }
            for model in models
            if isinstance(model, dict)
            and "slug" in model
            and isinstance(model.get("supported_reasoning_levels"), list)
        }
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return [f"runtime-model-cache:{type(error).__name__}"]

    findings: list[str] = []
    for family, efforts in FAMILY_EFFORTS.items():
        model = f"gpt-5.6-{family}"
        if model not in supported:
            findings.append(f"runtime-model:{model}:missing")
            continue
        for effort in efforts:
            if effort not in supported[model]:
                findings.append(f"runtime-model:{model}:{effort}")
    return findings


def verify_install(
    codex_home: Path, global_agents: Path, policy_path: Path | None = None
) -> list[str]:
    errors: list[str] = []
    config_path = codex_home / "config.toml"
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [f"config:{error}"]

    agents_config = config.get("agents", {})
    if agents_config.get("enabled") is not True:
        errors.append("config:agents.enabled")
    for forbidden in (
        "max_concurrent_threads_per_session",
        "max_threads",
        "default_subagent_model",
        "default_subagent_reasoning_effort",
    ):
        if forbidden in agents_config:
            errors.append(f"config:agents.{forbidden}")
    if config.get("features", {}).get("hooks") is not True:
        errors.append("config:features.hooks")

    for role in RETIRED_AGENT_ROLES:
        if (codex_home / "agents" / f"{role}.toml").exists():
            errors.append(f"agent:{role}:retired")

    for role, expected in EXPECTED_ROLES.items():
        role_path = codex_home / "agents" / f"{role}.toml"
        try:
            role_config = tomllib.loads(role_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            errors.append(f"agent:{role}:{error}")
            continue
        if role_config.get("name") != role:
            errors.append(f"agent:{role}:name")
        if role_config.get("model") != expected[0]:
            errors.append(f"agent:{role}:model")
        if role_config.get("model_reasoning_effort") != expected[1]:
            errors.append(f"agent:{role}:model_reasoning_effort")
        if not role_config.get("description") or not role_config.get("developer_instructions"):
            errors.append(f"agent:{role}:required-fields")

    try:
        guidance = global_agents.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"guidance:{error}")
    else:
        if guidance.count(BLOCK_START) != 1 or guidance.count(BLOCK_END) != 1:
            errors.append("guidance:managed-block")
        else:
            start = guidance.index(BLOCK_START)
            end = guidance.index(BLOCK_END, start) + len(BLOCK_END)
            installed_block = guidance[start:end]
            if policy_path is not None:
                policy = policy_path.read_text(encoding="utf-8").rstrip()
                expected_block = f"{BLOCK_START}\n{policy}\n{BLOCK_END}"
                if installed_block != expected_block:
                    errors.append("guidance:managed-block-content")
        if any(pattern.search(guidance) for pattern in FIXED_CHILD_CAP_PATTERNS):
            errors.append("guidance:fixed-concurrency-cap")

    hook_path = codex_home / "hooks" / HOOK_FILENAME
    try:
        installed_hook = hook_path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"hook-script:{error}")
    else:
        if policy_path is not None:
            source_hook = policy_path.parents[1] / "hooks" / HOOK_FILENAME
            if installed_hook != source_hook.read_text(encoding="utf-8"):
                errors.append("hook-script:content")

    try:
        hooks_config = json.loads(
            (codex_home / "hooks.json").read_text(encoding="utf-8")
        )
        groups = hooks_config["hooks"]["SubagentStart"]
        managed_handlers = []
        for group in groups:
            if not isinstance(group, dict) or group.get("matcher") != "*":
                continue
            handlers = group.get("hooks", [])
            if not isinstance(handlers, list):
                continue
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                if (
                    handler.get("type") != "command"
                    or handler.get("statusMessage") != HOOK_STATUS
                    or handler.get("timeout") != 5
                ):
                    continue
                command_parts = shlex.split(str(handler.get("command", "")))
                if len(command_parts) != 2:
                    continue
                if (
                    Path(command_parts[0]).expanduser().resolve()
                    == Path(sys.executable).resolve()
                    and Path(command_parts[1]).expanduser().resolve()
                    == hook_path.resolve()
                ):
                    managed_handlers.append(handler)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        errors.append(f"hooks-config:{error}")
    else:
        if len(managed_handlers) != 1:
            errors.append("hooks-config:managed-handler")
        else:
            smoke_payload = {
                "hook_event_name": "SubagentStart",
                "agent_type": "sol-xhigh",
                "model": "runtime-model",
            }
            expected_message = (
                "Subagent started | role: sol-xhigh | model: runtime-model | "
                "reasoning: xhigh"
            )
            try:
                smoke = subprocess.run(
                    [sys.executable, str(hook_path)],
                    input=json.dumps(smoke_payload),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                smoke_output = json.loads(smoke.stdout)
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
                errors.append(f"hook-script:smoke:{type(error).__name__}")
            else:
                if (
                    smoke.returncode != 0
                    or smoke_output.get("systemMessage") != expected_message
                ):
                    errors.append("hook-script:smoke")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--global-agents", type=Path)
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parents[1]
    global_agents = args.global_agents or args.codex_home / "AGENTS.md"

    errors = [f"shareable:{item}" for item in scan_shareable_tree(source_root)]
    warnings = verify_runtime_model_matrix(args.codex_home / "models_cache.json")
    errors.extend(
        verify_install(
            args.codex_home,
            global_agents,
            source_root / "policy" / "subagent-routing.md",
        )
    )
    for warning in warnings:
        print(f"warning:{warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Router source and installed configuration verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
