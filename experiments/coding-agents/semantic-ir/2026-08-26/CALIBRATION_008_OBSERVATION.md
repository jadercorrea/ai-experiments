# Matched Nested Instruction-Grammar calibration 008

## Status

**Execution valid and complete as a repeated within-instance descriptive
calibration. Nested Grammar v3 was admitted by the provider and acted as an
effective pre-dispatch safety boundary, but it did not make model adherence or
task convergence reliable. The eleven provider-call cells produced sixteen
reserved-phase grammar rejections, split evenly between commit and finish.
Valid provider-call terminals rose from four in Calibration 007 to five, yet
the supported hidden outcome remained source 1/5 versus semantic 0/5. Three
semantic cells terminated without ever submitting a mutation. Total tokens
fell 0.67% and estimated cost fell 1.36%, differences too small and too
confounded by independent sampling to support an efficiency claim. Exact JSON
Schema validation can prevent invalid dispatch; provider acceptance of that
schema does not imply constrained decoding or productive use of the permitted
language.**

Calibration 008 executed all twelve scheduled cells under freeze
`e72c87ff0141913dfa48f391c63ada9a6669e410a302c690da778c958a48d943`.
Eleven cells called the locked model; the unsupported semantic cell remained a
zero-call local result. The evidence lock contains 455 files with tree digest
`7e4528860c496819040bfbbd889c7215a3e8f55aa046d019c9532978d11ba922`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 126 |
| Input tokens | 445,597 |
| Output tokens | 38,539 |
| Total tokens | 484,136 |
| Estimated cost | USD 1.914876 |
| Public evaluator runs | 1 |
| Repair cycles | 4 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 126 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. The launch is bound by digest
`b021e97e3284caa2b586327fabc8bec56c0f0f923e6f8e4dcd3eb4f45a9235fa`.
Provider usage, cell costs, schedule identities, launch and freeze bindings,
progress contracts, reserved schema identities, the exact shared `x` tool,
message roles, and the artifact lock reconcile. The artifact-lock file digest
is `6e44e47aada0c23c190aee43575386bb5c468366c2651679d9604bd8367cd1e9`.

The account-level Amazon Bedrock retention mode remains unreadable by the
inference-scoped credential and is not claimed. The launch records the current
public service-policy basis and this limitation.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 1 | 0 |
| Supported-task hidden Pass@1, denominator 5 | 1 | 0 |
| Semantic applicability | — | 5 / 6 |
| Provider requests, all-task accounting | 66 | 60 |
| Input tokens, all-task accounting | 148,882 | 296,715 |
| Output tokens, all-task accounting | 15,977 | 22,562 |
| Total tokens, all-task accounting | 164,859 | 319,277 |
| Estimated cost, all-task accounting | USD 0.686301 | USD 1.228575 |

The automatic unsupported semantic cell costs zero. Across only the five
supported pairs:

| Supported-task resource | Source | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Provider requests | 54 | 60 | +11.1% |
| Input tokens | 127,536 | 296,715 | +132.7% |
| Output tokens | 13,743 | 22,562 | +64.2% |
| Total tokens | 141,279 | 319,277 | +126.0% |
| Estimated cost | USD 0.588753 | USD 1.228575 | +108.7% |
| Sum of cell durations | 188.78 s | 411.05 s | +117.7% |

## What exact instruction grammar changed

Calibration 008 changed the reserved request schemas shared by both arms. Work
turns retained the same byte-identical Session ISA requests. Commit and finish
wrapped an opcode-specific discriminated instruction under the required `v`
property, with exact arity and payload shape, and validated that same schema
before runtime dispatch.

| Measure | Calibration 007 | Calibration 008 | Realized change |
| --- | ---: | ---: | ---: |
| Provider requests | 127 | 126 | -0.79% |
| Total tokens | 487,384 | 484,136 | -0.67% |
| Estimated cost | USD 1.941276 | USD 1.914876 | -1.36% |
| `F` instructions | 7 | 5 | -2 |
| Valid provider-call terminals | 4 | 5 | +1 |
| Source all-task hidden passes | 2 / 6 | 1 / 6 | -1 |
| Source supported hidden passes | 1 / 5 | 1 / 5 | 0 |
| Semantic supported hidden passes | 0 / 5 | 0 / 5 | 0 |
| Repair cycles | 4 | 4 | 0 |

The source cross-module cell explains the all-task hidden-pass difference: it
passed in Calibration 007 and failed after a valid terminal in Calibration
008. The supported estimand did not change. Because trajectories were sampled
independently, none of these realized deltas is a causal estimate of Grammar
v3.

## Reserved-phase adherence

The freeze defined 22 possible reserved requests. One source cell terminated
early, so execution reached 20 of them, using the schema frozen for each exact
arm, phase, and remaining budget. Across the 23 tool calls sampled in those
responses,
the model produced four object-valued `F`, five `I`, five `S`, seven `W`, and
two string-valued `v` payloads. Sixteen calls failed exact validation:

| Phase | Rejected calls | Observed forms |
| --- | ---: | --- |
| Commit | 8 | 3 `I`, 2 `S`, 3 `W` |
| Finish | 8 | 2 `I`, 4 `W`, 2 string-valued `v` payloads containing source `S` |

Every rejection occurred before underlying dispatch. Seven attempted reads,
five inspections, and four submissions or submission-shaped values therefore
could not mutate state or consume runtime action budgets beyond the already
spent provider turn. There was no missing top-level `v` in these samples. The
two malformed envelopes nested a serialized JSON instruction string under
`v`; the remaining fourteen used an object-valued instruction whose opcode,
arity, or payload was outside the phase-specific union.

The result refines the capability-probe evidence. Probe 003 established that
Bedrock admits these nested-union schema objects and recorded two conforming
samples. Calibration 008 demonstrates that admission is not enforcement: the
model can still sample arguments rejected by the advertised exact schema.
Runtime validation remains necessary.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | Nonterminal after one mutation; four grammar rejections | Nonterminal after two mutation attempts; two grammar rejections |
| Normalization policy | Nonterminal after three mutation attempts | Valid `F`, no mutation, hidden fail |
| Raw-ID retry | Nonterminal after two mutation attempts | Valid `F`, no mutation, hidden fail |
| Reserved-ID guard | Early valid `F`; hidden pass | Valid `F`, no mutation, hidden fail |
| Directory fallback | Nonterminal after one mutation | Nonterminal, no mutation |
| Cross-module rename | Valid `F`; hidden fail | Unsupported by construction |

Terminal validity and task correctness again separate. Three semantic cells
used the semantic inspection surface repeatedly, then finished with their
baseline program unchanged. Exact finalization prevents malformed actions; it
cannot establish that the agent has constructed the required motion.

## Interpretation

The experiment sharpens four boundaries:

1. **Provider schema admission is not constrained decoding.** An accepted tool
   schema can still receive nonconforming sampled arguments.
2. **Pre-dispatch validation is a real safety property.** All sixteen invalid
   reserved actions were rejected before mutation or evaluator execution.
3. **A valid terminal is not evidence of completed work.** Four of five
   provider-call terminals failed hidden evaluation; three semantic terminals
   contained no mutation at all.
4. **Grammar exactness does not solve representation use.** The semantic arm
   remained more expensive on every supported resource measure and produced no
   hidden pass.

This is another Experimental-TDD split result. The safety test turned green:
invalid reserved instructions cannot dispatch. The stronger adherence and
task-efficacy tests stayed red.

## Interpretation boundary

- Calibration 008 reuses the exact Calibration 007 instances to isolate the
  request-grammar change. It is not a fresh benchmark.
- This is one unreplicated schedule over six family-derived tasks and one model
  endpoint.
- Provider-native model identity is verified; model weights are not
  cryptographically pinned.
- Hidden Pass@1 is descriptive, not a powered statistical comparison.
- Independent sampling means run-to-run differences cannot be assigned solely
  to the grammar intervention.
- The source and semantic arms share progress control and outer transport but
  retain different representations and memory projections.
- The result establishes exact local rejection, not provider-side schema
  enforcement.

No cell will be replaced or rerun under this freeze. Both inferential and
general efficacy claims remain unauthorized.

## Next red test

Do not add another grammar revision merely because Grammar v3 exposed invalid
samples. It already supplies the intended runtime safety property. Before any
new provider launch, design the registered Representational Dependence
calibration so that lexical cues and structural packaging vary while the
decoded canonical IR, capabilities, evidence, budgets, verification, model,
and sampling remain fixed. Its first checkpoint must be call-free and must
include power, cost, contamination, and launch gates. This preserves the new
hypothesis without retrofitting it onto Calibration 008.
