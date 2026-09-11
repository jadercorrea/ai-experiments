# Representational confirmatory canary 002 plan

Status: `protocol_v1_canary_planned_launch_blocked`

## Why this canary exists

Canary 001 passed its behavior-blind operational gate but exposed two protocol
defects: rejected submissions consumed the mutation budget, and typed action
history grew on every turn. Protocol v1 separates rejection categories from
applied mutations and replaces append-only history with a reduced current-state
projection.

Canary 002 is the first provider observation of that repair. It is not a retry
of canary 001 and cannot release the rest of the campaign.

## Fixed selection

The selected cell is the next entry in the immutable schedule:

- sequence: `2`
- slot: `capability_lookup_fallback-001`
- condition: `opaque_nested`
- initial request SHA-256:
  `bd230b535da6962f70ada16488553b8652addd35c44042043095848420e45cf8`
- canonical initial request size: `12,832` bytes
- model: `us.anthropic.claude-sonnet-4-6`
- region: `us-east-1`

The selection is non-adaptive. The result of canary 001 did not determine the
task, family, or realization used here.

## Delta under observation

Turn one remains the exact request already frozen in the confirmatory cohort.
Subsequent turns replace transcript-like action history with
`SESSION_STATE/v1`, whose state is keyed by current context, workspace,
submission, evaluation, finish, and unresolved-failure slots.

The result records these categories independently:

- outer instruction rejection;
- submission validation rejection;
- valid submission rejected by the mutation budget; and
- successfully applied mutation.

Only the last category consumes the three-mutation budget.

## Transmission and execution boundary

If separately authorized, the runner may transmit the selected synthetic task,
instruction outline, opaque-nested semantic observation, and subsequent
protocol-v1 reduced state and typed tool results. It excludes credentials, the
reference solution, the hidden evaluator, the canary-001 transcript, and files
outside the selected cell.

The runner permits at most 12 provider requests, zero retries, and USD 4.00. It
keeps the 958 not-yet-observed cells blocked and explicitly prohibits retrying
canary 001. Behavioral success or failure is excluded from the operational
gate and cannot release additional cells.

## Provider-free evidence

The local tests demonstrate that:

- the plan is bound to schedule sequence 2 and protocol v1;
- plan or launch drift is rejected before inference;
- an invalid Motion submission remains recoverable without consuming an
  applied mutation;
- the next request contains `SESSION_STATE/v1` and no `actions` history; and
- tool calls appearing after `F` are recorded but not executed.

The reconstructed request contains two messages (`system`, `user`), no
`reference/` path, and no `hidden.json` path.

## Current gate

`provider_call_authorized` remains `false`. Credential presence and current
pricing must be rechecked only after a new authorization explicitly names the
content-bound canary-002 payload. A generic continuation instruction does not
release this gate.
