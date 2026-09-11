# Representational confirmatory canary 001

## Status

**The one-cell Bedrock path passed its behavior-blind operational gate, while
the participant failed to reach a terminal submission in 12 turns. The other
959 cells remain blocked. This is an infrastructure admission result and a
productive protocol failure, not confirmatory evidence for a representational
effect.**

The canary used the immutable first cell in the confirmatory schedule:
`capability_lookup_fallback-001`, attempt 1, `meaningful_nested`. Selection was
fixed before provider contact. The user authorization was content-bound to
this cell, its synthetic participant payload, at most 12 provider requests,
zero retries, and USD 4.00. Reference material, the hidden evaluator,
credentials, and files outside the cell were excluded from model context.

## Operational result

Amazon Bedrock admitted the frozen endpoint, credential, model, request
adapter, tool transport, and provider-native usage surface:

- 1/1 authorized cell dispatched;
- 12 provider requests, all to
  `us.anthropic.claude-sonnet-4-6` through the frozen `us-east-1` endpoint;
- zero retries and zero dispatches from the remaining 959 cells;
- 112,629 input tokens and 3,753 output tokens;
- USD 0.394182 estimated from current provider rates;
- USD 3.096576 conservatively reserved under the USD 4.00 ceiling; and
- a complete 12-event hash-chained gateway evidence log.

The operational gate deliberately ignores whether the task passed. It is
green because the externally observable infrastructure contract worked.

## Behavioral result

The participant did not issue `F`, so no hidden evaluation ran. Its accepted
opcode trajectory was:

```text
I C R R C L R W I
```

Five recoverable errors were returned across four attempted `S` turns:

1. an invalid patch identifier;
2. a string where the outer Session ISA required an argument array;
3. the word `match` where Motion v1 required a root reference;
4. a binding identifier where Motion v1 required an opcode; and
5. mutation-budget exhaustion on the final turn.

Three structurally invalid Motion submissions consumed all three mutation
attempts before a semantically applicable candidate existed. The fourth
structurally valid-enough attempt was therefore rejected at the budget guard.
This ended as `model_turn_limit_exhausted`, classified as a product failure.

## What the canary falsified

### Schema admission is not schema enforcement

The exact tool schema was accepted and transported by Bedrock, but the model
still emitted a tool call whose `a` property was a string despite the schema's
`type: array`. The existing provider capability probe established schema
admission; it never established constrained decoding. The canary now gives us
direct evidence that the two properties must not be conflated.

This does not show that JSON Schema or the Session ISA is useless. The local
validator rejected every malformed instruction without corrupting the
workspace. It shows that correctness still depends on deterministic
post-generation validation and recovery unless the inference backend offers a
separately verified grammar-constrained decoder.

### The mutation budget currently charges representation errors

`ConfirmatorySession._submit` increments the mutation counter before the
Motion payload is decoded and validated. Therefore serialization and grammar
failures consume the same scarce budget as accepted workspace mutations. If
left unchanged, the confirmatory outcome would combine at least two effects:

- whether a realization helps the model express a valid instruction; and
- whether the resulting semantic mutation solves the programming task.

That may be a legitimate composite outcome, but it is not yet the clean
semantic-effect estimand the experiment intends to claim. The budget boundary
must be made explicit before the remaining cells can be interpreted.

### Typed history is still not reduced state

Post-turn requests replaced natural-language chat history with a typed action
list, but the list is append-only. Repeated inspections and reads remain in
every later request. The canary therefore implemented a structured transcript,
not a normalized state IR.

The growth is visible in provider-native usage:

| Turn | Request bytes | Input tokens |
| ---: | ---: | ---: |
| 1 | 14,433 | 4,667 |
| 2 | 26,799 | 8,447 |
| 6 | 29,164 | 9,376 |
| 10 | 31,642 | 10,158 |
| 12 | 36,740 | 11,845 |

Turn 12 carried 2.54 times the input tokens of turn 1. The absolute increase
is not merely conversational prose: a large initial inspection and later
repeated context reads were retained as historical actions even when newer
state made parts of them redundant.

This is a concrete instance of the project's central thesis: changing the
syntax of the transcript does not turn it into state.

## Claim boundary

- The Bedrock execution path is operational for the frozen model and adapter.
- One behavioral product failure was observed in one preselected
  `meaningful_nested` cell.
- No comparison between lexicalization or packaging conditions exists.
- No representational effect, efficacy, interaction, or generalization claim
  is supported.
- The canary remains the first campaign observation, but its behavioral result
  may not authorize or shape release of the other cells.
- The remaining 959 cells are still blocked.

## Next red tests

Before campaign release, freeze and test two separable protocol corrections:

1. **Validation accounting:** distinguish malformed/unapplied instructions
   from accepted workspace mutations, and predeclare which budget each class
   consumes.
2. **State reduction:** replace the append-only action list with a canonical
   current-state projection containing the live program/workspace digest,
   current handles and capabilities, unresolved validation frontier, latest
   relevant observations, and remaining budgets.

Then run a provider-free replay proving that both corrections preserve the
four-condition information boundary. A new external canary, if desired, will
require a new cell, launch record, and explicit authorization; canary 001 has
zero retry authority.

## Evidence

- [`representational-confirmatory-canary-launch-001.json`](construction/representational-confirmatory-canary-launch-001.json)
  binds the exact authorization, cell, hashes, provider, and limits.
- [`representational-confirmatory-canary-launch-001.preflight.json`](construction/representational-confirmatory-canary-launch-001.preflight.json)
  records source integrity, credential presence, current rates, and the
  behavior-blind gate design.
- [`result.json`](observations/representational-confirmatory-canary-001/result.json)
  records the operational and behavioral outcomes without conflating them.
- [`tool-transcript.json`](observations/representational-confirmatory-canary-001/evidence/tool-transcript.json)
  contains the typed instructions, deterministic results, and recoverable
  errors.
- [`gateway-events.jsonl`](observations/representational-confirmatory-canary-001/evidence/gateway-events.jsonl)
  is the hash-chained provider-routing record.
- [`artifact-lock.json`](observations/representational-confirmatory-canary-001/publication/artifact-lock.json)
  seals the complete observation tree.
