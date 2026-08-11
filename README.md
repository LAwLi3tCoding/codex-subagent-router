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
| Luna | `medium`, `high`, `xhigh`, `max` |
| Terra | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| Sol | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

Current Codex runtime metadata describes `ultra` as automatic task delegation. It
is an orchestration mode for exceptional independently decomposable Sol or Terra
work, not reasoning depth above `max`, and Luna has no Ultra route.
Luna Medium is the lowest named Luna route; the runtime low tag remains only to
describe an explicitly inherited parent-session choice.

Luna and Terra may collect, transform, or organize evidence, but they never own
the final architecture, security, release, migration, or other high-risk decision.
Those conclusions are synthesized by a Sol specialist.

This mapping follows OpenAI's GPT-5.6 guidance: Luna is the cost-sensitive,
high-volume tier, Terra balances intelligence and cost, Sol is the flagship tier,
and `max` is the highest documented reasoning effort. See the
[official model guidance](https://developers.openai.com/api/docs/guides/latest-model).

The global policy splits work before deciding whether to delegate. Multiple
independent, non-trivial workstreams run in parallel by default; dependency order,
overlapping writes, authorization, duplicated context, or excessive integration
cost keep work direct or serial. The parent still owns integration and verification.

## How model and effort are selected

Routing is a two-step decision: select the family from the kind of work and its
authority boundary, then select effort from the complexity that remains inside
that family. A higher effort never compensates for choosing the wrong family.

### Step 1: select the model family

| Candidate | Select it when | Do not select it when |
| --- | --- | --- |
| Work directly | The work is trivial, contains no useful child assignment, or a concrete parallel-delegation exception applies | A bounded child assignment has concrete value, or multiple independent non-trivial workstreams are ready |
| `default` | The child affirmatively needs the same model and effort already selected for the parent session, and no named specialist is a better fit | It is merely unclear which specialist to use, or the parent tier is too weak |
| Luna (`gpt-5.6-luna`) | The scope, design, interfaces, file boundaries, prohibited choices, acceptance criteria, and mechanical oracle are all complete | Exploration is open-ended, implementation needs local judgment, risk is high, or the oracle is incomplete |
| Terra (`gpt-5.6-terra`) | The assignment is read-only exploration, source research, relationship mapping, or evidence synthesis | The child must edit files or own an architecture, security, migration, release, or other high-risk conclusion |
| Sol (`gpt-5.6-sol`) | The work requires local judgment, non-mechanical writing, review, verification, architecture, conflict resolution, or a high-risk final decision | A cheaper closed Luna or read-only Terra assignment fully satisfies the boundary |

Mixed work is split at its authority boundary. Non-trivial isolated read-only
evidence work defaults to Terra. Closure established by the parent during the task
qualifies for Luna even when it was absent from the original prompt; once complete,
non-trivial mechanical implementation defaults to the lowest suitable Luna role.
Sol owns implementation only while local judgment remains. Routes are re-evaluated
between phases.

When multiple ready workstreams can proceed independently and each is more than a
trivial lookup or edit, the parent runs them in parallel unless dependency order,
overlapping writes, authorization, duplicated context, or integration overhead
erases the expected benefit. Ordinary parallelism uses multiple normal named roles;
it does not require `ultra`. Ultra is reserved for one child that must itself
orchestrate an exceptional multi-workstream program.

### Step 2: select reasoning effort

Choose the lowest effort whose conditions are all positively established. An
unknown condition blocks a downgrade; it is not evidence that the task is easy.

| Effort | Complexity signals | Selection boundary |
| --- | --- | --- |
| `low` | One narrow step, complete inputs, low risk, and one exact acceptance check | Available as a named Terra or Sol role. Luna Low is observation-only when `default` inherits that parent setting. |
| `medium` | Routine bounded multi-step work with established patterns and little interaction | Use when the steps are known and neighboring choices are easy to reject mechanically. |
| `high` | Several explicit constraints or edge cases within a bounded area | Use when deeper reasoning is required but the causes, modules, or decisions do not materially interact. |
| `xhigh` | At least two interacting signals: multiple modules, several plausible causes, substantial edge cases, or conflicting evidence | Use when interactions must be reconciled, but the assignment is still one bounded workstream. |
| `max` | The hardest single bounded assignment | For Luna, this means closed logic-heavy work with an exact oracle; for Terra, the hardest read-only synthesis; for Sol, high-risk judgment or full cross-component design. |
| `ultra` | At least two genuinely independent workstreams that benefit from automatic delegation | Sol or Terra only. It is an orchestration mode, not a quality rank above `max` and not a retry tier. |

### Canonical family and effort combinations

Luna roles are implementation-capable only under the closed-design contract. The
result must be independently and mechanically verified.

| Role | Typical assignment | Stop or escalate when |
| --- | --- | --- |
| `luna-medium` | Literal edits, repetitive conversions, generated mappings, or a simple implementation with no materially interacting rules | Multiple explicit rules begin to interact, or any required decision is missing |
| `luna-high` | Several explicit rules and edge cases inside one bounded subsystem | Rules span interacting modules or the expected result is no longer exact |
| `luna-xhigh` | Interacting explicit rules across several specified files, with every decision and expected result already fixed | The implementation reopens design, introduces an unresolved cause, or becomes high risk |
| `luna-max` | The hardest closed implementation: many interacting branches, states, or business rules with an exact oracle | Scope, design, or verification ceases to be complete; move to the appropriate Sol role |

Terra roles never write. Raising Terra effort increases research depth, not its
authority.

| Role | Typical assignment | Stop or escalate when |
| --- | --- | --- |
| `terra-low` | Locate one known symbol, file, fact, or source with an exact readback | The lookup expands into relationship mapping or ambiguity |
| `terra-medium` | Map a routine call path or inventory a bounded set of files and references | Several sources or constraints must be reconciled |
| `terra-high` | Compare multiple sources or trace several explicit relationships and edge cases | Evidence conflicts or multiple modules interact materially |
| `terra-xhigh` | Reconcile broad cross-module evidence, plausible causes, or conflicting sources | The assignment becomes the hardest single synthesis or requires a final judgment |
| `terra-max` | Perform the hardest single bounded read-only investigation or evidence synthesis | The work separates into independent research streams or crosses into decision authority |
| `terra-ultra` | Orchestrate at least two independent read-only research streams | The streams are not truly independent, or any downstream write or high-risk conclusion is required |

Sol owns judgment and write authority outside Luna's mechanical contract.

| Role | Typical assignment | Stop or escalate when |
| --- | --- | --- |
| `sol-low` | One narrow, low-risk change or verification step that still needs limited local judgment | The task becomes multi-step or adds explicit edge cases |
| `sol-medium` | Routine bounded implementation, review, or verification where local judgment remains | Several constraints or edge cases require deeper reconciliation |
| `sol-high` | Demanding bounded work where local judgment remains across several explicit constraints or edge cases | Multiple modules, plausible causes, or conflicting evidence interact |
| `sol-xhigh` | Complex cross-file implementation, analysis, debugging, planning, or review with interacting signals | Evidence remains unstable, risk becomes high, or full solution design is required |
| `sol-max` | High-risk final judgment, unstable XHigh evidence, or the hardest cross-component architecture and solution design | The assignment contains multiple genuinely independent workstreams |
| `sol-ultra` | Orchestrate exceptional Sol work that can be divided into at least two independent streams | The work is one hard bounded assignment; use `sol-max` instead |

### Selection examples

| Remaining assignment | Route | Why |
| --- | --- | --- |
| Rename a specified field in known files and pass an exact fixture | `luna-medium` | Closed, literal implementation with a mechanical oracle |
| Implement several specified validation rules and edge cases in one module | `luna-high` | Multiple explicit rules, but no cross-module interaction |
| Implement a fully designed state transition across named files with exact tests | `luna-xhigh` or `luna-max` | Use XHigh for interacting files; Max when many branches, states, or rules make it the hardest closed assignment |
| Discover where a request field is transformed across a bounded call path | `terra-medium` | Read-only relationship mapping with established scope |
| Reconcile conflicting behavior evidence across several modules | `terra-xhigh` | Multiple modules and conflicting evidence interact, but no final decision is delegated |
| Implement a bounded feature whose design still requires local trade-offs | `sol-medium` to `sol-xhigh` | The missing mechanical closure blocks Luna; effort follows the remaining interactions |
| Decide a high-risk migration or security boundary from gathered evidence | `sol-max` | High-risk final judgment cannot be owned by Luna or Terra |
| Investigate two independent subsystems in parallel | multiple `terra-medium` children | Ordinary parent-level parallelism does not require Ultra |
| Orchestrate an exceptional research program inside one child | `terra-ultra` | The child must itself coordinate several independent evidence streams |

For retries of the same unresolved assignment, effort only escalates within the
family: Luna uses `medium -> high -> xhigh -> max`; Terra and Sol use
`low -> medium -> high -> xhigh -> max`. If Luna loses design closure or Terra
needs to write, change family to Sol instead of compensating with more effort.

## Routing receipt and precedence

Every child prompt carries a compact routing receipt: remaining work, delegation
benefit, phase, work mode, closure, risk, complexity signals, independent
workstreams, selected model and effort, rejected neighboring tiers, and fallback.
This makes every downgrade, inheritance, and escalation inspectable.

Conflict resolution is fail-closed: authorization and single-writer boundaries
come first; split the task before deciding between parallel, serial, or direct
execution; then choose family before effort. Every downgrade condition must hold,
any high-risk signal may block a cheaper route, and unknown state never proves a
downgrade. `default` is considered last and requires an affirmative same-tier
reason.

## Phase and assignment re-evaluation

Routes are selected from the child's remaining work, not inherited from the
original task's most difficult phase. The parent re-evaluates the route at
`design -> implementation`, `implementation -> verification`,
`exploration -> decision`, and every task split or handoff.

A completed design is not an automatic reason to lower the tier. The design must
actually resolve the decisions, interfaces, file boundaries, acceptance evidence,
prohibited choices, and an independent mechanical oracle. The parent may establish
that closure during the task. When all of those stay closed, delegate non-trivial
literal or repetitive implementation to Luna Medium, explicit multi-rule
implementation to Luna High, interacting multi-file implementation to Luna XHigh,
and the hardest closed logic-heavy implementation to Luna Max.
Implementation that still needs local judgment uses `sol-low`, `sol-medium`, or
`sol-high`, while reopened design or unresolved cross-module work uses Sol XHigh
or Max.

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
| `gpt-5.6-luna` | named roles use `medium` through `max`; `low` is inherited observation only | `gpt56_luna_<effort>` |
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
