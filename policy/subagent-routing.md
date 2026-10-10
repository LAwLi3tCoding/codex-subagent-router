## Model and effort routing

Preserve the human-selected primary model and reasoning effort, including Ultra.
Do not change primary defaults or introduce a global subagent model/effort default.
The primary owns requirements, overall design, integration, evidence-based review
adjudication, verification, and the final completion claim. Short, connected, or
unclassified work stays in the primary session.

- Delegate only when independent parallel progress, context isolation, or independent
  judgment provides a concrete benefit worth startup, reading, and integration work.
  Define the goal, inputs, ownership, dependencies, and acceptance check together.
  Keep short tasks, sequential edits to one module, and work needing frequent exchange
  of intermediate results with one executor. Do not split merely because a task is
  long or uses Ultra. A bounded design question can precede the overall design.
- For delegated execution use `sol-low` for closed, mechanically checkable work and
  `sol-medium` for routine implementation, source investigation, and test fixes.
  Use `sol-high` when unresolved causes, cross-module compatibility, or open design
  require judgment. Reserve `sol-xhigh` for multiple interacting invariants across
  concurrency, migration, or failure/recovery paths. A state field, many files, task
  length, or domain label alone does not justify high/xhigh. Reassess when uncertainty
  is resolved; do not carry a design effort into routine execution by default.
- These roles use `gpt-6.1-sol` at low/medium/high/xhigh respectively. Choose the lowest
  effort sufficient for the actual uncertainty and interacting constraints; do not
  downgrade consequential work to meet a cost target. Reassess at phase transitions.
  Missing evidence or failing tools require evidence/tool recovery, not guessed facts
  or blind effort escalation. Max is an evaluated exception; Luna and Terra are not
  part of the normal routing path.
- Select review by concrete risk and required gates. Review-only requests go directly
  to this selection; do not first dispatch an execution role to forward the review.
  Local, reversible changes with clear checks use primary verification unless independent review is requested or
  a mandatory gate applies. Ordinary feature reviews and generic review requests
  use independent read-only `sol-reviewer` (`gpt-6.1-sol`, `high`).
  Use independent read-only `astra-reviewer` (`gpt-6-astra`, `xhigh`) for an explicit
  Astra request or concrete consequential risks in security, permissions, data
  consistency, irreversible operations, critical shared/recovery protocols, or
  high-consequence business-definition, cause, or completion judgments. Identify the
  invariant or failure consequence; architecture/domain labels alone are insufficient.
  Classify before dispatch: a batch containing such risk goes directly to Astra,
  even when the primary uses Astra. Evidence insufficiency never waives required
  review. Routine questions, source learning, status, and wording need no automatic
  review. Stronger workspace/user gates still apply.
- If Sol review uncovers a consequential risk, keep it unresolved and escalate that
  risk and affected scope to Astra with the original evidence and Sol findings.
  Escalation is not a second full review by default. The Astra reviewer owns rechecks
  of that risk; unchanged Sol coverage remains valid at its reviewed version.
- Give the read-only reviewer original requirements, constraints, an exact version,
  candidate artifacts, and evidence/verification entry points, not just the primary's
  conclusions. Submit a stable batch with its callers and necessary checks; do not
  batch across a required authorization, design, or external-action review gate.
  The primary adjudicates findings with evidence or marks them unresolved. After
  substantive repairs and affected checks, the same reviewer rechecks the original
  findings and affected scope at the new version. Unchanged coverage may be reused;
  later substantive changes invalidate it. No findings or wording-only edits require
  no repeated review. Recurring findings call for root-cause/design correction before
  resubmission; review-count limits never waive unresolved risks or required review.
- Prefer an independent context (`fork_turns="none"` when supported), supplying the
  necessary facts and fixed evidence locations/versions. Full-history forks need a
  concrete dependency on that history. Read enough source and callers to verify the
  assignment; do not repeatedly copy entire designs or logs between agents.
- Use only supported spawn fields. Explicit model/effort overrides require an
  independent or finite-history context when the interface rejects full-history
  overrides. Role files can override spawn parameters; confirm actual settings from
  runtime evidence when exposed, otherwise report requested/unconfirmed values.
- Respect effective runtime capacity and user concurrency limits. Parallel writers
  require disjoint ownership; external writes have one owner. Initialize shared
  browser/SSO serially before parallel read-only work. Do not automatically nest agents.
- Consolidate follow-up instructions before sending. Interrupt ongoing work only for
  changed requirements, blockers, or findings affecting correctness, ownership, or
  dependent work. Report completion and use the native wait mechanism when waiting;
  avoid routine status messages and repeated unchanged polling.
- Return a concise result, changed artifacts/version and evidence locations, checks
  with results/coverage, and unresolved gaps or tool failures. Keep large logs in
  files. The primary verifies critical evidence according to risk instead of repeating
  every child read; independent review still examines original sources.
  Unknown external effects stay UNKNOWN until reconciled;
  do not blindly retry. Ordinary dispatch failure may return work to the unchanged
  primary; required review failure remains pending review. Never treat a child ending,
  design approval, or passing tests as proof of publication or business acceptance.
- Preserve existing authorization, permissions, business Gates, and unrelated work.
  Do not require another confirmation for already authorized reversible work, and
  do not expand authority through delegation or model selection.
