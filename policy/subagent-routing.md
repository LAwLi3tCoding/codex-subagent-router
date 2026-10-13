## Subagent model and effort selection

Apply this guidance only after the current session has independently decided to
run a subagent task and selected its role. This router selects only model and
reasoning effort. It does not decide whether to delegate, enable agents, select
or replace roles, require review, escalate findings, or repeat a review.

Preserve the human-selected primary model and reasoning effort, including Ultra.
Resolve model and effort independently: retain each explicit user choice or
applicable task/role binding, and recommend only the unspecified parameter.
Preserve the selected role's instructions, permissions, tools, context mode,
and workflow requirements.

Use these six automatic combinations, subject to runtime support and any fixed
parameters. `gpt-6.1-sol` is the default model. Luna is excluded from automatic
selection. Astra/high and Astra/max are explicit choices only, not automatic
routes; explicit choices and role bindings remain authoritative.

| Model | Effort | Selection boundary |
| --- | --- | --- |
| `gpt-6.1-sol` | `low` | The solution is known, scope is closed, and inputs and checks are clear; execution needs little judgment. Mechanical edits, precise lookups, and applying an established fix fit here. |
| `gpt-6.1-sol` | `medium` | Requirements and affected scope are understood, but routine implementation, bounded investigation, or test repair needs local judgment. |
| `gpt-6.1-sol` | `high` | A material question remains open and needs hypothesis testing or alternative comparison: unknown cause, uncertain compatibility, or a local design decision. |
| `gpt-6.1-sol` | `xhigh` | Several constraints interact across components or states and need joint reasoning: concurrency, migration order, or failure recovery. |
| `gpt-6.1-sol` | `max` | The problem, evidence, and constraints are well formulated, but reaching a complete conclusion requires deep exploration of interacting paths and competing solutions. The difficulty is thorough reasoning within the established problem frame. |
| `gpt-6-astra` | `xhigh` | The problem frame itself may be inadequate: contradictions need a new explanation, cross-component evidence needs a new causal model, or design assumptions need reconstruction. Adequate evidence and a concrete reason to expect Sol to be insufficient are required. |

Choose the lowest sufficient Sol effort for the current assignment. Sol/max is
a regular candidate for a well-formulated difficult problem; a prior xhigh run
is not required. Select Astra/xhigh for a specific need to reconsider the problem
frame, not merely for more reasoning depth. State that need briefly. If the
boundary is unclear, prefer Sol. These are selection heuristics, not measured
quality, cost, or speed guarantees.

A prior Sol attempt is not mandatory for Astra. If a Sol result motivates a model
change, identify its reasoning limitation rather than treating a failed check
as proof of insufficient capability. Security, architecture, review status, task
length, file count, or the primary's Ultra setting alone does not select Astra
or a higher effort. A consequential but straightforward task can use low/medium.
Missing sources, authorization, or working tools require recovery rather than a
blind model/effort increase.

Reassess at existing assignment or phase boundaries. Once the cause or design is
settled, routine implementation normally returns to Sol/medium, and mechanical
follow-up to Sol/low. Retain explicit settings. Choose settings for a subsequent
invocation only when the existing workflow already calls for it; do not create,
restart, split, or repeat tasks solely to change model or effort.

Apply recommendations only through model/effort fields supported by the current
runtime and compatible with the selected role and context. Fixed parameters
limit eligible recommendations; do not change them to obtain a preferred pair.
For an explicitly selected Astra model with no fixed effort, recommend xhigh;
other explicit model choices remain outside this automatic model policy. If a
recommended level is unsupported, use another eligible supported level only
when sufficient; otherwise preserve the invocation and report the limitation.
Do not silently call xhigh max, change roles/context, edit configuration, or
alter workflow to force the mapping. Distinguish recommended/requested settings
from runtime-confirmed settings; installation alone does not prove selection.
