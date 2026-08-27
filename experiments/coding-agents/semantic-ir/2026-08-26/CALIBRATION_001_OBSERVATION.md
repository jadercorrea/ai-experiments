# Heterogeneous semantic patch calibration 001

## Status

**Execution complete; paired efficacy and token comparisons invalidated by a
treatment-asymmetric context-addressability defect. All raw evidence is
retained. No replacement run is authorized.**

The calibration executed the exact predeclared schedule under freeze
`02bb16238584057e809d8bd2655a13b8b5d163a2317774735e4e636d18a83c05`.
It completed all twelve terminal cells without an infrastructure or spend stop.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 43 |
| Input tokens | 184,940 |
| Output tokens | 9,613 |
| Total tokens | 194,553 |
| Estimated cost | USD 0.699015 |
| Public evaluator runs | 8 |
| Repair cycles | 3 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

Every retained provider response reported the exact locked model
`us.anthropic.claude-sonnet-4-6`. Request policy, response counts, token sums,
cell costs, schedule identities, result analysis, and the evidence artifact lock
were checked after execution. No credential, hidden-evaluator path, or reference
path was found in a model request.

## Raw outcomes

The frozen summarizer produced these descriptive counts:

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 3 | 0 |
| Supported-task hidden Pass@1, denominator 5 | 3 | 0 |

Semantic applicability remained the predeclared 5/6, with the unsupported
cross-module semantic cell counted as an all-task failure. Source completed four
terminal submissions: three passed hidden evaluation and one failed it. Two
source cells ended before terminal submission. No supported semantic cell
reached a mutation or terminal submission.

The source arm consumed 108,822 tokens across 33 responses. The semantic arm
consumed 85,731 tokens across ten responses. Those totals are not comparable:
the semantic trajectories were systematically stopped early.

## Why the comparison is invalid

All five supported semantic subjects attempted `workspace_read` on an artifact
label shown in their system context. Four tried their task's
`base/program.json`; one first tried its participant `TASK.md`. The rendered
context named those artifacts under `tasks/...`, but the workspace tool exposed
only files materialized inside the ephemeral participant repository. Therefore
every requested path was unavailable.

This would have been recoverable in a normal coding-agent trajectory. The frozen
runner instead converted an unavailable read into terminal
`tool_protocol_failure` and did not return the error to the subject. Every
supported semantic trajectory stopped with zero mutation attempts.

The defect is treatment-asymmetric. The semantic arm receives its persistent
program, catalog, and schemas as embedded context artifacts and has a natural
reason to address them again. The source arm operates on repository files that
are readable through the same tool. Consequently, the observed 3/6 versus 0/6
cannot distinguish representation quality from interface addressability and
fatal error handling.

The raw results remain true descriptions of this frozen execution, but they do
not support the proposition that direct source editing is more effective or
more token-efficient than semantic patching.

## Other observed failures

The remaining failures are retained without post hoc correction:

- the source error-taxonomy submission passed public evaluation and failed the
  hidden evaluator;
- the source directory-fallback trajectory exhausted its three mutation
  attempts after two public evaluations;
- the source cross-module trajectory exceeded the four-tool-call per-turn cap;
- the cross-module semantic outcome was the predeclared automatic unsupported
  failure.

These observations may inform a later protocol but are not changed or replaced
inside calibration 001.

## Disposition and next gate

The evidence bundle receives an explicit invalidation record. No cell will be
rerun under this freeze. A new, separately identified design must:

1. make every model-visible context artifact addressable through an explicit
   read-only context surface, or remove path-like labels that imply such access;
2. return invalid tool requests as recoverable observations while retaining the
   frozen trajectory budget;
3. preserve the same isolation, hidden-evaluator, accounting, unsupported-task,
   and nonadaptive analysis rules; and
4. use fresh sealed task instances before making another paired efficacy claim,
   because the provider has now seen these exact instances.

Until that new protocol and task set are frozen, calibration 001 supports only
an interface-design finding: a semantic state representation is insufficient if
the agent cannot reliably address the state it was given.
