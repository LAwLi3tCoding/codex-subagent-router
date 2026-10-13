# Codex Subagent Router

[中文说明](README.zh-CN.md)

Model and reasoning-effort guidance for subagent tasks that a session has already
chosen to run. The router does not decide whether to start a subagent, select its
role, require independent review, escalate findings, or repeat a review.

## Selection

Preserve the human-selected primary model and effort, including Ultra. Explicit
user choices and applicable task/role bindings take precedence. For unspecified
subagent settings, recommend `gpt-6.1-sol` with the lowest sufficient effort:

| Effort | Task uncertainty |
| --- | --- |
| `low` | Closed, mechanically checkable work. |
| `medium` | Routine implementation, bounded investigation, or test fixes. |
| `high` | Unresolved causes, compatibility, open design, or an already-requested review needing independent judgment. |
| `xhigh` | Interacting invariants across concurrency, migration, recovery, or an already-requested consequential-risk assessment. |

Astra is excluded from automatic selection until explicitly restored by the user.
Length, file count, domain labels, and the primary's effort do not determine the
subagent effort. `max` requires an explicit task-specific choice.

The [policy](policy/subagent-routing.md) is advisory guidance, not a runtime
interceptor. Apply recommendations only when the runtime supports model/effort
fields compatible with the selected role and context. If the role fixes its
settings or overrides are unavailable, preserve the invocation. Do not switch
roles or context modes to force the mapping. Installation does not prove which
model or effort a child actually ran.

## Install

Requires Python 3.11 or newer. From this checkout:

```sh
sh ./install.sh
```

For a separate profile or explicit guidance destination:

```sh
sh ./install.sh --codex-home /path/to/profile
sh ./install.sh --codex-home /path/to/profile --global-agents /path/to/AGENTS.md
```

The installer updates only the router's marked block in global `AGENTS.md`.
A nonempty `AGENTS.override.md` is selected instead when present. Existing guidance
outside the block is retained; guidance symlinks are followed to their target.
Changed guidance is backed up under `subagent-router-backups/`. Writes are atomic;
failed writes attempt restoration and report incomplete recovery. Duplicate,
incomplete, reversed, or empty policy markers are rejected before profile writes.

It does not create or edit `config.toml`, enable agents, set global model defaults,
install/replace/delete role files, change permissions, install hooks, or change
review workflows. Use a fresh session to load updated guidance.

## Upgrade from the role-based router

Reinstalling replaces the old router block, removing its delegation and review
workflow instructions. The new version ships no role templates. Existing role
files and configuration remain untouched, including files written by older
versions. Those roles can still contain old instructions and fixed model/effort
bindings.

For a complete migration, inspect and back up the six old router roles, then
remove them explicitly: `worker-low`, `worker-medium`, `worker-high`,
`worker-xhigh`, `reviewer`, and `risk-reviewer`. Check project references before
removal; workflows that name those custom roles need their own role definitions.
Preserve roles owned by other tools or projects. The installer never performs
this cleanup automatically and does not disable subagents or restore previously
deleted configuration. Reinstall the guidance and start a fresh session after
cleanup; an existing session can retain loaded instructions and roles.

## Verify

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/verify.py --codex-home /path/to/profile
```

Verification checks the managed guidance and source privacy. It does not require
agents to be enabled or any particular role inventory. Tests cover preservation
of configuration, role files, hooks, unrelated guidance, backups, and recovery.
See [task-level validation](docs/performance-validation.md) for runtime evidence.

## Repository layout

```text
policy/                 Model and effort guidance only
scripts/install.py      Guidance-only installer with backups and recovery
scripts/verify.py       Managed-guidance and source privacy checks
tests/                  Installer preservation and recovery tests
```

Keep personal data, internal information, credentials, host details, and absolute
local paths out of commits and GitHub metadata.
