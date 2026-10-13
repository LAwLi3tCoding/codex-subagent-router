## Subagent model and effort selection

Apply this guidance only after the current session has independently decided to
run a subagent task and selected its role. This router selects only model and
reasoning effort. It does not decide whether to delegate, enable agents, select
or replace roles, require review, escalate findings, or repeat a review.

Preserve the human-selected primary model and reasoning effort, including Ultra.
Resolve model and effort independently: keep each explicitly selected parameter
or applicable task/role binding, and recommend only the unspecified parameter.
Preserve the selected role's instructions, permissions, tools, context mode,
and workflow requirements.

For an unspecified model, recommend `gpt-6.1-sol`. Astra is excluded from
automatic model selection until the human explicitly restores it.

For an unspecified effort, choose the lowest sufficient supported level based
on the reasoning needed for the current assignment:

| Effort | Selection boundary |
| --- | --- |
| `low` | The solution is known, inputs and checks are clear, and execution needs little judgment: a mechanical edit, a precise lookup, or applying an established fix. |
| `medium` | Routine work needs local judgment, but requirements and affected scope are understood: ordinary implementation, bounded investigation, or test repair. This is the starting point for routine tasks, not a fallback for unresolved complexity. |
| `high` | A material question remains open and requires comparing hypotheses or alternatives: unknown cause, uncertain compatibility, open design, or an already-selected review needing substantive judgment. |
| `xhigh` | Several constraints interact across components or states, so local choices cannot be assessed separately: concurrency, migration, recovery, or competing evidence affecting the same contract. Reason through the interactions together. |
| `max` | The assignment combines tightly coupled constraints, competing plausible solutions, and consequential failure modes; evidence is available, yet a defensible decision requires deeper synthesis than xhigh is reasonably expected to provide. Use for the difficult decision itself, not routine work around it. |

Select `max` directly when all of its conditions are evident; a prior xhigh run
is not required. It is also appropriate when an xhigh analysis leaves a specific
reasoning gap despite adequate evidence and a working tool path. State briefly
which unresolved interaction or competing explanation needs xhigh/max. Explicit
human choices remain authoritative; do not downgrade them automatically.

Reassess at natural assignment or phase boundaries. Once the cause or design is
settled, routine implementation normally returns to medium, and mechanical
follow-up to low. Select settings for the next invocation only when the existing
workflow already calls for one; do not create, restart, split, or repeat tasks
solely to change effort.

Task length, file count, domain labels, a state field, review status, or the
primary's Ultra setting alone do not justify higher effort. High consequence
alone does not require max when the reasoning is straightforward. Missing
sources, authorization, runtime capability, or tool failures require evidence
or tool recovery rather than a blind effort increase. A failed check calls for
classification of its cause, not automatic escalation. Do not repeatedly raise
effort without identifying the new reasoning need.

Apply a recommendation only through model/effort fields supported by the current
runtime and compatible with the selected role and context. If the requested
level is unsupported, use a supported level only when it is sufficient; otherwise
retain the existing invocation and report the limitation. Do not silently call
xhigh max, change models/roles/context, edit configuration, or alter workflow to
force the mapping. Distinguish recommended/requested settings from runtime-
confirmed settings; installation alone does not prove actual selection.
