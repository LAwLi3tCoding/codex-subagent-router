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

### App-visible task-name labels

Every spawn must set `task_name` to `<route_tag>_<short_purpose>`. The route tag
must be the first component so the Codex App's Subagents list exposes the selected
model tier and reasoning effort directly in each task title. Keep the purpose
short and use only lowercase letters, digits, and underscores.

Derive the route tag from the child's effective model and reasoning effort after
normal Codex configuration precedence is resolved. Never derive the tag from the role name.
A role may help select a configuration, but two roles that resolve to the same
model and effort must receive the same tag.

- `gpt-5.6-luna` + `low` -> `gpt56_luna_low`
- `gpt-5.6-luna` + `medium` -> `gpt56_luna_medium`
- `gpt-5.6-luna` + `high` -> `gpt56_luna_high`
- `gpt-5.6-luna` + `xhigh` -> `gpt56_luna_xhigh`
- `gpt-5.6-luna` + `max` -> `gpt56_luna_max`
- `gpt-5.6-terra` + `low` -> `gpt56_terra_low`
- `gpt-5.6-terra` + `medium` -> `gpt56_terra_medium`
- `gpt-5.6-terra` + `high` -> `gpt56_terra_high`
- `gpt-5.6-terra` + `xhigh` -> `gpt56_terra_xhigh`
- `gpt-5.6-terra` + `max` -> `gpt56_terra_max`
- `gpt-5.6-terra` + `ultra` -> `gpt56_terra_ultra`
- `gpt-5.6-sol` + `low` -> `gpt56_sol_low`
- `gpt-5.6-sol` + `medium` -> `gpt56_sol_medium`
- `gpt-5.6-sol` + `high` -> `gpt56_sol_high`
- `gpt-5.6-sol` + `xhigh` -> `gpt56_sol_xhigh`
- `gpt-5.6-sol` + `max` -> `gpt56_sol_max`
- `gpt-5.6-sol` + `ultra` -> `gpt56_sol_ultra`
- effective model or effort not available before spawn -> `runtime_selected`

For example, a Luna Max task uses `gpt56_luna_max_analyze_rules`, encoding the
human-readable label `GPT56 · luna · max` within the identifier-safe task name.
An XHigh review uses `gpt56_sol_xhigh_review_installer`. Apply the prefix to every
child, including parallel children, retries, and escalations. Current Codex runtime
metadata exposes `low`, `medium`, `high`, `xhigh`, and `max` for all three families,
plus `ultra` for Sol and Terra. `ultra` is an automatic task delegation mode, not
reasoning depth above `max`; Luna has no `ultra` route.
For `default`, use the current parent model and effort only when both effective
values are explicitly available before spawn. Otherwise use `runtime_selected`
instead of guessing inherited values. The title prefix communicates the resolved
pre-spawn selection; the
`SubagentStart` hook remains the source for the runtime model actually used.

### Default inheritance

- `default` is the ordinary delegation role.
- `default` must inherit the current parent session's manually selected model and
  reasoning effort.
- Do not set a model or reasoning override for `default`.
- Use `default` only when the routing receipt establishes an affirmative same-tier match:
  the remaining assignment genuinely needs the parent's effective capability and
  no canonical family-effort role is a better fit.
- The absence of an obvious specialist is not evidence for `default`. State why a
  cheaper role would be unsafe and why a stronger role would add no material value.
- Do not silently upgrade or downgrade `default`; choose a canonical named role
  when a different family or effort is justified.
- `default` is not a fallback for work that exceeds the capability of the
  parent session's selected model. Route that work to the appropriate named Sol
  specialist.

### Canonical model and effort roles

Choose the model family from the work mode and decision boundary, then choose the
effort from the remaining complexity. New routes use `{family}-{effort}` names.

- Luna is for closed, cost-sensitive extraction, transformation, classification,
  formatting, inventory, bounded reasoning, or implementation from an executable
  design. The result must be independently and mechanically verified.
  Never route open-ended exploration or final high-risk judgment to Luna.
- Terra is for read-only codebase exploration, source research, relationship
  mapping, and evidence synthesis. Terra roles stay read-only. They
  must not make the final decision for architecture, security, release,
  migration, or other high-risk work.
- Sol is for implementation that still requires local judgment, judgment-heavy
  analysis, review, verification, architecture, and final synthesis, with effort
  scaled to remaining complexity.

Use effort consistently within the selected family:

- `low`: a narrow single-step task with complete inputs, low risk, and an exact
  acceptance check.
- `medium`: routine bounded multi-step work with established patterns.
- `high`: several explicit constraints or edge cases requiring deeper reasoning.
- `xhigh`: at least two interacting complexity signals, such as multiple modules,
  several plausible causes, substantial edge cases, or conflicting evidence.
- `max`: the hardest single bounded assignment. For Luna, this includes logic-heavy
  implementation with many explicit or interacting rules and an exact oracle; for
  Sol, it includes high-risk final judgment, unstable XHigh evidence, or full
  cross-component solution design.
- `ultra`: Sol or Terra only, for exceptional work that divides into at least two
  genuinely independent workstreams. It enables automatic delegation and is not a
  generic retry tier or a quality rank above `max`.

### Selection rules

1. Work directly when delegation has no material benefit.
2. Identify the remaining phase and work mode before selecting a family. Split
   evidence collection, implementation, final judgment, and verification when
   their boundaries or best families differ.
3. Use Luna only when scope, design inputs, decisions, interfaces, file boundaries,
   acceptance criteria, prohibited choices, and the mechanical oracle are complete.
   Use Luna Max as the primary route for logic-heavy implementation when those
   conditions remain closed and risk is not high. Missing or uncertain closure
   blocks a Luna route.
4. Use Terra for broad read-only evidence work. Route the downstream write or
   high-risk conclusion separately to Sol.
5. Use Sol for non-mechanical writes, any implementation that does not satisfy the
   Luna Max closed-implementation contract, judgment-heavy synthesis, and final
   high-risk conclusions. Choose the lowest effort whose explicit conditions are
   all satisfied.
6. Use `default` only for an affirmative same-tier match, never merely because no
   specialist was selected.
7. Use `ultra` only for exceptional independently decomposable work; otherwise use
   the appropriate single-assignment effort through `max`.

### Routing decision receipt

Every spawn prompt must include a compact routing receipt with these fields:

- `remaining_work`: the child's exact residual deliverable.
- `delegation_benefit`: the concrete speed, quality, isolation, or review benefit.
- `phase` and `work_mode`: the current phase and evidence, mechanical, write,
  judgment, verification, or orchestration mode.
- `scope_closed` and `design_closed`: whether the child has complete boundaries
  and decisions for its assignment.
- `risk`: `low`, `standard`, or `high`.
- `complexity_signals`: the explicit signals used to choose effort.
- `independent_workstreams`: the count of genuinely independent workstreams.
- `same_tier_required`: why inheriting the parent is affirmatively required when
  `default` is selected; otherwise `false`.
- `selected_role`, `selected_model`, and `selected_effort`: the resolved route.
- `rejected_lower_tier` and `rejected_higher_tier`: concise evidence for both
  neighboring choices.
- `fallback`: the stop or escalation route if assumptions fail.

The receipt is part of the bounded context package. Never include credentials,
private values, or unrelated user context in it.

### Conflict precedence

Apply these rules in order when signals overlap:

1. Direct-work and authorization boundaries come before model selection.
2. Split mixed-mode work into sequential assignments when evidence gathering,
   writing, final judgment, or verification need different families.
3. High-risk final decisions require Sol even when Terra or Luna can prepare the
   evidence.
4. Choose family before effort; do not compensate for the wrong family by raising
   effort.
5. A lower tier requires all downgrade conditions to be positively established.
6. Any high-risk escalation signal is sufficient to block the cheaper route and
   select the appropriate stronger Sol route.
7. Unknown is not evidence for a cheaper route. Preserve the current safe tier or
   escalate until the uncertainty is resolved.
8. `default` is last: use it only after proving an affirmative same-tier match.

### Runtime compatibility fallback

- Treat an absent, incomplete, stale, or corrupt runtime model cache as
  `advisory compatibility evidence`, not as authority to block delegation or the
  parent task.
  Report the condition, then try the configured route; the child-start result is
  the source of truth for what the current runtime accepts.
- If a Sol or Terra `ultra` route is rejected, make the single fallback attempt in
  the same family at `max`; the parent retains decomposition and orchestration.
- If another named route is rejected, an alternate route must stay in the same
  family and must still satisfy the assignment's risk and acceptance conditions.
  Never silently cross model families or use `default` to hide incompatibility.
- Permit at most one alternate child start for the assignment. If it also fails,
  or no safe same-family alternate exists, the parent executes the assignment
  directly instead of blocking the user's task or entering a retry loop.
- Preserve authorization and single-writer boundaries during every fallback, and
  record the fallback in the routing receipt and visible launch disclosure.

### Re-evaluate at phase and assignment boundaries

- Select the role for the remaining assignment, not the parent agent's model, the
  original task's peak complexity, or the route used by an earlier phase.
- Re-evaluate before every spawn and whenever responsibility changes, including
  `design -> implementation`, `implementation -> verification`,
  `exploration -> decision`, and a `task split or handoff`.
- A completed design does not by itself justify a cheaper route. Lower the tier
  only when the decisions, interfaces, file boundaries, acceptance evidence,
  prohibited choices, and independent mechanical oracle needed by the child are
  actually complete. Once they are, use Luna Max as the primary route for
  logic-heavy implementation with many explicit or interacting rules; literal
  mechanical edits may use a lower matching Luna effort. Bounded implementation
  that still requires local judgment may use `sol-low`, `sol-medium`, or
  `sol-high`, while reopened design, interacting unresolved causes, or unstable
  cross-component decisions justify Sol XHigh or Max.
- A genuinely new and narrower bounded assignment may select a lower tier than an
  earlier phase. A retry of the same unresolved assignment follows one-way
  escalation and must not be relabeled as a new phase merely to reset the tier.
- Treat verification as its own assignment. Explicit mechanical checks may use a
  cheaper role, but judgment-heavy or high-risk completion claims require Sol-level
  synthesis and remain owned by the parent agent.
- If a child discovers missing design decisions, conflicting evidence, or material
  scope expansion, it must stop before out-of-scope work. It must then
  return the evidence and scope change to the parent. The parent re-routes the
  work while preserving the single-writer boundary.

### Escalation and orchestration

- Within a family, escalate one direction for the same unresolved assignment:
  `low -> medium -> high -> xhigh -> max`.
- Move Luna work to Sol when its executable design or exact oracle stops being
  complete, local judgment reopens, risk becomes high, or final ownership crosses
  the family boundary. Move Terra work to Sol before any write. A closed mechanical
  code write alone does not force Luna to Sol, but higher Luna or Terra effort is
  never a substitute for Sol authority outside those boundaries.
- Select Sol or Terra `ultra` only when exceptional parallel decomposition is
  useful. Ultra is automatic delegation, not the next retry after `max`.
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
