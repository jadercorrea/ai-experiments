# Provider Schema Capability Probe 002 observation

## Outcome

Provider Schema Capability Probe 002 advanced past the missing-root failure
observed by Probe 001, then failed at the next provider-ABI boundary. Amazon
Bedrock rejected both exact Grammar v2 schemas with HTTP 400 because the
selected model endpoint does not support `oneOf`, `allOf`, or `anyOf` at the
top level of a tool input schema.

Both schemas declared the required root `type: object`. The response therefore
confirms that the provider-target lowering fixed the first admission error and
that validation advanced to the top-level union.

No model generation occurred. Usage was zero input tokens, zero output tokens,
and zero estimated cost. Calibration 008 was neither authorized nor executed.

## Probe boundary

The user authorization was content-bound to four identities:

- execution freeze
  `40b0d3e2f2041dd6deb70da5db2960afbba609a9f1757032bd684b7261e47c72`;
- Grammar v2 artifact lock
  `7b9da576168f6589af6223aa720baaedcfd18f7ff1f818a0ba64619a4dc5de16`;
- commit schema
  `a6f6a271f44b634a6b1750d89ba4fbdc0f829ad8d3b2cb0c7ac9d5e49e199f40`;
- finish schema
  `6d68e540eb5eb5132c2228cb684876fd1a3c311c94d12f9c6e76262b617e4049`.

The gateway admitted at most two cloud requests. Both used synthetic messages,
the exact locked schema object, the frozen model and sampling configuration,
and no task, repository, Session state, or candidate content. The retained
gateway evidence contains exactly two events.

## Results

| Case | Root | Top-level union | HTTP | Generation | Tokens | Cost |
| --- | --- | --- | ---: | --- | ---: | ---: |
| Commit, valid `F[]` request | `object` | `E/S/F` `oneOf` | 400 | none | 0 | $0 |
| Finish, adversarial extra argument | `object` | `F` `oneOf` | 400 | none | 0 | $0 |

The provider returned the same schema error for both cases: the tool
`input_schema` does not support `oneOf`, `allOf`, or `anyOf` at the top level.
The response bodies consequently have the same SHA-256 digest. No tool call was
sampled, so the adversarial finish case produced no adherence evidence.

This observation establishes rejection of the exact complete schema objects,
not the independent support status of every keyword within their branches.
`const`, `prefixItems`, and `items: false` were present but validation stopped at
the top-level union before their acceptance or enforcement could be observed.

## Classification correction

The initial result was derived with the Probe 001 classifier, which recognized
schema errors containing the Bedrock spelling `inputSchema`. This endpoint
returned the Anthropic-facing spelling `input_schema`, so the first derived
result incorrectly labeled both HTTP 400 responses as infrastructure errors.

A regression test reproduced the exact message. Classification revision 2
normalizes both spellings and distinguishes root-type rejection from an inner
schema-keyword rejection. The retained requests, response bodies, gateway
events, authorization, status codes, and schema hashes were then reclassified
offline. No provider request was repeated. The corrected result explicitly
records `classification_corrected_offline: true`, and the regenerated artifact
lock verifies the complete retained tree.

## Interpretation

Grammar v2 was a valid, semantics-preserving fix for the known root invariant,
but it is not a valid target encoding for this endpoint. The target ABI accepts
an object root and rejects a discriminated union placed directly at that root.
This is another infrastructure failure before inference, not evidence against
the instruction semantics or the model's ability to follow them.

The next lowering should preserve the complete local grammar while moving the
discrimination away from the top level. One candidate is an object envelope
whose required property contains the opcode-discriminated union, with a
deterministic wrap/unwrap adapter and the exact same schema at request and
pre-dispatch validation. That candidate must first prove local bijection and
measure its byte cost; nested-union provider acceptance remains a separate red
test rather than an assumption.

## Claim boundary

- The selected endpoint accepted the explicit object-root precondition far
  enough to report the next schema defect.
- It rejected top-level `oneOf` in both exact v2 schema objects.
- It produced no model output, tool call, usage, latency comparison, Pass@1, or
  adherence evidence.
- This does not prove whether a nested union is accepted.
- This does not prove whether `const`, `prefixItems`, or `items: false` are
  accepted or enforced.
- Calibration 008 remains unauthorized and unexecuted.

## Next red test

Construct Provider-Admissible Session Instruction Grammar v3 in parallel with
an object envelope and nested discriminated instruction payload. Prove a local
bijection with Grammar v2 for all seven opcode subsets, bind the exact envelope
schema to request and backstop, and keep work-phase requests unchanged. Only
then may a separately authorized Probe 003 ask whether the endpoint accepts the
nested union.

The experimental-TDD state is now:

`root admission failed -> explicit root passed -> top-level union admission failed -> nested target lowering required`
