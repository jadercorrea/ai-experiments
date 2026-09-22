# Representational construction diagnostic: semantic resolution v2

## Status

**A provider-free, grammar-valid corpus samples semantic rejection paths after
the v1 grammar frontier. Ten rejected submissions receive bounded diagnostics
in the immediate result and in reduced state. Two controls pass. No session
mutation, provider request, or external launch is authorized.**

This checkpoint extends the [grammar v1 freeze](REPRESENTATIONAL_CONSTRUCTION_DIAGNOSTIC_GRAMMAR_V1.md)
without changing its protocol or artifacts. The successor diagnostic memory is
used only by this construction replay, not by the published participant runtime.

## Corpus and result

All twelve instructions decode as `S` and satisfy the frozen Motion JSON Schema.
Each probe starts from the same sealed reference submission. The ten negative
cases cover:

| Boundary | Rejections |
| --- | --- |
| Capability resolution | stale state token; stale target token |
| Motion resolution | duplicate operation identity; unknown catalog symbol; call arity; unknown, shared, and unreachable motion references; out-of-scope binding |
| IR validation | incompatible result type |

The diagnostic names its stage, stable code, participant JSON Pointer, bounded
expected and observed values, and the validating rule. Capability tokens are
never copied into diagnostics. The error's existing category remains
`submission_validation`; the stage identifies the internal boundary it crossed.
The ten diagnostics survive an immediate-result check and a canonical
`SESSION_STATE/v1` round-trip. The condition label does not enter the state.

The second valid control intentionally changes `users.get_by_id` to
`directory.get_by_id` in the reference motion. This changes the inferred effect
set from `db.read:users` to `network.read:directory`. It is **accepted**, not an
effect-preservation failure: the v2 applicator canonicalizes the declaration
from the resulting IR. The control computes an in-memory candidate and verifies
that the session/workspace mutation counter remains zero. This replaces the
earlier proposed “effect mismatch” negative probe with an observed rule of the
backend.

## Accounting and claim boundary

The freeze records twelve grammar-valid cases, ten semantic rejections with ten
distinct codes, two valid controls, ten immediate diagnostics, ten reduced-state
round-trips, zero unexpected outcomes, zero session mutations, and zero provider
requests. It binds the task lock, previous grammar freeze, corpus, schemas,
diagnostic implementation, and relevant resolver sources by SHA-256.

These are **corpus-bounded samples**, not a proof that every semantic rejection
has a diagnostic. In particular, multi-operation location inference, other IR
type failures, and arbitrary Motion graphs remain outside this version. The
diagnostic is derived from trusted runtime error text plus the exact submitted
instruction; it is not a model repair observation. The 957 unobserved
confirmatory cells remain blocked.

## Evidence

- [`corpus.json`](construction/representational-construction-diagnostic-semantic-v2/corpus.json)
  fixes the declarative mutations and expected codes.
- [`freeze.json`](construction/representational-construction-diagnostic-semantic-v2/freeze.json)
  records the replayed diagnostics, counts, source hashes, and limits.
- [`representational-construction-diagnostic-semantic-v2.schema.json`](protocol/representational-construction-diagnostic-semantic-v2.schema.json)
  defines the bounded diagnostic.
- [`representational-construction-diagnostic-semantic-freeze-v2.schema.json`](protocol/representational-construction-diagnostic-semantic-freeze-v2.schema.json)
  constrains the freeze.
- [`representational_construction_diagnostic_semantic_v2.py`](scripts/representational_construction_diagnostic_semantic_v2.py)
  maps covered semantic rejections into immediate and inherited state.
- [`build_representational_construction_diagnostic_semantic_v2.py`](scripts/build_representational_construction_diagnostic_semantic_v2.py)
  rebuilds and verifies the provider-free experiment.
- [`test_representational_construction_diagnostic_semantic_v2.py`](../../../../tests/test_representational_construction_diagnostic_semantic_v2.py)
  checks the fixed code/path vocabulary, schema, replay, and accounting.

## Next red test

Integrate grammar and semantic diagnostics into one versioned participant
runtime, then replay both the valid reference action and historical rejection
sequences. Only after the same runtime reproduces both should a controlled
repair probe ask whether a model uses the structured diagnostic better than
plain error prose. No cloud launch is implied by this freeze.
