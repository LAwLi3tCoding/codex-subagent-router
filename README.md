[English](README.md) | [简体中文](README.zh-CN.md)

# Codex Subagent Router

A global delegation policy with four Sol work roles and an independent Astra reviewer. The main session owns requirements and overall design, and keeps the model and reasoning effort selected by the user. Short, connected, or unclassified tasks stay in the main session.

## Delegate when it helps

Delegate a task only when its goal, scope, dependencies, and acceptance checks are clear, and parallel work, context isolation, or independent judgment provides a concrete benefit. Otherwise, do the work directly. A bounded design investigation can qualify before the full design exists; `sol-high` can explore the open questions.

| Role | Model | Effort | Typical work |
| --- | --- | --- | --- |
| `sol-low` | `gpt-6.1-sol` | `low` | Bounded work with few decisions and clear checks. |
| `sol-medium` | `gpt-6.1-sol` | `medium` | Routine implementation and investigation with local judgment. |
| `sol-high` | `gpt-6.1-sol` | `high` | Difficult debugging, synthesis, or an open design topic with a clear boundary. |
| `sol-xhigh` | `gpt-6.1-sol` | `xhigh` | Complex work with interacting constraints and substantial reasoning. |
| `astra-reviewer` | `gpt-6-astra` | `xhigh` | Independent, read-only review of consequential decisions and changes. |

Choose effort from the task's reasoning needs. The four Sol roles do not override sandbox or permission settings: each assignment must state whether it is read-only or owns a limited write scope. Parallel writers require disjoint file ownership or isolated worktrees. Delegation preserves the user's authorization.

The installer sets no global child model or effort default and installs no custom `default`, `explorer`, `owner`, `mechanical`, or `high-risk-owner`. Luna and Terra roles are retired. `max` is an explicit exception, not a resident role.

## Independent review and completion

Use an independent `astra-reviewer` subagent at `xhigh` for core shared design, material changes to security, consistency or recovery, major business judgments, or an explicit user review request. Effort level, Ultra, and domain keywords alone do not trigger review. Missing evidence is a review gap, not an exemption.

The main agent adjudicates findings against evidence and makes the corrections. Material revisions return to the same reviewer for review of the new version. No findings, or wording-only corrections, do not require repeated review. Children return evidence, verification results, and coverage gaps; a finished child run does not establish business completion. The main agent owns integration, verification, and the final completion claim.

Use the fields actually exposed by the current spawn tool. If that tool prohibits model or effort overrides with full-history forks, use `fork_turns="none"` or a finite number of turns when overriding them. Role configuration can override spawn parameters. Check runtime records for actual model and effort when available.

## Install

Python 3.11 or newer is required.

```bash
./install.sh
```

Install into another Codex home:

```bash
./install.sh --codex-home /path/to/.codex
```

The installer adds the five role files and a managed policy block to the global `AGENTS.md`, enables subagents, and removes global `default_subagent_model` and `default_subagent_reasoning_effort` settings. It preserves the main model and effort, permissions, MCP configuration, user concurrency limits, unrelated guidance, and existing hooks and features. Replaced or retired files are backed up under `subagent-router-backups/` before migration. Invalid managed inputs, unsafe managed-file symlinks, and inline `agents` tables are rejected before profile writes; use an `[agents]` table or dotted keys. If an installation write fails, the installer attempts to restore every changed file and retains backups; incomplete recovery reports the backup location.

The policy applies globally; workspace instructions and role overrides still matter. No hook is installed or enabled. Restart Codex to reload the configuration. The installer does not edit shell startup files or install dependencies.

## Verify

```bash
python3 scripts/verify.py --codex-home ~/.codex
```

Run the repository tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Repository layout

```text
agents/                 Four Sol roles and the read-only Astra reviewer
policy/                 Delegation, review, and ownership policy
scripts/install.py      Installer with input validation and backups
scripts/verify.py       Installed-state and source privacy checks
tests/                  Focused installer and contract tests
```

## Publishing safety

Keep personal data, company-internal information, credentials, host details, and absolute local paths out of commits and GitHub metadata.
