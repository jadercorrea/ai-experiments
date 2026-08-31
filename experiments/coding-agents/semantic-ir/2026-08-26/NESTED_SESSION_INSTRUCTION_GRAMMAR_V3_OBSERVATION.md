# Nested Session Instruction Grammar v3 observation

## Outcome

Nested Session Instruction Grammar v3 passes the local red test created by
Provider Schema Capability Probe 002. It removes the provider-rejected
top-level union without deleting or weakening any instruction branch.

The wire mapping is a one-property envelope:

```json
{"v":{"i":"F","a":[]}}
```

The tool input root remains an exact object with one required property and no
additional properties. The complete v2 discriminated instruction grammar now
lives below `properties.v`. A deterministic runtime validates that exact
advertised envelope, unwraps `v`, and dispatches only the original inner
instruction.

This is a call-free construction freeze. Nested-union provider acceptance has
not been observed, Probe 003 is not authorized, and Calibration 008 remains
unauthorized.

## Bijection with Grammar v2

The construction enumerates all seven nonempty subsets of `E`, `S`, and `F`.
For each subset:

- the v3 root has no `oneOf`;
- `v` is the only required property;
- additional root properties are forbidden;
- the nested instruction retains the complete v2 branches; and
- reattaching the root `$defs` to the nested schema reconstructs the exact v2
  schema object.

The wrap operation `instruction -> {"v": instruction}` is injective. Because
the envelope permits exactly one `v` and no sibling properties, unwrap is its
unique inverse over every schema-valid v3 value. The encoded languages are
therefore bijective rather than merely similar.

The local tests exercise `E`, source-form `S`, semantic-form `S`, and `F`.
Grammar v2's locked evidence remains the behavioral reference: 11/11 commit
instructions and 11/11 finish instructions were accepted there. The v3 proof
transfers that language through a deterministic representation change; it does
not claim a new model observation.

## `$defs` resolution red test

The first envelope draft nested the complete v2 schema literally. That looked
structurally correct, but its absolute `$ref: #/$defs/...` pointers still
resolved from the document root while `$defs` had moved below `v`. Textual
source submissions did not exercise those references; semantic submissions
would fail resolution.

A regression case introduced a valid semantic `S` instruction and exposed the
defect before the construction was committed. The final v3 schema hoists
`$defs` to the envelope root and leaves the referring branches under `v`.
Reconstruction puts those definitions back beside the branches and recovers v2
exactly. This preserves semantics without duplicating the definition catalog.

## Request and runtime binding

The parallel runtime establishes the following local properties:

- all 110 work-phase requests remain byte-identical to the frozen comparator;
- all eleven commit requests carry the nested `E/S/F` schema;
- all eleven finish requests carry the nested `F` schema;
- zero of the 22 reserved schemas place a union at the top level;
- all 22 place the complete union under `properties.v`;
- a valid enveloped `F[]` unwraps and reaches the dispatcher exactly once;
- an enveloped extra-argument `F` is rejected before dispatch; and
- a missing `v` envelope is rejected before dispatch.

The same provider-visible schema object is used as the pre-dispatch validator.
The local OpenAI-to-Bedrock adapter preserves both representative schema
objects exactly, including the root object, absent top-level union, nested
union, and hoisted definitions.

## Surface cost

| Phase | Grammar v2 | Grammar v3 | Delta |
| --- | ---: | ---: | ---: |
| Commit `E/S/F` | 1,917 bytes | 2,000 bytes | +83 bytes |
| Finish `F` | 176 bytes | 259 bytes | +83 bytes |

The commit schema hash is
`bc482f59403f07e1174683c839a60571b8e042dd04981ebeb0774038aabc225d`.
The finish schema hash is
`cb1ce59a749115ddb203dc2588ab6ac8db914f85a48aa05619cafd13a3c63a83`.

The fixed envelope overhead is modest relative to the complete commit grammar
and proportionally large for the tiny finish grammar. These are canonical JSON
bytes, not provider token measurements.

## Claim boundary

- Grammar v3 is locally bijective with Grammar v2 over all seven opcode
  subsets.
- Its request and runtime backstop use the same exact schema object.
- It removes top-level `oneOf` while retaining the union one level below.
- It does not establish that Bedrock accepts nested `oneOf`.
- It does not establish acceptance or enforcement of `const`, `prefixItems`,
  `items: false`, or the hoisted `$defs` catalog.
- It contains no provider call, sampled model choice, Pass@1, token, latency, or
  cost result.
- It creates no Calibration 008 execution freeze or launch authorization.

## Next red test

Provider Schema Capability Probe 003 should use the two exact v3 schema hashes
under a new content-bound authorization. Its only purpose is to determine
whether endpoint validation admits the nested envelope or advances to another
keyword boundary. It must remain synthetic and separate from Calibration 008.

If Probe 003 passes, the following stage is a successor Calibration 008
execution freeze that binds the enveloped wire representation and its
wrap/unwrap runtime. The calibration itself still requires another explicit
authorization after that freeze is reviewed.

The experimental-TDD state is now:

`top-level union admission failed -> nested envelope implemented -> local bijection passed -> nested provider admission untested`
