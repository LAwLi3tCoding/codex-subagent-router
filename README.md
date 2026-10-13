# Codex Subagent Router

[中文说明](README.zh-CN.md)

Model and reasoning-effort guidance for subagent tasks that a session has already
chosen to run. The router does not decide whether to start a subagent, select its
role, require independent review, escalate findings, or repeat a review.

## Selection

Preserve the human-selected primary model and effort, including Ultra. Resolve
model and effort independently: preserve each explicit user choice or applicable
task/role binding, and recommend only the missing parameter. For an unspecified
model, recommend `gpt-6.1-sol`; Astra is excluded from automatic selection until
the user explicitly restores it.

Choose the lowest sufficient supported effort for the current assignment:

| Effort | Selection boundary |
| --- | --- |
| `low` | Known solution, precise inputs and checks, little judgment. |
| `medium` | Routine implementation or bounded investigation with local judgment. |
| `high` | A material open question needs hypothesis testing or alternative comparison. |
| `xhigh` | Multiple interacting constraints across components or states need joint reasoning. |
| `max` | Coupled constraints, competing plausible solutions, and consequential failure modes need unusually deep synthesis despite adequate evidence. |

`max` is an automatic candidate when all its conditions hold; it no longer needs
an explicit exception. A prior xhigh attempt is not required. Explain the specific
reasoning need for xhigh/max briefly. High consequence, task length, file count,
review status, and the primary's Ultra setting alone do not justify higher effort.
Missing evidence or failing tools call for recovery, not automatic escalation.

Reassess at existing phase boundaries: after the cause or design is settled,
routine implementation normally returns to medium, mechanical follow-up to low.
Keep human-selected settings and do not spawn, restart, split, or repeat a task
just to change effort. See the [policy](policy/subagent-routing.md) for boundaries.

The policy is guidance, not a runtime interceptor. Apply recommendations only
through supported model/effort fields compatible with the selected role and
context. If a level is unsupported, use another supported level only when it is
sufficient; otherwise retain the invocation and report the limitation. Fixed
role bindings remain authoritative. Do not change models, roles, context modes,
configuration, or workflows to force a mapping. Installation does not prove the
actual model or effort a child ran.

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
