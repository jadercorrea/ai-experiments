# Representational confirmatory protocol freeze v2

## Status

**The lexically total observation codec is now integrated into a successor
confirmatory runtime. All 960 frozen cells pass both full-node codec inspection
and provider-free reference replay. External launch remains blocked.**

This checkpoint answers the red test produced by Representational
Lexicalization Totality v0. It does not reinterpret or overwrite either
confirmatory canary. The protocol v1 runtime, both canary launch records, and
all recorded Bedrock responses remain frozen as historical evidence.

## Versioned runtime delta

Protocol v2 inherits the protocol v1 Session ISA, current-state reducer,
validation ordering, and separated accounting. Its sole semantic delta is the
observation codec:

```text
representational_observation_codec_v0
  → representational_observation_codec_v1
  → opaque label arguments[0] becomes k32
```

The meaningful surface remains unchanged. The opaque surface no longer fails
on the positional slot reached by canary 002. The historical codec is not
modified.

## Full-node integration probe

Each of the 960 immutable schedule cells received one legal inspection over
every node reachable from its task outline. The runtime then decoded the
condition-specific observation back to canonical inspection bytes.

- 960/960 full-node inspections round-tripped;
- 3,552 unique nodes were covered across the 240 tasks;
- `arguments[0]` was encoded in every applicable opaque realization;
- zero opaque realizations exposed the meaningful positional label; and
- all decoded inspections matched their canonical form.

This is a runtime-level integration check, not only a codec unit proof.

## Provider-free reference replay

The frozen condition-agnostic reference trajectory was executed through the
successor runtime in a fresh temporary workspace for each cell:

- 960/960 initial request digests matched the frozen cohort;
- 960/960 reference trajectories passed;
- 1,920 reduced-state requests were built;
- 960 submissions produced 960 applied mutations;
- zero instruction, validation, or mutation-budget rejections occurred;
- 960/960 public and 960/960 post-finish hidden evaluations passed;
- zero hidden evaluations occurred before finish;
- zero condition-label leaks were found; and
- program, workspace, public evidence, hidden evidence, and terminal reduced
  state were equivalent across all four conditions in all 240 tasks.

No provider request was made and no cost was incurred.

## Decision record

**Context:** totality was proven for the successor codec, but the confirmatory
runner still used the historical codec that failed canary 002.

**Options:** mutate protocol v1; insert a canary-only patch; or integrate the
successor codec into a versioned runtime and replay the complete frozen
schedule locally.

**Decision:** preserve protocol v1, introduce protocol v2 with the codec as its
only semantic delta, bind it to the totality proof, and require both all-node
inspection and full reference replay before considering another canary.

**Consequences:** the known lexical hole is closed without rewriting evidence,
and the full local protocol is green. Because the participant-visible opaque
language changed, prior launch authority cannot transfer to v2.

## Claim boundary

- The successor runtime is proven compatible with the frozen cohort and
  grammar under exhaustive reachable-node inspection and deterministic
  reference replay.
- Totality is not claimed for future ASTs, schemas, catalogs, positional
  arities, or model-generated trajectories outside the frozen reachable set.
- No behavioral participant response was generated.
- No representational efficacy or generalization claim is supported.
- No provider execution is authorized.

## Evidence

- [`freeze.json`](construction/representational-confirmatory-protocol-freeze-v2/freeze.json)
  binds the successor runtime, source freezes, gates, and claim boundary.
- [`preflight/result.json`](construction/representational-confirmatory-protocol-freeze-v2/preflight/result.json)
  records all 960 integration probes and reference replays.
- [`representational_confirmatory_protocol_v2.py`](scripts/representational_confirmatory_protocol_v2.py)
  implements the versioned runtime delta.
- [`build_representational_confirmatory_protocol_freeze_v2.py`](scripts/build_representational_confirmatory_protocol_freeze_v2.py)
  builds and verifies the content-locked provider-free artifact.
- [`test_representational_confirmatory_protocol_freeze_v2.py`](../../../../tests/test_representational_confirmatory_protocol_freeze_v2.py)
  verifies the integration, replay, schema, lock, and reproducible rebuild.

## Next red test

Bind a new behavior-blind canary plan to immutable schedule sequence 3 under
protocol v2. Canary 001 and canary 002 have no retry authority. The plan must
have its own content-bound launch record and explicit external authorization;
the other 957 cells remain blocked.
