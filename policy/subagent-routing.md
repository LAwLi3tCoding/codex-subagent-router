## Automatic subagent model routing

Apply this policy whenever subagents are available. Work directly when delegation
would not materially improve speed, quality, isolation, or independent review.

### Visible launch disclosure

- A user-level `SubagentStart` hook reports every child launch in the Codex App
  UI or CLI event stream as `role`, runtime `model`, and reasoning effort.
- For named router roles, reasoning comes from the installed role configuration.
  For `default`, report that reasoning is inherited from the parent rather than
  guessing a value the runtime event does not expose.
- For built-in or unknown roles without a configured effort, state that reasoning
  was runtime-selected and is not exposed by `SubagentStart`. Never invent it.
- Reinstalling or updating the hook requires the user to review and trust its
  current definition once through Codex's hook trust flow.

### Default inheritance

- `default` is the ordinary delegation role.
- `default` must inherit the current parent session's manually selected model and
  reasoning effort.
- Do not set a model or reasoning override for `default`.
- Do not silently upgrade or downgrade `default`; choose a named specialist when
  a different tier is justified.
- `default` is not a fallback for work that exceeds the capability of the
  parent session's selected model. Route that work to the appropriate named Sol
  specialist.

### Named routing tiers

- `luna-batch`: repetitive extraction, classification, formatting, inventory, and
  other clear high-volume work whose correctness is mechanically checkable.
- `luna-reasoner`: strictly bounded, reasoning-heavy work with complete explicit
  inputs and a result that can be independently and mechanically verified.
- `terra-explorer`: broad codebase exploration, large-file reading, symbol and
  call-path mapping, and evidence collection.
- `terra-researcher`: documentation and reference research across a broad source
  set where source coverage matters more than final synthesis.
- `sol-high`: demanding general work when an explicit Sol baseline is needed.
- `sol-xhigh`: relatively complex cross-file analysis, multi-cause debugging,
  integration planning, or review with substantial edge cases.
- `sol-max`: highly complex architecture, cross-component design, critical root
  cause analysis, migration planning, and primary solution design.
- `sol-ultra`: a Sol Max orchestration role for exceptional, quality-first
  planning or design that divides cleanly into multiple independent workstreams.

### Selection rules

1. Use `default` for ordinary delegated work so the user's current session choice
   remains authoritative.
2. Use Luna only when scope, inputs, and acceptance criteria are complete. Never route open-ended
   exploration, architecture, ambiguous multi-cause analysis,
   security or release decisions, or other high-risk judgment to Luna. Luna Max
   increases reasoning budget; it does not turn Luna into a frontier model.
3. Prefer Terra over Luna for open-ended exploration or broad context gathering.
   Terra agents collect and organize evidence but must not make the final decision
   for architecture, security, release, migration, or other high-risk work. Hand
   those conclusions to a Sol specialist.
4. Use `sol-xhigh` when at least two complexity signals are present: multiple
   modules, several plausible causes, substantial edge cases, conflicting
   evidence, or a failed High-effort attempt.
5. Use `sol-max` for cross-component architecture, high-risk technical decisions,
   full solution design, or when XHigh cannot form a stable evidence-backed result.
6. Use `sol-ultra` only when both conditions hold: the task is exceptionally
   difficult, and it can be divided into at least two independent workstreams.
   Ultra is an orchestration pattern using a Sol Max leader, not a reasoning
   effort above `max`, and it is not a generic retry tier.

### Escalation and orchestration

- Escalate in one direction: Luna or Terra -> Sol High -> Sol XHigh -> Sol Max.
- Escalate Max -> Ultra only when parallel decomposition is useful; both roles use
  Sol Max reasoning, while Ultra adds active multi-workstream orchestration.
- Stop the previous writer before escalating a write task. Never let two agents
  write the same checkout, branch, or file boundary concurrently.
- The parent agent owns decomposition, task boundaries, integration, conflict
  resolution, final verification, and the final completion claim.
- The parent agent decides how many children to run, whether to run them in
  parallel or in batches, and when to stop spawning. Base that decision on the
  number of genuinely independent workstreams, effective runtime capacity,
  write isolation, expected coordination cost, and verification needs. Do not
  encode a fixed numeric preference or concurrency cap in this shared policy.
- Give every child a bounded context package: goal, owned scope, required evidence,
  constraints, acceptance criteria, current facts, and prohibited actions.
- Use limited or no history for model-switched children when supported. Copy full
  history only when the complete decision record is essential.
- A cheaper run is successful only when the final verified result still meets the
  acceptance criteria; retries and verifier work count toward total cost.
- A Luna or Terra result may inform a high-risk decision but may not be the sole
  basis for the final decision. Require Sol-level synthesis and current evidence.
