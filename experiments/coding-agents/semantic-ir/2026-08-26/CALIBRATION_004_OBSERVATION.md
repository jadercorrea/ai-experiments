# Matched Session ISA calibration 004

## Status

**Execution valid and complete as a descriptive calibration. The local
known-reference byte advantage did not survive model-driven trajectories. On
six frozen tasks, source passed 2 hidden evaluations and semantic passed 1. On
the five supported pairs, semantic generated 18.0% fewer output tokens but used
20.9% more requests, 86.8% more input tokens, 78.6% more total tokens, and 55.5%
more estimated cost. No infrastructure-invalid cell occurred. The sample and
development exposure do not authorize an inferential or general efficacy
claim.**

Calibration 004 executed all twelve cells under freeze
`c2e49b3b32c2e9af6c577cab70c425a6ab74637744a01b9557535c6eca3f6232`.
The evidence lock contains 279 files with tree digest
`d2668917dfb99788f60eb9e4f9d2646a2b4b03b88c38c6202ba777fc3cbea202`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 101 |
| Input tokens | 523,748 |
| Output tokens | 29,007 |
| Total tokens | 552,755 |
| Estimated cost | USD 2.006349 |
| Public evaluator runs | 15 |
| Repair cycles | 15 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 101 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. Provider usage, cell costs, schedule
identities, launch and freeze bindings, the exact shared `x` tool, and the
artifact lock reconcile. Request and evidence scans found no reference,
hidden-evaluator, keychain identity, bearer token, or credential-shaped value.

The account-level Amazon Bedrock retention mode remained unreadable by the
inference-scoped credential (`403`) and is not claimed. The launch records the
current public service-policy basis and this limitation.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 2 | 1 |
| Supported-task hidden Pass@1, denominator 5 | 2 | 1 |
| Semantic applicability | — | 5 / 6 |
| Provider requests, all-task accounting | 49 | 52 |
| Input tokens, all-task accounting | 192,714 | 331,034 |
| Output tokens, all-task accounting | 16,616 | 12,391 |
| Total tokens, all-task accounting | 209,330 | 343,425 |
| Estimated cost, all-task accounting | USD 0.827382 | USD 1.178967 |

The automatic unsupported semantic cell makes all-task resource accounting
slightly favorable to semantic because it costs zero. Across only the five
supported pairs, the comparison is:

| Supported-task resource | Source | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Provider requests | 43 | 52 | +20.9% |
| Input tokens | 177,187 | 331,034 | +86.8% |
| Output tokens | 15,112 | 12,391 | -18.0% |
| Total tokens | 192,299 | 343,425 | +78.6% |
| Estimated cost | USD 0.758241 | USD 1.178967 | +55.5% |
| Sum of cell durations | 222.57 s | 264.38 s | +18.8% |

The denser instruction representation reduced generated output, as intended.
It did not reduce the accumulated input transcript. More semantic requests
repeated a larger initial state plus prior interaction history, overwhelming
the output saving.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | Hidden failure | Hidden failure |
| Normalization policy | Hidden pass | Turn-limit failure |
| Raw-ID retry | Turn-limit failure | Hidden pass |
| Reserved-ID guard | Hidden pass | Turn-limit failure |
| Directory fallback | Turn-limit failure | Turn-limit failure |
| Cross-module rename | Hidden failure | Unsupported by construction |

Among the five supported pairs there was one semantic-only pass, two source-only
passes, no joint pass, and two joint failures. The result is heterogeneous: the
semantic arm helped on raw-ID retry but hurt on normalization and reserved-ID
guard. Both representations failed the directory-effect task within the frozen
budget.

## Where the construction advantage was lost

The prior known-reference construction measured 23,256 semantic bytes versus
27,762 targeted-source bytes. It assumed the correct observation and mutation
trajectory. Calibration 004 charged model-selected trajectories instead.

The supported semantic cells made 52 requests and reached only two terminal
submissions; the matched source cells made 43 requests and reached three.
Semantic recorded 14 recoverable tool errors, 14 rejected instructions, 11
rejected patches, and 9 repair cycles. Source recorded 11 recoverable errors, 9
rejected instructions, 8 rejected patches, and 6 repair cycles. Semantic issued
24 submit instructions plus 9 inspections; source issued 20 submits.

These observations are consistent with two costs:

1. the model had more difficulty constructing valid positional semantic
   motions and recovering from typed rejection; and
2. each additional turn replayed a larger semantic state through a transcript
   transport with no provider caching.

The calibration does not isolate how much each mechanism caused. It establishes
that static reference-path density is insufficient to predict agent-path
efficiency.

## Relationship to Calibration 003

Calibration 003 found semantic hidden passes of 4/6 versus 2/6 source using a
larger, more explicit capability interface. Calibration 004 compressed both
arms behind one matched Session ISA and reversed the descriptive semantic
advantage to 1/6 versus 2/6.

That is not evidence that semantic IR itself became worse. Several things moved
together between calibrations: exact task bytes, context projection, motion
lexicalization, transport grammar, repair surface, and agent trajectories. The
result does show that interface compression can remove useful affordances even
when a deterministic decoder preserves formal validity.

## Interpretation boundary

- This is one unreplicated schedule over six family-derived tasks and one model
  endpoint.
- Exact instances were fresh to the experimental subject, but task families and
  protocol development were exposed to coding agents.
- Provider-native model identity is verified; model weights are not
  cryptographically pinned.
- Hidden Pass@1 is descriptive, not a powered statistical comparison.
- Turn-limit failures conflate navigation, mutation, repair, and budget effects.
- The run does not identify an optimal ISA, graph encoding, tokenizer, or
  semantic language.

No cell will be replaced or rerun under this freeze. Both inferential and
general efficacy claims remain unauthorized.

## The next red test

The experiment has now exposed a sharper problem than wire density: **a compact
instruction can still induce an expensive transcript**.

The next construction slice should preserve the exact frozen Session ISA and
replay evidence while replacing transcript accumulation with explicit session
state: bounded semantic working sets, typed error state, acknowledged facts,
and compaction that does not require the model to reconstruct prior tool turns.
It should first replay the failed trajectories deterministically and measure how
much historical input can be removed without changing the next valid action.

Only after that local replay gate should new instances or model calls be
considered. The next hypothesis is not “make the ISA denser.” It is:

`semantic state must replace transcript history, not merely travel inside it`.
