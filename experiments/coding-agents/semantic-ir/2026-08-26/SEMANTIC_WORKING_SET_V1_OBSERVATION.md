# Semantic Working-Set Replay v1

## Status

**A deterministic semantic replay split persistent target capabilities from an
LRU of full subtrees. A two-subtree working set was the smallest tested capacity
that reconstructed all 24 recorded semantic submissions. It required five
current-action `I` re-fetches and reproduced all 61 recorded action results
without a model call. After conservatively charging both re-fetch instructions
and results, the effective surface was 710,631 bytes: 21.42% below Explicit
Session State Replay v1 and 25.00% below the original transcript requests. A
one-subtree control was smaller but failed three width-two submissions. This is
an operational replay result, not evidence that a model would choose the same
actions from compact state.**

The generated bundle contains eight files with tree digest
`b0bde06ed3cbc2a1b601e2bdf8d2706d96a081df274342ce907a413adb8bfd2c`.
It binds the Calibration 004 observation, Explicit Session State Replay v1,
the working-set schema and policy, five semantic cell trajectories, and the
builder implementation.

## Working-set contract

Every successful semantic inspection is split into two layers:

- a persistent capability index containing handle, node identity, operation,
  parent, slot, scope, state token, and target token; and
- an evictable LRU containing only the handle and full subtree.

The policy receives no next action or future transcript. When the current `S`
instruction arrives, the runtime extracts its target handles. Missing handles
produce one deterministic `I` instruction against the local semantic store
before `S` is dispatched. Hits refresh LRU order. The evidence records the
instruction, result, canonical exchange bytes, required handles, resident
handles, and whether the current submission became reconstructible.

The capacity grid `[1, 2, 4, 8, 16]` was evaluated over one replay of the same
frozen actions. It was not adaptively reordered or stopped after a favorable
result.

## Replay equivalence

The five supported semantic cells contain 52 provider turns, 61 tool actions,
and 24 `S` submissions. All 61 action results reproduce the Calibration 004
records after the same evaluator-only canonicalization used by Explicit
Session State Replay v1.

The primary capacity of two reconstructs 24/24 submissions. Its five re-fetches
restore five targets and contribute 4,548 bytes. They are local deterministic
operations, not provider calls, but their complete instruction and result bytes
are charged to avoid treating cache misses as free.

This establishes that the frozen submissions can execute through a bounded
live-subtree state. It does not establish that a model shown that state would
generate those submissions.

## Capacity curve

All sizes use sorted, minified UTF-8 JSON. `Effective` is compacted request
bytes plus canonical re-fetch instruction and result bytes.

| LRU capacity | Re-fetches | Unsatisfied `S` | Effective | vs explicit state | vs transcript |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 7 | 3 | 700,609 B | -22.53% | -26.06% |
| **2** | **5** | **0** | **710,631 B** | **-21.42%** | **-25.00%** |
| 4 | 1 | 0 | 746,467 B | -17.46% | -21.22% |
| 8 | 1 | 0 | 825,127 B | -8.76% | -12.92% |
| 16 | 0 | 0 | 929,909 B | +2.83% | -1.86% |

Capacity one is not a valid success despite having the smallest byte total.
Three recorded submissions target two distinct handles, which cannot coexist in
a one-entry working set. Capacity two is therefore the smallest viable point on
this trace, not merely the cheapest successful point selected after the fact.

The curve also exposes the opposite failure mode. Capacity sixteen eliminates
re-fetches, but retaining every full subtree alongside the capability index
makes it 2.83% larger than the prior explicit-state baseline. Avoiding all
faults is not the byte optimum.

## State-cost decomposition

Across the 52 capacity-two snapshots:

| Component | Repeated bytes |
| --- | ---: |
| Persistent capability index | 178,756 B |
| Two-subtree working set | 24,554 B |
| Working-set policy and counters | 9,796 B |

The capability index plus live subtrees occupies 203,310 repeated bytes,
48.46% below the 394,439 bytes previously occupied by full semantic inspections.
The complete request improvement is smaller because workspace, context reads,
errors, evaluations, submissions, tools, and initial messages remain unchanged.

## Claim boundary

- No model or provider call occurred or is authorized by this bundle.
- Canonical UTF-8 bytes are not provider-native tokens.
- Recorded-action result equivalence is not model-choice equivalence.
- Re-fetch happens after the current `S` is available; it proves runtime
  reconstruction, not that the evicted subtree was unnecessary for generation.
- The trusted local semantic store remains the authoritative backing state.
- LRU capacity two is a result on one frozen trace, not a universal optimum.
- Capacity one is an explicit negative control and must not be reported as a
  successful compression result.

## The next red test

The next checkpoint should freeze a matched compacted-session execution before
any new model call. Source cells should receive Explicit Session State v1;
semantic cells should receive the capacity-two capability/working-set policy
with deterministic `I` fault handling. The freeze must bind the exact request
builder, runtime transition rules, paired schedule, limits, evidence accounting,
and a separate explicit launch authorization.

Only after local references and preflight pass should a fresh Calibration 005
ask whether models shown compact state choose valid actions with lower provider
input, rather than merely whether recorded actions can be replayed.
