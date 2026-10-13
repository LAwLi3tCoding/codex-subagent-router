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
