# Representational confirmatory canary 003 plan

Status: `protocol_v2_canary_planned_launch_blocked`

## Why this canary exists

Canary 002 reached a legal positional slot that the historical opaque codec
could not represent. Protocol v2 preserves the reduced-state and accounting
semantics of protocol v1 while selecting the successor codec whose reachable
vocabulary is total over the frozen cohort.

Canary 003 is the first proposed provider observation of that versioned
runtime. It is neither a retry of canary 001 nor of canary 002, and it cannot
release the rest of the campaign.

## Fixed selection

The selected cell is the next entry in the immutable schedule:

- sequence: `3`
- slot: `capability_lookup_fallback-001`
- condition: `opaque_table`
- initial request SHA-256:
  `7ec4c5ad73975bf1a0d6e56ecc71a16c8ecb2c6e1497b3bfdcb43881bc39eb7c`
- canonical initial request size: `13,920` bytes
- Bedrock request SHA-256:
  `fe7ea7b227b7e281c726ac1f82161a4c786e68406bd5599fdc1280c4c728a610`
- model: `us.anthropic.claude-sonnet-4-6`
- region: `us-east-1`

The selection is non-adaptive. The outcomes of the first two canaries did not
choose the task, family, or realization.

## Bound protocol evidence

The plan binds the exact protocol v2 freeze and artifact lock. For the selected
cell, the frozen provider-free preflight records:

- 15 reachable nodes;
- a successful full-node inspection and canonical decode;
- opaque-table realization SHA-256
  `af0a717cfc403e21e89f2cc3aa95711712c24f6393f1a40389e62726022698f3`;
- a successful reference replay; and
- final reduced-state SHA-256
  `e866497d36b9dcfb09a1203fbbcb5cf9ae2d25e647aeecaba3f3a7390a5e3146`.

The participant runtime is fixed to protocol v2, `SESSION_STATE/v1`, opaque
table packaging, and observation codec v1 with `arguments[0] -> k32`.

## Prior observations

Both earlier canaries remain immutable evidence:

- sequence 1 is bound to canary 001's result and artifact lock;
- sequence 2 is bound to canary 002's infrastructure-failure record and
  artifact lock; and
- neither sequence has retry authority.

The plan therefore records two previously observed cells and keeps the other
957 cells blocked.

## Transmission boundary

A future, separately authorized runner may transmit only the selected synthetic
task, instruction outline, opaque-table semantic observation under codec v1,
and subsequent protocol-v2 reduced state and typed tool results. Credentials,
the reference solution, hidden evaluator, both prior transcripts, and files
outside immutable schedule sequence 3 remain excluded.

The prospective execution ceiling remains 12 provider requests, zero retries,
and USD 4.00. These are bounds, not spending authority.

## Current gate

`provider_call_authorized` and `launch_artifact_materialized` are both `false`.
No credential or pricing check was performed. This checkpoint deliberately
does not contain an execution path.

The next red test is to implement and freeze a sequence-3-only runner and
launch schema. A later launch would still require a new explicit authorization
bound to this exact plan; a generic continuation instruction cannot release
the gate.
