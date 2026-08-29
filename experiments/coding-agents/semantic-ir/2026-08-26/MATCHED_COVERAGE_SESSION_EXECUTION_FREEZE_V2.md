# Matched Coverage-Session Execution Freeze v2

## Status

**Calibration 006 is frozen before execution. The freeze changes the semantic
memory projection from handle-level LRU v1 to coverage-root state v2 while
binding the same task bytes, inline contexts, tool, source memory, provider
model, sampling, limits, schedule, accounting, and stopping rule used by
Calibration 005. Its local preflight builds 22 requests, passes 6/6 source and
5/5 supported semantic references, exercises five receipt-only semantic
reinspections, and records zero evictions, re-fetches, exceptions, or model
calls. Provider execution is not authorized.**

Freeze digest:

`0672b13b493a2f47bad56074f9b75d1a01bd8042b3a347a9245bcbf4c8996462`

Artifact tree digest:

`166f2ad560e7f0421e156ba613ab42be585852df7263bf7a133240a11e6eedf2`

## Experimental question

The local runtime result established that coverage roots remove structural
churn while increasing fixed-trace state bytes by 12.77%. The provider-backed
question is narrower:

`does preserving coherent structural coverage eliminate enough repeated
inspection actions to repay the larger state?`

The freeze does not assume that it will.

## Frozen intervention

Only the semantic state shown after turn one changes at the experimental
boundary.

| Field | Calibration 005 | Calibration 006 |
| --- | --- | --- |
| State schema | `semantic-working-set-state/v1` | `semantic-working-set-state/v2` |
| State prefix | `SEMANTIC_WORKING_SET_STATE/v1` | `SEMANTIC_WORKING_SET_STATE/v2` |
| Capacity | 2 serialized handles | 2 disjoint coverage roots |
| Replacement | handle LRU | coverage-antichain LRU |
| Capability coverage | implicit | explicit `covered_by` |
| Repeated covered inspection | re-admit subtree | receipt only |

The source arm remains on `session-state/v1`. It is rerun on the unchanged
schedule as a contemporaneous stability control, not as a new intervention.

## Executable isolation gate

The builder rejects the freeze if any of these subject variables drift from
Calibration 005:

- initial user message;
- model sources and provider access contract;
- provider model and endpoint identity;
- sampling;
- limits and spending ceiling;
- accounting rules;
- task records;
- source memory policy;
- schedule order, arms, contexts, tools, and terminal policies;
- stopping rule and analysis policy.

Every callable context, manifest, and the shared `x` tool are copied byte for
byte from the previous artifact. New cell IDs, schemas, runner hashes, launch
contract, audit date, and preflight evidence are recorded as administrative
differences rather than experimental variables.

## Memory policy

The semantic arm freezes:

- root capacity: `2`;
- capacity unit: `non_overlapping_subtree_root`;
- normalization: `maximal_requested_ancestor_antichain`;
- replacement: `coverage_antichain_lru`;
- persistent `covered_by` capability field;
- subtree as the only evictable payload;
- current-submit uncovered target as the only fault trigger;
- no future-action input;
- deterministic local `I` re-fetch with zero provider calls;
- typed recoverable rejection if disjoint submit width exceeds capacity.

## Local preflight

| Measure | Result |
| --- | ---: |
| Callable cells | 11 |
| Requests built | 22 |
| Source hidden passes | 6/6 |
| Supported semantic hidden passes | 5/5 |
| Unsupported semantic cells | 1 |
| Receipt-only semantic reinspections | 5 |
| Semantic re-fetches | 0 |
| Semantic evictions | 0 |
| Preflight exceptions | 0 |
| Reference failures | 0 |
| Model calls | 0 |

The preflight first inspects a coverage root with each reference target, then
reinspects only the already-covered targets. This makes the receipt path an
executed invariant rather than a policy string. It then submits the frozen
reference, finishes, and runs the hidden evaluator.

A separate simulated live-runner test performs a three-turn semantic session:
inspection, v2-state reconstruction and submit, then finish. It passes the
hidden reference without automatic re-fetch or eviction.

## Schedule and accounting

The twelve-cell order is unchanged: six source and six semantic cells, with
one semantic-unsupported cell and eleven provider-call cells. Pair ordering
remains fixed at three source-first and three semantic-first pairs.

The same limits remain in force:

- 12 model turns per callable cell;
- 4 tool calls per turn;
- 3 mutation attempts;
- 2 public evaluations;
- 1 hidden evaluation;
- zero provider retries;
- at most 132 provider requests;
- at most USD 10.00 reserved spend.

Calibration 006 retains canonical request bytes, model-visible state bytes,
automatic re-fetch accounting, working-set evictions, unsatisfied submissions,
provider tokens, latency, repair cycles, terminal payload size, hidden result,
and estimated cost. The v2 runner additionally records admitted roots,
receipt-only inspections, and coalescences in each cell result.

## Contamination and claim boundary

- These are the exact instances already used by Calibrations 004 and 005.
- This is a repeated within-instance memory-policy calibration, not a fresh
  benchmark.
- The references and hidden evaluators are used only by local preflight and are
  excluded from model context.
- Local construction observed zero experimental-subject calls.
- Temperature zero does not imply deterministic provider behavior; the
  unchanged source arm helps expose run-to-run drift.
- The freeze authorizes no efficacy, generalization, Pass@1, or provider-token
  claim.

## Remaining launch gate

Exactly one state transition remains:

`explicit_launch_006`

Before provider execution, a launch artifact must bind this freeze digest and
artifact-lock digest, repeat the contamination audit, reverify every frozen
digest, confirm fresh subject contexts, credentials, endpoint/IAM scope, and
provider retention policy, and record explicit new user authorization.

No previous launch authorization is inherited.
