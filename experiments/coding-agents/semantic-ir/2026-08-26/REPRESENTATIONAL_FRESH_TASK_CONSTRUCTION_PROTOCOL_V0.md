# Representational fresh-task construction protocol v0

## Status

**Protocol frozen; 240 task slots and 1,920 deterministic attempts are sealed,
but no fresh task has been materialized.** The artifact fixes family quotas,
four-period counterbalancing, candidate order, rejection behavior, equivalence
requirements, evaluator isolation, contamination checks, and the boundary
between task construction and participant execution.

This freeze made no model call, sent no provider request, and incurred no
provider cost. It is a pre-construction commitment, not task evidence or a
behavioral result.

## What is frozen

Finite-sample simulation selected 240 fresh task units. Protocol v0 turns that
number into named experimental slots:

| Mechanism family | Definition | Slots |
| --- | --- | ---: |
| `capability_lookup_fallback` | Declared effectful lookup with ordered lazy fallback | 48 |
| `error_option_taxonomy` | Distinguish absence, typed failure, and successful value | 48 |
| `guarded_retry_control_flow` | Bounded retry or fallback selected by an explicit guard | 48 |
| `identity_state_consistency` | Stable target identity and stale-state protection during mutation | 48 |
| `pure_dataflow_normalization` | Deterministic validation or normalization without external effects | 48 |

Every family assigns twelve slots to each of the four already selected
counterbalance sequences. Each condition consequently occurs equally often in
each execution period, and every sequence receives 60 tasks overall.

The slot is the experimental unit. Its four condition requests are dependent
realizations of one task, not four independent observations.

## Construction is deterministic and separate from participation

The task-construction generator is deliberately specified as non-LLM and
deterministic. It may consume only a frozen slot identity, family definition,
attempt seed, and the already frozen Session ISA and semantic inspection
vocabulary. Its implementation must itself be tested and content locked before
the first task is produced.

This avoids introducing an unmeasured task-generator model whose lexical or
semantic preferences could shape the population being used to test lexical and
structural effects. It also separates two roles:

- the **construction generator** creates candidate repositories, requirements,
  canonical observations, references, and evaluators locally; and
- the future **participant model** attempts each accepted task under all four
  conditions.

The participant model is not selected in this artifact. Before launch, one
exact model identity and one inference policy must be frozen and used unchanged
across all four conditions. Every condition receives a fresh independent
context; cross-condition transcript or memory reuse is forbidden. The balanced
sequence controls execution order without creating conversational carryover. No
provider execution is authorized here.

## Non-adaptive candidate rule

Each slot receives eight ordered attempt seeds derived from base seed
`24121980`, the slot identity, and the attempt index through domain-separated
SHA-256. The constructor must evaluate attempts from zero through seven and
accept only the first candidate satisfying every eligibility gate.

Rejected candidates and machine-readable reasons remain evidence. Manual
substitution, family reallocation, and skipping an eligible candidate are
forbidden. If all eight attempts fail, construction blocks. The experiment may
not respond by changing the family, quota, template, vocabulary, or acceptance
criteria.

This is the construction analogue of leaving a TDD test red: failure remains
visible and drives an explicit new design decision rather than disappearing
through a convenient replacement.

## Eligibility pipeline

A candidate can occupy its slot only after this ordered pipeline passes:

1. materialize it from the content-locked family generator and assigned seed;
2. reject it if it requires an unplanned Session ISA or vocabulary extension;
3. show locally that the baseline fails while the reference solution passes
   both public and hidden evaluators;
4. encode all four treatments, decode each to the same canonical bytes, and
   establish lexical-skeleton equality within each packaging condition;
5. prove participant bytes exclude references, hidden evaluators, condition
   labels, and the evaluator-only codebook;
6. reject exact participant-byte or canonical-task-signature duplication
   against historical provider requests and accepted fresh slots; and
7. content lock the task, evaluator, four realizations, and audit evidence.

The first five provider-exposed construction fixtures remain useful codec
coverage but are prohibited as confirmatory tasks.

## Treatment boundary

Only the semantic inspection result realization varies:

| Factor | Levels |
| --- | --- |
| Lexicon | meaningful, opaque |
| Packaging | nested, table |

The task requirement, repository, outline and handle interface, Session ISA,
mutation backend, capabilities and effects, public and hidden evaluators,
future model and inference policy, tools, budgets, stopping rule, and accounting
remain fixed within a task.

All four representations must round-trip to one byte-identical canonical
observation. Meaningful and opaque surfaces must also have identical normalized
lexical skeletons within a packaging level. These are construction gates, not
empirical outcomes.

## What this artifact does not establish

- The family-specific construction generator is not implemented or locked.
- None of the 240 tasks or 960 condition realizations exists.
- No evaluator has been validated on a fresh task.
- No contamination or duplicate audit has run.
- No cost ceiling, participant-model freeze, launch artifact, or authorization
  exists.
- No behavioral, lexical, packaging, interaction, prevalence, or
  generalization claim follows from this protocol.

## Evidence

- [`protocol.json`](construction/representational-fresh-task-construction-protocol-v0/protocol.json)
  is the canonical slot and gate freeze.
- [`build_representational_fresh_task_construction_protocol.py`](scripts/build_representational_fresh_task_construction_protocol.py)
  verifies all source locks and deterministically emits the protocol.
- [`test_representational_fresh_task_construction_protocol_v0.py`](../../../../tests/test_representational_fresh_task_construction_protocol_v0.py)
  proves slot counts, within-family balance, stable attempt seeds, role
  separation, red downstream gates, and byte-deterministic reconstruction.
- [`REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_OBSERVATION_V0.md`](REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_OBSERVATION_V0.md)
  records why the selected count is 240.

## Next red test

The deterministic five-family generator is now implemented and content locked.
It audited all 1,920 blueprints in memory and semantically validated all 60
family profiles without materializing the cohort. The next red test is a
persisted five-task local smoke cohort, one predeclared attempt-zero slot per
family. See
[`REPRESENTATIONAL_FRESH_TASK_GENERATOR_FREEZE_V0.md`](REPRESENTATIONAL_FRESH_TASK_GENERATOR_FREEZE_V0.md).
