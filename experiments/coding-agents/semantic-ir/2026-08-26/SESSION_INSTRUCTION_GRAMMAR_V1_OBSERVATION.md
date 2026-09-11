# Session Instruction Grammar v1 observation

## Outcome

The local red test passes. A phase-specialized discriminated grammar now
describes complete `E`, `S`, and `F` instructions instead of masking only the
opcode. It accepts all eleven known commit and finish reference transitions,
preserves the work-phase tool surface, and rejects all seven invalid final-turn
instructions recorded in Calibration 007 before runtime dispatch.

This is construction and replay evidence only. No provider request occurred,
no recorded response was resampled, and Calibration 008 is not authorized.

## The failure under test

Terminal Reserve v1 changed the final-turn opcode enum to `F`, but retained the
generic argument rule `a: array`. In Calibration 007, six of ten cells that
reached the reserved final turn produced an instruction valid under that coarse
schema. Only three were valid Session ISA terminals. The other three attached
one or five arguments to the zero-argument `F` instruction and were rejected
later by the runtime.

The missing layer was therefore not another opcode policy. It was lexicalization
of the complete instruction shape:

`phase -> available opcode -> opcode-specific arity -> payload grammar`

## Candidate

The candidate leaves turns one through ten unchanged. During `commit`, it
replaces the coarse enum with a discriminated union containing only the
still-budgeted branches:

- `E` has `i: const E` and an exactly empty argument array;
- `F` has `i: const F` and an exactly empty argument array; and
- `S` has `i: const S` plus either one non-empty source-diff string or the
  three positional semantic fields: patch ID, state token, and typed Motion
  operations.

If the mutation budget is exhausted, the complete `S` branch and all of its
semantic payload definitions disappear. The same generated schema is used by
both arms; it does not reveal which representation is active. During `finish`,
only the complete `F[]` branch remains.

The implementation is parallel to the frozen Calibration 007 runtime. It does
not mutate any dependency bound by that observation.

## Local reference gate

| Gate | Result |
| --- | ---: |
| Callable reference cells | 11 |
| Commit `S` instructions accepted | 11 / 11 |
| Finish `F[]` instructions accepted | 11 / 11 |
| Work-phase tool projections unchanged | 11 / 11 |
| Commit schemas shared between arms | yes |
| Finish schemas shared between arms | yes |
| Model calls | 0 |

The eleven cells comprise six source references and five supported semantic
references. The unsupported semantic cross-module cell remains outside the
callable set, as in the frozen schedule.

## Calibration 007 replay

Twenty recorded commit/finish responses were revalidated against their exact
request-time progress contracts. The final-turn decomposition is:

| Final-turn classification | Coarse opcode schema | Complete grammar |
| --- | ---: | ---: |
| Accepted | 6 / 10 | 3 / 10 |
| Exact valid `F[]` | 3 | 3 |
| Extra-argument `F` accepted | 3 | 0 |
| Unavailable opcode rejected | 3 | 3 |
| Malformed argument envelope rejected | 1 | 1 |

The candidate therefore adds exactly three useful local rejections on this
trace: the three `F` instructions that passed the old enum-plus-array schema but
failed the Session ISA's zero-argument rule. It neither changes nor claims to
change what the model would have sampled under the new schema.

## Surface cost

| Reserved phase | Coarse schema | Complete grammar | Delta |
| --- | ---: | ---: | ---: |
| Commit (`E/S/F`) | 130 bytes | 1,901 bytes | +1,771 bytes |
| Finish (`F`) | 122 bytes | 160 bytes | +38 bytes |

These are canonical JSON bytes, not provider tokens. The commit increase is the
cost of disclosing both source and semantic `S` payload grammars through one
shared tool. The final-turn correction is small because no submission grammar
remains. This checkpoint therefore does not establish a token win; it isolates
a reliability-versus-disclosure trade-off for the next matched execution.

## Claim boundary

- The exact known references were used to construct the acceptance gate.
- Recorded Calibration 007 instructions were only reclassified locally.
- JSON Schema validation proves local grammar behavior, not provider adherence.
- The replay cannot establish counterfactual model choices, Pass@1, latency,
  token use, or cost.
- The schema uses Draft 2020-12 discriminators and positional arrays; provider
  support must be verified before any launch.
- No previous authorization carries forward to a future calibration.

## Next red test

Integrate this grammar into a parallel request and dispatch runtime, validate
the decoded instruction against the exact request-time schema as a backstop,
and freeze a matched execution package. Its preflight must preserve the first
ten turns, accept all eleven references, bind exact commit/finish schema bytes,
and verify that the selected provider path transports the required schema
features without weakening them.

Only after that call-free freeze should a separately authorized Calibration 008
ask whether complete instruction lexicalization converts more forced terminal
choices into valid terminals, and whether that benefit justifies the larger
commit surface.

The experimental-TDD result is now:

`opcode lexicalization passed -> instruction-shape lexicalization passed -> provider behavior untested`
