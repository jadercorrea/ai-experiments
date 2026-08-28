# Matched Compacted-Session calibration 005

## Status

**Execution valid and complete as a repeated within-instance descriptive
calibration. Explicit state reduced input per provider request by 37.14% against
Calibration 004 and reduced total tokens by 20.94%, despite 22.77% more
requests. It did not improve the semantic trajectory: source passed 3/6 hidden
evaluations and semantic passed 0/6. On the five supported pairs, semantic used
98.2% more total tokens and 76.7% more estimated cost than source. No
infrastructure-invalid cell occurred. The repeated instances, stochastic
trajectories, and development exposure do not authorize an inferential or
general efficacy claim.**

Calibration 005 executed all twelve scheduled cells under freeze
`4ea8b4e2d654c36ca41d62afcf22a9f9ea9351fa98effdced20974eae73a2b69`.
Eleven cells called the locked model; the unsupported semantic cell remained a
zero-call local result. The evidence lock contains 325 files with tree digest
`1df47f3077e9d64ab7e04f08512cd5f119962f6d0b6a428c458d5e68b733b52a`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 124 |
| Input tokens | 404,225 |
| Output tokens | 32,771 |
| Total tokens | 436,996 |
| Estimated cost | USD 1.704240 |
| Public evaluator runs | 5 |
| Repair cycles | 5 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 124 responses reported the locked model
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
| All-task hidden Pass@1, denominator 6 | 3 | 0 |
| Supported-task hidden Pass@1, denominator 5 | 2 | 0 |
| Semantic applicability | — | 5 / 6 |
| Provider requests, all-task accounting | 64 | 60 |
| Input tokens, all-task accounting | 146,284 | 257,941 |
| Output tokens, all-task accounting | 16,269 | 16,502 |
| Total tokens, all-task accounting | 162,553 | 274,443 |
| Estimated cost, all-task accounting | USD 0.682887 | USD 1.021353 |

The automatic unsupported semantic cell costs zero, so the all-task resource
comparison understates the semantic overhead. Across only the five supported
pairs:

| Supported-task resource | Source | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Provider requests | 52 | 60 | +15.4% |
| Input tokens | 124,919 | 257,941 | +106.5% |
| Output tokens | 13,550 | 16,502 | +21.8% |
| Total tokens | 138,469 | 274,443 | +98.2% |
| Estimated cost | USD 0.578007 | USD 1.021353 | +76.7% |
| Sum of cell durations | 241.51 s | 397.13 s | +64.4% |

## What compaction changed

Calibration 004 accumulated assistant and tool history. Calibration 005 kept
only the initial system/user messages plus one typed state projection. The task,
context, shared tool, model, sampling, limits, and schedule bytes remained
locked. The observed transport changed as follows:

| Measure | Calibration 004 | Calibration 005 | Change |
| --- | ---: | ---: | ---: |
| Provider requests | 101 | 124 | +22.77% |
| Input tokens | 523,748 | 404,225 | -22.82% |
| Input tokens/request | 5,185.62 | 3,259.88 | -37.14% |
| Output tokens | 29,007 | 32,771 | +12.98% |
| Total tokens | 552,755 | 436,996 | -20.94% |
| Estimated cost | USD 2.006349 | USD 1.704240 | -15.06% |

Source input per request fell 41.88%; semantic input per request fell 32.47%.
The central transport hypothesis therefore survived contact with provider token
accounting: replacing transcript history with typed state made each turn
materially smaller. It did not make the agent need fewer turns.

Because the trajectories are separately sampled, the aggregate deltas are not
a controlled decomposition of prompt compaction alone. They are the realized
cost of each complete locked run.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | Turn-limit failure | Turn-limit failure |
| Normalization policy | Hidden pass | Turn-limit failure |
| Raw-ID retry | Turn-limit failure | Turn-limit failure |
| Reserved-ID guard | Hidden pass | Turn-limit failure |
| Directory fallback | Turn-limit failure | Turn-limit failure |
| Cross-module rename | Hidden pass | Unsupported by construction |

The five supported semantic cells all exhausted twelve model turns without a
terminal submission. Four spent every turn inspecting semantic state and never
submitted a patch. Across the arm, the capacity-two working set recorded 140
evictions, one automatic current-target re-fetch, eight recoverable tool errors,
and zero unsatisfied width submissions. The one re-fetch, rather than the five
known-reference re-fetches, is not a replay mismatch: the model reached only one
of those reference submission paths.

Source reached three valid terminals and three turn-limit failures. Semantic
reached zero valid terminals and five turn-limit failures. This is a product
outcome, not an infrastructure failure.

## Interpretation

The experiment turns one large red test green and exposes another:

1. **Transcript compaction works as transport.** Typed state cut average input
   per request by 37.14% and total realized cost by 15.06% even though the model
   made 23 additional calls.
2. **A compact state is not automatically a usable state.** The semantic arm
   repeatedly cycled through inspections and evictions instead of converging on
   a mutation.
3. **Token efficiency and action efficiency are distinct layers.** Compression
   can make a bad trajectory cheaper without making it good.

This is why the result does not support either “state solved the agent loop” or
“semantic IR failed.” It supports a narrower conclusion: state transport is a
real optimization, while the capacity-two semantic observation policy and its
model-facing affordances are not yet sufficient.

## Interpretation boundary

- Calibration 005 reuses the exact Calibration 004 instances to isolate the
  memory-policy change. It is not a fresh benchmark.
- This is one unreplicated schedule over six family-derived tasks and one model
  endpoint.
- Provider-native model identity is verified; model weights are not
  cryptographically pinned.
- Hidden Pass@1 is descriptive, not a powered statistical comparison.
- Independent sampling means run-to-run outcome differences cannot be assigned
  solely to the memory policy.
- Turn-limit failures conflate observation choice, working-set churn, mutation,
  repair, and budget effects.

No cell will be replaced or rerun under this freeze. Both inferential and
general efficacy claims remain unauthorized.

## The next red test

The next slice should explain and constrain **semantic observation churn**
before adding more model calls. Replay the five Calibration 005 semantic
trajectories locally and measure:

- repeated inspection of already observed targets;
- eviction/reinspection cycles by node;
- state bytes spent on observations never used by a submission;
- the minimum deterministic hint or affordance that preserves non-oracular
  semantics while making progress toward `S` observable.

The new hypothesis is not merely `state must replace transcript history`; that
transport hypothesis passed its first provider test. It is:

`a semantic working set needs a progress-preserving observation policy, not
only bounded memory`.
