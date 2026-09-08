# Representational power-sensitivity curve v0

## Status

**Call-free sensitivity valid; its scientific selection is now frozen in a
separate artifact, while finite-sample and launch decisions remain blocked.**
The frozen grid contains 64 scenarios crossing four baseline Pass@1 rates,
four absolute smallest effects of interest, and four null task-level
intraclass correlations. It reports the approximate number of fresh tasks,
four-condition cells, maximum requests, and descriptive cost scale for every
scenario. It deliberately selects none of them.

The materialized curve contains two data files with tree digest
`98eaf94295550d14a08560c1966576bfcdfec86e5612137a099329c069525b6b`.
Its artifact-lock digest is
`ad41a640646687b2fb3c6a40f6e3fe24c175e547e6258579f918433dbe329873`.
No model or provider call occurred and no spend was incurred.

## Why the unit is a task

Each fresh task is evaluated once in all four representational conditions,
using independent sessions and a balanced order. The primary lexical contrast
averages the meaningful-minus-opaque difference across both packaging levels;
the primary packaging contrast averages nested-minus-table across both
lexicons. The resulting task-level contrast, not any individual request, is
the unit of analysis.

Repeated requests could reduce uncertainty about one task's trajectory, but
they would not create new task diversity. Counting them as independent units
would be pseudoreplication and would overstate what can generalize to unseen
tasks.

## Frozen sensitivity model

For each scenario, latent task difficulty is represented by a probability
`theta` with mean baseline `p` and variance `rho * p * (1 - p)`. Under the null,
the four condition outcomes are conditionally independent Bernoulli draws with
probability `theta`; `rho` is therefore their intraclass correlation.

An effect of absolute magnitude `delta` is evaluated in both directions:

- a proportional rescue maps `theta` to
  `theta + delta / (1 - p) * (1 - theta)`; and
- a proportional harm maps `theta` to
  `(1 - delta / p) * theta`.

Both constructions preserve valid probabilities and produce exact marginal
changes of `+delta` and `-delta`. The curve retains the direction requiring
more tasks, avoiding a favorable directional assumption.

The task count uses a two-sided normal approximation with unequal null and
alternative task-contrast variances:

```text
n = ((z_(1-alpha*/2) * sqrt(V0) + z_power * sqrt(V1)) / delta)^2
```

`alpha*` is 0.025, the smallest Holm threshold when controlling familywise
alpha 0.05 across the two primary main effects. Target power is 0.80. The raw
count is rounded upward to complete four-task counterbalancing blocks.

This is an explicit design model, not a distribution-free guarantee. The
normal approximation is not exact, order and task-family effects are not yet
modeled, and the secondary interaction is not powered.

## Frozen grid

| Input | Values |
| --- | --- |
| Baseline hidden Pass@1 | 0.20, 0.40, 0.60, 0.80 |
| Absolute main-effect SESOI | 0.05, 0.10, 0.15, 0.20 |
| Null within-task ICC | 0.00, 0.25, 0.50, 0.75 |
| Primary hypotheses | 2 |
| Familywise alpha | 0.05 |
| Target power per primary | 0.80 |

All 64 combinations permit both directional alternatives. The grid is broad
enough to expose sensitivity; it is not evidence that every point is equally
plausible.

## Resulting scale

Across the complete grid:

| Projection | Minimum | Maximum |
| --- | ---: | ---: |
| Fresh task units | 16 | 920 |
| Four-condition cells | 64 | 3,680 |
| Maximum requests at 12 per cell | 768 | 44,160 |
| Calibration-008 mean-rate cost | USD 15.73 | USD 904.23 |
| Calibration-008 observed-maximum-rate cost | USD 18.87 | USD 1,084.85 |

At baseline 0.60, a useful cross-section is:

| SESOI | Null ICC | Tasks | Cells | Mean-rate cost | Max-rate cost |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 0.00 | 920 | 3,680 | USD 904.23 | USD 1,084.85 |
| 0.05 | 0.50 | 472 | 1,888 | USD 463.91 | USD 556.57 |
| 0.10 | 0.00 | 232 | 928 | USD 228.02 | USD 273.57 |
| 0.10 | 0.50 | 124 | 496 | USD 121.87 | USD 146.22 |
| 0.15 | 0.00 | 104 | 416 | USD 102.22 | USD 122.63 |
| 0.15 | 0.50 | 56 | 224 | USD 55.04 | USD 66.03 |
| 0.20 | 0.00 | 60 | 240 | USD 58.97 | USD 70.75 |
| 0.20 | 0.50 | 32 | 128 | USD 31.45 | USD 37.73 |

Positive within-task correlation lowers the variance of a paired contrast in
this model. That is why higher ICC scenarios can require fewer fresh tasks;
the curve does not treat correlated cells as independent observations.

## Cost boundary

Cost projections multiply the required cells by Calibration 008's descriptive
mean and maximum observed semantic-cell costs. The new representations differ
in byte size and may change both tokenization and trajectories, so these are
scale indicators, not budgets or forecasts. No scenario, request ceiling,
spend ceiling, or launch has been selected.

## Decision exposed and subsequently frozen

The sensitivity exposed the following scientific decisions:

1. choose a defensible SESOI separately for lexical and packaging effects;
2. choose the baseline and ICC planning envelope, including whether to use a
   conservative corner or an externally justified prior range;
3. define the fresh task-family mixture that determines the target population;
4. validate the selected asymptotic design with deterministic simulation; and
5. only then construct fresh instances, audit contamination, and freeze a cost
   ceiling.

Power Selection Freeze v0 subsequently fixed both main-effect SESOIs at 0.10,
selected baseline 0.20–0.80 and null ICC 0.00–0.75 as the planning envelope,
and defined an equal five-family task mixture. The continuous-envelope maximum
and joint rounding produce a 240-task asymptotic candidate. Selecting a cheap
row because it is cheap would have reversed the intended order of evidence;
the separate freeze records the choice before new outcomes. See
[`REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md`](REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md).

## Evidence

- [`curve.json`](construction/representational-power-sensitivity-v0/curve.json)
  is the canonical machine-readable sensitivity record.
- [`curve.csv`](construction/representational-power-sensitivity-v0/curve.csv)
  provides the same scenario grid for inspection and plotting.
- [`representational_power_sensitivity.py`](scripts/representational_power_sensitivity.py)
  implements the task-level moment calculation.
- [`build_representational_power_sensitivity.py`](scripts/build_representational_power_sensitivity.py)
  materializes the curve, cost scale, integrity dependencies, and red gates.

The paired-binary distinction follows the dependence warning in the sample-size
review by [Zhong](https://pmc.ncbi.nlm.nih.gov/articles/PMC5738522/). The
multiplicity boundary follows [Holm's original sequentially rejective
procedure](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf). The latent
binary-cluster parameterization is consistent with the beta-binomial ICC model
described by [Crowder](https://academic.oup.com/jrsssb/article/41/2/230/7027494).

## Next red test

Construct and freeze the deterministic finite-sample simulation protocol for
the selected 240-task candidate. Validate null type-I behavior and both effect
directions under the frozen envelope before constructing fresh tasks.
