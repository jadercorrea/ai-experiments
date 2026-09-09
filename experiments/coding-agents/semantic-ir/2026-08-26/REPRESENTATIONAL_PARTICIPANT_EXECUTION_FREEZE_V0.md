# Representational participant execution freeze v0

## Status

**The participant model, initial request constructor, provider translation,
session isolation, inference limits, accounting rates, and USD 350 hard ceiling
are frozen. Confirmatory task construction and launch remain blocked.**

This checkpoint makes no model call. It creates twenty exact requests from the
development smoke fixtures solely to prove that the frozen constructor and the
Bedrock translation compose. The 960 exact confirmatory requests do not yet
exist because their participant-visible task bytes have not been materialized.

## Frozen execution contract

All four conditions use the same participant and policy:

- Amazon Bedrock `us.anthropic.claude-sonnet-4-6` in `us-east-1`, with provider
  substitution forbidden;
- temperature 0, no seed, and at most 4,096 output tokens per turn;
- at most 12 turns, four tool calls per turn, three mutation attempts, two
  public evaluations, one post-finish hidden evaluation, and zero provider
  retries per cell;
- one model-facing tool, `x`, carried through the Bedrock Converse adapter;
- one fresh session and fresh ephemeral workspace for every condition cell,
  with empty initial history and no cross-condition parent or memory; and
- provider-native token accounting over every trajectory request.

The request constructor assembles the participant-visible task, outline,
condition-specific observation state, and Session ISA in one fixed order. It
does not receive a condition identifier. Canonical request identity is SHA-256
over sorted, minified UTF-8 JSON.

## Independent schedule

The locked schedule contains 960 unique session identities and 960 unique
workspace identities: four independent cells for each of 240 frozen task
slots. It preserves each slot's predeclared counterbalance order without using
conversation carryover to implement that order.

The five development-exposed `*-001` slots resume at attempt 1 in all twenty of
their cells. The remaining 235 slots begin at attempt 0, producing 940
attempt-zero cells. Candidate selection remains first-eligible-only.

## Exact-envelope preflight

The local preflight generated twenty exact OpenAI-compatible requests and their
twenty Bedrock Converse translations from the persisted smoke fixtures:

- all twenty canonical request digests are unique;
- all non-system request fields are identical;
- no factorial condition label appears in any request bytes;
- all translated requests preserve the exact `x` tool input schema; and
- none matches the canonical bytes of 867 historical `request*.json` artifacts
  representing 832 unique request digests.

This replaces the smoke checkpoint's provisional comparison unit with an exact
one for those twenty engineering fixtures. It does not pre-clear future
confirmatory requests: every one of those requests must be audited after its
task passes local eligibility.

## Cost boundary

Calibration 008 and the frozen power-selection scale imply descriptive totals
of USD 235.8864 at the mean observed rate and USD 283.0032 at the maximum
observed cell rate. The execution freeze sets a USD 350 hard ceiling, leaving
USD 66.9968, or 23.67%, above the latter projection.

The ceiling is a stop condition, not authorization to spend it. At launch,
pricing must be rechecked and the runner must refuse a request whose reservation
would cross the ceiling. The full theoretical 11,520-request envelope at the
maximum context/output reservation would cost more than the ceiling; therefore
the hard stop, rather than that deliberately loose turn envelope, is the
binding budget control.

## Claim boundary

- Engineering smoke requests constructed and translated locally: 20.
- Confirmatory tasks and exact confirmatory requests: 0.
- Model calls, provider requests, and provider cost in this checkpoint: 0.
- Behavioral, lexical, packaging, interaction, and generalization claims: none.
- Launch authorization: absent.

## Evidence

- [`freeze.json`](construction/representational-participant-execution-freeze-v0/freeze.json)
  records the full immutable policy, limits, gates, and dependencies.
- [`schedule.json`](construction/representational-participant-execution-freeze-v0/schedule.json)
  records all independent future cells and their attempt disposition.
- [`preflight/result.json`](construction/representational-participant-execution-freeze-v0/preflight/result.json)
  records exact-request and local Bedrock-translation evidence.
- [`representational_participant_execution.py`](scripts/representational_participant_execution.py)
  defines canonical request construction and independent scheduling.
- [`test_representational_participant_execution_freeze_v0.py`](../../../../tests/test_representational_participant_execution_freeze_v0.py)
  captures the red-to-green contract and byte-deterministic rebuild.

## Next red test

Materialize all 240 confirmatory tasks through the locked first-eligible rule,
starting the five exposed slots at attempt 1 and the other 235 at attempt 0.
For every accepted task, run the complete local eligibility pipeline, construct
all four exact requests with the now-locked constructor, and repeat the exact
historical-request and cross-cohort duplicate audits. Provider admission,
current-rate verification, and explicit launch authorization remain later
gates.
