## Model and effort routing

Preserve the human-selected primary model and reasoning effort, including Ultra.
Do not change primary defaults or introduce a global subagent model/effort default.
The primary owns requirements, overall design, integration, evidence-based review
adjudication, verification, and the final completion claim. Short, connected, or
unclassified work stays in the primary session.

- Delegate after defining the goal, input, boundaries, dependencies, and acceptance
  check, when parallel progress, context isolation, or independent judgment has
  clear value. A design specialist needs a clear question and constraints, not an
  already completed design. Do not split merely because a task is long or uses Ultra.
- For explicitly delegated execution choose `sol-low` for closed, mechanically
  checkable extraction/conversion; `sol-medium` for ordinary bounded implementation,
  source investigation, fixed-metric queries, or editing verified facts; `sol-high`
  for unknown causes, cross-module compatibility, open design, business definitions,
  or multi-source synthesis; `sol-xhigh` for coupled state machines, concurrency,
  consistency, migration/recovery, or difficult conflicting evidence.
- These execution roles use `gpt-6.1-sol` at low/medium/high/xhigh respectively.
  Reassess remaining work at design/implementation/verification or evidence/judgment
  transitions. Missing evidence or failing tools require evidence/tool recovery,
  not guessed facts or blind effort escalation. Max is an evaluated exception;
  Luna and Terra are not part of the normal routing path.
- Complex review must start a separate `astra-reviewer` subagent using
  `gpt-6-astra` with `xhigh`, even when the primary itself uses Astra. Trigger it for
  explicit review requests, substantive core architecture/shared-protocol changes,
  consequential safety/permission/consistency/recovery decisions, or important
  business-definition, cause, or completion judgments with significant consequences.
  Evidence insufficiency is not an exemption. Effort, Ultra, length, or a domain
  label alone does not trigger review; routine queries/editing/learning need no heavy review.
- Give the read-only reviewer original requirements, constraints, an exact version,
  candidate artifacts, and evidence/verification entry points, not just the primary's
  conclusions. The primary accepts/rejects findings with evidence or marks them
  unresolved. After substantive repairs and affected verification, the same reviewer
  rechecks the new version and affected scope. No substantive findings/changes means
  no mandatory second review. Later substantive changes invalidate older coverage.
- Use only supported spawn fields. Explicit model/effort overrides require an
  independent or finite-history context when the interface rejects full-history
  overrides. Role files can override spawn parameters; confirm actual settings from
  runtime evidence when exposed, otherwise report requested/unconfirmed values.
- Respect effective runtime capacity and user concurrency limits. Parallel writers
  require disjoint ownership; external writes have one owner. Initialize shared
  browser/SSO serially before parallel read-only work. Do not automatically nest agents.
- Return artifacts, verification, evidence references, checked/unchecked scope, tool
  failures, and remaining gaps. Unknown external effects stay UNKNOWN until reconciled;
  do not blindly retry. Ordinary dispatch failure may return work to the unchanged
  primary; required review failure remains pending review. Never treat a child ending,
  design approval, or passing tests as proof of publication or business acceptance.
- Preserve existing authorization, permissions, business Gates, and unrelated work.
  Do not require another confirmation for already authorized reversible work, and
  do not expand authority through delegation or model selection.
