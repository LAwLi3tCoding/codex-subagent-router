#!/usr/bin/env python3
"""Install model and effort guidance without changing configuration or roles."""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BLOCK_START = "<!-- CODEX-SUBAGENT-ROUTER:START -->"
BLOCK_END = "<!-- CODEX-SUBAGENT-ROUTER:END -->"


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
    separator = "" if not content or content.endswith("\n\n") else "\n" if content.endswith("\n") else "\n\n"
    return content + separator + block + "\n"


def install(source_root: Path, codex_home: Path, global_agents: Path) -> list[Path]:
    source_root = source_root.resolve()
    codex_home = codex_home.expanduser().resolve()
    global_agents = global_agents.expanduser().resolve()
    policy = (source_root / "policy/subagent-routing.md").read_text(encoding="utf-8")
    if not policy.strip() or BLOCK_START in policy or BLOCK_END in policy:
        raise ValueError("Routing policy is empty or contains managed markers")
    old_guidance = global_agents.read_text(encoding="utf-8") if global_agents.exists() else ""
    new_guidance = update_guidance(old_guidance, policy)

    writes = [(global_agents, new_guidance, "AGENTS.md")]
    changed_writes = [(path, content, label) for path, content, label in writes
                      if not path.exists() or path.read_text(encoding="utf-8") != content]
    if not changed_writes:
        return []
    for path in [item[0] for item in changed_writes]:
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
    print(f"Installed model/effort guidance; changed {len(changed)} file(s)." if changed else "Router is already installed and current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
