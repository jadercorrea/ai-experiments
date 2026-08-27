# Semantic capability calibration 003

## Status

**Execution valid and complete as a descriptive calibration. The capability-v2
precondition defect did not recur. On these six frozen tasks, the semantic arm
passed more hidden evaluations and used fewer provider requests and output
tokens, while consuming more input tokens, total tokens, and estimated cost.
The sample is too small and development-exposed to authorize an inferential or
general efficacy claim.**

Calibration 003 executed all twelve cells under capability freeze
`d8a3083ad2a08c5e66c5b10d61c390df6d75f42b7419a61f7906fe1896e8eab1`.
The evidence lock contains 233 files with tree digest
`f90fc924ca8407f95ed775dbc71d9c7b52190152559c316f75ae143cadfd521b`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 78 |
| Input tokens | 555,631 |
| Output tokens | 28,995 |
| Total tokens | 584,626 |
| Estimated cost | USD 2.101818 |
| Public evaluator runs | 12 |
| Repair cycles | 9 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 78 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. Provider usage sums, cell costs, schedule
identities, launch and freeze bindings, capability issuance, request
exclusions, and the artifact lock reconcile. A format-aware credential scan
found no access-key, secret-key, API-key, or bearer-token value in the retained
evidence. Broader prefix matches were reviewed as ordinary task text rather
than credential-shaped values.

The account-level Amazon Bedrock retention setting was not observable with the
inference-scoped credential and is not claimed. The preflight records the
limited provider-policy basis used for the authorized call and the failed
account-setting read.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 2 | 4 |
| Supported-task hidden Pass@1, denominator 5 | 2 | 4 |
| Semantic applicability | — | 5 / 6 |
| Provider requests | 46 | 32 |
| Input tokens | 207,304 | 348,327 |
| Output tokens | 19,887 | 9,108 |
| Total tokens | 227,191 | 357,435 |
| Estimated cost | USD 0.920217 | USD 1.181601 |

The semantic arm used 30.4% fewer provider requests and 54.2% fewer output
tokens. It nevertheless used 57.3% more total tokens on the all-task accounting
and cost 28.4% more. Excluding the automatic zero-call unsupported semantic
cell, its total-token use was 68.2% higher than the corresponding five source
cells.

The difference came from input, not generated payload. Semantic trajectories
repeatedly carried a larger structured program and protocol surface: 348,327
input tokens versus 207,304 for source. The output reduction therefore did not
reach whole-trajectory token break-even.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | Hidden failure | Hidden failure |
| Normalization policy | Hidden pass | Hidden pass |
| Raw-ID retry | Turn-limit failure | Hidden pass |
| Reserved-ID guard | Hidden pass | Hidden pass |
| Directory fallback | Turn-limit failure | Hidden pass |
| Cross-module rename | Hidden failure | Unsupported by construction |

Among the five supported pairs, there were two semantic-only passes, two joint
passes, one joint failure, and no source-only pass. The all-task result counts
the predeclared unsupported semantic outcome as failure. These paired counts
describe this frozen calibration; they are not a powered significance test.

## What capability v2 fixed

All five supported semantic cells reached a terminal submission. They made six
successful `semantic_state_inspect` calls and eight patch submissions. Every
submission used a state token and target token previously issued by the trusted
store. No submission attempted to supply a digest, and no rejection concerned a
state token, target token, stale state, or cryptographic precondition.

Three semantic patches were rejected before a successful repair. Each
rejection identified a real program invariant: the replacement failed to
preserve the stable identity of its target node. Inspection did not consume the
mutation budget, and the rejected mutations remained atomic. Supported
semantic cells recorded zero recoverable tool errors.

The calibration therefore passes the infrastructure test that invalidated
calibration 002: the model selected semantic state through opaque capabilities
and was evaluated on its replacement, not on its ability to reconstruct hidden
SHA-256 values.

## Interpretation boundary

This is the first heterogeneous run in the series that permits a descriptive
comparison of the two complete interfaces. It supplies evidence that, for
these instances and this model snapshot, checked semantic mutation can reduce
trajectory length and improve completion while still losing the total-token
and cost comparison to source patches because of input-context overhead.

It does not establish that semantic IR is generally more accurate, cheaper, or
faster. The result is bounded by:

- six exact tasks and only five semantically supported pairs;
- one model, provider, sampling policy, and execution schedule;
- calibration tasks exposed during protocol development;
- a domain-specific JSON IR with limited repository expressiveness;
- no human auditability or readability study; and
- a provider model identifier, not a cryptographic model-weight snapshot.

The frozen result itself marks both efficacy and inferential claims as
unauthorized. No cell will be replaced or rerun under this freeze.

## The next red test

The mutation protocol is no longer the dominant observed defect. Input
representation is.

The next construction step should preserve the exact checked semantic state
and capability semantics while varying only how much of that state is projected
into each model turn. Candidate mechanisms include stable handles, typed local
slices, graph neighborhoods, and progressive disclosure through inspection.
The test must verify that a compact view remains sufficient to construct every
accepted patch and that omitted context can be recovered deterministically
without reintroducing transcript reconstruction or hidden preconditions.

Only after that interface is measured locally should a fresh, larger,
confirmatory task set be frozen. The next claim is not “semantic IR wins.” It is
whether semantic structure can retain the completion and output advantages
observed here while crossing whole-trajectory input-token and cost break-even.
