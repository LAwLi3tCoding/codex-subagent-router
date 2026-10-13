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

For an unspecified model, choose from the following candidates, subject to the
runtime's available models and any already-selected effort:

| Model | Automatic effort choices | Selection boundary |
| --- | --- | --- |
| `gpt-6-luna` | `max` only | Closed, bounded work with an established solution, explicit inputs and checks, and little unresolved behavioral judgment: mechanical edits, precise extraction, or applying a verified transformation. |
| `gpt-6.1-sol` | `low`, `medium`, `high`, `xhigh`, `max` | Default for implementation and investigation requiring judgment, uncertain callers or compatibility, and tasks not clearly eligible for Luna or Astra. |
| `gpt-6-astra` | `high`, `xhigh`, `max` | Exceptionally demanding reasoning: deeply coupled constraints, competing explanations/designs, and consequential failure modes, with adequate evidence and a specific reason to expect Sol to be insufficient. |

Astra is now permitted in automatic model selection. Its selection requires a
concrete reasoning need; security, architecture, review, task length, or a failed
tool alone does not select Astra. A prior Sol attempt is not mandatory; an observed
Sol limitation must be a reasoning gap rather than missing evidence or tools.
Ordinary difficult work remains on Sol. Explain an Astra selection briefly.

Luna is eligible only when the resulting effort is max: if effort is unspecified,
recommend max for Luna; if a different effort is already fixed, choose another
eligible model without changing that effort. Do not recommend Luna at low,
medium, high, or xhigh, including as an unsupported-max fallback. Explicit user
choices or fixed role bindings still take precedence; report a non-router pair
as an explicit setting, not as this router's recommendation.

Effort is model-relative. Luna/max is a fixed pairing for bounded work, not a claim
that the task requires Sol/max or Astra/max reasoning. Model eligibility comes
before choosing an unspecified effort. The five-level rubric below applies to
Sol and Astra, constrained by their automatic effort choices above. This policy
sets selection heuristics, not measured quality, price, or speed guarantees.

For an unspecified Sol/Astra effort, choose the lowest sufficient supported level based
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
settled, routine implementation normally returns to Sol/medium, and mechanical
follow-up can use Luna/max or Sol/low according to eligibility. Select settings for the next invocation only when the existing
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
level is unsupported, use a supported level only when it is sufficient and allowed
for the selected model; otherwise
retain the existing invocation and report the limitation. Do not silently call
xhigh max, change models/roles/context, edit configuration, or alter workflow to
force the mapping. Distinguish recommended/requested settings from runtime-
confirmed settings; installation alone does not prove actual selection.
