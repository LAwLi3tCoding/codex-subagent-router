# Codex Subagent Router

[English](README.md) | [简体中文](README.zh-CN.md)

A dependency-free, user-level routing policy for Codex subagents. It keeps the
ordinary `default` agent aligned with the model and reasoning effort selected in
the current session, while exposing named Luna, Terra, and Sol tiers for work that
benefits from a deliberate override.

## Routing model

- `default` inherits the current session model and reasoning effort.
- `luna-batch` handles clear high-volume work at Medium effort.
- `luna-reasoner` uses Luna Max only for strictly bounded reasoning with complete
  inputs and independently mechanically verifiable results.
- `terra-explorer` and `terra-researcher` handle broad read-heavy work.
- `sol-high`, `sol-xhigh`, and `sol-max` cover increasingly complex work.
- `sol-ultra` uses Sol Max as an orchestration leader for exceptional planning or
  design that divides into multiple independent workstreams. `ultra` is not used
  as a model reasoning-effort value.

Luna and Terra may collect, transform, or organize evidence, but they never own
the final architecture, security, release, migration, or other high-risk decision.
Those conclusions are synthesized by a Sol specialist.

This mapping follows OpenAI's GPT-5.6 guidance: Luna is the cost-sensitive,
high-volume tier, Terra balances intelligence and cost, Sol is the flagship tier,
and `max` is the highest documented reasoning effort. See the
[official model guidance](https://developers.openai.com/api/docs/guides/latest-model).

The global policy keeps delegation selective, requires one-way escalation,
preserves single-writer boundaries, and leaves concurrency, batching, final
integration, and verification decisions with the parent agent.

## Visible launch details

Every subagent start produces a user-visible lifecycle message in the Codex App
or CLI event stream:

```text
Subagent started | role: sol-xhigh | model: gpt-5.6-sol | reasoning: xhigh
```

The model is taken from the runtime `SubagentStart` event, so it reflects the
model actually selected for that child. Named router roles report the reasoning
effort pinned in their installed TOML file. Because the event does not expose a
reasoning-effort field, `default` truthfully reports `inherited from parent`, and
unknown roles report `runtime-selected (not exposed by SubagentStart)` instead of
guessing.

## Install

Requires Python 3.11 or newer and a current Codex release.

One-command install from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/LAwLi3tCoding/codex-subagent-router/main/install.sh | sh
```

Or clone the repository and run:

```bash
./install.sh
```

Codex requires a one-time trust review for new or changed command hooks. After
installation, start Codex CLI, run `/hooks`, and trust the router's
`SubagentStart` hook. Restart the App or CLI session afterward. This trust step
cannot be safely bypassed by the installer.

### What changes after installation

- Installs the Luna, Terra, and Sol role definitions in the user's Codex
  configuration home.
- Adds one managed routing block to the global Codex `AGENTS.md`, which makes the
  policy available to every new session.
- Installs and enables a user-level `SubagentStart` lifecycle hook that displays
  each child's role, runtime model, and configured or inherited reasoning effort.
- Enables multi-agent support while leaving concurrency and batching decisions to
  the Codex runtime and parent agent.
- Removes legacy child-model and fixed-concurrency overrides that conflict with
  session inheritance and dynamic concurrency. As a result, `default` uses the
  model and reasoning effort selected for the current session.
- Normalizes the matching legacy delegation sentence when it imposes a fixed
  child count.

### Safety and recovery

- Creates timestamped local backups before changing existing managed targets.
- Changes only the router's managed guidance block, known agent settings, named
  role files, and the exact supported legacy fixed-count delegation sentence;
  unrelated configuration and guidance are preserved.
- Is idempotent, so it can be run again safely after updating the repository.
- Installs only a Codex lifecycle hook; it does not modify shell startup files or
  run a resident background process.

## Verify

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify.py
```

Verification checks the exact role/model matrix, default inheritance, managed
global guidance, lifecycle-hook registration, configuration parsing, idempotence,
and repository privacy.

## Files

- `agents/`: Codex custom agent definitions.
- `hooks/`: user-visible subagent launch disclosure.
- `policy/subagent-routing.md`: globally loaded routing policy.
- `scripts/install.py`: idempotent user-level installer.
- `scripts/verify.py`: installed-state and shareability checks.
- `tests/`: installer regression tests.

## Publishing

The repository intentionally contains no personal paths, account identifiers,
private configuration, credentials, or organization-specific material. Review the
complete Git history and run the verification command before publishing or
pushing it to any hosting provider.
