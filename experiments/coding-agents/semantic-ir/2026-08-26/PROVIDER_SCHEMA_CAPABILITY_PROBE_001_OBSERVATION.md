# Provider Schema Capability Probe 001 observation

## Outcome

The provider capability red test failed before model generation. Amazon Bedrock
rejected both exact frozen Session Instruction Grammar schemas with HTTP 400:

> The value at toolConfig.tools.0.toolSpec.inputSchema.json.type must be one of
> the following: object.

The commit schema and finish schema use object-valued `oneOf` branches, but do
not declare `type: object` at the schema root. Bedrock requires that declaration
explicitly. The current Calibration 008 freeze is therefore not executable on
the selected endpoint without changing its provider-visible schema bytes.

This result does **not** establish whether Bedrock accepts or enforces `oneOf`,
`const`, `prefixItems`, or `items: false`. Validation stopped at the missing
root type before those features could be tested.

## Probe boundary

The probe was deliberately separate from Calibration 008:

- it sent two synthetic requests with no task, repository, Session state, or
  matched-arm content;
- it used the exact provider model, endpoint, API format, and gateway adapter
  bound by the freeze;
- commit used the exact frozen schema hash `69f33750eeeeb6bbf9a7f17d7733bc577d8709d0285559b5d4e92861535c6fd0`;
- finish used the exact frozen schema hash `906c0f473a1f6182b831c54d5ed34e67b14eadc0c52c2eeb3fbdc087f492ebf4`;
- authorization was capped at two provider requests and explicitly set
  `calibration_launch_authorized: false`; and
- no `launch.json` was created or inherited.

The authorization is content-bound to freeze
`40b0d3e2f2041dd6deb70da5db2960afbba609a9f1757032bd684b7261e47c72`.

## Results

| Case | Schema | HTTP | Generation | Tokens | Cost |
| --- | --- | ---: | --- | ---: | ---: |
| Commit, valid `F[]` request | exact `E/S/F` union | 400 | none | 0 | $0 |
| Finish, adversarial extra argument | exact `F[]` | 400 | none | 0 | $0 |

Both responses had the same content hash because the provider rejected the
same missing root declaration. No tool call was sampled, so this probe contains
no model-adherence evidence and says nothing about constrained decoding.

The retained observation contains the synthetic requests, sanitized response
bodies, hash-chained gateway events, result classification, authorization, and
an artifact lock. No credential is retained.

## Why the local gate passed

Draft 2020-12 treats the root `type: object` as redundant here because every
selected `oneOf` branch already has `type: object`. Local validation therefore
correctly accepts and rejects instances according to the branch grammar.

Bedrock has an additional transport contract: its
[`ToolInputSchema`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolInputSchema.html)
documentation states that the top-level schema type must be `object`. The local
JSON Schema gate and the provider API gate were testing different validity
conditions. The adapter preserved the object exactly, including the omission,
so transport identity passed while endpoint admission failed.

## Interpretation

This is a useful separation-of-concerns failure. The semantic grammar is locally
sound, and the adapter is byte-faithful, but the target ISA has a stricter
calling convention. In compiler terms, the candidate needs a provider-target
lowering invariant, not weaker instruction semantics.

Adding `type: object` at the root is semantics-preserving for the current
grammar, but it changes provider-visible bytes and schema hashes. It must not be
silently injected into the frozen v1 package. A successor construction should
make the root invariant explicit and use the same lowered schema for both the
request and runtime backstop.

## Claim boundary

- The exact v1 schemas were rejected by the selected Bedrock Converse endpoint
  on 2026-08-31.
- The rejection proves a missing root-type admission requirement only.
- Inner-keyword acceptance and sampled adherence remain unobserved.
- No model response, task outcome, Pass@1, latency, or token comparison was
  measured.
- Calibration 008 remains unauthorized and unexecuted.

## Next red test

Build Session Instruction Grammar v2 in parallel with an explicit root
`type: object`, prove local language equivalence with v1, and bind that exact
schema to request construction and the runtime backstop. Then a new, separately
authorized two-request capability probe can ask the provider whether validation
advances past the root and whether the inner keywords are accepted.

The experimental-TDD state is now:

`local grammar passed -> adapter identity passed -> provider root admission failed -> target lowering required`
