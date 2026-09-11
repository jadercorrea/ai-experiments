# Representational confirmatory protocol freeze v1

## Status

**Validation errors are now accounted separately from applied candidate
mutations, and post-turn context is now a canonical current-state projection
rather than an append-only typed action log. All 960 confirmatory cells pass a
provider-free reference replay. External launch remains blocked.**

This checkpoint answers the two red tests produced by confirmatory canary 001.
It does not reinterpret or overwrite that observation. The v0 runtime, its
launch record, and all 12 Bedrock responses remain frozen as evidence of the
failure that motivated v1.

## Separated accounting

The runtime now records five distinct quantities:

| Counter | Meaning |
| --- | --- |
| `submission_attempts` | Every `S` envelope that reaches Motion decoding |
| `instruction_rejections` | Invalid outer Session ISA or dispatch requests |
| `submission_validation_rejections` | Invalid Motion grammar, capability, scope, type, effect, or atomicity precondition |
| `mutation_budget_rejections` | A submission resolved as valid but blocked before application |
| `applied_mutations` | A candidate successfully applied and projected into the workspace |

The validation order is now explicit:

```text
Session ISA validation
  → Motion decode
  → capability/type/effect resolution
  → applied-mutation budget
  → atomic application
  → workspace projection
```

This ordering matters. Even after the applied-mutation budget is full, an
invalid state token is classified as a submission validation rejection. A
budget rejection is reserved for a submission that was first resolved as
valid. Representation failures can no longer consume the applied-mutation
budget.

## Canonical reduced state

`SESSION_STATE/v1` contains no `actions` array. It projects the current
participant-visible state into fixed semantic slots:

- context index and latest read per context handle;
- latest semantic inspection;
- workspace index and latest read per workspace path;
- latest accepted submission;
- latest public evaluation;
- terminal state;
- the latest unresolved failure; and
- aggregate outcome and budget counters.

Repeated reads replace the value at their stable handle or path. A new
inspection replaces the preceding inspection. A newer rejection replaces the
previous unresolved failure; successful recovery by the same opcode clears
it. An accepted submission conservatively evicts target-token-bearing
inspection data, candidate-specific workspace reads, and any public evaluation
of the preceding candidate.

This is a state reducer, not a more compact transcript encoding.

## Canary 001 counterfactual replay

The exact twelve recorded instruction turns from canary 001 were replayed
offline through v1. No model response was changed or regenerated.

Under v0, three malformed Motion submissions consumed all three mutation
attempts, and the final well-formed submission was rejected. Under v1, the
same recorded instructions produce:

- 4 submission attempts;
- 1 outer instruction rejection;
- 3 submission validation rejections;
- 0 mutation-budget rejections;
- 1 applied mutation; and
- acceptance of the submission recorded in turn 12.

The unresolved failure frontier is cleared by that accepted submission. The
replay does not turn canary 001 into a behavioral success: the recorded model
never had a thirteenth turn in which to evaluate or issue `F`. It isolates the
effect of the accounting correction without inventing new behavior.

## Replacement-semantics probe

One large three-target inspection was observed twenty times by the reducer.
The canonical state measured:

- 10,586 bytes after the first observation;
- 10,589 bytes after the twentieth observation; and
- 3 bytes of total growth, caused only by wider turn and count numerals.

An append-only representation would have retained twenty copies of the
inspection. V1 retains one current inspection plus a scalar count.

## Full provider-free replay

The same condition-agnostic reference trajectory was then executed across the
immutable 240-task, four-condition schedule:

- 960/960 initial requests matched their frozen digests;
- 960/960 reference trajectories passed;
- 1,920 reduced-state requests were constructed;
- zero append-only action lists were found;
- zero condition-label leaks were found;
- 960 submission attempts produced 960 applied mutations;
- zero instruction, submission-validation, or mutation-budget rejections;
- 960/960 public evaluations passed;
- 960/960 hidden evaluations passed after `F`;
- zero hidden evaluations occurred before `F`; and
- final program, workspace, public evidence, hidden evidence, and terminal
  reduced state were equivalent across all four conditions in all 240 tasks.

No provider request was made and no cost was incurred.

## Decision record

**Context:** canary 001 showed that provider schema admission does not prevent
malformed tool calls, and that the typed action list grew like a transcript.

**Options:** increase the mutation budget; retain the action list but compress
it; or correct the semantic boundaries.

**Decision:** keep the experimental limits, make validation and mutation
accounting disjoint, and replace historical accumulation with canonical
current state.

**Consequences:** v1 preserves recoverable evidence without charging syntax
errors as applied candidates, and repeated observations have constant storage.
It also changes the participant context after turn one. Therefore it is a new
protocol version and cannot inherit canary 001's external authorization.

## Claim boundary

- The accounting and reducer invariants are proven locally.
- The exact v0 canary trajectory has one successful counterfactual mutation
  under v1; no counterfactual model continuation is claimed.
- No new behavioral participant response was generated.
- No lexicalization, packaging, interaction, efficacy, or generalization claim
  is supported.
- The remaining confirmatory campaign is not authorized.

## Evidence

- [`freeze.json`](construction/representational-confirmatory-protocol-freeze-v1/freeze.json)
  binds the v1 contracts, gates, dependencies, and claim boundary.
- [`preflight/result.json`](construction/representational-confirmatory-protocol-freeze-v1/preflight/result.json)
  records the 960 cell replays, counterfactual canary replay, and replacement
  probe.
- [`representational_confirmatory_protocol_v1.py`](scripts/representational_confirmatory_protocol_v1.py)
  implements separated accounting and current-state reduction.
- [`build_representational_confirmatory_protocol_freeze_v1.py`](scripts/build_representational_confirmatory_protocol_freeze_v1.py)
  builds and verifies the content-locked provider-free artifact.
- [`test_representational_confirmatory_protocol_v1.py`](../../../../tests/test_representational_confirmatory_protocol_v1.py)
  exercises error classification, budget ordering, recovery, and replacement
  semantics.
- [`test_representational_confirmatory_protocol_freeze_v1.py`](../../../../tests/test_representational_confirmatory_protocol_freeze_v1.py)
  verifies the full replay and deterministic rebuild.

## Next red test

Build a new one-cell provider canary for protocol v1. It must use a new cell,
a new launch record, and new explicit authorization. Canary 001 has no retry
authority, and its observed behavior may not select the replacement cell. The
other confirmatory cells remain blocked until that canary is evaluated under a
predeclared behavior-blind operational gate.
