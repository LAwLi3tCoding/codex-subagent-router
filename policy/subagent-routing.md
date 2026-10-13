## Subagent model and effort selection

Apply this guidance only after the current session has independently decided to
run a subagent task and selected its role. This router selects only model and
reasoning effort. It does not decide whether to delegate, enable agents, select
or replace roles, require review, escalate findings, or repeat a review.

Preserve the human-selected primary model and reasoning effort, including Ultra.
Explicit user choices and applicable task or role model/effort bindings take
precedence over the recommendations below. Preserve the selected role's
instructions, permissions, tools, context mode, and workflow requirements.

When model and effort are not already specified:

- Recommend `gpt-6.1-sol` for the subagent. Astra is excluded from automatic
  model selection until the human explicitly restores it.
- Choose the lowest effort sufficient for the task's unresolved uncertainty:
  - `low`: closed, mechanically checkable work with clear inputs and acceptance.
  - `medium`: routine implementation, bounded source investigation, or test fixes
    requiring local judgment.
  - `high`: unresolved causes, cross-module compatibility, open design, or an
    already-requested review requiring independent judgment.
  - `xhigh`: multiple interacting invariants across concurrency, migration,
    failure/recovery, or an already-requested consequential-risk assessment.
- Task length, file count, a state field, domain labels, or the primary's Ultra
  setting alone do not justify a higher effort. Reassess when uncertainty changes;
  keep explicitly selected settings. `max` requires an explicit task-specific choice.

Apply a recommendation only through model/effort fields supported by the current
runtime and compatible with the selected role and context. If those fields are
unavailable or the role fixes its settings, preserve the existing invocation;
do not change roles, context mode, configuration, or workflow to force the mapping.
Distinguish recommended/requested settings from runtime-confirmed settings.
