# Task-level routing validation

Installer tests check files and configuration. Performance needs actual task runs,
including the main agent, its children, checks, and the final acceptance result.
This guide is a comparison protocol, not an automated benchmark or a performance claim.

## Cases

Use ordinary requests without instructing the agent to spawn a particular role.
Run each version from a fresh copy of the same fixture and the same request:

| Case | Request and acceptance | Routing behavior to inspect |
| --- | --- | --- |
| Local fix | Fix one real parsing or formatting defect; existing regression checks must pass. | A short dependent sequence normally stays in the main session. |
| Independent modules | Implement two substantial modules with separate ownership and checks; both must satisfy their acceptance criteria. | Parallel delegation is useful only when the modules are independently executable and coordination has concrete value. No fixed spawn count is required. |
| Ordinary review | Review a routine feature against requirements and existing checks. | A generic review request uses an independent Sol/high reviewer unless concrete consequential risk or a stronger gate requires Astra. |
| Shared recovery change | Change an actual recovery invariant; callers and failure/recovery regressions must agree. | Coupled decisions stay together. Required independent review and repair rechecks remain effective. |

If ordinary review reveals consequential risk, verify that the risk stays unresolved
until Astra reviews its original evidence and affected scope. A Sol pass must not
substitute for that review. An explicit Astra request must select Astra directly.

A miniature fixture can test routing behavior but cannot establish savings for a
large product task. A source-analysis or hypothetical-choice response is not a
completed implementation run. Do not manufacture receipt-only tests or force
delegation to make the result match the examples.

## Comparable runs

1. Record the policy and role file versions, effective main/child model and effort,
   permissions, tools, concurrency, fixture baseline, request, and acceptance checks.
2. Run the baseline and candidate in separate fresh sessions and isolated fixture
   copies. Preserve the user's main model/effort and authorization. Do not publish,
   message other chats, or use production mutations as test fixtures.
3. Record whether the process actually loaded the intended policy and roles. An
   already-open session is not proof of loading newly installed files. Check child
   runtime records rather than inferring actual settings from role configuration.
4. Run the same acceptance checks and inspect the result and review findings.
   Incomplete, blocked, or failed runs remain so; do not count them as faster passes.
5. Compare more than one paired run before claiming a general improvement. Note
   request order, cache state, model/tool failures, and differences in reviewed scope.

## Measurements and limits

- Measure request-to-accepted-result time. Sum child/review durations separately;
  overlapping durations are not additive delays on the critical path.
- Record input, cached input, output, and reasoning tokens separately for the main
  agent and children. Reasoning is a subset of output, not an extra amount to add.
- Use one identified usage record format throughout a comparison. If per-response
  records are available, deduplicate by response identity and check inherited
  baselines before aggregating. Missing usage is unknown, not zero. Divergent
  cumulative and per-response counters must be disclosed, not mixed.
- Token counts do not establish a charge. Cached-input discounts, model rates,
  account billing, and other charges require their own evidence.
- Track spawn/follow-up/message counts, failed checks, repairs, missed requirements,
  and meaningful review findings. Fewer messages are useful only if quality and
  required gates remain intact.
- Record fixture scope, checked/unchecked behavior, tool failures, and unresolved
  risks. A configuration pass, routing smoke test, or finished child does not prove
  product completion or net time/token savings.

Keep machine-specific logs and private task content outside this shareable repository.
Only publish sanitized, repository-relative evidence and supported conclusions.
