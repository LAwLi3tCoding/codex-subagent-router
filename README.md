# Codex Subagent Router

[中文说明](README.zh-CN.md)

Model and reasoning-effort guidance for subagent tasks that a session has already
chosen to run. The router does not decide whether to start a subagent, select its
role, require independent review, escalate findings, or repeat a review.

## Selection

Preserve the human-selected primary model and effort, including Ultra. Resolve
model and effort independently: retain each explicit user choice or applicable
task/role binding, and recommend only the missing parameter.

The router uses six automatic combinations:

| Model + effort | Selection boundary |
| --- | --- |
| **Sol/low** (`gpt-6.1-sol`) | Known solution, closed scope, explicit inputs and checks; little judgment. |
| **Sol/medium** | Understood requirements and scope; routine work needs local judgment. |
| **Sol/high** | A material open question requires hypothesis testing or alternative comparison. |
| **Sol/xhigh** | Interacting constraints across components or states require joint reasoning. |
| **Sol/max** | A well-formulated problem needs deep exploration of paths and competing solutions for a complete conclusion. |
| **Astra/xhigh** (`gpt-6-astra`) | The problem frame may be inadequate and needs reconstruction, with adequate evidence and a concrete reason Sol is expected to be insufficient. |

**Sol is the default; Luna is excluded from automatic selection.** Astra/high
and Astra/max remain explicit choices only. Explicit user settings and role
bindings take precedence and limit eligible automatic combinations.

Sol/max deepens reasoning within an established problem frame; Astra/xhigh is
for reconsidering the frame itself. If this distinction is unclear, prefer Sol.
Explain the concrete need for Astra briefly. Neither route requires a prior
attempt at a lower level. These boundaries are heuristics, not measured quality,
price, or speed guarantees. See the [policy](policy/subagent-routing.md).

Choose the lowest sufficient Sol effort. High consequence, domain labels,
review status, task length, and the primary's Ultra setting alone do not justify
an increase. Missing evidence or failed tools require recovery. Reassess at
existing phase boundaries: settled design normally leads to Sol/medium for
implementation and Sol/low for mechanical follow-up. Do not spawn, restart,
split, or repeat a task just to change settings.

The policy is guidance, not a runtime interceptor. Apply recommendations only
through supported fields compatible with the selected role and context. If a
level is unavailable, choose another eligible supported level only if sufficient;
otherwise preserve the invocation and report the limitation. Do not change roles,
context, configuration, or workflow to force a pair. Installation does not prove
the actual model or effort used.

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
