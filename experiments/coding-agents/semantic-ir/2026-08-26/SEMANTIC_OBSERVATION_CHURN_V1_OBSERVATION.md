# Semantic Observation Churn Replay v1

## Status

**Local replay complete. Calibration 005's semantic working set churn was not
caused only by repeated model inspection. The capacity-two LRU counted
overlapping handles as independent cache entries even when one retained
ancestor subtree structurally contained the requested descendants. Across 49
inspection calls, 112 of 167 target transfers were redundant under ancestry
coverage and the observed handle LRU produced 140 evictions. A coverage-aware
antichain with the same numeric capacity reduces those evictions to zero and
keeps all eight valid recorded submissions reconstructible, but increases the
counterfactual model-visible state by 12.85%. This is a local fixed-action
replay, not evidence that the model would make better choices.**

The replay is bound to Calibration 005's result and artifact lock. It processes
the exact 60 recorded semantic turns, makes no model call, uses no future action
to admit observations, and does not claim provider-native token equivalence.

## Observed churn

| Measure | Calibration 005 semantic trace |
| --- | ---: |
| Semantic call cells | 5 |
| Recorded turns | 60 |
| Inspection calls | 49 |
| Transferred target records | 167 |
| Unique inspected handles | 39 |
| Repeated target transfers | 128 |
| Exact repeated inspection signatures | 30 |
| Inspections with no new handle | 43 |
| Structurally redundant targets within inspection results | 112 |
| Handle-LRU evictions | 140 |
| Valid semantic submissions | 8 |

Thus 76.65% of target transfers revisited a handle and 87.76% of inspection
calls discovered no new handle. More importantly, 67.07% of transferred target
records were descendants already contained by another target subtree returned
in the same inspection.

This last distinction changes the diagnosis. Repetition is partly agent
behavior; treating every overlapping handle as an independent capacity unit is
an infrastructure choice.

## The candidate policy

`Coverage Antichain LRU v1` changes only the working-set admission unit:

- capabilities and target tokens remain persistent by handle;
- full subtree residency is normalized to maximal requested ancestors;
- a descendant maps to the resident root that structurally covers it;
- a new ancestor coalesces any resident descendant roots;
- LRU eviction occurs only between disjoint roots;
- a repeated inspection of already covered handles produces a receipt rather
  than admitting another copy of the subtree;
- current-submit refetch remains driven only by the handles in the current `S`;
- no future action, reference patch, hidden evaluation, or oracle enters the
  policy.

This is closer to a graph slice than a bag of JSON subtrees: handle identity is
preserved, while shared structure is represented once.

## Capacity curve

| Root capacity | Evictions | Receipt-only inspections | Admitted roots | Submit refetches | Unsatisfied submits | All valid submits reconstructible |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 15 | 38 | 20 | 8 | 8 | No |
| 2 | 0 | 43 | 7 | 0 | 0 | Yes |
| 4 | 0 | 43 | 7 | 0 | 0 | Yes |

Capacity one is the negative control: the error-taxonomy task requires two
disjoint roots to keep sibling targets simultaneously available. Capacity two
is therefore the smallest observed viable antichain. Capacity four retains no
additional root and changes no replay outcome.

At capacity two, the five cells finish with at most two roots each. Error
taxonomy needs two disjoint roots; normalization, reserved-ID guard, and
directory fallback each collapse to one ancestor root; raw-ID retry needs at
most two.

## The byte trade-off

The candidate removes structural cache churn, but it retains larger ancestor
subtrees instead of the small descendant leaves that happened to survive the
handle LRU.

| Model-visible state measure | Observed handle LRU | Coverage antichain | Change |
| --- | ---: | ---: | ---: |
| Complete typed state bytes over turns 2-12 | 449,360 | 507,096 | +12.85% |
| Observation components only | 218,219 | 275,955 | +26.46% |
| Resident subtree bytes not covering a submitted target | 33,922 | 74,083 | +118.39% |

The final row is deliberately not labeled waste. Four cells never submitted a
semantic patch, so all resident context in those traces fails the narrow
"covers a submitted target" test even if it may have supported planning.

The candidate's cost is therefore explicit: pay roughly 58 KB more state over
the fixed trace to retain coherent structural context and eliminate 140
evictions. A provider experiment would be needed to learn whether that context
reduces inspection turns enough to repay the larger state.

## What this establishes

The replay makes three claims that survive the local gate:

1. **Capacity by handle is the wrong abstraction for overlapping AST views.**
   It can evict an ancestor and retain duplicated descendants even when the
   ancestor covers the entire requested set.
2. **Capacity two was not intrinsically too small.** The same number is enough
   when it counts disjoint coverage roots; capacity one still fails as expected.
3. **Progress preservation has a measurable price.** Coverage eliminates
   structural churn but increases fixed-trace state bytes. The optimization
   target must include action count, not only bytes per request.

The replay does not establish that 43 future calls disappear, that Pass@1
improves, or that provider tokens follow canonical byte ratios. The recorded
model choices are inputs to the counterfactual state machine, not outputs from
it.

## Relationship to the AI-native language hypothesis

This failure is a small concrete instance of the broader representation
problem. The semantic content was already present, but it was packaged as
independent JSON subtrees. The runtime could not express that several handles
were views into the same underlying structure, so its memory policy charged and
evicted them independently.

An agent-native IR needs identity, sharing, and coverage to be first-class. A
tree-shaped wire format can serialize a graph, but without graph semantics the
agent infrastructure still behaves as if every repeated subtree were new
state.

## Claim boundary

- The source is one repeated within-instance calibration over five supported
  semantic cells.
- The exact instruction sequence is replayed; counterfactual model-choice
  equivalence is false.
- Canonical UTF-8 JSON bytes are construction metrics, not provider tokens.
- No model call, hidden-evaluator feedback, or future action is used.
- The coverage relation is derived only from node identity inside the current
  inspected subtrees.
- The policy is a candidate construction, not a frozen execution interface.

## The next red test

Implement `Coverage Working-Set State v2` as a local runtime projection with an
explicit `covered_by` index and root-based capacity. It must pass three gates
before any provider launch:

1. reproduce every frozen known-reference semantic submission and hidden pass;
2. preserve exact dispatch results for the Calibration 005 recorded actions
   wherever model choice is not involved; and
3. expose the byte/action trade-off explicitly in a matched freeze rather than
   assuming that zero evictions implies lower total cost.

The next hypothesis is:

`semantic memory should count disjoint structural coverage, not serialized
handles`.
