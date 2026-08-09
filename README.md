# Codex Subagent Router

[English](README.md) | [简体中文](README.zh-CN.md)

A dependency-free, user-level routing policy for Codex subagents. It keeps the
ordinary `default` agent aligned with the model and reasoning effort selected in
the current session, while exposing named Luna, Terra, and Sol tiers for work that
benefits from a deliberate override.

## Routing model

Routing uses two axes. The model family follows the work mode and authority
boundary; effort follows the remaining complexity.

- Luna handles closed, cost-sensitive work with a mechanical oracle, including
  implementation from a complete executable design.
- Terra handles read-only exploration, research, and evidence synthesis.
- Sol handles implementation that still requires local judgment, plus review,
  verification, architecture, and final high-risk synthesis.
- `default` still inherits the current session model and effort, but only when the
  routing receipt proves an affirmative same-tier match.

Canonical roles use `{family}-{effort}` names. This release supports:

| Family | Canonical efforts |
| --- | --- |
| Luna | `low`, `medium`, `high`, `xhigh`, `max` |
| Terra | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| Sol | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

Current Codex runtime metadata describes `ultra` as automatic task delegation. It
is an orchestration mode for exceptional independently decomposable Sol or Terra
work, not reasoning depth above `max`, and Luna has no Ultra route.

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

## Routing receipt and precedence

Every child prompt carries a compact routing receipt: remaining work, delegation
benefit, phase, work mode, closure, risk, complexity signals, independent
workstreams, selected model and effort, rejected neighboring tiers, and fallback.
This makes every downgrade, inheritance, and escalation inspectable.

Conflict resolution is fail-closed: split mixed evidence/write/decision/verification
work into sequential assignments; choose family before effort; require every
downgrade condition; allow any high-risk signal to block a cheaper route; and never
treat unknown state as evidence for downgrading. `default` is considered last and
requires an affirmative same-tier reason.

## Phase and assignment re-evaluation

Routes are selected from the child's remaining work, not inherited from the
original task's most difficult phase. The parent re-evaluates the route at
`design -> implementation`, `implementation -> verification`,
`exploration -> decision`, and every task split or handoff.

A completed design is not an automatic reason to lower the tier. The design must
actually resolve the decisions, interfaces, file boundaries, acceptance evidence,
prohibited choices, and an independent mechanical oracle. When all of those stay
closed, Luna Max is the primary route for logic-heavy implementation with many
explicit or interacting rules; literal mechanical edits may use a lower Luna
effort. Implementation that still needs local judgment uses `sol-low`,
`sol-medium`, or `sol-high`, while reopened design or unresolved cross-module work
uses Sol XHigh or Max.

A new, narrower assignment may use a lower tier. Retrying the same unresolved work
still follows one-way escalation. If the child's scope expands or design gaps
reappear, it returns the evidence to the parent for re-routing instead of silently
stretching its role. Verification is routed independently by the risk and judgment
needed for the completion claim, which remains owned by the parent.

## Runtime compatibility fallback

The local Codex model cache is advisory. A missing effort entry or corrupt, stale,
incomplete, or absent cache is reported when observable, but it does not fail the
installer, verifier, delegation, or parent task. The router tries the configured
role and treats the runtime child-start result as authoritative.

If an `ultra` child is rejected, the router may try the same family at `max` while
the parent performs orchestration. Other rejected named roles may make one safe
same-family fallback attempt. The router never silently crosses model families or
uses `default` to conceal incompatibility. If that attempt fails or no safe
alternative exists, the parent executes the work directly so routing metadata
cannot block the user's task.

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

The router also prefixes every spawned task name so the same information is
visible directly in the Codex App's **Subagents** list. For example:

```text
gpt56_luna_max_analyze_rules
```

Current App versions render that identifier as the row title. Its leading fields
encode the human-readable label `GPT56 · luna · max`; underscores are required
because Codex task names accept only lowercase letters, digits, and underscores.
These are text prefixes rather than native App badges. Tags are derived from the
child's effective model and effort, not its role name. The complete matrix is:

| Effective child family | Efforts | Task-name prefix pattern |
| --- | --- | --- |
| `gpt-5.6-luna` | `low` through `max` | `gpt56_luna_<effort>` |
| `gpt-5.6-terra` | `low` through `max`, `ultra` | `gpt56_terra_<effort>` |
| `gpt-5.6-sol` | `low` through `max`, `ultra` | `gpt56_sol_<effort>` |
| Model or effort unavailable before spawn | — | `runtime_selected` |

For `default`, the router uses the parent's effective values only when both
are available before spawn, otherwise it falls back to `runtime_selected`. The
lifecycle message remains the runtime check for the model actually selected by
Codex.

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
- Removes retired pre-canonical role files during upgrades after including them in
  the timestamped backup.
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

Verification checks the exact role/model/effort matrix, default inheritance,
routing receipts and synthetic scenarios, managed global guidance, lifecycle-hook
registration, configuration parsing, idempotence, and repository privacy. When a
Codex model cache is present, verification reports unsupported family-effort
combinations or an unreadable cache as advisory warnings. Installed role, policy,
hook, configuration, and privacy defects still fail verification.

## Files

- `agents/`: Codex custom agent definitions.
- `hooks/`: user-visible subagent launch disclosure.
- `policy/subagent-routing.md`: globally loaded routing policy.
- `policy/routing-scenarios.json`: synthetic routing-receipt contract cases.
- `scripts/install.py`: idempotent user-level installer.
- `scripts/verify.py`: installed-state and shareability checks.
- `tests/`: installer and routing-policy regression tests.

## Publishing

The repository intentionally contains no personal paths, account identifiers,
private configuration, credentials, or organization-specific material. Review the
complete Git history and run the verification command before publishing or
pushing it to any hosting provider.
