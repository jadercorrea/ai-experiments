# Matched Compacted-Session Execution Freeze v1

## Status

**Calibration 005 is frozen but not launched. The package preserves the exact
six tasks, twelve paired cells, alternating arm order, context bytes, and shared
one-tool Session ISA from Calibration 004. It changes the live memory policy:
source receives Explicit Session State v1 and semantic receives Semantic
Working-Set State v1 with an LRU capacity of two. A content-bound runner replaces
prior assistant/tool history after turn one, performs current-submit semantic
re-fetch without provider calls, and rejects capacity exhaustion recoverably.
Local preflight built 22 requests, passed 6/6 source and 5/5 supported semantic
hidden references, exercised five semantic re-fetches, and made zero model
calls. A separate `explicit_launch_005` remains mandatory.**

The generated package contains 27 files with tree digest
`42f9e196901985007f5f5203354c56c58c57cf9a5c0dc65963737cf43139556d`.
Its freeze digest is
`4ea8b4e2d654c36ca41d62afcf22a9f9ea9351fa98effdced20974eae73a2b69`.

## What is frozen

The package inherits the immutable execution surface from Matched Session
Execution Freeze v1:

- six heterogeneous task instances and twelve paired cells;
- six source calls and five supported semantic calls;
- three source-first and three semantic-first pairs;
- the exact context and context-manifest bytes for every callable cell;
- the exact shared `x` tool, with no shell or repository-wide access;
- the same model, sampling, turn, tool, mutation, evaluation, timeout, request,
  retry, and spend limits; and
- the same unsupported semantic disposition for the cross-module task.

Cell identities are versioned to
`semantic-ir-compacted-session-calibration-005/...`. The model-facing task and
tool bytes are otherwise unchanged.

## Frozen memory policy

Turn one uses the original initial system and user messages. Every later turn
contains exactly:

```text
initial system + initial user + current typed state
```

No prior assistant message or tool-result message is retained.

Source cells use:

- schema `session-state/v1`;
- prefix `SESSION_STATE/v1`; and
- the bounded state policy established by Explicit Session State Replay v1.

Semantic cells use:

- schema `semantic-working-set-state/v1`;
- prefix `SEMANTIC_WORKING_SET_STATE/v1`;
- persistent handle, node, operation, parent, slot, scope, state-token, and
  target-token capabilities;
- an LRU of at most two full subtrees; and
- deterministic local `I` re-fetch on a current `S` target miss.

The re-fetch boundary is operationally explicit. It receives the current
instruction, never a future action, contributes zero provider requests, and is
recorded as canonical instruction-plus-result bytes. If one `S` requires more
than two simultaneously live targets, the runtime returns a typed recoverable
rejection instead of silently bypassing the capacity constraint.

## Local preflight

The artifact-bound report records:

| Check | Result |
| --- | ---: |
| Callable cells | 11 |
| Requests built | 22 |
| Source hidden references | 6/6 |
| Supported semantic hidden references | 5/5 |
| Unsupported semantic cells | 1 |
| Semantic re-fetches exercised | 5 |
| Preflight exceptions | 0 |
| Model calls | 0 |

Each callable cell builds both its initial request and a second request from
typed state. Semantic preflight deliberately evicts reference targets before
submission, forcing one deterministic re-fetch in each supported cell. The
result is reproduced under the final freeze digest and retained inside the
artifact lock.

The test suite also drives the live runner with scripted provider responses:
a source reference completes across `S -> state -> F`; a semantic reference
completes across `I -> working-set state -> S -> state -> F`; and an invalid
tool name cannot trigger semantic re-fetch as a side effect.

## Content boundary

Sixteen dependency digests bind:

- the freeze and launch schemas;
- the freeze builder and exact execution runner;
- both state schemas and their implementations;
- the Explicit Session State Replay v1 summary and artifact lock;
- the Semantic Working-Set Replay v1 summary and artifact lock;
- the task suite and artifact lock; and
- the Calibration 004 matched freeze and artifact lock from which context and
  tool bytes are copied exactly.

This ensures that capacity two is connected to its recorded construction
evidence rather than appearing as an unmotivated constant in the new freeze.

## Repeated-instance boundary

Calibration 005 intentionally reuses the exact Calibration 004 task instances.
That enables a within-instance follow-up on session-memory policy, but it is not
a fresh benchmark. The contamination audit therefore records
`exact_instances_used_as_experimental_inputs: true` and requires fresh stateless
subject contexts at launch.

Any future result must be reported as a repeated within-instance calibration.
It cannot be promoted to contamination-clean efficacy evidence, and differences
from Calibration 004 may still contain sampling and provider-time variation.

## Claim boundary

- No model or provider call occurred or is authorized by this freeze.
- Local hidden-reference passes establish runner feasibility, not model
  performance.
- Canonical bytes remain separate from provider-native token accounting.
- The freeze does not claim that models will choose the same actions under
  compact state.
- The semantic runtime may restore an evicted subtree only after the current
  `S` exists; this does not prove the subtree was unnecessary for generation.
- Calibration 005 requires a separately validated launch artifact bound to the
  freeze, artifact lock, model lock, contamination repeat, credentials,
  endpoint/IAM scope, and retention-policy basis.

## Next gate

The construction sequence is complete. The next step is not another code
change: repeat the prelaunch audit and provider preflight, create an
`explicit_launch_005` only after direct user authorization, and execute the
frozen eleven-call schedule without changing any artifact.

The resulting observation should compare Calibration 005 both internally
(source-state versus semantic-working-set) and descriptively against
Calibration 004, while keeping repeated-instance and stochastic-run caveats
visible.
