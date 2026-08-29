# Matched Progress-Session Execution Freeze v1

## Status

**Calibration 007 is frozen before execution. It preserves Calibration 006's
tasks, context and tool bytes, source and semantic memory policies, provider
model, sampling, limits, schedule, accounting, isolation, and stopping rule.
The only model-visible intervention is a matched state-dependent instruction
surface: the complete shared vocabulary through turn ten, the still-budgeted
subset of `E/S` plus `F` at turn eleven, and only `F` at turn twelve. The
candidate freeze reproduces 110/110 open-phase requests byte for byte, passes
all eleven reference mutations and reserved finishes, and observes no model
calls. Provider execution is not authorized.**

Freeze digest:

`46f33d10f32dc3f5b3e523b9bf369eeffcb1ec9f0659ccae73ee3515f85f4551`

Artifact tree digest:

`070985e26d6837f83a37c0f99dbee5b7142fb924431e073eddfc91968db6fa83`

## Experimental question

Calibration 006 showed that exposing `remaining_turns` as data did not cause
the model to finish: ten cells consumed all twelve turns without `F`. Terminal
Reserve v1 makes that budget operational. Calibration 007 asks:

`does the provider use a structurally reserved terminal opportunity
productively?`

The freeze does not assume that it will. A provider may escape the schema,
emit `F` without a useful mutation, finish a failing workspace, or shift work
earlier without changing hidden success.

## Frozen intervention

The request-time instruction enum is a pure function of counters already
present in the compact state:

| Remaining turns, including current | Phase | Advertised opcodes |
| ---: | --- | --- |
| 3 or more | `work` | `C R I L W E S F` |
| 2 | `commit` | budgeted subset of `E S`, plus `F` |
| 1 | `finish` | `F` |

The policy is identical for source and semantic. `E` disappears from commit
when the public-evaluation budget is exhausted; `S` disappears when the
mutation budget is exhausted. `F` remains available in both reserved phases.
No future action, reference, hidden result, or arm-specific schedule input is
used.

The runtime projects the enum before sampling and validates the returned
instruction before dispatch. A disallowed opcode is returned as the typed
recoverable result `session_progress_opcode_unavailable` and is counted
separately from ordinary tool errors.

## Executable isolation gate

The builder rejects drift from Calibration 006 in:

- initial user message and final-suite identity;
- model sources, provider-access contract, model, and sampling;
- limits, accounting, isolation, and stopping rule;
- all six task records;
- complete source and semantic memory policies;
- analysis policy;
- schedule ordering, pair counts, provider-call count, cells, arms, contexts,
  tools, and terminal policy; and
- every copied context, manifest, and shared tool byte.

Cell IDs, schemas, runner and dependency hashes, the launch contract,
contamination audit, preflight evidence, and progress policy are explicit
administrative or treatment differences.

## Local preflight

| Measure | Result |
| --- | ---: |
| Callable cells | 11 |
| Work-phase requests, turns 1–10 | 110 |
| Byte-identical to Calibration 006 requests | 110 / 110 |
| Reference mutations accepted at turn 11 | 11 / 11 |
| Sessions terminated with `F` at turn 12 | 11 / 11 |
| Source hidden-reference passes | 6 / 6 |
| Supported semantic hidden-reference passes | 5 / 5 |
| Unsupported semantic cells retained | 1 |
| Reference failures | 0 |
| Model calls | 0 |

The builder executes this preflight once against a preliminary self-bound
freeze and again after embedding the report. The two summaries must be
identical. The retained negative gate injects `I` against an `F`-only request,
records the typed recoverable error, performs no dispatch, and leaves the
session unfinished.

A separate simulated live-runner test exercises twelve semantic turns: an
inspection, nine allowed work actions, a known valid semantic mutation under
the commit surface, and `F` under the finish surface. The hidden reference
passes. A source negative trajectory forces disallowed actions at turns eleven
and twelve; both are counted as schema escapes, neither reaches the dispatcher,
and the cell ends as a product failure rather than an infrastructure failure.

## Runner and evidence

Each provider turn will retain:

- the exact masked request and provider response;
- the derived progress contract and its digest;
- phase and allowed opcodes in the tool transcript;
- typed tool results and automatic semantic re-fetch evidence;
- recoverable-tool-error and progress-schema-escape counts;
- canonical request bytes and model-visible state bytes; and
- the existing usage, cost, latency, mutation, evaluation, hidden-result,
  terminal, workspace, and coverage-working-set metrics.

The runner cannot execute without a separate launch document that validates
against the new Calibration 007 launch schema and binds the exact freeze,
artifact lock, and model lock digests.

## Schedule and accounting

The twelve-cell order is unchanged: six source and six semantic cells, with
one automatic semantic-unsupported cell and eleven provider-call cells. Pair
ordering remains three source-first and three semantic-first.

All Calibration 006 limits remain unchanged:

- 12 model turns per callable cell;
- 4 tool calls per turn;
- 3 mutation attempts;
- 2 public evaluations;
- 1 hidden evaluation;
- zero provider retries;
- at most 132 provider requests; and
- at most USD 10.00 reserved spend.

## Contamination and claim boundary

- These exact instances were already used by Calibrations 004–006.
- Calibration 007 is a repeated within-instance control-policy calibration,
  not a fresh benchmark.
- References and hidden evaluators are local preflight inputs only and never
  enter provider context.
- No experimental-subject call occurred while building this freeze.
- Temperature zero does not establish deterministic provider behavior.
- No efficacy, generalization, Pass@1, token, latency, or cost claim is
  authorized by construction.

## Remaining launch gate

Exactly one state transition remains:

`explicit_launch_007`

No `launch.json` exists in the freeze. Before provider execution, a new launch
artifact must bind the freeze and artifact-lock digests, repeat the
contamination audit, reverify all frozen dependencies, confirm fresh subject
contexts, credentials, endpoint and IAM scope, provider retention policy, and
record explicit new user authorization. No previous authorization is
inherited.
