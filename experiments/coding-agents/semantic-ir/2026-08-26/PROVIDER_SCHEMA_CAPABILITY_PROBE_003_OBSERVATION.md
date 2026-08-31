# Provider Schema Capability Probe 003 observation

## Outcome

Provider Schema Capability Probe 003 crossed the provider-ABI boundary exposed
by Probe 002. Amazon Bedrock accepted both exact Grammar v3 tool input schemas
with HTTP 200 after the unchanged discriminated instruction union was moved
below the required `v` envelope property.

Both responses contained exactly one call to the synthetic tool. The valid
commit case produced `{"v":{"i":"F","a":[]}}`. The adversarial finish case
was explicitly asked to place a forbidden item in `v.a`, but sampled the same
schema-valid empty array. The observation therefore contains two valid samples,
including one adversarial sample, but it does not establish constrained
decoding, keyword enforcement, or future adherence.

The two calls consumed 2,296 input tokens and 84 output tokens, for 2,380 total
tokens and an estimated cost of USD 0.008148. Calibration 008 was neither
authorized nor executed.

## Probe boundary

The user authorization was content-bound to four identities:

- execution freeze
  `40b0d3e2f2041dd6deb70da5db2960afbba609a9f1757032bd684b7261e47c72`;
- Grammar v3 artifact lock
  `dc7a516b0eece966edb3aeb4dbe48043db87ae91187d19eba2c208ea689e8bc3`;
- commit schema
  `bc482f59403f07e1174683c839a60571b8e042dd04981ebeb0774038aabc225d`;
- finish schema
  `cb1ce59a749115ddb203dc2588ab6ac8db914f85a48aa05619cafd13a3c63a83`.

The gateway admitted at most two cloud requests. Both used synthetic messages,
the exact locked schema object, the frozen model and sampling configuration,
and no task, repository, Session state, or candidate content. The retained
gateway evidence contains exactly two events.

## Results

| Case | Root | Nested union | HTTP | Sampled arguments | Schema-valid | Input | Output |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| Commit, valid `F[]` request | `object` | `v.oneOf` | 200 | `{"v":{"i":"F","a":[]}}` | yes | 1,518 | 42 |
| Finish, adversarial extra argument | `object` | `v.oneOf` | 200 | `{"v":{"i":"F","a":[]}}` | yes | 778 | 42 |

The provider model identity matched the frozen
`us.anthropic.claude-sonnet-4-6` identifier in both responses. Each response
ended with `tool_calls`; neither contained an infrastructure or schema-admission
error. The result and retained observation tree validate against their schemas
and content lock.

## Interpretation

The object envelope is a provider-admissible lowering for these two complete
Grammar v3 schema objects. This is the first provider observation in the
sequence to reach model generation with the exact instruction grammar still
present. It resolves the narrow question left by Probe 002: this endpoint
accepts the discriminated union when it is nested beneath the object root.

The adversarial sample is encouraging but deliberately weak evidence. A model
can ignore the conflicting instruction without the provider enforcing the
schema, and two successful samples cannot distinguish model adherence from
constrained decoding. Likewise, accepting each complete schema does not prove
the independent enforcement of every `const`, `prefixItems`, `items`, pattern,
or reference constraint inside it.

## Claim boundary

- The selected endpoint accepted both exact Grammar v3 schema objects.
- The selected endpoint accepted a `oneOf` nested under the required `v`
  property in both schema objects.
- Two tool-call samples were observed and both validated locally; one resisted
  the explicit adversarial request for an extra finish argument.
- This does not prove constrained decoding, independent keyword enforcement,
  future response adherence, improved task success, or lower token use.
- No task, repository, Session state, candidate, or hidden evaluator content
  entered either request.
- Calibration 008 remains unauthorized and unexecuted.

## Next red test

Bind the accepted Grammar v3 envelope to both request construction and the
pre-dispatch backstop in a parallel, immutable Calibration 008 execution
package. Re-run the complete local reference and contamination gates, then
require a separate content-bound launch authorization before any task call.

The experimental-TDD state is now:

`root admission failed -> explicit root passed -> top-level union admission failed -> nested union admitted -> task behavior remains untested`
