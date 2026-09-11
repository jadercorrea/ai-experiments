# Construction observation: compact-IR token break-even curve

## Outcome

Compact IR reached the pre-registered sustained observed break-even at **eight
function bodies**. It used more total provider tokens at sizes 1, 2, and 4,
then fewer at both measured points 8 and 16.

| Function bodies | TypeScript total | Compact total | Compact change |
| ---: | ---: | ---: | ---: |
| 1 | 1,920 | 2,022 | +5.31% |
| 2 | 2,110 | 2,176 | +3.13% |
| 4 | 2,462 | 2,484 | +0.89% |
| 8 | 3,354 | 3,100 | **−7.57%** |
| 16 | 4,494 | 4,332 | **−3.60%** |

Every one of the ten cells used one provider request, made one terminal
submission, and passed the same public and hidden executable behavior. No cell
received test feedback or a correction opportunity.

This is a descriptive curve for one synthetic repeated-body task family. It is
not an estimate of coding-agent performance over natural repository work and
does not authorize an efficacy claim.

## Frozen design

The grid `[1, 2, 4, 8, 16]` and all ten cells were frozen before model calls.
There was no adaptive stopping. Arm order alternated by size, and the observed
break-even definition was fixed as:

> The smallest measured size where compact total tokens are at or below source
> and remain so at every larger measured size.

Both arms received byte-identical messages within each size pair. Function
headers and ABI metadata were compiler-supplied for both arms. The source arm
submitted one TypeScript function body per slot; the compact arm submitted one
tuple/opcode program per slot. Their tool schemas stayed constant across the
entire grid.

This boundary intentionally measures body-representation amortization rather
than full-file authoring. The repeated function bodies all implement the same
user-lookup contract, but each is independently compiled and exercised.

## Detailed measurements

| Bodies | Source input | Compact input | Source output | Compact output | Source payload | Compact payload |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,761 | 1,903 | 159 | 119 | 305 B | 167 B |
| 2 | 1,831 | 1,973 | 279 | 203 | 573 B | 333 B |
| 4 | 1,971 | 2,113 | 491 | 371 | 1,105 B | 665 B |
| 8 | 2,251 | 2,393 | 1,103 | 707 | 2,509 B | 1,281 B |
| 16 | 2,811 | 2,953 | 1,683 | 1,379 | 3,921 B | 2,657 B |

The compact contract imposed exactly **142 additional input tokens** at every
point. Break-even occurred when output savings exceeded that fixed tax. At four
bodies the compact arm saved 120 output tokens and still lost by 22 total. At
eight it saved 396 output tokens and won by 254 total.

Across the complete fixed grid:

- compact IR used 14,114 total tokens versus 14,340 for source, a 1.58% saving;
- compact output used 2,779 tokens versus 3,715, a 25.20% saving;
- compact solution payloads used 5,103 bytes versus 8,413, a 39.34% saving;
- estimated compact cost was $0.075690 versus $0.087600, a 13.60% saving.

The cost reduction is larger than the total-token reduction because output
tokens cost five times as much as uncached input tokens under the frozen price
schedule.

## Why the curve is not monotonic

Compact's advantage was larger at eight bodies than at sixteen. That is not a
mathematical reversal of the encoding ratio; it is trajectory variation.

The compact outputs were structurally stable: every submitted program occupied
159–165 serialized characters. Source output was more variable. At eight
bodies, individual TypeScript bodies ranged from 229 to 401 characters. At
sixteen, the model converged on one concise 229-character body and repeated it
uniformly. That source-side compression reduced compact's observed lead.

Temperature zero does not make outputs at different prompts counterfactual
copies of one another. Prompt length changes the generation context, and this
experiment has one trajectory per point. The result therefore supports an
observed crossing at eight, not a smooth universal cost function.

## Interpretation

The earlier single-shot result showed that compact output can be much denser
while fixed input overhead erases the whole-request gain on a tiny task. This
curve demonstrates the predicted amortization mechanism under a controlled
repeated-body workload:

```text
compact total = shared task context
              + fixed compact-grammar tax
              + smaller per-body output
```

The fixed grammar tax was paid once per request, while body savings accumulated.
The observed crossing at eight is evidence that the transport/core separation
can become token-positive without changing the validator or target runtime.

It does not establish that eight functions is the general break-even point.
Natural tasks contain heterogeneous logic, shared helpers, imports, edits, and
repository navigation. The source arm may compress repeated work using language
abstractions that this compact v0 cannot express. Conversely, a persistent
agent runtime could avoid retransmitting the compact grammar entirely.

## Next gate

The next experiment should leave synthetic repetition behind. Freeze a small
set of fresh heterogeneous tasks at three solution-size bands, retain the same
compact grammar, and compare semantic patches against source patches rather
than whole bodies. That tests whether the observed amortization survives real
variation and persistent state.

## Evidence

- [`break-even-001`](observations/break-even-001) contains all ten requests,
  responses, gateway events, materialized workspaces, and evaluator results.
- [`break-even-comparison-v0.json`](construction/break-even-comparison-v0.json)
  freezes the grid, ordering, prompt digests, model, accounting, and validity
  rules.
- [`break_even_comparison.py`](scripts/break_even_comparison.py) implements the
  size-invariant tools, deterministic assemblers, evaluators, and curve rule.
