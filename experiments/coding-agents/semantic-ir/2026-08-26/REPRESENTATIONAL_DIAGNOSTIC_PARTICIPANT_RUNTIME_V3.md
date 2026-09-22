# Diagnostic participant runtime v3: local replay

## Status

**One versioned local runtime now attaches the grammar-v1 and semantic-v2
diagnostic vocabularies to the same reduced confirmatory session. A
provider-free replay preserves the accepted reference submission, the first
eight turns of canary 003, and all ten semantic-corpus rejections. No new
participant treatment or external launch is authorized.**

The runtime owns one session and one diagnostic memory. The outer Session ISA,
Motion resolver, mutation budget, lexicalized observation codec, and
`SESSION_STATE/v1` request format remain unchanged. Covered failures add a
`diagnostic` field to their existing recoverable error and inherited state.
An unrecognized semantic rejection remains a recoverable plain error; the
runtime records a local diagnostic-coverage miss instead of inventing a code.

## Replays

The builder verifies the immutable task and canary-003 artifact locks before
running in fresh temporary workspaces. It compares baseline and successor
records and state after removing **only** the new error diagnostic field.

| Probe | Result |
| --- | --- |
| Canary-003 turns 1–8 | Eight tool calls reproduce the frozen transcript. Turns 6–8 add `S_OPERATION_ARITY`, `MOTION_PATCH_ID_PATTERN`, and `MOTION_ROOT_PATTERN`; all other outcomes, counters, and workspace digests remain identical. |
| Sealed reference `S` action | Accepted by both runtimes, with one applied mutation and identical result and workspace digests. |
| Semantic-v2 corpus | All ten frozen negative cases emit the exact frozen diagnostic immediately and through reduced state, with zero applied mutations. |
| Unsupported root reference | Rejected recoverably with original prose and no diagnostic; one local coverage miss, zero applied mutations. |

Every successor turn request round-trips through `SESSION_STATE/v1` and excludes
the condition identifier. The reference action is a local transactional edit
inside a disposable workspace; it is not a model-generated repair or cloud
experiment.

The repository's bounded `--ci` validation passed (66 tests), as did the
four diagnostic test modules (14 tests) and the freeze verifier. An attempted
unbounded discovery of the entire historical suite was stopped after it
entered long-running legacy Deno preflights; it is not counted as a pass.

## Claim boundary

This proves compatibility for the selected reference, historical prefix, and
semantic corpus. It does not prove diagnostic totality or that a model can use
the new field to improve repair. The wrapper is a local versioned runtime, not
a change to the historical canary runner or a new treatment arm. The 957
unobserved confirmatory cells remain blocked.

## Evidence

- [`freeze.json`](construction/representational-diagnostic-participant-runtime-v3/freeze.json)
  binds source hashes, replay digests, diagnostic counts, accounting, and claim limits.
- [`representational-diagnostic-participant-runtime-freeze-v3.schema.json`](protocol/representational-diagnostic-participant-runtime-freeze-v3.schema.json)
  constrains the frozen artifact.
- [`representational_diagnostic_participant_runtime_v3.py`](scripts/representational_diagnostic_participant_runtime_v3.py)
  composes the unchanged session with diagnostic memory and recoverable fallback.
- [`build_representational_diagnostic_participant_runtime_v3.py`](scripts/build_representational_diagnostic_participant_runtime_v3.py)
  verifies the locks and replays all four probes locally.
- [`test_representational_diagnostic_participant_runtime_v3.py`](../../../../tests/test_representational_diagnostic_participant_runtime_v3.py)
  checks the freeze, unsupported-error fallback, and turn sequencing.

## Next red test

Pre-register a controlled repair comparison between plain prose errors and
structured diagnostics using this frozen runtime and one authorized schedule
cell. Fix the task, provider, model, budgets, stopping rules, and success
criteria before any call. The current construction gives no permission to
launch that comparison.
