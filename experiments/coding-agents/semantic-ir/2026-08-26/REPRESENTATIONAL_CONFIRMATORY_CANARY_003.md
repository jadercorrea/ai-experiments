# Representational confirmatory canary 003

## Status

**The protocol-v2 Bedrock path passed its behavior-blind operational gate, and
the participant failed to reach a terminal submission in 12 turns. The
lexicalization failure observed in canary 002 did not recur. Instead, three
successively deeper construction errors exposed a new repair frontier at the
Motion submission grammar. The remaining 957 cells stay blocked.**

Canary 003 used immutable confirmatory schedule sequence 3:
`capability_lookup_fallback-001`, attempt 1, `opaque_table`. Its selection was
fixed before provider contact. The launch was content-bound to protocol v2,
the selected cell, the runner and schemas frozen at repository revision
`b9c8b122f5f8dc64bd8af021d5a1a8ea1396e74e`, at most 12 provider requests,
zero retries, and USD 4.00.

## Operational result

Amazon Bedrock admitted the frozen endpoint, credential, model, request
adapter, tool transport, and protocol-v2 runtime:

- 1/1 authorized cell dispatched;
- 12 provider requests, all returning HTTP 200 from
  `us.anthropic.claude-sonnet-4-6`;
- zero provider retries and no retry of canary 001 or 002;
- zero dispatches from the remaining 957 cells;
- 126,630 input tokens and 3,746 output tokens;
- USD 0.436080 estimated from the frozen current rates;
- USD 3.096576 conservatively reserved under the USD 4.00 ceiling; and
- a complete 12-event hash-chained gateway record.

The operational gate passed. As predeclared, it did not inspect the behavioral
outcome and therefore does not imply that the task succeeded.

## Behavioral result

The participant did not issue `F`, so no hidden evaluation ran. Its accepted
opcode trajectory was:

```text
I I I I I I C I I
```

Three attempted `S` instructions were rejected recoverably before any mutation
was applied:

| Turn | Validation frontier | Deterministic rejection |
| ---: | --- | --- |
| 6 | Session ISA envelope | `S` expected 5 fields at index 0 and received 6 |
| 7 | Motion document identity | `patch_id="p01"` violated the namespaced identifier grammar |
| 8 | Motion operation reference | `root="n8"` violated the required `r[0-9]+` root grammar |

The participant then requested context and two further inspections rather than
producing another submission. The 12-request bound stopped the cell as
`model_turn_limit_exhausted`, classified as `product_failure`.

Accounting remained separated correctly:

- submission attempts: 3;
- submission-validation rejections: 3;
- instruction-validation rejections: 0;
- mutation-budget rejections: 0;
- applied mutations: 0;
- public evaluations: 0; and
- hidden evaluation: absent because the session was non-terminal.

## What changed after canary 002

Canary 002 stopped before turn four because a legal inspection exposed the
previously unsupported scalar slot label `arguments[0]`. Protocol v2 replaced
that partial observation codec with the lexically total successor frozen over
the reachable cohort.

Canary 003 completed all 12 provider turns without `RealizationError` or any
other infrastructure-invalid transition. This does not prove a behavioral
benefit from opaque lexicalization, but it shows that the specific
infrastructure defect that invalidated canary 002 is absent from this new live
trajectory. The exact canary-002 trajectory remains covered separately by the
provider-free regression.

## State result

Protocol v2 continued to expose canonical current state rather than an
append-only action transcript:

- 11 post-initial state projections were observed;
- maximum canonical state size was 29,256 bytes;
- final canonical state size was 10,714 bytes; and
- the final state digest was
  `13f6e6a86fb274c8c50edc34a25d6df33bf4571d4e4c52ce43d5b3efbdaed12a`.

The final state being smaller than the maximum is consistent with replacement
of current projections rather than monotonic transcript accumulation. This is
an observation about this session, not a general token-efficiency estimate.

## New hypothesis: bidirectional totality

The canary motivates, but does not establish, a stronger interface hypothesis:

> An agent-native protocol needs bidirectional totality. Its observation
> language must represent every reachable state the agent may read, while its
> action language and diagnostic channel must make every legal construction
> expressible and every illegal construction finitely repairable.

Protocol v2 addressed the first direction. The three rejected submissions
suggest that the next bottleneck is the second: the participant crossed one
grammar boundary at a time, but each response exposed the next constraint only
after another provider turn. The current rejection object carries a category
and a prose message; it does not yet carry a canonical error code, structural
path, expected production, observed value, and grammar reference as separate
machine-addressable fields.

This is not evidence that structured diagnostics would have made the task
pass. It identifies a falsifiable next intervention.

## Claim boundary

- The protocol-v2 execution path is operational for the frozen model, cell,
  endpoint, and adapter.
- One behavioral product failure was observed in one preselected
  `opaque_table` cell.
- The canary did not reproduce the infrastructure-invalid lexicalization
  failure from canary 002.
- No valid mutation, terminal submission, public evaluation, or hidden
  evaluation occurred.
- No comparison between lexicalization or packaging conditions exists.
- No representational effect, token-efficiency effect, interaction, or
  generalization claim is supported.
- The result cannot authorize a retry or release the remaining campaign.

## Next red test

Before another provider observation, freeze a versioned construction-diagnostic
IR. Replay the three recorded invalid submissions locally and require each
rejection to produce a bounded structured diagnostic containing at least an
error code, structural path, expected grammar production, observed value, and
recoverability. Prove that the diagnostic round-trips through the reduced
session state without exposing condition labels or changing mutation
accounting.

Any subsequent external canary must use the next immutable schedule cell and a
new content-bound authorization. Canary 003 has zero retry authority.

## Evidence

- [`representational-confirmatory-canary-launch-003.json`](construction/representational-confirmatory-canary-launch-003.json)
  binds the authorization, exact cell, protocol, runner, provider, and limits.
- [`representational-confirmatory-canary-launch-003.preflight.json`](construction/representational-confirmatory-canary-launch-003.preflight.json)
  records source integrity, credential presence without its value, current
  pricing, and the behavior-blind launch gate.
- [`result.json`](observations/representational-confirmatory-canary-003/result.json)
  separates the operational pass from the behavioral product failure.
- [`tool-transcript.json`](observations/representational-confirmatory-canary-003/evidence/tool-transcript.json)
  records accepted instructions and all three recoverable submission
  rejections.
- [`gateway-events.jsonl`](observations/representational-confirmatory-canary-003/evidence/gateway-events.jsonl)
  is the 12-event hash-chained provider-routing record.
- [`artifact-lock.json`](observations/representational-confirmatory-canary-003/publication/artifact-lock.json)
  seals the 30-file observation tree.
