# Representational finite-sample simulation observation v0

## Result

**The first candidate passed. The finite-sample task count is 240.** All nine
global-null sentinels and all four isolated-primary alternatives satisfied the
predeclared Wilson-bound criteria. The frozen stop rule therefore selected 240
fresh tasks without evaluating 260–400.

The campaign completed 13 scenario streams and 260,000 Monte Carlo
replications under CPython 3.14.x. The result tree contains the complete
checkpoint and canonical result with tree digest
`0fa575e86b894be467d356a07d0acdd2fc76eafc482171f48ad3d8312c1ce8aa`.
No model call, provider request, fresh-task construction, or spend occurred.

## Null behavior

Each row reports the simulated probability that Holm rejected either primary
under the global null and the upper endpoint of its predeclared 95% Wilson
interval. Every upper endpoint had to be at most 0.06.

| Baseline | ICC | Rejections / 20,000 | Estimate | Wilson upper | Pass |
| ---: | ---: | ---: | ---: | ---: | :---: |
| 0.20 | 0.000 | 957 | 0.04785 | 0.05090 | yes |
| 0.20 | 0.375 | 1,039 | 0.05195 | 0.05511 | yes |
| 0.20 | 0.750 | 981 | 0.04905 | 0.05213 | yes |
| 0.50 | 0.000 | 1,069 | 0.05345 | 0.05665 | yes |
| 0.50 | 0.375 | 1,029 | 0.05145 | 0.05460 | yes |
| 0.50 | 0.750 | 972 | 0.04860 | 0.05167 | yes |
| 0.80 | 0.000 | 1,029 | 0.05145 | 0.05460 | yes |
| 0.80 | 0.375 | 1,015 | 0.05075 | 0.05388 | yes |
| 0.80 | 0.750 | 914 | 0.04570 | 0.04868 | yes |

The largest upper bound was 0.05665 at baseline 0.50 and ICC zero, leaving a
0.00335 margin below the acceptance ceiling. This checks the frozen sentinel
grid; it is not a proof over every continuous baseline/ICC pair.

## Power and inactive-primary behavior

Each isolated alternative carried an absolute Pass@1 effect of 0.10 at its
direction-specific worst asymptotic baseline and ICC zero. Active-primary power
required a Wilson lower bound of at least 0.80. The inactive primary's
false-positive probability required a Wilson upper bound of at most 0.06.

| Active primary | Direction | Power estimate | Power lower | Inactive estimate | Inactive upper | Pass |
| --- | --- | ---: | ---: | ---: | ---: | :---: |
| Lexical | Increase | 0.81230 | 0.80683 | 0.04565 | 0.04863 | yes |
| Lexical | Decrease | 0.80905 | 0.80354 | 0.04475 | 0.04770 | yes |
| Packaging | Increase | 0.81160 | 0.80612 | 0.04795 | 0.05100 | yes |
| Packaging | Decrease | 0.80725 | 0.80172 | 0.04545 | 0.04843 | yes |

Packaging/decrease was the limiting power scenario. Its lower endpoint cleared
the target by 0.00172. The smallest candidate therefore passes, but not by a
margin that supports weakening any downstream control.

## Selection consequence

The asymptotic candidate is now the finite-sample-selected design:

| Quantity | Selected value |
| --- | ---: |
| Fresh task units | 240 |
| Task families | 5 |
| Tasks per family | 48 |
| Conditions per task | 4 |
| Condition cells | 960 |
| Counterbalancing sequences | 4 |

Calibration 008's prior rate basis still gives descriptive projections of USD
235.89 at its mean cell cost, USD 283.00 at its observed maximum cell cost, and
11,520 requests at its maximum requests per cell. Simulation does not turn
those projections into a budget or authorize any provider call.

## Interpretation boundary

- The result validates 240 tasks under the frozen Beta latent-task generator,
  proportional effect transforms, sentinel scenarios, analysis, and criteria.
- It does not show that real task difficulty follows the Beta completion.
- It does not model family-specific baseline, ICC, or effect heterogeneity.
- The predeclared Wilson intervals are individual 95% intervals; simultaneous
  joint coverage across all reported event rates is not claimed.
- It does not establish that meaningful lexicalization or nested packaging has
  any behavioral effect. Those are future empirical estimands.
- The same participant LLM identity, version, inference parameters, budgets,
  and tools must later be frozen across all four conditions. No participant LLM
  was involved here.
- No fresh instance, contamination audit, exact execution freeze, cost ceiling,
  or launch exists yet.

## Evidence

- [`result.json`](observations/representational-finite-sample-simulation-v0/result.json)
  is the canonical selection result.
- [`checkpoint.json`](observations/representational-finite-sample-simulation-v0/checkpoint.json)
  retains all thirteen stream summaries, event counts, intervals, criteria,
  task count, and derived seeds.
- [`artifact-lock.json`](observations/representational-finite-sample-simulation-v0/publication/artifact-lock.json)
  seals both files.
- [`run_representational_finite_sample_simulation.py`](scripts/run_representational_finite_sample_simulation.py)
  is the exact runner recorded by digest in the result.
- [`REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_PROTOCOL_V0.md`](REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_PROTOCOL_V0.md)
  records the pre-outcome generator and acceptance choices.

## Next red test

Freeze the fresh-instance construction protocol for 240 tasks before creating
them. It must enforce 48 tasks per mechanism family, complete within-family
counterbalancing, new participant bytes and stable identities, deduplication
against every prior provider request, reference/evaluator separation, four-way
canonical observational equivalence, and no unplanned Session ISA or semantic
vocabulary extension. Only after local task validation should cost and provider
launch gates be considered.
