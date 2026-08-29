# Matched Coverage-Session calibration 006

## Status

**Execution valid and complete as a repeated within-instance descriptive
calibration. Coverage Working-Set State v2 eliminated the memory churn observed
in Calibration 005: semantic evictions fell from 140 to zero and automatic
re-fetches from one to zero. That mechanical success did not improve action
efficiency. All five supported semantic cells again exhausted twelve turns
without a terminal submission, hidden Pass@1 remained 0/5, semantic total
tokens rose 1.60%, and semantic estimated cost rose 4.71%. The result rejects
the narrow hypothesis that coverage-preserving state alone would make the
agent converge. It does not reject semantic IR. The next red test is explicit
progress and terminal-budget control in the agent ISA.**

Calibration 006 executed all twelve scheduled cells under freeze
`0672b13b493a2f47bad56074f9b75d1a01bd8042b3a347a9245bcbf4c8996462`.
Eleven cells called the locked model; the unsupported semantic cell remained a
zero-call local result. The evidence lock contains 333 files with tree digest
`1753ad3b220b0016e38a39673109375e78995561d50cb2f9c3d2a0cd1c91b5d1`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 128 |
| Input tokens | 412,320 |
| Output tokens | 35,991 |
| Total tokens | 448,311 |
| Estimated cost | USD 1.776825 |
| Public evaluator runs | 3 |
| Repair cycles | 5 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 128 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. Provider usage, cell costs, schedule
identities, launch and freeze bindings, the exact shared `x` tool, compacted
message roles, and the artifact lock reconcile. Request and evidence scans
found no reference, hidden-evaluator, keychain identity, bearer token, or
credential-shaped value.

The account-level Amazon Bedrock retention mode remains unreadable by the
inference-scoped credential and is not claimed. The launch records the current
public service-policy basis and this limitation.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 1 | 0 |
| Supported-task hidden Pass@1, denominator 5 | 1 | 0 |
| Semantic applicability | — | 5 / 6 |
| Provider requests, all-task accounting | 68 | 60 |
| Input tokens, all-task accounting | 152,895 | 259,425 |
| Output tokens, all-task accounting | 16,578 | 19,413 |
| Total tokens, all-task accounting | 169,473 | 278,838 |
| Estimated cost, all-task accounting | USD 0.707355 | USD 1.069470 |

The automatic unsupported semantic cell costs zero, so the all-task resource
comparison understates the semantic overhead. Across only the five supported
pairs:

| Supported-task resource | Source | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Provider requests | 56 | 60 | +7.1% |
| Input tokens | 132,501 | 259,425 | +95.8% |
| Output tokens | 14,228 | 19,413 | +36.4% |
| Total tokens | 146,729 | 278,838 | +90.0% |
| Estimated cost | USD 0.610923 | USD 1.069470 | +75.1% |
| Sum of cell durations | 240.95 s | 437.38 s | +81.5% |

## What coverage state changed

Calibration 005 stored inspected semantic handles in a capacity-two
handle-level LRU. Calibration 006 replaced only that post-turn-one semantic
memory projection with maximal non-overlapping coverage roots. The source
memory, task and context bytes, tool schema, model, sampling, limits, schedule,
accounting, and stopping rule remained locked.

| Semantic measure | Calibration 005 | Calibration 006 | Change |
| --- | ---: | ---: | ---: |
| Provider requests | 60 | 60 | 0.0% |
| Input tokens | 257,941 | 259,425 | +0.58% |
| Output tokens | 16,502 | 19,413 | +17.64% |
| Total tokens | 274,443 | 278,838 | +1.60% |
| Estimated cost | USD 1.021353 | USD 1.069470 | +4.71% |
| Sum of cell durations | 397.13 s | 437.38 s | +10.13% |
| Model-visible state bytes | 451,010 | 461,112 | +2.24% |
| Canonical request bytes | 721,215 | 733,079 | +1.64% |
| Working-set evictions | 140 | 0 | -100% |
| Automatic re-fetches | 1 | 0 | -100% |
| Receipt-only inspections | not available | 47 | — |

The provider trace therefore agrees with the local replay on the mechanism:
coverage roots preserve already observed subtrees without eviction and make
reinspection cheap at the tool-result layer. The realized model-visible state
was slightly larger, not smaller. The model used the recovered capacity to
inspect more coherently, but not to finish.

Because the trajectories are independently sampled, token and outcome deltas
are realized run differences, not a controlled causal decomposition. This is
visible in the unchanged source arm: it passed three tasks in Calibration 005
but only one in Calibration 006. That variation is direct evidence against
assigning hidden-pass changes solely to the semantic memory treatment.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | Turn-limit failure | Turn-limit failure |
| Normalization policy | Turn-limit failure | Turn-limit failure |
| Raw-ID retry | Turn-limit failure | Turn-limit failure |
| Reserved-ID guard | Hidden pass | Turn-limit failure |
| Directory fallback | Turn-limit failure | Turn-limit failure |
| Cross-module rename | Turn-limit failure | Unsupported by construction |

The five supported semantic cells emitted 52 `I` instructions over 60 provider
turns. They recorded 47 receipt-only reinspections, zero evictions, zero
automatic re-fetches, and zero width failures. They also emitted six `S`
attempts, but none reached `F`; all five exhausted the turn budget. The source
arm reached one valid terminal and five turn-limit failures.

## Interpretation

The experiment makes the distinction between representation and control flow
sharper:

1. **Coverage state works as memory infrastructure.** The candidate removed
   the precise eviction/re-fetch churn it was designed to remove.
2. **Memory coherence does not imply task convergence.** The model continued
   observing until the turn budget expired.
3. **An agent ISA needs progress semantics.** A compact state can say what is
   known while still failing to say when observation must yield to mutation,
   validation, and finish.

The result is a clean Experimental-TDD failure. The infrastructure assertion
turned green; the behavioral assertion stayed red. The useful conclusion is
not “semantic IR failed,” but “semantic persistence and agent control flow
cannot be optimized independently.”

## Interpretation boundary

- Calibration 006 reuses the exact Calibration 005 instances to isolate the
  semantic memory-policy change. It is not a fresh benchmark.
- This is one unreplicated schedule over six family-derived tasks and one model
  endpoint.
- Provider-native model identity is verified; model weights are not
  cryptographically pinned.
- Hidden Pass@1 is descriptive, not a powered statistical comparison.
- Independent sampling means run-to-run outcome differences cannot be assigned
  solely to the memory policy.
- Turn-limit failures conflate observation choice, mutation, repair, and budget
  awareness.

No cell will be replaced or rerun under this freeze. Both inferential and
general efficacy claims remain unauthorized.

## The next red test

Before another provider launch, replay Calibration 006 locally and make turn
spending observable. The next candidate should add an explicit progress state
to the session ISA, including at least:

- remaining model turns and mutation/evaluation budgets;
- the current phase (`observe`, `mutate`, `validate`, or `finish`);
- evidence that justifies another inspection rather than a submission;
- a deterministic terminal reserve that prevents the last available turn from
  being consumed by observation.

The next hypothesis is:

`a bounded semantic state needs a bounded action protocol that preserves a
terminal opportunity`.
