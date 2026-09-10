# Representational confirmatory canary 002

Status: `infrastructure_invalid_opaque_lexicon_not_total`

## Outcome

Canary 002 reached Amazon Bedrock and received three successful HTTP responses
from the frozen Claude Sonnet 4.6 model. No provider retry occurred, all request
and cost limits were respected, and the remaining 958 cells stayed blocked.

The session did not complete. The third model response requested a legal
inspection over handles `n8` through `n14`. While encoding that observation for
the `opaque_nested` condition, the lexicalizer encountered the scalar slot label
`arguments[0]`, which was absent from its closed opaque vocabulary. The runner
raised `RealizationError` before constructing turn four.

The result is therefore an infrastructure-invalid observation, not a model or
protocol-v1 behavioral failure.

## Observed provider use

- requests: `3`
- retries: `0`
- input tokens: `25,453`
- cached input tokens: `0`
- output tokens: `530`
- total tokens: `25,983`
- estimated observed cost: `USD 0.084309`
- worst-case reservation consumed: `USD 0.774144`

All three responses identify
`us.anthropic.claude-sonnet-4-6`. The gateway event chain is complete and ends
at sequence 3.

## What the red test found

Provider-free replay had exercised the reference target handles. The live
model inspected a different, still legal subset of semantic nodes. Some of
those nodes expose positional slot labels such as `arguments[0]`.

The opaque codec treated every value under `slot` as a member of the fixed
semantic-key vocabulary. That assumption was narrower than the legal state
space of the inspection ISA. In other words, the grammar was closed over the
reference trajectory, but not over every trajectory available to a
participant.

This is evidence for a stronger invariant: lexicalization must be total over
the reachable observation space, not merely over the observations produced by
reference solutions.

## Claim boundary

This canary says nothing about whether protocol v1 improves task completion,
token use, or error recovery. No terminal submission or hidden evaluation was
reached. It does establish that:

1. the content-bound Bedrock transport works for sequence 2;
2. reduced state successfully supported two subsequent turns; and
3. the opaque lexicalization grammar is incomplete for legal participant-led
   inspection.

Canary 002 must not be retried. The remaining campaign stays blocked.

## Next red test

Enumerate every scalar label reachable from every legal inspection handle in
all 240 task units. Require meaningful and opaque encode/decode round trips for
all four realization conditions, including positional slots, before preparing
the next non-adaptive schedule cell as a new canary.
