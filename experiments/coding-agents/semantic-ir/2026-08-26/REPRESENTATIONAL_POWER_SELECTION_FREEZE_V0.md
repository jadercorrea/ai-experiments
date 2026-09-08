# Representational power-selection freeze v0

## Status

**Scientific selection frozen; finite-sample validation and every execution
gate remain blocked.** Both primary effects now have an absolute Pass@1 SESOI
of 0.10. The planning envelope spans baseline probability 0.20–0.80 and null
within-task ICC 0.00–0.75. The target population is equally divided across
five mechanism families within the frozen Session ISA and semantic inspection
vocabulary.

The asymptotic candidate contains 240 fresh task units, 48 per family and 960
four-condition cells. This is a candidate for simulation, not a power claim,
provider budget, task suite, or launch.

The materialized selection contains one data file with tree digest
`0ed432f41697ff4221c918cb9ddc80a0616d1487f6e61b653412d79287341c2a`.
Its artifact-lock digest is
`85f44f331b6f956def87bb62fab02c8619ce15608aac2005e99a609487b98703`.
No model or provider call occurred and no spend was incurred.

## Frozen scientific choices

| Choice | Frozen value |
| --- | --- |
| Lexical absolute SESOI | 0.10 Pass@1 |
| Packaging absolute SESOI | 0.10 Pass@1 |
| Baseline envelope | 0.20–0.80 |
| Null within-task ICC envelope | 0.00–0.75 |
| Target power per primary | 0.80 |
| Familywise alpha | 0.05 |
| Multiplicity | Holm across two main effects |
| Interaction | Secondary, estimation-first |
| Task-family allocation | Equal across five families |

A ten-point absolute Pass@1 difference is small enough to avoid restricting
the study to only dramatic representational effects and large enough to be
operationally material for an infrastructure choice. The same threshold is
used for both primary effects so neither factor receives a more favorable
evidentiary standard.

This is an explicit engineering judgment, not an estimate learned from the
five provider-exposed construction fixtures. Those fixtures remain
confirmatory-ineligible.

## Conservative envelope rule

For SESOI 0.10 and baseline 0.20–0.80, the proportional rescue or harm
transform never exceeds 0.50. Under the frozen latent-task moment model, both
the null and alternative paired-contrast variances decrease as ICC increases
over that range. The conservative correlation boundary is therefore ICC 0.

A deterministic golden-section search over the continuous baseline interval
was run independently for increase and decrease. Each result was checked
against an independent 601-point baseline grid after first verifying the
source curve's content lock. The worst directional point was:

| Quantity | Value |
| --- | ---: |
| Direction | Increase |
| Baseline Pass@1 | 0.486251052 |
| Null ICC | 0.00 |
| Unrounded tasks | 236.503122 |

The symmetric decrease maximum lies on the other side of 0.50 and yields the
same design scale. The computation then rounds upward to a block that supports
both the four counterbalancing sequences and all five task families. Their
least common multiple is 20, producing 240 tasks.

## Frozen target population

The study targets fresh patch tasks expressible without extending the frozen
Session ISA or semantic inspection vocabulary. It does not claim to represent
all software engineering or all coding-agent workloads.

| Family | Operational boundary | Tasks | Weight |
| --- | --- | ---: | ---: |
| Capability lookup and fallback | Declared effectful lookup with ordered lazy fallback | 48 | 0.20 |
| Error/option taxonomy | Distinguish absence, typed failure, and successful value | 48 | 0.20 |
| Guarded retry/control flow | Bounded retry or fallback selected by an explicit guard | 48 | 0.20 |
| Identity/state consistency | Stable target identity and stale-state mutation protection | 48 | 0.20 |
| Pure dataflow normalization | Deterministic validation or normalization without external effects | 48 | 0.20 |

Equal allocation estimates the bounded mechanism mixture defined here. It is
not a claim about real-world prevalence. Each family count is divisible by
four, so the complete counterbalancing sequence family can be applied within
every family rather than only across the aggregate.

Future task construction must introduce new participant bytes and stable
identities, reject equality with prior provider requests, keep references and
hidden evaluators outside participant context, decode all four realizations to
one canonical observation, and add no unplanned language extension.

## Candidate scale

| Projection | Candidate |
| --- | ---: |
| Fresh tasks | 240 |
| Tasks per family | 48 |
| Four-condition cells | 960 |
| Maximum requests at 12 per cell | 11,520 |
| Calibration-008 mean-rate cost | USD 235.89 |
| Calibration-008 observed-maximum-rate cost | USD 283.00 |

The request and cost values are linear projections from Calibration 008's
semantic cells. New lexical and structural realizations can change tokenization
and trajectories. These numbers establish scale only; no request or spend
ceiling has been authorized.

## Frozen failure behavior

The candidate must pass deterministic finite-sample simulation before it can
become the final task count. If it fails, the scientific inputs may not be
relaxed: SESOIs, envelope, task-family mixture, alpha, power target, and
multiplicity remain fixed. The only permitted response is to increase the task
count in complete 20-task blocks and simulate again.

This prevents a failed power check from turning into a post hoc search for a
larger effect size or a friendlier task distribution.

## Claim boundary

- The scientific selection is frozen before new provider outcomes.
- The 240-task value is asymptotic and has not passed finite-sample validation.
- No task has been created.
- No contamination audit or execution freeze exists.
- No cost ceiling, provider request ceiling, or launch exists.
- No behavioral, power, generalization, or efficiency claim is authorized.
- No model call occurred.

## Evidence

- [`selection.json`](construction/representational-power-selection-freeze-v0/selection.json)
  is the canonical selection record.
- [`build_representational_power_selection_freeze.py`](scripts/build_representational_power_selection_freeze.py)
  derives the envelope maximum, joint rounding block, family allocation, cost
  scale, and red gates from the frozen curve.
- [`REPRESENTATIONAL_POWER_SENSITIVITY_V0.md`](REPRESENTATIONAL_POWER_SENSITIVITY_V0.md)
  documents the preceding 64-scenario sensitivity analysis.

## Next red test

The deterministic finite-sample protocol is now frozen without executing it.
Its next red test is to implement the campaign aggregator and run the thirteen
predeclared scenarios from 240 tasks upward. It must preserve the frozen
20-task escalation rule and record Wilson-bound acceptance or failure before
fresh task creation. See
[`REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_PROTOCOL_V0.md`](REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_PROTOCOL_V0.md).
