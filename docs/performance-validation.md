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

## Effort calibration cases

Keep delegation and review decisions fixed. Compare the reasoning boundaries
below rather than assuming a larger task needs a higher level:

| Assignment | Candidate | Distinguishing evidence |
| --- | --- | --- |
| Apply a known rename with clear callers and checks | low | No unresolved behavioral choice. |
| Implement an established interface in a bounded module | medium | Local judgment within a settled contract. |
| Diagnose a reproducible fault with several plausible causes | high | Need to discriminate hypotheses. |
| Plan a migration with concurrent writers and failure recovery | xhigh | Correctness depends on interacting states and constraints. |
| Resolve incompatible recovery designs with competing evidence and consequential failure modes | max | Adequate evidence still leaves a tightly coupled decision needing unusually deep synthesis. |
| Retrieve a missing log or recover a failed tool invocation | No automatic increase | The blocker is evidence or tool availability. |
| Implement routine edits after a max-level design decision | medium or low | The remaining assignment no longer contains the design uncertainty. |
| User pins high, model is unspecified | Keep high; recommend Sol | Resolve parameters independently. |
| User pins a model, effort is unspecified | Keep model; select supported effort | Do not replace the model to obtain max. |

These are policy examples, not measured runtime outcomes. Unsupported max remains
an explicit limitation when a lower supported level is insufficient; do not count
an xhigh run as a max run. Phase changes do not authorize new invocations.
