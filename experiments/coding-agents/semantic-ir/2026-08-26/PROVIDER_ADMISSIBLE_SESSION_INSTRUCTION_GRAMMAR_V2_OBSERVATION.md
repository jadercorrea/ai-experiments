# Provider-Admissible Session Instruction Grammar v2 observation

## Outcome

Session Instruction Grammar v2 passes the local successor test prompted by
Provider Schema Capability Probe 001. It adds the explicit top-level
`type: object` required by the Bedrock tool-input ABI while leaving every v1
instruction branch unchanged.

The change is structurally redundant under JSON Schema Draft 2020-12: every
selected `oneOf` branch was already an object. Removing the new root declaration
reconstructs the exact v1 schema for all seven nonempty subsets of `E`, `S`, and
`F`. The accepted instance language is therefore unchanged locally.

This is a construction freeze, not a provider-execution freeze. No provider
request was made, no model output was sampled, and Calibration 008 remains
unauthorized.

## Local equivalence proof

The construction enumerates every nonempty opcode subset:

| Opcodes | v1 bytes | v2 bytes | Root object | v2 minus root equals v1 |
| --- | ---: | ---: | --- | --- |
| `E` | 160 | 176 | yes | yes |
| `S` | 1,603 | 1,619 | yes | yes |
| `F` | 160 | 176 | yes | yes |
| `E/S` | 1,752 | 1,768 | yes | yes |
| `E/F` | 309 | 325 | yes | yes |
| `S/F` | 1,752 | 1,768 | yes | yes |
| `E/S/F` | 1,901 | 1,917 | yes | yes |

The provider-target lowering adds exactly 16 canonical bytes to every schema.
The reserved commit schema is now 1,917 bytes with SHA-256
`a6f6a271f44b634a6b1750d89ba4fbdc0f829ad8d3b2cb0c7ac9d5e49e199f40`.
The finish schema is 176 bytes with SHA-256
`6d68e540eb5eb5132c2228cb684876fd1a3c311c94d12f9c6e76262b617e4049`.

The frozen v1 evidence remains the reference for behavioral applicability:
11/11 known commit instructions and 11/11 known finish instructions passed that
grammar. Because v2 changes no branch and the exhaustive structural proof shows
the same local instance language, those references transfer without claiming a
new model observation.

## Request and runtime binding

The parallel v2 runtime projects the provider-admissible schema at the two
reserved phases and uses that exact schema as the pre-dispatch validator:

- all 110 work-phase requests remain byte-identical to the frozen v1 runtime;
- all eleven commit requests carry the exact v2 `E/S/F` schema;
- all eleven finish requests carry the exact v2 `F` schema;
- all 22 reserved schemas declare the root object explicitly;
- a valid `F[]` reaches the dispatcher once; and
- an extra-argument `F` is rejected with
  `session_instruction_grammar_invalid` and zero underlying dispatches.

The local OpenAI-to-Bedrock adapter preserves both representative schema
objects exactly, including the new root declaration. The schema advertised to
the provider and the schema enforced before execution are therefore the same
object, rather than two independently reconstructed approximations.

## What changed after the failed probe

Provider Schema Capability Probe 001 established one target-ABI precondition:
the selected Bedrock Converse endpoint rejects a tool input schema unless its
root declares `type: object`. Grammar v2 satisfies that known precondition
locally without weakening the instruction grammar or modifying the frozen v1
artifact.

It does not establish that the endpoint accepts the remaining inner keywords.
Validation may next stop at `oneOf`, `const`, `prefixItems`, or `items: false`.
It also does not establish constrained decoding, schema adherence, better
terminal selection, Pass@1, latency, token use, or cost.

## Reproducibility boundary

The retained construction contains the exact commit and finish schemas, seven
subset-equivalence records, a deterministic runtime report, dependency hashes,
and an artifact lock. Two independent local builds produced byte-identical
summaries and locks. The build verifies the locks of the execution freeze,
Grammar v1, and Provider Schema Capability Probe 001 before deriving v2.

No credential, provider response, launch authorization, or Calibration 008
result is present in this artifact.

## Next red test

Run a new, separately authorized two-request provider capability probe using
the exact v2 hashes. The probe should ask only whether endpoint validation now
advances beyond the root declaration and whether commit and finish schemas are
admitted. A model response, if one occurs, can additionally be classified for
shape adherence, but it must not be treated as a Calibration 008 result.

Only after that probe passes should a successor execution freeze bind the v2
schema and request fresh authorization for Calibration 008.

The experimental-TDD state is now:

`provider root admission failed -> target lowering implemented -> local language equivalence passed -> provider inner-keyword admission untested`
