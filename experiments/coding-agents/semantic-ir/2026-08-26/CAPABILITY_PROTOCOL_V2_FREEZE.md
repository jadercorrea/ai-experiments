# Experimental TDD for agent infrastructure: capability protocol v2

Date: 2026-08-27

## Outcome

The next infrastructure layer is implemented, locally exercised, and frozen
without experimental subject calls. A semantic agent no longer has to invent or
calculate canonical program and subtree digests. It selects stable node IDs and
calls the read-only `semantic_state_inspect` operation, which returns an opaque
`state_token` plus one node-bound `target_token` per selected target.

The subsequent `semantic_patch_submit` payload carries those tokens. Trusted,
deterministic infrastructure resolves them to the existing canonical digest
guards and applies the already checked v0/v1/v2 semantic patch transaction. The
wire representation contains no model-facing `sha256` or digest field.

## The test that failed next

The first capability-store test passed for program IR v0, then the fresh-suite
test failed on the directory task because the store assumed every persistent
program used schema v0. The six-task population contains program IR v0, v1, and
v2. The protocol was therefore made version-neutral while preserving one
capability patch wire format and dispatching validation and application through
the matching frozen backend.

That failure is retained as part of the experimental-TDD chronology: after
hypothesis, ISA, IR, wire format, patches, checks, and addressable context, the
next broken assumption was that semantic concurrency infrastructure could be
tied to one IR version.

## Frozen interfaces

- `semantic_state_inspect({node_ids})` is present only in supported semantic
  cells.
- Inspection is read-only and does not consume the mutation budget.
- `semantic_patch_submit({patch})` is the only semantic mutation operation.
- A rejected state or target token leaves the candidate unchanged and consumes
  one mutation attempt, matching other rejected submissions.
- State tokens are bound to one program state and issuer; target tokens are
  additionally bound to one node identity and subtree state.
- Tokens expose neither the canonical program digest nor subtree digests.
- The infrastructure resolves tokens and reuses the existing atomic patch
  validator and deterministic lowering path.
- Context and workspace namespaces remain disjoint and addressable; subject
  tool errors remain recoverable within the frozen trajectory budget.

## Fresh instances

The suite `semantic-ir-capability/heterogeneous-patches-v2` contains six new
exact instances derived from context v1. Identity namespaces, exported symbols,
cross-module names, repository bytes, hidden evaluator bytes, capability
reference bytes, and artifact locks changed. Local references pass the hidden
evaluator for all six source tasks and all five supported semantic tasks; each
supported pair converges byte-for-byte.

- Suite digest: `be3a565ac4aba5a618062dc2feb69cd8cc5f8b849c125ea72825dc19a6c9d3ab`
- Suite artifact count: 99
- Suite tree digest: `fd8c47b4d52633d0bc4e3dc05eb279aa7b39033d1e35d69c847c9845799c14fd`
- Experimental subject calls observed: 0

## Execution freeze

The freeze preserves the previous model, endpoint, sampling, paired schedule,
budgets, stopping rules, evaluator policy, token accounting, and closed-tool
isolation. It changes only the fresh task bytes and the semantic precondition
interface.

- Freeze ID: `semantic-ir-capability-calibration/heterogeneous-patches-v2`
- Freeze digest: `d8a3083ad2a08c5e66c5b10d61c390df6d75f42b7419a61f7906fe1896e8eab1`
- Freeze artifact count: 35
- Freeze tree digest: `6903eebdc895ddccf266bcf1f5a10c9960b8b945efb56a10c0d0ad37a5d23dde`
- Scheduled cells: 12
- Provider-call cells: 11
- Model calls authorized: false
- Experimental subject calls observed: 0

The local synthetic trajectory inspected semantic state, submitted a valid
capability patch, finalized the workspace, and passed the hidden evaluator with
one mutation attempt. A stale reference token was rejected atomically and
counted as one attempted mutation.

## Claim boundary and next gate

This checkpoint demonstrates construction feasibility, addressability,
transactional enforcement, fresh-instance convergence, and deterministic
freezing. It does not demonstrate higher semantic Pass@1, lower token use, or a
representation winner.

No provider call is authorized by the freeze. The only remaining gate is a new,
explicit, content-bound launch record after contamination, credentials,
endpoint/IAM scope, retention basis, and every frozen digest are checked again.
