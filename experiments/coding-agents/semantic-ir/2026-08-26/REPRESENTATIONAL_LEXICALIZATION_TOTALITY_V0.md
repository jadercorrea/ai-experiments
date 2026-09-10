# Representational lexicalization totality v0

Status: `cohort_totality_proved_call_free`

## Why this proof exists

Confirmatory canary 002 exposed a legal participant trajectory that the local
reference replay had never taken. An inspection of a call argument produced
the scalar slot label `arguments[0]`; the opaque codec had no corresponding
word and stopped before turn four.

The failure showed that reference-trajectory coverage is weaker than protocol
coverage. A codec used as an experimental treatment must be total over every
observation the frozen ISA permits a participant to request.

## TDD result

The first exhaustive test inspected every reachable node in every one of the
240 frozen tasks and attempted all four realization conditions. Before the
fix, all 240 tasks reproduced the same missing-label failure.

The historical codec remains unchanged because its digest is evidence in
earlier freezes. A successor codec adds exactly one lexical entry:

- meaningful: `arguments[0]`
- opaque: `k32`

The exhaustive test then passed.

## Coverage

- frozen tasks: `240`
- mechanism families: `5`
- reachable semantic nodes: `3,552`
- nodes per task: `14` to `15`
- realization conditions per task: `4`
- encode/decode round trips: `960/960`
- lexical-skeleton comparisons: `480/480`
- provider requests: `0`
- provider cost: `USD 0`

All nine observed slot labels, all eight semantic operations, all three scope
field labels, all observation keys, and the compact-inspection schema value are
present in the successor codebook. Every decoded result equals the canonical
inspection bytes, and meaningful versus opaque realizations normalize to the
same surface within each packaging condition.

The result and all 240 per-task proof records are retained under
`construction/representational-lexicalization-totality-v0/`. Its artifact lock
contains the result and evaluator-only codebook.

## Claim boundary

This proves totality only for the complete observation space reachable in the
already frozen 240-task cohort, catalog, inspection schema, and semantic AST
operations. It does not prove totality for a future catalog with additional
argument positions, a new AST operation, another observation schema, or an
unbounded future language.

It also says nothing about participant behavior. The failed canary remains
infrastructure-invalid and must not be retried.

## Next red test

Freeze a successor runtime that imports the versioned codec, binds its exact
dependencies, and passes a complete provider-free replay. Only then may a new
non-adaptive canary plan select the next immutable schedule cell. Neither prior
failed cell may be retried, and no provider call is authorized by this proof.
