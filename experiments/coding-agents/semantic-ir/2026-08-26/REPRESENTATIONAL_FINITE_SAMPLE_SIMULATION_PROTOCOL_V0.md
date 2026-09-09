# Representational finite-sample simulation protocol v0

## Status

**Protocol frozen and executed; the first candidate selected 240 tasks.** The
protocol fixes the joint data generator, thirteen validation scenarios,
task-level tests, Holm
correction, seed derivation, replication count, Wilson uncertainty intervals,
candidate escalation schedule, and acceptance criteria before any simulation
outcome is observed.

The campaign runner was first locally exercised with synthetic event counts and
a five-replication generator smoke test. It validates the protocol and its
dependency hashes before work, writes one atomic checkpoint after every
completed scenario, resumes only from a canonical campaign prefix,
and content-locks the result only after selection or exhaustion. This does not
change the frozen protocol artifact. The later 20,000-replication campaign ran
all thirteen streams for 240 tasks and stopped there because every criterion
passed.

The selected count is 240 fresh task units. Each evaluated scenario used 20,000
replications. No model call, fresh-task construction, provider request, or
spend occurred while freezing or executing this simulation protocol.

## Is this the same generator as the power curve?

Yes, at the scientific-model boundary. The power curve already fixed:

- one latent success probability shared by the four conditions of a task;
- its baseline mean and intraclass correlation (ICC);
- conditionally independent Bernoulli outcomes;
- proportional rescue for an increasing effect;
- proportional harm for a decreasing effect; and
- the lexical and packaging marginal task contrasts.

The curve needed only the resulting moments. Simulation needs an actual
distribution from which to draw the latent probability. Protocol v0 therefore
completes, rather than replaces, that moment model:

```text
ICC = 0: theta = baseline
ICC > 0: theta ~ Beta(alpha, beta)
concentration = 1 / ICC - 1
alpha = baseline * concentration
beta = (1 - baseline) * concentration
```

This Beta completion has exactly the frozen baseline mean and ICC. It is an
assumption, not an empirical discovery. Family-specific or multimodal latent
task distributions remain outside v0 and cannot be claimed away by a passing
simulation.

For an increasing effect, the active probability is
`theta + effect / (1 - baseline) * (1 - theta)`. For a decreasing effect, it is
`(1 - effect / baseline) * theta`. A lexical scenario applies that probability
to meaningful cells and leaves opaque cells at `theta`; a packaging scenario
applies it to nested cells and leaves table cells at `theta`. Protocol v0 tests
one nonzero primary at a time. It deliberately introduces no arbitrary rule for
composing simultaneous lexical and packaging effects.

## Analysis frozen at the task boundary

The four requests belonging to one task are dependent observations, never four
experimental units. Each replication first reduces every task to two marginal
contrasts:

```text
lexical = 0.5 * ((meaningful_nested - opaque_nested)
               + (meaningful_table  - opaque_table))

packaging = 0.5 * ((meaningful_nested - meaningful_table)
                 + (opaque_nested     - opaque_table))
```

Each mean contrast receives a two-sided one-sample normal test using the
observed task-level standard error. If its variance is exactly zero, a zero
mean receives `p = 1` and a nonzero mean receives `p = 0`. Holm's step-down
procedure controls the two-primary family at alpha 0.05; its ordered thresholds
are 0.025 and 0.05.

This is the same contrast and conservative first Holm threshold used by the
asymptotic curve. The purpose of simulation is precisely to test whether that
normal approximation behaves acceptably at the planned finite sizes.

## Thirteen frozen scenarios

Nine global-null sentinels cross three baseline values and three ICC values:

| Baseline | ICC values | Event scored |
| ---: | --- | --- |
| 0.20 | 0.000, 0.375, 0.750 | Either primary rejected |
| 0.50 | 0.000, 0.375, 0.750 | Either primary rejected |
| 0.80 | 0.000, 0.375, 0.750 | Either primary rejected |

Four isolated-primary scenarios cross lexical versus packaging with increasing
versus decreasing effects. Each uses SESOI 0.10 and the corresponding exact
worst-baseline point from the selection freeze at ICC zero. They score both the
active factor's power and the inactive factor's false-positive rate.

The null scenarios are envelope sentinels rather than proof over every real
number in the envelope. The alternative scenarios target the two exact
asymptotic maxima. A later robustness protocol would be required to claim
family-specific or distributional robustness.

## Randomness and Monte Carlo precision

The base seed is `24121980`. Every `(scenario, task count)` pair receives a
separate 64-bit seed from a SHA-256 derivation, so evaluating a later candidate
cannot consume or alter an earlier candidate's stream. Execution is pinned to
the locked runner and CPython 3.14.x because bit identity across random-library
implementations is not claimed.

Each scenario uses 20,000 replications and reports a 95% Wilson score interval
for every event rate. The maximum binomial Monte Carlo standard error is about
0.00354; at power 0.80 it is about 0.00283, and at Type I probability 0.05 it
is about 0.00154. Acceptance uses interval bounds, not point estimates.

## Candidate and acceptance rule

Candidates are evaluated in this immutable order:

```text
240, 260, 280, 300, 320, 340, 360, 380, 400 tasks
```

The first candidate passes only if all of the following hold:

1. every global-null scenario has Wilson upper bound at or below 0.06 for
   rejecting either primary;
2. every isolated-primary scenario has Wilson lower bound at or above 0.80 for
   rejecting its active primary; and
3. every isolated-primary scenario has Wilson upper bound at or below 0.06 for
   rejecting its inactive primary.

If a candidate fails, only the task count advances by one complete 20-task
block. SESOI, envelope, target population, alpha, multiplicity, and criteria do
not move. If 400 fails, the experiment remains blocked and requires a new
explicit design decision rather than a friendlier post hoc assumption.

## Claim boundary

- The content-locked protocol remains distinct from its later simulation result.
- The 240-task count has passed the protocol's finite-sample criteria.
- Its later pass validates this analysis under this generator; it does not prove
  that the generator describes real coding-agent tasks.
- v0 contains no family-specific baseline, ICC, or effect heterogeneity.
- No fresh task, contamination audit, execution freeze, budget, or launch
  exists.
- No model or provider call occurred.

## Evidence

- [`protocol.json`](construction/representational-finite-sample-simulation-protocol-v0/protocol.json)
  is the canonical frozen protocol.
- [`representational_finite_sample_simulation.py`](scripts/representational_finite_sample_simulation.py)
  implements the exact generator, contrasts, test, Holm procedure, Wilson
  intervals, seed derivation, and single-replication execution.
- [`build_representational_finite_sample_simulation_protocol.py`](scripts/build_representational_finite_sample_simulation_protocol.py)
  derives the scenarios and escalation schedule from the locked scientific
  selection.
- [`run_representational_finite_sample_simulation.py`](scripts/run_representational_finite_sample_simulation.py)
  executes or resumes the exact candidate/scenario sequence and emits a final
  content-locked result only after the frozen stop rule resolves.
- [`REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md`](REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md)
  records the preceding pre-outcome choices.

## Next red test

The campaign is complete and the subsequent construction protocol now freezes
240 slots, family allocation, counterbalancing, contamination rejection,
canonical four-condition equivalence, reference/evaluator isolation, and local
validation without materializing a task. The next red test is the deterministic
five-family generator. See
[`REPRESENTATIONAL_FRESH_TASK_CONSTRUCTION_PROTOCOL_V0.md`](REPRESENTATIONAL_FRESH_TASK_CONSTRUCTION_PROTOCOL_V0.md).

## Method references

- Holm, S. (1979), *A Simple Sequentially Rejective Multiple Test Procedure*.
- Brown, Cai, and DasGupta (2001), [*Interval Estimation for a Binomial
  Proportion*](https://projecteuclid.org/journals/statistical-science/volume-16/issue-2/Interval-Estimation-for-a-Binomial-Proportion/10.1214/ss/1009213286.pdf).
