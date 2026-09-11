# Explicit Session State Replay v1

## Status

**A deterministic replay replaced accumulated assistant/tool history with one
typed session-state snapshot before each recorded request. All 131 observed tool
actions reproduced their original normalized results without a model call. The
canonical request surface fell 17.73% overall: 41.64% for source and 4.56% for
semantic. Compaction paid a 43.14% aggregate overhead at turn two and crossed
break-even at turn four. Full semantic inspection subtrees are now the dominant
state cost. This establishes action-result replay and a local byte curve, not
model-choice or provider-token equivalence.**

The generated bundle contains 13 files with tree digest
`3cd6f296651d5133c37fefba3942cef2aa34b8c9e1b3e6b228c9f5b77d15fdaa`.
It binds the Calibration 004 result and artifact lock, the matched execution
freeze, the state schema, the replay policy, and one exact state trajectory per
provider-call cell.

## Replay contract

The original request history grew as:

```text
system + user + assistant/tool + assistant/tool + ...
```

For every request after turn one, the replay constructs:

```text
initial system + initial user + SESSION_STATE/v1
```

The state snapshot contains:

- disjoint context, workspace, and semantic-handle namespaces;
- current workspace paths, hashes, and UTF-8 contents;
- context artifacts already read;
- the latest semantic inspection for each inspected handle;
- at most eight distinct typed errors with counts and last occurrence;
- only the latest public evaluation and submission result; and
- mutation, evaluation, opcode, validation, terminal, and remaining-budget
  counters.

It does not contain hidden evaluators, references, host repository access,
credentials, provider history, or private chain of thought. Errors, evaluations,
and submissions are bounded collections; workspace and inspection state remain
bounded by the frozen task and inspected handle set.

## Equivalence check

The replay materializes each task from its frozen baseline and executes the
recorded `x` instructions in their original order. Before every response action,
it captures the explicit state and constructs the compact request. It then
compares every resulting tool record with the retained Calibration 004 record.

All 101 turns and 131 tool actions match. Equality is byte-exact after
canonicalizing only evaluator-runtime noise:

- the absolute temporary workspace path;
- Deno's cache-dependent `Check ...` progress line; and
- per-test millisecond durations.

Canonicalization is applied only to evaluator `stdout` and `stderr`. Workspace
reads, context reads, inspections, patches, errors, hashes, classifications, and
all other tool results remain exact.

This proves deterministic operational replay of recorded actions. It does not
prove that a model shown the compact request would choose those actions.

## Aggregate measurement

Counts use sorted, minified UTF-8 JSON for the complete request, including
messages, tool schema, model, and sampling fields.

| Surface | Original history | Explicit state | Change |
| --- | ---: | ---: | ---: |
| Source, 49 requests | 522,198 B | 304,774 B | -41.64% |
| Semantic, 52 requests | 947,564 B | 904,342 B | -4.56% |
| **Combined, 101 requests** | **1,469,762 B** | **1,209,116 B** | **-17.73%** |

The explicit state removes 260,646 canonical bytes overall. It is smaller in
37/43 post-initial source requests and 23/47 post-initial semantic requests.

## Break-even by turn

| Turn | Active cells | Change | Beneficial cells |
| ---: | ---: | ---: | ---: |
| 1 | 11 | 0.00% | 0 |
| 2 | 11 | +43.14% | 0 |
| 3 | 11 | +4.27% | 7 |
| 4 | 11 | -5.85% | 7 |
| 6 | 11 | -22.02% | 7 |
| 9 | 6 | -24.88% | 6 |
| 12 | 5 | -38.64% | 5 |

The snapshot is not free. At turn two it repeats current workspace and working
state before enough transcript has accumulated to amortize that materialization.
The aggregate curve crosses at turn four and continues improving through the
longest trajectories. Explicit state is therefore a horizon-dependent trade,
not a universal first-turn compression.

## Per-cell direction

All six source cells shrink, ranging from -21.71% to -52.03%. Semantic is
heterogeneous:

| Semantic cell | Change |
| --- | ---: |
| Error taxonomy | +1.14% |
| Normalization policy | +5.29% |
| Raw-ID retry | +13.13% |
| Reserved-ID guard | -22.92% |
| Directory fallback | -5.08% |

The aggregate semantic reduction is produced by the two long failed
trajectories where history became larger than the retained working state. Three
semantic cells become more expensive under the conservative snapshot.

## State-cost decomposition

Across all semantic snapshots, component bytes are:

| Semantic state component | Repeated bytes |
| --- | ---: |
| Semantic inspections | 394,439 B |
| Workspace | 172,835 B |
| Context reads | 22,693 B |
| Typed errors | 21,667 B |
| Counters | 14,144 B |
| Evaluations | 12,637 B |
| Namespaces | 11,336 B |
| Submissions | 7,062 B |

The inspection cache is 2.28 times the repeated semantic workspace and alone
explains why semantic state barely crosses aggregate break-even. It retains full
subtrees for every inspected handle because the replay deliberately chose a
conservative sufficient-state policy before testing liveness or eviction.

For source, workspace contents are the largest state component at 149,308
bytes, yet replacing repeated diffs, evaluator output, and dialogue still
creates a large net reduction.

## Claim boundary

- No model or provider call occurred or is authorized by this bundle.
- Canonical UTF-8 bytes are not provider-native tokens.
- Recorded-action result equivalence is not model-choice equivalence.
- The replay preserves model-visible outcomes, not hidden evaluation state or
  private reasoning.
- The compactor is evaluated on one frozen run and is not yet an online agent
  memory policy.
- Full workspace contents make the snapshot conservative and auditable, not
  minimal.

## The next red test

The next recorte is now specific: split semantic inspection into a persistent
capability index and an evictable subtree working set. A compact snapshot should
retain handle, node identity, scope, state token, and target token while moving
large subtrees behind deterministic `I` re-fetch. The red test is whether every
recorded semantic submission can still be reconstructed from the retained live
set plus explicit re-fetches, without oracle knowledge of the next action.

Only after that construction gate should an online compacted-session model run
be considered. The experimental sequence is now:

`transcript history -> explicit session state -> semantic working-set liveness`.
