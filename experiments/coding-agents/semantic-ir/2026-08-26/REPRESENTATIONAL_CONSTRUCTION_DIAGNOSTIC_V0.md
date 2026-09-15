# Representational construction diagnostic v0

## Status

**A provider-free, content-bound construction freeze reproduces the three
submission-validation failures in canary 003 and projects structured diagnostics
through the existing reduced session state. All historical dispatch outcomes,
workspace state, and mutation counters remain unchanged. External launch is
blocked.**

This checkpoint answers the [next red test](REPRESENTATIONAL_CONFIRMATORY_CANARY_003.md#next-red-test)
left by canary 003. The canary observation and artifact lock are loaded and
verified; neither is regenerated. Protocols v1/v2 and their launch records remain
historical evidence. The diagnostic memory is a local successor construction,
not a participant treatment or a modified canary runner.

## Diagnosed rejection frontiers

| Turn | Code | Participant path | Expected | Observed | Added state bytes |
| ---: | --- | --- | --- | --- | ---: |
| 6 | `S_OPERATION_ARITY` | `/a/2/0` | Five operation fields | Six fields | 349 |
| 7 | `MOTION_PATCH_ID_PATTERN` | `/a/0` | Namespaced patch ID pattern | `p01` | 391 |
| 8 | `MOTION_ROOT_PATTERN` | `/a/2/0/2` | Motion reference pattern `^r[0-9]+$` | `n8` | 386 |

Each diagnostic carries a version, stable error code, structural path into the
submitted `S` instruction, expected production, bounded observed value,
reference to the frozen grammar, and recoverability. The historical prose
message and `submission_validation` category are still present in the error
object. The decoder and Motion JSON Schema are rerun on the submitted object to
derive the fields; the new code refuses to manufacture a diagnostic when the
original rejection and its grammar check disagree.

The byte figures compare canonical reduced-state snapshots immediately after
each rejection under the historical memory and diagnostic memory. They are
local payload measurements, **not provider token measurements**. The diagnostic
replaces the latest unresolved failure as before; it does not append an error
history to each future request.

## Replay and preservation gate

The local replay executes turns 1–8 of the immutable canary-003 tool transcript
twice in fresh task workspaces: once with protocol-v2 memory and once with
diagnostic memory. After removing only the new diagnostic field, each dispatch
record is canonically byte-identical to its historical counterpart. At turns
6–8, the complete state round-trips through `SESSION_STATE/v1` request
construction and contains no condition identifier.

Both paths end the replay prefix with three submission attempts, three
submission-validation rejections, zero applied mutations, zero public
evaluations, and the same workspace tree digest. The freeze binds hashes of the
diagnostic code and schemas, the ISA and Motion grammars, historical protocol
modules, selected task lock, canary transcript, and canary artifact lock. Its
builder rebuilds and verifies the artifact without
calling a model, accessing a credential, or writing to historical observations.

## Claim boundary

The v0 vocabulary covers **these three observed construction errors**. It does
not prove that every invalid Motion operation is diagnosed, that every legal
action is constructible by the participant, or that a structured diagnostic
would have changed canary 003's outcome. Unsupported or mismatched errors fail
closed in this local construction. No comparison between lexicalization or
packaging treatments has been run. Sequences 1–3 remain immutable observations;
957 schedule cells remain blocked.

## Evidence

- [`freeze.json`](construction/representational-construction-diagnostic-v0/freeze.json)
  binds source hashes, three diagnostic records, local state bytes, accounting,
  and blocked launch.
- [`representational-construction-diagnostic-v0.schema.json`](protocol/representational-construction-diagnostic-v0.schema.json)
  defines the bounded diagnostic object.
- [`representational-construction-diagnostic-freeze-v0.schema.json`](protocol/representational-construction-diagnostic-freeze-v0.schema.json)
  defines the provider-free construction artifact.
- [`representational_construction_diagnostic_v0.py`](scripts/representational_construction_diagnostic_v0.py)
  derives diagnostics and places them in reduced memory.
- [`build_representational_construction_diagnostic_v0.py`](scripts/build_representational_construction_diagnostic_v0.py)
  reproduces the canary prefix and verifies the freeze.
- [`test_representational_construction_diagnostic_v0.py`](../../../../tests/test_representational_construction_diagnostic_v0.py)
  checks the exact three frontiers, state round-trips, accounting, leak
  exclusion, unsupported-error refusal, and rebuild.

## Next red test

Expand the construction-diagnostic vocabulary beyond the three canary examples
using a frozen grammar-coverage corpus. Every covered invalid action should
return a finite diagnostic; legal actions should still pass the same validator.
Then integrate that vocabulary into a versioned participant runtime and replay
the frozen reference trajectories and historical rejections without changing
their outcome accounting. A new external canary would require the next immutable
schedule cell and its own content-bound authorization.
