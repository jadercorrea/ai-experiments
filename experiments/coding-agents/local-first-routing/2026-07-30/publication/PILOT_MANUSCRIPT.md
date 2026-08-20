# When Should a Coding Agent Go to the Cloud?

## A calibration study of transparent local-first routing

Status: pilot manuscript draft; calibration evidence only; not peer reviewed.

### Abstract

Local-first routing may reduce paid inference by attempting repository-level
coding tasks on a local model and escalating only when observable signals
indicate failure. It can also add latency, fail operationally, or accept a
locally plausible patch that does not resolve the task. We evaluated a frozen,
transparent local-first policy against local-only and cloud-only conditions on
six repository-disjoint Go calibration tasks spanning three provisional
complexity strata. The local-first condition escalated four tasks and resolved
two. The paired Sonnet 4.6 cloud-only condition resolved three, while local-only
resolved three. Local-first used USD 4.037955 of hosted inference compared with
USD 7.417368 for cloud-only, a descriptive reduction of 45.56%, but its
resolution-rate difference was -16.67 percentage points, outside the
pre-specified -10 percentage-point non-inferiority margin. Post-calibration
simulation reduced the original design's joint power from 91.28% under planning
assumptions to 1.18% when observed escalation and resolution uncertainty were
substituted. An exploratory design recovered 92.68% simulated joint power only
at 48,600 policy runs, approximately USD 34,137 of hosted inference and 16,854
serial hours under calibration-based projections. These results are not a
population estimate of local-first effectiveness. They show that the tested
policy is not confirmatory-ready and demonstrate why routing calibration and
feasibility gates should precede large agent evaluations.

### 1. Research question

The study asks whether a disclosed local-first coding-agent policy can reduce
hosted inference cost while remaining non-inferior to a fixed cloud-only agent
for verified repository-level issue resolution.

The object of comparison is the complete policy—model, agent scaffold, tools,
budget, runtime, routing rule, and evaluation—not an isolated model response.
The router may observe public development signals but cannot access held-out
tests used to determine final resolution.

### 2. Calibration design

Six real issue-derived tasks were selected from six repositories. Two tasks
were assigned to each provisional complexity stratum. Each policy received the
same issue, immutable base repository, bounded agent environment, and held-out
evaluation contract.

The three conditions were:

1. **Local-only:** Qwen3-Coder 30B A3B Q4_K_M through Ollama.
2. **Cloud-only:** Claude Sonnet 4.6 through Amazon Bedrock in `us-east-1`.
3. **Local-first:** attempt the local condition, accept only after a clean agent
   exit, material patch, no backend inference failure, and successful public
   verification; otherwise reset to the immutable base and invoke the cloud
   condition with a structured router report.

The local-first policy, schedules, model identities, timeouts, hosted-cost cap,
and fallback semantics were frozen before local-first outcomes were generated.
Fallback was determined only by the executable routing policy. Held-out
evaluation did not influence routing.

Two local-first attempts were invalidated and excluded according to recorded
rules: one pre-inference Docker metadata failure and one intentional daytime
interruption after compute was restricted to an overnight window. Both
evidence bundles remain retained.

### 3. Results

| Policy | Resolved | L1 | L2 | L3 | Hosted cost | Wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Local-only | 3/6 | 2/2 | 0/2 | 1/2 | USD 0 | 9,479.207 s |
| Cloud-only Sonnet 4.6 | 3/6 | 2/2 | 1/2 | 0/2 | USD 7.417368 | 2,365.354 s |
| Local-first | 2/6 | 2/2 | 0/2 | 0/2 | USD 4.037955 | 10,627.930 s |

Local-first accepted two tasks locally and escalated four. Escalation triggers
were two hard timeouts, one backend failure, and one no-material-patch outcome.
One locally accepted patch passed the observable routing checks but failed the
held-out evaluator. This false acceptance is evidence about router precision,
not a harness invalidation.

The valid local-first stages recorded 257 successful and two failed local
inference calls, followed by 82 successful cloud calls. Every successful cloud
event used the locked Sonnet 4.6 model identity; no cloud identity violation was
observed.

Hosted cost excludes local hardware, electricity, and opportunity cost. Wall
time is descriptive and includes the recorded agent and evaluation stages.
Neither quantity should be extrapolated without uncertainty.

### 4. Feasibility reassessment

The routing lock retrospectively projected two escalations and four resolved
tasks. Execution produced four escalations and two resolved tasks. Under the
original 90-task planning assumptions, the 1,350-run design reproduced 91.28%
joint simulated power. Replacing the escalation assumption with the observed
rate reduced joint power to 25.92%. Also replacing resolution assumptions with
stratum-level Beta posterior estimates reduced it to 1.18%.

An exploratory search found a tested point above 90% joint simulated power:
1,080 tasks from 270 repositories, with 15 trajectories per task-policy pair.
That point requires 48,600 runs across three policies. Its projected USD 34,137
of hosted inference and 16,854 serial hours are feasibility estimates, not
campaign consumption or a recommended design.

The confirmatory gate is therefore no-go for the tested policy and current
design.

### 5. Interpretation

The calibration supports three bounded conclusions.

First, transparent local-first routing can reduce observed hosted spend because
some tasks terminate locally. Second, local execution is not free at the system
level: it introduces hardware use and can add substantial latency before
fallback. Third, public checks alone did not prevent a false local acceptance,
so the tested routing rule did not preserve resolution at the calibration
point estimate.

The calibration does **not** establish that local-first routing is generally
inferior, that Sonnet is generally superior, or that the observed effect sizes
generalize beyond these tasks and systems. Six tasks were selected to exercise
the apparatus and routing decision, not to estimate a population treatment
effect.

### 6. Limitations

- The sample contains only six Go tasks and provisional, not learned,
  complexity strata.
- There is one trajectory per task-policy pair, so stochastic repeatability is
  not estimated.
- Hosted pricing is recorded, while local hardware, energy, and opportunity
  costs are not monetized.
- Provider behavior and latency can change even when the requested model
  identifier remains fixed.
- The exploratory powered candidate depends on calibration-informed simulation
  assumptions and is neither optimized nor preregistered.
- Policy comparisons apply to complete agent systems and cannot be reduced to
  model-only claims.

### 7. Prospective successor series

The pilot is treated as development evidence for a separately named successor
series. The successor may add pre-execution admission, strengthen post-local
acceptance, or revise time budgets, but every change creates a new treatment.
Its policy and gates must be frozen before new calibration outcomes are
generated. Pilot and successor results will be reported side by side and will
not be pooled as repetitions of one unchanged policy.

### 8. Reproducibility and availability

The study retains valid and invalidated trajectories, schedules, model and
routing locks, analysis code, summaries, patches, event streams, and held-out
evaluation results. The publication release candidate is checksummed by
[`artifact-lock.json`](artifact-lock.json). Exact reproduction commands and the
remaining external release steps are recorded in [`README.md`](README.md).

Related-work citations and venue-specific formatting remain intentionally
deferred until a submission destination is selected. They cannot alter the
empirical claims or the frozen evidence boundary.
