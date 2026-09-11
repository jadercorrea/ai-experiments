# Coverage Working-Set State v2

## Status

**Local runtime projection complete. The coverage-aware policy is now an
executable state implementation rather than only a counterfactual replay. It
passes all five supported frozen semantic references and their hidden
evaluations, reproduces all 66 recorded dispatch results across Calibration
005's 60 semantic turns, and finishes the fixed trace with zero evictions,
automatic re-fetches, or unsatisfied submissions. Its model-visible state is
506,758 canonical bytes, 12.77% larger than the observed v1 handle LRU. No
model call was made, and no provider launch is authorized by this result.**

The implementation is parallel to the frozen v1 runtime. It does not mutate
the source files whose hashes bind Calibration 005, so the previous experiment
remains reproducible.

## What changed

`Semantic Working-Set State v1` gave each inspected handle an independent LRU
slot. `Coverage Working-Set State v2` keeps the persistent capability for every
handle but stores full subtrees only at maximal non-overlapping roots.

Each capability now exposes `covered_by`:

- the handle of its resident coverage root when its node is reconstructible;
- its own handle when it is a resident root; or
- `null` when no resident root currently covers it.

Capacity therefore counts disjoint structural regions, not serialized handles.
Repeated inspection of a covered descendant becomes a receipt. A newly
inspected ancestor coalesces resident descendants, and LRU replacement occurs
only between disjoint roots.

The state has a new schema version rather than silently changing v1:

`ai-experiments.semantic-ir.semantic-working-set-state/v2`

## Gate 1: known-reference behavior

The runtime executed the frozen semantic reference patch for every supported
task through the real semantic store, submit dispatcher, finisher, and hidden
evaluator.

| Measure | Result |
| --- | ---: |
| Supported semantic cells | 5 |
| Satisfied reference submissions | 5 |
| Hidden passes | 5 |
| Reference failures | 0 |
| Model calls | 0 |

This establishes compatibility with the five known-good semantic patches. It
does not establish that a model can discover those patches more reliably.

## Gate 2: recorded-action equivalence

The runtime then replayed the exact tool calls emitted during Calibration 005.
Before every recorded turn it produced a validated v2 state projection; every
tool call still passed through the real session dispatcher.

| Measure | Result |
| --- | ---: |
| Semantic cells | 5 |
| Recorded turns | 60 |
| Tool actions | 66 |
| Exact dispatch-result matches | 66 |
| Result mismatches | 0 |
| Automatic re-fetches | 0 |
| Model calls | 0 |

Malformed submissions are rejected at the same memory boundary and with the
same typed error as the frozen runner. Calls using another tool name cannot
trigger a semantic re-fetch.

## Runtime state result

| Measure | Observed v1 handle LRU | Executable v2 coverage state |
| --- | ---: | ---: |
| Capacity | 2 handles | 2 disjoint roots |
| Fixed-trace state bytes | 449,360 | 506,758 |
| Change | — | +12.7733% |
| Evictions | 140 | 0 |
| Automatic re-fetches | recorded policy behavior | 0 |
| Unsatisfied valid submissions | 0 | 0 |

Across the replay, v2 admitted seven roots. Forty-three inspections admitted no
new root because their targets were already structurally covered. Four cells
ended with one root; error taxonomy ended with two disjoint roots.

The executable result is 338 bytes smaller than the analytical candidate
(506,758 versus 507,096, a 0.07% reconciliation difference). The analytical
replay substituted candidate observation components into recorded v1 states;
the runtime result constructs the complete v2 state directly from replayed
events and validates it against the v2 schema.

## What this establishes

1. **The coverage policy is implementable without changing semantic dispatch.**
   The real runtime preserved all known-reference hidden outcomes and every
   recorded tool result.
2. **The churn diagnosis survives implementation.** Capacity two still
   suffices when its unit is a disjoint root, and the 140 handle-level evictions
   disappear.
3. **The cost survives implementation too.** Coherent structural state is
   larger on the fixed trace. Coverage is a progress-preservation mechanism,
   not a byte-compression result by itself.

## Claim boundary

- The reference gate uses known patches and therefore tests infrastructure,
  not model discovery.
- The action gate replays recorded model choices; counterfactual model-choice
  equivalence is false.
- Canonical UTF-8 JSON bytes are construction metrics, not provider tokens.
- No future action, hidden-evaluator feedback, or oracle enters admission or
  replacement.
- No model call or provider request occurs.
- The v2 bundle is bound to the previous matched freeze, but is not itself a
  new provider execution freeze.

## The next red test

Freeze a matched coverage-state execution that changes only the semantic memory
projection from v1 handle LRU to v2 coverage roots. The freeze must bind the new
schema, prefix, runner, capacity unit, accounting, task bytes, model, sampling,
limits, schedule, and stopping rule before any provider call.

The provider-backed question is now narrow:

`does preserving coherent structural coverage eliminate enough repeated
inspection actions to repay 12.77% more state per fixed trace?`

Until that test runs, zero evictions is an infrastructure result, not an
efficacy result.
