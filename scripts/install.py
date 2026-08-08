#!/usr/bin/env python3
"""Install the shareable Codex subagent routing policy into a user profile."""

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
MANAGED_AGENT_KEYS = {
    "enabled",
    "max_concurrent_threads_per_session",
    "max_threads",
    "default_subagent_model",
    "default_subagent_reasoning_effort",
}
LEGACY_CHILD_CAP = re.compile(
    r"(?m)^- Never exceed [A-Za-z0-9-]+ children; "
    r"inherit model defaults absent a concrete reason\.$"
)
LEGACY_CHILD_CAP_REPLACEMENT = (
    "- Let the leader decide child count and batching dynamically from task "
    "independence, effective runtime capacity, coordination cost, and safety; "
    "inherit model defaults absent a concrete reason."
)


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
    if content.strip():
        tomllib.loads(content)
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
        if dotted_key is None:
            root.append(line)
        elif dotted_key not in MANAGED_AGENT_KEYS:
            raise ValueError(
                "Unsupported top-level dotted agents setting; convert it to an "
                "[agents] table before installing"
            )
    lines = root + lines[first_table:]
    section_start = None
    section_end = None

    for index, line in enumerate(lines):
        if re.match(r"^\s*\[agents\]\s*(?:#.*)?$", line.rstrip("\r\n")):
            section_start = index
            break

    if section_start is None:
        prefix = "".join(lines).rstrip()
        if prefix:
            prefix += "\n\n"
        updated = prefix + "[agents]\n" + "enabled = true\n"
        tomllib.loads(updated)
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
    tomllib.loads(updated)
    return updated


def update_guidance(content: str, policy: str) -> str:
    content = LEGACY_CHILD_CAP.sub(LEGACY_CHILD_CAP_REPLACEMENT, content)
    block = f"{BLOCK_START}\n{policy.rstrip()}\n{BLOCK_END}"
    has_start = BLOCK_START in content
    has_end = BLOCK_END in content
    if has_start != has_end:
        raise ValueError("Global AGENTS.md contains an incomplete router managed block")
    if has_start:
        start = content.index(BLOCK_START)
        end = content.index(BLOCK_END, start) + len(BLOCK_END)
        return content[:start] + block + content[end:]
    prefix = content.rstrip()
    if prefix:
        prefix += "\n\n"
    return prefix + block + "\n"


def install(source_root: Path, codex_home: Path, global_agents: Path) -> list[Path]:
    source_root = source_root.resolve()
    codex_home = codex_home.expanduser().resolve()
    global_agents = global_agents.expanduser().resolve()
    changed: list[Path] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = codex_home / "subagent-router-backups" / timestamp

    config_path = codex_home / "config.toml"
    old_config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    new_config = update_agents_config(old_config)
    if new_config != old_config:
        _backup(config_path, backup_root, "config.toml")
        _atomic_write(config_path, new_config)
        changed.append(config_path)

    policy = (source_root / "policy" / "subagent-routing.md").read_text(encoding="utf-8")
    old_guidance = global_agents.read_text(encoding="utf-8") if global_agents.exists() else ""
    new_guidance = update_guidance(old_guidance, policy)
    if new_guidance != old_guidance:
        _backup(global_agents, backup_root, "AGENTS.md")
        _atomic_write(global_agents, new_guidance)
        changed.append(global_agents)

    target_agents = codex_home / "agents"
    target_agents.mkdir(parents=True, exist_ok=True)
    for source in sorted((source_root / "agents").glob("*.toml")):
        target = target_agents / source.name
        new_content = source.read_text(encoding="utf-8")
        old_content = target.read_text(encoding="utf-8") if target.exists() else None
        if old_content == new_content:
            continue
        _backup(target, backup_root, f"agents/{target.name}")
        _atomic_write(target, new_content)
        changed.append(target)

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path.home() / ".codex",
        help="Codex configuration home (default: ~/.codex)",
    )
    parser.add_argument(
        "--global-agents",
        type=Path,
        help="Global AGENTS.md path (default: <codex-home>/AGENTS.md)",
    )
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parents[1]
    global_agents = args.global_agents or args.codex_home / "AGENTS.md"
    changed = install(source_root, args.codex_home, global_agents)
    if changed:
        print(f"Installed router; changed {len(changed)} file(s).")
    else:
        print("Router is already installed and current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
