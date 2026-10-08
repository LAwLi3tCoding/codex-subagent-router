#!/usr/bin/env python3
"""Install the current Codex routing policy without changing primary defaults."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

BLOCK_START = "<!-- CODEX-SUBAGENT-ROUTER:START -->"
BLOCK_END = "<!-- CODEX-SUBAGENT-ROUTER:END -->"
EXPECTED_AGENT_ROLES = ("sol-low", "sol-medium", "sol-high", "sol-xhigh", "astra-reviewer")
# Installation cleanup only: no aliases, routing, or fallback for these names.
RETIRED_AGENT_ROLES = (
    "default", "explorer", "mechanical", "owner", "high-risk-owner",
    "luna-low", "luna-batch", "luna-reasoner", "luna-medium", "luna-high",
    "luna-xhigh", "luna-max", "terra-explorer", "terra-researcher", "terra-low",
    "terra-medium", "terra-high", "terra-xhigh", "terra-max", "terra-ultra",
    "sol-max", "sol-ultra",
)
MANAGED_AGENT_KEYS = {"enabled", "default_subagent_model", "default_subagent_reasoning_effort"}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.router-tmp-",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, target_mode)
        temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _backup(path: Path, backup_root: Path, label: str) -> None:
    if not path.exists():
        return
    destination = backup_root / label
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def _restore_backup(source: Path, destination: Path) -> None:
    temporary: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
        shutil.copy2(source, temporary)
        temporary.replace(destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _key_name(line: str) -> str | None:
    match = re.match(
        r"^\s*(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_-]+))\s*=",
        line,
    )
    if not match:
        return None
    return next(group for group in match.groups() if group is not None)


def _root_agents_dotted_key(line: str) -> str | None:
    match = re.match(
        r"^\s*(?:\"agents\"|'agents'|agents)\s*\.\s*"
        r"(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_-]+))\s*=",
        line,
    )
    if not match:
        return None
    return next(group for group in match.groups() if group is not None)


def update_agents_config(content: str) -> str:
    original = tomllib.loads(content) if content.strip() else {}
    if re.search(r"(?m)^\s*(?:agents|\"agents\"|'agents')\s*=\s*\{", content):
        raise ValueError("Inline agents table is unsupported; use an [agents] table or dotted keys")
    if content and not content.endswith("\n"):
        content += "\n"
    expected = dict(original)
    agent_settings = dict(original.get("agents", {}))
    for key in MANAGED_AGENT_KEYS:
        agent_settings.pop(key, None)
    agent_settings["enabled"] = True
    expected["agents"] = agent_settings
    lines = content.splitlines(keepends=True)

    first_table = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^\s*\[.+\]\s*(?:#.*)?$", line.rstrip("\r\n"))
        ),
        len(lines),
    )
    root: list[str] = []
    for line in lines[:first_table]:
        dotted_key = _root_agents_dotted_key(line)
        if dotted_key is None or dotted_key not in MANAGED_AGENT_KEYS:
            root.append(line)
    lines = root + lines[first_table:]
    section_start = None
    section_end = None

    for index, line in enumerate(lines):
        if re.match(r"^\s*\[\s*(?:agents|\"agents\"|'agents')\s*\]\s*(?:#.*)?$", line.rstrip("\r\n")):
            section_start = index
            break

    if section_start is None:
        if any(_root_agents_dotted_key(line) is not None for line in root):
            updated = "".join(root) + "agents.enabled = true\n" + "".join(lines[len(root):])
            if tomllib.loads(updated) != expected:
                raise ValueError("Agent config update would change unrelated configuration")
            return updated
        prefix = "".join(lines).rstrip()
        if prefix:
            prefix += "\n\n"
        updated = prefix + "[agents]\n" + "enabled = true\n"
        if tomllib.loads(updated) != expected:
            raise ValueError("Agent config update would change unrelated configuration")
        return updated

    for index in range(section_start + 1, len(lines)):
        if re.match(r"^\s*\[.+\]\s*(?:#.*)?$", lines[index].rstrip("\r\n")):
            section_end = index
            break
    if section_end is None:
        section_end = len(lines)

    body = [
        line
        for line in lines[section_start + 1 : section_end]
        if _key_name(line) not in MANAGED_AGENT_KEYS
    ]
    while body and not body[-1].strip():
        body.pop()
    if body:
        body.append("\n")
    body.append("enabled = true\n")
    if section_end < len(lines):
        body.append("\n")

    updated = "".join(lines[: section_start + 1] + body + lines[section_end:])
    if tomllib.loads(updated) != expected:
        raise ValueError("Agent config update would change unrelated configuration")
    return updated


def update_guidance(content: str, policy: str) -> str:
    block = f"{BLOCK_START}\n{policy.rstrip()}\n{BLOCK_END}"
    starts, ends = content.count(BLOCK_START), content.count(BLOCK_END)
    if (starts, ends) not in {(0, 0), (1, 1)}:
        raise ValueError("Global AGENTS.md contains an incomplete or duplicate router managed block")
    if starts:
        start = content.index(BLOCK_START)
        if content.index(BLOCK_END) < start:
            raise ValueError("Global AGENTS.md contains reversed router managed markers")
        end = content.index(BLOCK_END, start) + len(BLOCK_END)
        return content[:start] + block + content[end:]
    prefix = content.rstrip()
    return (prefix + "\n\n" if prefix else "") + block + "\n"


def install(source_root: Path, codex_home: Path, global_agents: Path) -> list[Path]:
    source_root = source_root.resolve()
    codex_home = codex_home.expanduser().resolve()
    global_agents = global_agents.expanduser().resolve()
    config_path = codex_home / "config.toml"
    old_config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    new_config = update_agents_config(old_config)
    policy = (source_root / "policy/subagent-routing.md").read_text(encoding="utf-8")
    if not policy.strip() or BLOCK_START in policy or BLOCK_END in policy:
        raise ValueError("Routing policy is empty or contains managed markers")
    old_guidance = global_agents.read_text(encoding="utf-8") if global_agents.exists() else ""
    new_guidance = update_guidance(old_guidance, policy)

    # Preflight all inputs before creating backups or changing the live profile.
    role_contents: dict[str, str] = {}
    allowed_fields = {"name", "description", "model", "model_reasoning_effort",
                      "developer_instructions", "sandbox_mode"}
    for role in EXPECTED_AGENT_ROLES:
        content = (source_root / "agents" / f"{role}.toml").read_text(encoding="utf-8")
        parsed = tomllib.loads(content)
        reviewer = role == "astra-reviewer"
        if (set(parsed) - allowed_fields or parsed.get("name") != role
                or parsed.get("model") != ("gpt-6-astra" if reviewer else "gpt-6.1-sol")
                or parsed.get("model_reasoning_effort") != ("xhigh" if reviewer else role.removeprefix("sol-"))
                or not str(parsed.get("description", "")).strip()
                or not str(parsed.get("developer_instructions", "")).strip()
                or parsed.get("sandbox_mode") != ("read-only" if reviewer else None)):
            raise ValueError(f"Invalid managed agent role: {role}")
        role_contents[role] = content

    writes = [(config_path, new_config, "config.toml"),
              (global_agents, new_guidance, "AGENTS.md")]
    writes.extend((codex_home / "agents" / f"{role}.toml", content,
                   f"agents/{role}.toml") for role, content in role_contents.items())
    changed_writes = [(path, content, label) for path, content, label in writes
                      if not path.exists() or path.read_text(encoding="utf-8") != content]
    removals = [codex_home / "agents" / f"{role}.toml" for role in RETIRED_AGENT_ROLES
                if (codex_home / "agents" / f"{role}.toml").exists()]
    if not changed_writes and not removals:
        return []
    for path in [item[0] for item in changed_writes] + removals:
        if path.is_symlink():
            raise ValueError(f"Managed file is a symbolic link; no changes made: {path.name}")
        if path.exists() and not path.is_file():
            raise ValueError(f"Managed destination is not a file: {path.name}")
        for parent in path.parents:
            if parent == codex_home.parent:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError(f"Managed parent is not a regular directory: {parent.name}")
    backup_root = codex_home / "subagent-router-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root.mkdir(parents=True, mode=0o700)
    for path, _, label in changed_writes:
        _backup(path, backup_root, label)
    for path in removals:
        _backup(path, backup_root, f"agents/{path.name}")
    changed: list[Path] = []
    existed = {path: path.exists() for path, _, _ in changed_writes}
    created_parents: set[Path] = set()
    for path, _, _ in changed_writes:
        for parent in path.parents:
            if parent.exists():
                break
            created_parents.add(parent)
    try:
        for path, content, _ in changed_writes:
            _atomic_write(path, content)
            changed.append(path)
        for path in removals:
            path.unlink()
            changed.append(path)
    except OSError as installation_error:
        recovery_errors: list[str] = []
        for path, _, label in changed_writes:
            try:
                if existed[path]:
                    _restore_backup(backup_root / label, path)
                else:
                    path.unlink(missing_ok=True)
            except OSError as error:
                recovery_errors.append(f"{path.name}:{type(error).__name__}")
        for path in removals:
            try:
                _restore_backup(backup_root / "agents" / path.name, path)
            except OSError as error:
                recovery_errors.append(f"{path.name}:{type(error).__name__}")
        for directory in sorted(created_parents, key=lambda p: len(p.parts), reverse=True):
            try:
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()
            except OSError as error:
                recovery_errors.append(f"{directory.name}:{type(error).__name__}")
        if recovery_errors:
            raise RuntimeError(f"Installation failed; incomplete recovery {recovery_errors}; backups: {backup_root}") from installation_error
        raise
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--global-agents", type=Path)
    args = parser.parse_args()
    override = args.codex_home / "AGENTS.override.md"
    active = override if override.is_file() and override.read_text(encoding="utf-8").strip() else args.codex_home / "AGENTS.md"
    changed = install(Path(__file__).resolve().parents[1], args.codex_home,
                      args.global_agents or active)
    print(f"Installed router; changed {len(changed)} file(s)." if changed else "Router is already installed and current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
