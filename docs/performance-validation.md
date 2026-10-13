# Task-level model and effort validation

The router recommends model and effort only after a session has chosen the task
and role. An installer or unit-test pass proves neither runtime selection nor
performance. Model recommendations must not change the decision to delegate,
review requirements, role responsibilities, permissions, or context mode.

## Comparable runs

1. Record the policy version, original task, selected role, explicit settings,
   context mode, permissions, and acceptance checks.
2. Compare baseline and candidate in fresh sessions with isolated fixture copies.
   Preserve the main model/effort and the same workflow requirements. Do not force
   delegation or add review steps to demonstrate routing.
3. Inspect child runtime records for actual model and effort. If the runtime does
   not support compatible overrides, record the recommendation as unapplied.
   Requested settings and role configuration are not confirmed runtime settings.
4. Run the same acceptance checks. Preserve failed, blocked, and incomplete results.
5. Use multiple comparable runs before claiming a general time or cost improvement.

## Measurements

Record wall time, input/cached-input/output tokens, actual model/effort, acceptance
results, and missing evidence. Reasoning tokens are a subset of output, not an
additional quantity. Missing usage is unknown, not zero. Charges require billing
and rate evidence; token counts alone do not establish savings.

Keep private task content and machine-specific logs outside this repository.

## Calibration cases

Keep delegation and review decisions fixed. Compare the six automatic combinations
using the same task and acceptance checks:

| Assignment | Candidate | Distinguishing evidence |
| --- | --- | --- |
| Apply a known rename with clear callers and checks | Sol/low | No unresolved behavioral choice. |
| Implement an established interface in a bounded module | Sol/medium | Local judgment within a settled contract. |
| Diagnose a reproducible fault with several plausible causes | Sol/high | Need to discriminate hypotheses. |
| Plan a migration with concurrent writers and failure recovery | Sol/xhigh | Correctness depends on interacting states and constraints. |
| Deeply explore recovery paths within a clearly defined protocol | Sol/max | Problem frame is established; completeness needs extensive reasoning. |
| Reconstruct a causal model when the established explanation cannot reconcile cross-component evidence | Astra/xhigh | Specific need to reconsider the problem frame with adequate evidence. |
| Retrieve a missing log or recover a failed tool invocation | No automatic increase | The blocker is evidence or tool availability. |
| Implement routine edits after a max-level design decision | Sol/medium or Sol/low | Remaining work no longer contains the design uncertainty. |
| User pins high, model is unspecified | Sol/high | Preserve the fixed effort. |
| User pins Astra, effort is unspecified | Astra/xhigh | Preserve the fixed model. |
| User explicitly pins Astra/max | Keep Astra/max | Explicit settings take precedence; this is not an automatic route. |

Luna is excluded from automatic selection. Astra/high and Astra/max are explicit
choices only. Unsupported settings remain limitations; do not record an xhigh
run as max. These examples are policy expectations, not runtime outcomes.

Calibrate Sol/max against Astra/xhigh on the same difficult tasks before asserting
that problem-frame reconstruction is a stable model boundary. Record missed
requirements, corrections, elapsed time, and usage separately. If the distinction
is unclear, prefer Sol. Phase changes do not authorize extra invocations.
