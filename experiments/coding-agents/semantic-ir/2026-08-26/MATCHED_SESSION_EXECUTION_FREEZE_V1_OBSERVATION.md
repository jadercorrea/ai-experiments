# Matched Session Execution Freeze v1

## Status

**Calibration 004 is frozen but not launched. Six fresh task instances preserve
the prior task families while changing program, node, symbol, repository,
reference, and hidden-evaluator bytes. The paired schedule contains twelve
cells, eleven provider-call cells, and an exact byte-identical one-tool Session
ISA in both arms. Local reference execution passes all six source tasks and all
five supported semantic tasks. No model call occurred or is authorized; a
separate content-bound launch record remains required.**

The fresh task suite contains 99 files with tree digest
`8e3e38c442f6e6d26e0b458f423ab91f1d8b34133a0a62f6a9c5bc04c461f759`
and canonical suite digest
`30e4a58a578b4b18c7a07b43cb04db1d97c0b7f8b93ae06d97b6c8ef28efa1ca`.
The execution freeze contains 25 files with tree digest
`ea3993791f6ffa98184a59615640548bd538c69bbb8189d15689578638c98dc7`
and canonical freeze digest
`c2e49b3b32c2e9af6c577cab70c425a6ab74637744a01b9557535c6eca3f6232`.

## Why fresh instances were necessary

The capability-v2 instances used in Calibration 003 cannot be reused as new
experimental inputs. The new `session-patch-tasks-v3` suite deterministically
derives the same six task families while changing:

- exported functions and cross-module contract names;
- program, patch, node, parameter, and local-binding identities;
- repository subject and hidden-evaluator bytes;
- reference capability tokens and all content locks; and
- mode instructions, which now expose only the one-tool `x` protocol.

These exact bytes have never been sent to the experimental subject. They are
nevertheless development-agent-exposed and family-derived. The appropriate
claim is a controlled calibration, not a contamination-clean general benchmark.

## Frozen comparison

The schedule retains all six tasks and alternates pair order: three pairs run
source first and three run semantic first. Five tasks support both arms. The
unsupported cross-module semantic cell performs no provider call and remains an
automatic semantic failure in all-task utility, leaving eleven callable cells.

Every callable cell receives the exact same 612-byte `tools/session.json` file,
with SHA-256
`f2e10bca9678e2519f5259648ec8e643d087f61262384626e9a3f6756e9a8eb3`.
The shared outer instruction is `x({i,a})`:

- both arms use `C/R` for allowlisted context, `L/W` for the workspace, `E`
  for public evaluation, and `F` to finish;
- source submits `S[unified-diff]`; and
- semantic inspects `I[handles]` and submits positional Motion through `S`.

The runtime makes invalid envelopes and instructions recoverable within the
frozen turn budget. It records opcode counts, envelope rejections, instruction
rejections, mutation attempts, repair cycles, evaluations, complete provider
usage, latency, cost, and content-addressed request/response evidence.

## Model and resource lock

For comparison with Calibration 003, the freeze inherits the pinned Bedrock
Claude Sonnet 4.6 model and sampling policy: temperature zero and at most 4,096
output tokens per turn. Each callable cell allows twelve turns, four tool calls
per turn, three mutation attempts, two public evaluations, and one hidden
evaluation. The run is capped at 132 provider requests and USD 10 estimated
spend, with zero provider retries.

These values are frozen experimental controls, not a prediction that the run
will consume the maximum.

## Local verification

Without inference, the deterministic runtime established:

- 6/6 source references pass the hidden evaluator through `x`;
- 5/5 supported semantic references inspect, submit, and pass through `x`;
- all five supported source and semantic projections converge byte-for-byte;
- an invalid source `I` instruction is recoverable and counted;
- the tool bytes are identical in every callable cell;
- rebuilding either bundle produces byte-identical manifests and locks; and
- preflight resolves to the frozen digest without a provider call.

The initial frozen contexts total 6,612 bytes across six source cells and
13,082 bytes across five supported semantic cells. Tool disclosure adds 3,672
and 3,060 bytes respectively. These are construction measurements only; actual
provider-native tokens and dynamic observation trajectories remain unobserved.

## Claim boundary

- No launch file exists in the frozen bundle.
- No model/provider call occurred or is authorized by the freeze.
- Reference solutions and hidden evaluators are content-bound but excluded from
  model-facing contexts and workspaces.
- Local reference success establishes runtime integrity, not model efficacy.
- Fresh bytes reduce exact-instance reuse but do not erase task-family or
  development-agent exposure.
- Calibration 004 must report both all-task utility and supported-task
  conditional efficacy, never only the latter.

## The next red test

The only remaining gate is an explicit Calibration 004 launch. Immediately
before launch, the contamination status, frozen digests, credentials, exact
endpoint and IAM scope, and provider retention basis must be checked again and
bound into a separate authorization record.

Only then may the eleven calls run. The result must determine whether agents can
realize the earlier construction advantage while choosing their own files,
handles, instructions, and repairs. Until that separately authorized run, the
sequence ends at:

`matched observation surface -> fresh execution freeze -> explicit launch`.

## Subsequent result

The separately authorized Calibration 004 completed all twelve cells with 101
successful provider responses and no infrastructure-invalid outcome. Source
passed 2/6 hidden evaluations and semantic passed 1/6; on supported tasks the
counts were 2/5 and 1/5. Semantic generated less output but required more turns
and accumulated substantially more input, total tokens, and cost. The freeze
therefore served its purpose: it preserved a negative result that the
known-reference construction could not predict. See
[`CALIBRATION_004_OBSERVATION.md`](CALIBRATION_004_OBSERVATION.md).
