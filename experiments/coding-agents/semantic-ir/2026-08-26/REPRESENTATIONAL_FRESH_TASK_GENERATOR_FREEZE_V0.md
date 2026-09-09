# Representational fresh-task generator freeze v0

## Status

**The deterministic five-family generator is implemented and content locked;
the task cohort is not materialized.** It generated all 1,920 predeclared
candidate blueprints in memory, found 1,920 distinct byte digests and 1,920
distinct semantic-task signatures, and semantically validated one attempt-zero
representative from each of the 60 family profiles.

No participant repository, participant context, condition realization, provider
request, or model output was created. The claim remains construction-only.

## What the generator produces

For one frozen `(slot, attempt)` pair, the pure generator returns a complete
semantic blueprint containing:

- a typed and effect-checked program IR v2 baseline;
- a transactional semantic patch with program and subtree preconditions;
- a participant objective;
- a public/hidden evaluator plan over values and ordered effect traces;
- the selected family profile and its semantic contract; and
- stable task, program, node, symbol, literal, and evaluator identities derived
  from the frozen construction seed.

Generation writes nothing. A later materializer will project the IR to a
repository, create participant-visible context and executable evaluator files,
and build the four observation realizations. Keeping these stages separate lets
the experiment test the semantic population before it creates persistent task
subjects.

## Profile design

Each family contains twelve profiles formed by one three-level axis and two
two-level axes. Four consecutive slots share a profile and occupy the four
different counterbalance sequences. Task-profile variation is therefore crossed
with, rather than confounded by, execution order.

| Family | Three-level axis | First two-level axis | Second two-level axis |
| --- | --- | --- | --- |
| Capability fallback | Identifier shape | Normalized/raw fallback argument | Public hit/miss focus |
| Error/option taxonomy | Identifier shape | Trim/preserve baseline | Public empty/missing focus |
| Guarded retry | Identifier shape | Retry when raw differs/matches | Public retry hit/miss focus |
| Identity/state | Replacement target depth | Program/target stale probe | Public reserved hit/miss focus |
| Pure normalization | Identifier shape | Raw-to-trim/trim-to-raw | Public padded/whitespace focus |

Condition order is not an input to candidate generation. The slot identity is
used only through its already frozen attempt seed and profile position; changing
the condition-order field leaves the candidate bytes unchanged.

## Executable semantic validation

The freeze validates one attempt-zero candidate for every family/profile pair,
60 candidates in total. Each must establish all of the following:

1. the baseline validates under program IR v2 and projects deterministically to
   TypeScript;
2. the reference patch applies transactionally and produces a different valid
   program and TypeScript projection;
3. the reference passes every public and hidden value/effect case;
4. the baseline is rejected by at least one public and one hidden case; and
5. a valid but stale base-program state rejects the frozen patch.

The five first family slots are also retained as compact smoke vectors in the
artifact. These are validation summaries and digests, not persisted tasks.

## Exhaustive call-free audit

All eight attempts for all 240 slots are generated in the frozen order. The
audit records:

| Measure | Result |
| --- | ---: |
| Blueprints generated in memory | 1,920 |
| Unique blueprint digests | 1,920 |
| Unique semantic signatures | 1,920 |
| Unique candidate/program identities | 1,920 / 1,920 |
| Blueprints per family | 384 |
| Persisted candidate files | 0 |
| Model/provider calls | 0 |

The ordered digest stream makes a future generator or runtime change visible.
Uniqueness includes task literals and evaluator inputs; it does not claim 1,920
independent algorithmic mechanisms. The target population remains a balanced
synthetic mechanism population, not an estimate of real-world task prevalence.

## Family invariants

- Capability fallback preserves ordered `users.get_by_id` then
  `directory.get_by_id` effects and lazy short-circuiting.
- Error/option taxonomy keeps absence (`None`), typed failure (`error`), and
  successful value (`ok`) distinct.
- Guarded retry permits at most two lookups and makes the second conditional on
  explicit `string.equals` control flow.
- Identity/state variants preserve the selected node identity and require both
  base-program and target-subtree preconditions.
- Pure normalization introduces no effect and varies only deterministic
  dataflow through `string.trim_ascii`.

## Remaining red gates

- No task repository or participant-visible context exists.
- The complete local eligibility pipeline has not run on persisted subjects.
- Four-condition round-trip equivalence has not been checked on fresh task
  observations.
- There are no participant bytes for contamination comparison.
- The model, inference policy, request bytes, cost ceiling, execution freeze,
  launch, and authorization remain unset.

## Evidence

- [`generator.json`](construction/representational-fresh-task-generator-freeze-v0/generator.json)
  records the profiles, exhaustive digest stream, 60 validation vectors, gates,
  limitations, and claim boundary.
- [`representational_fresh_task_generator.py`](scripts/representational_fresh_task_generator.py)
  implements the side-effect-free generator and executable validator.
- [`build_representational_fresh_task_generator_freeze.py`](scripts/build_representational_fresh_task_generator_freeze.py)
  verifies the preceding protocol and runtime dependencies, audits all outputs,
  and seals the artifact.
- [`test_representational_fresh_task_generator_freeze_v0.py`](../../../../tests/test_representational_fresh_task_generator_freeze_v0.py)
  proves family behavior, seed binding, profile/sequence crossing, downstream red
  gates, no task files, and byte-deterministic reconstruction.

## Next red test

Materialize one predeclared attempt-zero smoke task per family and run the whole
local eligibility pipeline: baseline/reference evaluator discrimination,
participant isolation, four-condition canonical equivalence, duplicate checks,
and a provisional contamination inventory. This remains provider-free.
