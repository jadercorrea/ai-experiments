# Representational construction diagnostic grammar v1

## Status

**A provider-free grammar corpus now expands the diagnostic vocabulary from the
three canary-003 failures to twenty single-defect invalid actions and one valid
control. All twenty failures produce a bounded diagnostic both immediately and
through reduced state; the valid control passes the same grammar. No mutation,
provider request, or external launch is authorized.**

This checkpoint answers the next red test from
[Construction Diagnostic v0](REPRESENTATIONAL_CONSTRUCTION_DIAGNOSTIC_V0.md#next-red-test).
It retains v0 and the canary-003 observation unchanged. The new v1 object is a
successor grammar representation and remains outside the participant runtime.

## Frozen corpus

The corpus applies one declarative mutation at a time to the sealed reference
submission for `capability_lookup_fallback-001`. Its 21 cases sample four
validation frontiers:

| Frontier | Invalid cases | Examples |
| --- | ---: | --- |
| Session instruction schema | 4 | missing arguments, extra property, unknown opcode, wrong argument type |
| Opcode-specific arity | 1 | two arguments supplied to `S` instead of three |
| Positional `S` decoding | 6 | wrong field types, empty operations, malformed operation tuple |
| Motion JSON Schema | 9 | identifier, token, target, root, and binding constraints |
| Valid control | 1 | unchanged sealed reference submission |

These are twenty frozen probes, not exhaustive coverage of every JSON Schema
keyword, every Motion graph rule, or every future grammar version. The artifact
calls each frontier *sampled* and keeps semantic resolution explicitly red.

## Diagnostic contract

Each failure is reconstructed from the exact submitted instruction and the
frozen grammar. The diagnostic contains:

- a stable code;
- a JSON Pointer into the participant's `S` instruction;
- the expected production and bounded observed value;
- a reference to the Session ISA rule or Motion schema path; and
- a recoverability flag.

The corpus produces 19 distinct codes. `MOTION_TARGET_PATTERN` occurs twice,
once for the handle and once for its capability token. Five cases are classified
as instruction validation and fifteen as submission validation.

The error remains compatible with v0's prose fields. V1 adds the diagnostic to
the immediate tool result before the same result enters `SESSION_STATE/v1`.
Every diagnostic survives a canonical state round-trip, and no condition name
appears in participant-visible state.

## Preservation and accounting

Each invalid case executes in a fresh workspace. The grammar rejects all twenty
before application, leaving zero applied mutations. The valid control is decoded
and validated without being applied. The builder verifies the selected task
lock, rebuilds the corpus from its declarative mutations, and binds hashes for
the grammar, diagnostic code, reduced-state protocols, corpus, and schemas.

The freeze records:

- 21 total cases;
- 1 valid action accepted by the grammar;
- 20 invalid actions diagnosed immediately;
- 20 diagnostic state round-trips;
- zero unexpected outcomes;
- zero applied mutations; and
- zero provider requests.

## Claim boundary

This construction shows that the frozen v1 diagnostic vocabulary handles the
specified 20-case grammar corpus. It does not establish totality for all invalid
Session or Motion documents. It does not cover semantic failures such as stale
capabilities, unknown catalog symbols, graph sharing, scope errors, type errors,
or effect mismatches. It does not show that a model can use the diagnostics to
repair an action. All 957 unobserved confirmatory cells remain blocked.

## Evidence

- [`corpus.json`](construction/representational-construction-diagnostic-grammar-v1/corpus.json)
  freezes the 21 declarative single-defect cases and expected code/path pairs.
- [`freeze.json`](construction/representational-construction-diagnostic-grammar-v1/freeze.json)
  records coverage, code counts, source hashes, accounting, and claim limits.
- [`representational-construction-diagnostic-v1.schema.json`](protocol/representational-construction-diagnostic-v1.schema.json)
  defines the generalized bounded diagnostic object.
- [`representational-construction-diagnostic-grammar-freeze-v1.schema.json`](protocol/representational-construction-diagnostic-grammar-freeze-v1.schema.json)
  defines the provider-free coverage freeze.
- [`representational_construction_diagnostic_v1.py`](scripts/representational_construction_diagnostic_v1.py)
  derives diagnostics from the frozen grammar and projects them into state.
- [`build_representational_construction_diagnostic_grammar_v1.py`](scripts/build_representational_construction_diagnostic_grammar_v1.py)
  materializes and verifies the corpus and freeze.
- [`test_representational_construction_diagnostic_grammar_v1.py`](../../../../tests/test_representational_construction_diagnostic_grammar_v1.py)
  tests the frozen cases, immediate channel, state round-trip, schema, accounting,
  and reproducible rebuild.

## Next red test

Create a separate semantic-resolution corpus from grammar-valid submissions.
Cover stale state and target capabilities, duplicate identities and references,
unknown catalog symbols, call arity, graph reachability and sharing, binding
scope, result typing, and effect preservation. The grammar freeze must remain
green while each semantic failure gains a finite diagnostic. Only after that
should a versioned participant runtime integrate both layers for provider-free
reference and historical-rejection replay.
