# Codex Subagent Router

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

The installer:

1. Installs the role files under the user's Codex configuration home.
2. Adds one managed routing block to the global Codex `AGENTS.md`.
3. Enables multi-agent support without imposing a shared concurrency limit.
4. Removes global child model defaults so `default` inherits the live session.
5. Creates timestamped local backups before replacing existing managed targets.

The installer also normalizes the matching legacy global delegation sentence
that imposed a fixed child count. Other unrelated guidance remains unchanged.

Run the installer again after updating the repository. Installation is idempotent
and preserves unrelated configuration and guidance.

The managed policy is written to the global Codex `AGENTS.md`, so Codex loads it
automatically in every new session. No shell startup hook or resident process is
required.

## Verify

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify.py
```

Verification checks the exact role/model matrix, default inheritance, managed
global guidance, configuration parsing, idempotence, and repository privacy.

## Files

- `agents/`: Codex custom agent definitions.
- `policy/subagent-routing.md`: globally loaded routing policy.
- `scripts/install.py`: idempotent user-level installer.
- `scripts/verify.py`: installed-state and shareability checks.
- `tests/`: installer regression tests.

## Publishing

The repository intentionally contains no personal paths, account identifiers,
private configuration, credentials, or organization-specific material. Review the
complete Git history and run the verification command before publishing or
pushing it to any hosting provider.
