# Local-first routing for repository-level coding agents

Status: calibration pilot released; confirmatory no-go; no confirmatory runs executed.

Protocol created: 2026-07-30

Scientific redesign: 2026-07-31

Current calibration interpretation:
[`CALIBRATION_PILOT_REPORT.md`](CALIBRATION_PILOT_REPORT.md)

Pilot publication:
[`publication/README.md`](publication/README.md)

The separately named prospective successor is intentionally outside this
release and must not pool v1 outcomes into future effect estimates.

This document pre-specifies an empirical evaluation of transparent local-first
routing for repository-level coding agents. It is intended to support a
peer-reviewed paper rather than a product demonstration.

The protocol treats each routing condition as a complete agent system. The
object of study is not an isolated language model response, but a policy that
selects inference resources, interacts with a repository, executes observable
checks, and produces a candidate patch under bounded compute.

No result may be interpreted before the protocol, benchmark construction code,
analysis code, model identities, routing thresholds, and stopping rules are
frozen in a timestamped revision.

## 1. Research objective

### 1.1 Primary research question

Can a transparent local-first routing policy reduce hosted inference cost while
remaining non-inferior to a fixed cloud-only agent on repository-level issue
resolution?

### 1.2 Secondary research questions

1. How does the effect of local-first routing vary with pre-treatment task
   complexity?
2. How repeatable are the three policies under independent stochastic runs?
3. What latency penalty is introduced before a failed local attempt escalates?
4. How often does the router incorrectly accept a locally generated patch that
   passes observable checks but fails the held-out evaluator?
5. How do the policies differ in regression rate, security findings,
   maintainability, patch minimality, and blind human review?
6. Which observable signals best predict whether local execution should be
   accepted, repaired, or escalated?

The experiment does not attempt to infer whether commercial providers secretly
route requests to smaller models. Provider internals are not observable. It
tests whether a disclosed and reproducible routing policy can achieve a useful
cost-reliability trade-off.

## 2. Claimed contribution

The intended contribution is a repository-level, execution-based evaluation of
inference routing policies, not another model leaderboard.

The study combines:

- real GitHub issues and repository snapshots, following the central evaluation
  unit introduced by SWE-bench;
- unbiased Pass@k estimates across independent agent trajectories;
- a confirmatory non-inferiority analysis for verified issue resolution;
- explicit cost, energy, and time-to-resolution measurements;
- routing-calibration and held-out evaluation splits;
- regression, security, static-quality, and blind-review outcomes;
- complete trajectory and evidence retention for successful and failed runs.

## 3. Experimental conditions

Each condition receives the same issue text, base repository, repository-level
instructions, tool API, network policy, and final evaluation harness.

The local and hosted model identities are fixed before confirmatory execution.
Provider-managed model routers are excluded from the primary study.

### 3.1 Local-only

```text
Issue + base repository
          |
          v
   fixed local agent
          |
          v
    candidate patch
          |
          v
  held-out evaluation
```

The agent may inspect, edit, execute allowed development commands, and repair
its work within a pre-registered budget. There is no hosted fallback.

### 3.2 Cloud-only

```text
Issue + base repository
          |
          v
 fixed hosted agent
          |
          v
    candidate patch
          |
          v
  held-out evaluation
```

This is the reference policy for non-inferiority, hosted cost, and latency.

### 3.3 Local-first

```text
Issue + base repository
          |
          v
   fixed local agent
          |
          v
 observable router signals
     |              |
   accept         escalate
     |              |
     |       retain local evidence
     |              |
     |        reset repository
     |              |
     |      fixed hosted agent
     |              |
     +-------+------+
             |
             v
       candidate patch
             |
             v
     held-out evaluation
```

The local patch and trajectory are retained before reset. In the primary
experiment, the hosted fallback starts from the original base repository. It
receives the original issue and a pre-specified router report, but not the local
patch or free-form local reasoning.

Patch handoff is reserved for a separate ablation because a failed patch can
either provide useful localization or contaminate the fallback.

### 3.4 Unit of comparison and harness compatibility

The primary object of comparison is an inference system, not an isolated model:

```text
model + scaffold + prompt + tools + routing policy + budget + environment
```

All components except the routing policy are frozen across the three primary
conditions wherever the policy permits. Every result records the exact harness
revision and configuration digest.

Model-to-model claims require a separate controlled ablation in which scaffold,
prompt, tools, budget, environment, and evaluation set are identical. Results
produced by incompatible major scaffold versions are separate series and are
never connected as a longitudinal model trend. Minor harness changes require a
bridge study on an overlapping frozen task sample before results may be pooled.

The published analysis includes a compatibility matrix identifying which
conditions share dataset, harness, prompt, tool, budget, and environment
identity. Scores without compatibility on all pre-registered dimensions are
described side by side but not treated as direct estimates of improvement.

## 4. Separation of routing and evaluation

The router must not observe the held-out tests used to score final correctness.
This separation is mandatory.

### 4.1 Router-observable signals

The local-first policy may use only signals available in a realistic
development environment:

- patch produced or not produced;
- elapsed time;
- token and tool-call budgets;
- build or type-check status;
- repository-provided public tests;
- public linters and static-analysis tools;
- unauthorized path writes;
- public API-diff checks;
- agent termination or explicit inability report.

These signals form the routing feature vector `X_route`.

### 4.2 Held-out evaluation signals

The final evaluator runs after the policy has terminated and is inaccessible to
the agent and router:

- fail-to-pass tests derived from the reference fix;
- pass-to-pass regression tests;
- additional adversarial tests;
- security queries;
- hidden contract and API checks;
- patch-application and repository-integrity checks.

These signals form `Y_eval` and cannot influence escalation.

Using held-out tests for routing would leak the outcome into the policy and
invalidate the comparison.

## 5. Benchmark construction

### 5.1 Task unit

One task consists of:

- a real GitHub issue or pull-request problem statement;
- the repository at the parent commit of the reference change;
- a reference patch that resolved the issue;
- tests introduced or modified by the reference change;
- the pre-change regression suite;
- a reproducible containerized execution environment.

The model sees the issue and base repository. It never sees the reference patch,
held-out tests, reference test results, or complexity label.

### 5.2 Candidate repositories

Repositories must:

- use an OSI-approved license compatible with redistribution;
- install and execute in a reproducible container;
- have a substantive automated test suite;
- have sufficient history to reconstruct issue, base commit, and merged fix;
- permit network-disabled evaluation;
- expose no credentials or private data in fixtures.

Repository identity is treated as a clustering variable. Results must not be
reported only as a micro-average dominated by a single large repository.

### 5.3 Candidate issue filtering

Following the execution-based logic of SWE-bench, a candidate is retained only
when:

1. a merged change is linked to an issue or explicit problem statement;
2. the reference change modifies or adds tests relevant to the issue;
3. the base repository installs successfully;
4. the test patch can be separated from the solution patch;
5. at least one test changes from fail before the solution to pass after it;
6. previously passing tests required by the evaluator continue to pass after
   the reference solution;
7. the full evaluation can be repeated in a clean container;
8. the issue can be evaluated without external mutable services;
9. the reference patch does not depend on unavailable secrets or datasets.

### 5.4 Test transition taxonomy

For task `i`, tests are classified by their status before and after the
reference patch:

- `F2P_i`: fail before, pass after;
- `P2P_i`: pass before, pass after;
- `F2F_i`: fail before, fail after;
- `P2F_i`: pass before, fail after.

Primary task resolution requires all `F2P_i` and all selected `P2P_i` tests to
pass for the candidate patch. Missing or unparseable required tests count as
failures.

`F2F_i` and `P2F_i` are retained for dataset diagnostics but are not silently
folded into the resolution criterion.

### 5.5 Outcome taxonomy

Candidate patches that apply successfully are assigned one mutually exclusive
functional outcome:

- `RESOLVED`: all F2P and P2P tests pass;
- `BREAKING_RESOLVED`: all F2P pass, at least one P2P fails;
- `PARTIALLY_RESOLVED`: some but not all F2P pass, all P2P pass;
- `WORK_IN_PROGRESS`: some F2P pass and at least one P2P fails;
- `NO_OP`: no F2P pass and all P2P pass;
- `REGRESSION`: no F2P pass and at least one P2P fails.

Patch-application failure, installation failure, timeout, policy failure, and
harness failure remain separate terminal states.

### 5.6 Temporal contamination control

The benchmark records issue creation, reference merge, dataset collection, and
model release dates.

Preferred tasks postdate the documented training cutoff of every evaluated
model. When a provider does not disclose a cutoff, the limitation is explicit
and results are stratified by issue date.

The evaluation environment has no network access. Exact-match and near-duplicate
checks are run against known public benchmarks and training corpora when
available. Contamination cannot be ruled out for proprietary models and is not
claimed to be eliminated.

### 5.7 Calibration and confirmatory splits

Tasks are divided by repository, not randomly by individual issue, into:

- construction set: harness and parser development;
- calibration set: routing thresholds, time budgets, and complexity model;
- confirmatory test set: final frozen evaluation.

No issue, repository snapshot, or near-duplicate bug family may appear in more
than one split. Repository-disjoint splitting is preferred because issue-level
random splits leak project conventions and architecture.

Results from construction and calibration are never pooled into confirmatory
estimates.

## 6. Complexity as a pre-treatment variable

The original three-level structure is retained, but levels are not assigned by
manual intuition or observed model success.

### 6.1 Observable complexity features

Complexity is estimated from information available before model execution and
from reference metadata hidden from the agent:

- non-test repository files and lines;
- dependency-graph breadth of affected modules;
- issue length and number of referenced symbols;
- number of files, functions, and lines changed by the reference patch;
- number of F2P and P2P tests;
- number of packages or architectural layers crossed;
- requirement for security, concurrency, persistence, or compatibility checks;
- test execution duration;
- minimum static call-graph distance between issue-mentioned symbols and
  reference-edited symbols.

No feature derived from an evaluated model's output is permitted.

### 6.2 Complexity strata

A complexity score is fit only on the construction and calibration sets. The
scoring rule and cut points are frozen before confirmatory execution.

The confirmatory tasks are divided into three approximately balanced strata:

- `L1`: localized repository change;
- `L2`: cross-file or cross-layer repository reasoning;
- `L3`: critical boundary or high-coordination change.

Primary conclusions use the continuous complexity score and its interaction
with policy. The three strata are used for interpretation and visualization,
not as the sole statistical representation of difficulty.

Sensitivity analyses repeat the model using individual structural features and
alternative pre-registered cut points.

## 7. Runs, independence, and Pass@k

### 7.1 Independent trajectories

For every task-policy pair, `n` independent trajectories are sampled. Each
trajectory starts from a clean container and base commit and receives no memory
from earlier trajectories.

Independence is approximated by:

- separate model conversations;
- clean worktrees and process state;
- no shared agent memory;
- fixed prompts and tools;
- recorded sampling parameters;
- randomized run order.

Provider-side nondeterminism and caching are recorded as limitations.

### 7.2 Pass@k

For a task with `n` independent samples and `c` resolved samples, secondary
Pass@k is estimated using the unbiased estimator introduced with HumanEval:

```text
Pass@k = 1 - C(n - c, k) / C(n, k)
```

Pass@1 is reported for every condition. Pass@k for `k > 1` is reported only
when `n >= k` and is explicitly described as the probability that at least one
of `k` independently sampled complete policy runs resolves the task.

Internal repair cycles within one trajectory are not counted as independent
samples and must not inflate Pass@k.

### 7.3 Repeatability

Pass@k measures best-of-k capability and does not by itself establish reliable
single-run operation. Repeatability is additionally reported as:

- per-task success proportion;
- all-runs-success proportion;
- between-run duration and cost variance;
- failure-mode entropy;
- intraclass correlation by task and repository;
- probability of `m` consecutive successful runs under the fitted model.

## 8. Routing policy

### 8.1 Policy family

The primary router is a deterministic threshold policy. A learned router may be
evaluated only as a pre-registered secondary policy trained exclusively on the
calibration set.

The deterministic router maps `X_route` to one of:

- `ACCEPT_LOCAL`;
- `REPAIR_LOCAL`;
- `ESCALATE_CLOUD`.

### 8.2 Escalation triggers

Candidate triggers include:

- no material patch by time threshold;
- local wall-clock, token, or tool-call budget reached;
- compilation or type checking remains broken after the repair allowance;
- observable public tests remain failing;
- public static analysis or workspace containment fails;
- unauthorized public API change;
- agent termination or explicit inability report.

Exact thresholds and repair allowances are estimated on calibration data and
frozen before confirmatory evaluation.

### 8.3 Clean fallback

For the confirmatory primary policy:

1. retain the complete local trajectory and patch;
2. reset to the immutable base commit;
3. provide the hosted agent with the original issue and fixed router report;
4. apply the same hosted-agent budget used by cloud-only;
5. evaluate only the final candidate patch.

Local compute spent before escalation remains part of local-first latency and
cost.

The inference gateway never converts a failed local request into an in-session
cloud request. A 429, 5xx response, timeout, or transport error terminates or
fails the local stage according to the frozen policy. The campaign runner owns
the escalation boundary so it can freeze the local evidence, restore the base
repository, and launch a separate cloud-only stage. Replaying the same request
or conversation against a hosted model is a different treatment and cannot be
reported as the primary clean-fallback policy.

## 9. Outcomes and estimands

Let:

- `P in {LO, LF, CO}` denote local-only, local-first, and cloud-only;
- `Y_irt(P)` be resolution for task `i`, repetition `r`, policy `P`;
- `C_irt(P)` be total cost;
- `T_irt(P)` be time to terminal disposition;
- `S_irt(P)` be security findings;
- `Q_irt(P)` be static and human quality outcomes.

### 9.1 Primary estimand: non-inferiority in resolution

```text
Delta_success = Pr[Y(LF) = 1] - Pr[Y(CO) = 1]
```

Local-first is non-inferior only if the lower bound of the pre-specified
confidence interval exceeds `-delta_NI`, where `delta_NI` is the maximum
acceptable absolute reduction in resolution rate.

`delta_NI` must be justified from calibration results and practical deployment
requirements before confirmatory execution. It cannot be selected after seeing
test results.

### 9.2 Co-primary estimand: hosted cost reduction

```text
R_hosted = 1 - E[hosted_cost(LF)] / E[hosted_cost(CO)]
```

The claim of useful local-first routing requires both:

1. non-inferior verified resolution; and
2. positive hosted-cost reduction exceeding a pre-specified minimum.

The two co-primary tests use a pre-registered family-wise error procedure.

### 9.3 Secondary estimands

- total compute-cost difference, including local execution;
- median time-to-verified-resolution difference;
- escalation probability by complexity;
- false-local-accept probability;
- regression probability;
- security finding rate;
- blind-review quality difference;
- policy-by-complexity interaction;
- local-only versus cloud-only resolution and cost differences.

## 10. Functional evaluation

### 10.1 Resolution

The principal functional metric is repository-level `% Resolved`: all required
F2P and P2P tests pass after applying the candidate patch.

Patch application, installation, and test parsing must also succeed. A model
claiming success has no evidentiary weight.

### 10.2 Test coverage

Coverage is measured at base and candidate revisions using the repository's
language-appropriate tool. Reported outcomes include:

- line and branch coverage delta;
- coverage of changed lines;
- newly uncovered code;
- test additions attempted by the agent;
- mutation score on a pre-registered subset where computationally feasible.

Coverage is not treated as correctness. It is a separate diagnostic outcome.

### 10.3 Regression scope

F2P tests establish issue-specific behavior. P2P tests establish preservation
of prior behavior. Both rates are reported separately in addition to the binary
resolved outcome.

## 11. Lexical, structural, and semantic similarity

CodeBLEU is computed only as a secondary diagnostic against the reference patch
for languages supported by a validated implementation.

The components are reported separately:

- token or n-gram similarity;
- weighted token similarity;
- AST match;
- data-flow match.

CodeBLEU is not a primary quality or correctness metric because repository
issues frequently admit multiple semantically correct patches that differ from
the historical reference solution. Correlation between CodeBLEU and execution,
static analysis, and human review is analyzed rather than assumed.

Patch-size-normalized tree-edit and data-flow measures may be included if their
implementations are validated across the benchmark languages before freezing.

## 12. Static quality and maintainability

Language-appropriate analyzers are executed in versioned containers. Candidate
metrics include:

- cyclomatic and cognitive complexity delta;
- maintainability index delta;
- duplication delta;
- code-smell count and severity;
- lint and type-check findings;
- dependency and API-surface changes;
- patch size, files touched, and change dispersion;
- dead code and unreachable branch findings.

Metrics are compared with both the base repository and reference patch. Raw
tool outputs and tool versions are retained.

No universal maintainability score is aggregated across languages unless
measurement invariance is demonstrated. Within-language standardized effects
are preferred.

## 13. Security evaluation

### 13.1 Automated analysis

Security-sensitive tasks are mapped to explicit CWE categories before model
execution. Versioned CodeQL, Semgrep, and language-specific SAST tools are run
where supported.

Reported outcomes include:

- new CWE-aligned findings introduced by the patch;
- reference vulnerability removed or retained;
- severity distribution;
- security-test pass rate;
- false local accepts at a security boundary.

### 13.2 Finding adjudication

Static-analysis alerts are not assumed to be true vulnerabilities. Findings are
deduplicated and independently adjudicated by reviewers blind to policy and
model identity. Disagreements are resolved by a pre-specified adjudication
procedure.

Security analysis is reported separately for security-targeted and general
tasks to avoid diluting rare high-impact failures in an overall average.

## 14. Blind human review

### 14.1 Review sample

All resolved patches and a stratified random sample of unresolved-but-applying
patches are reviewed. Sampling is balanced by policy, complexity, and
repository.

### 14.2 Blinding

Review packages remove:

- model and provider identity;
- policy identity;
- trajectory and cost information;
- timestamps and generated metadata;
- comments that directly reveal authorship when removal does not change code
  meaning.

Patch order is independently randomized for each reviewer.

### 14.3 Reviewers and rubric

At least three software engineers independently rate each selected patch on:

- issue adherence;
- correctness plausibility beyond tests;
- readability and idiomaticity;
- architectural fit;
- maintainability;
- error handling;
- patch minimality;
- security and operational risk;
- willingness to approve after ordinary review.

The rubric, anchors, training examples, and reviewer qualification criteria are
frozen before review.

### 14.4 Reliability

Inter-rater reliability is reported using an appropriate statistic selected
before analysis, such as Krippendorff's alpha for ordinal items and Fleiss'
kappa for categorical approval. Individual and adjudicated scores are retained.

Human-review outcomes are not replaced by a single consensus score without
showing disagreement.

If external reviewers are recruited or compensated, ethics and consent
requirements are assessed before data collection.

## 15. LLM-as-a-judge

LLM judgment is exploratory and cannot serve as ground truth.

One or more fixed judge models receive the same anonymized patch packages and
human rubric. Judge prompts, order, temperature, and model versions are frozen.

Judge validity is evaluated against held-out human ratings using:

- rank or ordinal correlation;
- mean absolute error where meaningful;
- calibration error;
- pairwise agreement;
- Cohen's or Fleiss' kappa for categorical outcomes;
- sensitivity to patch order and author-label perturbations.

An LLM judge is reported only after calibration. Low agreement is a result, not
a reason to replace human labels.

## 16. Cost, energy, and latency

### 16.1 Hosted inference

For each request:

- provider and model version;
- client-request and upstream-request SHA-256 digests and byte counts, recorded
  separately after any treatment-specific model rewrite or protocol
  normalization;
- input, cached-input, reasoning, and output tokens where exposed;
- request count and retries;
- price schedule and capture date;
- provider-reported latency;
- computed monetary cost.

### 16.2 Local inference

For each run:

- model digest and quantization;
- runtime version;
- prompt and generated tokens;
- tokens per second;
- GPU, CPU, and memory residency;
- elapsed GPU and CPU time;
- measured wall energy when instrumentation permits.

Marginal energy cost and hardware-amortized cost are reported as separate
scenarios. Local inference is never described as free.

### 16.3 Time-to-event outcomes

Latency outcomes include:

- time to first material repository action;
- local-stage duration;
- time to escalation;
- hosted-stage duration;
- verification duration;
- total time to resolution or terminal failure.

Timeouts are right-censored for time-to-resolution analysis rather than
silently replaced by the timeout threshold in means. Competing terminal events
such as explicit failure and harness failure remain distinguishable.

## 17. Randomization and execution control

Runs are executed in randomized blocks by task and repetition. Within each
block, policy order is randomized.

The design records and controls:

- machine and thermal state;
- concurrent workload;
- model loading and warm/cold cache state;
- runtime and container image digest;
- context window and sampling parameters;
- system prompt, issue prompt, repository instructions, and skills;
- tool definitions and permissions;
- network policy;
- wall-clock, token, tool-call, and repair budgets.

If only one local machine is available, blocks are distributed across time so
that policy and complexity are not confounded with thermal drift or time of
day.

Cloud requests are interleaved across the campaign to reduce confounding from
silent provider updates. Request dates and any returned model fingerprints are
retained.

## 18. Sample size and power

The earlier fixed proposal of 15 fixtures and 225 runs is insufficiently
justified for a confirmatory paper and is withdrawn.

Final sample size is selected before confirmatory execution using simulation
based on calibration estimates of:

- cloud-only resolution rate;
- local-first resolution rate;
- task and repository intraclass correlation;
- between-run variance;
- escalation rate;
- non-inferiority margin;
- expected attrition from invalid tasks and harness failure.

The target is at least 80% power for the non-inferiority test at the
pre-specified family-wise error rate, with a preference for 90% when compute
permits.

Power simulation uses the same hierarchical model planned for primary analysis
and clusters by repository and task. The simulation code, random seed,
assumptions, and resulting sample size are committed before test-set execution.

A minimum design floor is:

- at least 30 confirmatory tasks per complexity stratum;
- at least three repositories per stratum where construction permits;
- at least five independent trajectories per task-policy pair.

This floor implies at least:

```text
90 tasks x 3 policies x 5 trajectories = 1,350 policy runs
```

The powered design may require more. A smaller study must be presented as a
pilot or workshop result, not as confirmatory evidence of non-inferiority.

The executable simulator is [`scripts/power_simulation.py`](../../../../scripts/power_simulation.py).
The checked-in [illustrative assumptions](power-assumptions.example.json) and
[illustrative result](power-result.example.json) are apparatus checks, not a
preregistration. Under those assumptions, the 90-task floor provides 100%
simulated power for the hosted-cost threshold but only 13.8% for resolution
non-inferiority and therefore 13.8% joint power. This demonstrates that the
nominal 1,350-run floor cannot be declared sufficient before calibration. The
final assumptions and sample size remain frozen only after calibration and
before any confirmatory outcome is inspected.

### 18.1 Post-calibration design sensitivity

The six-task local-first calibration completed on 2026-08-18 before any
confirmatory outcome was generated. Its observed 4/6 escalation rate and 2/6
resolution count contradicted the frozen retrospective projection of 2/6
escalations and 4/6 resolutions. The machine-readable calibration summary is
[`calibration/local-first-summary.json`](calibration/local-first-summary.json).

The original 90-task design still reproduces its checked-in 91.28% joint power
under the pre-local-first assumptions. Substituting only the observed
escalation rate reduces joint power to 25.92%; substituting the Beta(1,1)
posterior resolution rates by stratum as well reduces it to 1.18%. Therefore the
checked-in design is not confirmatory-ready under completed calibration.

An exploratory search found one tested candidate above the preferred 90%
target: 360 tasks and 90 repositories per stratum, with 15 trajectories per
task-policy pair. It reached 92.68% joint power across 5,000 simulations and
implies 1,080 tasks, 270 repositories, and 48,600 three-policy runs. This
candidate is a feasibility bound, not a preregistration. Full inputs, hashes,
scenario overrides, and results are in
[`calibration/local-first-power-sensitivity.json`](calibration/local-first-power-sensitivity.json).

## 19. Statistical analysis

### 19.1 Primary success model

Verified resolution is analyzed with a hierarchical logistic model containing:

- fixed effect for policy;
- continuous complexity score;
- policy-by-complexity interaction;
- repository and language covariates;
- random intercepts for task and repository;
- pre-specified random slopes if calibration supports stable estimation.

The primary local-first versus cloud-only contrast is reported as an absolute
probability difference with confidence or credible interval. Odds ratios may be
reported secondarily but do not define non-inferiority.

### 19.2 Cost analysis

Cost distributions are expected to be zero-inflated and right-skewed.

Hosted cost is analyzed using paired task-level contrasts and clustered
bootstrap intervals. Total cost is analyzed under the declared local hardware
cost scenarios. Cost per resolved task is reported with uncertainty and without
dropping failed runs.

### 19.3 Latency analysis

Time to verified resolution is analyzed using survival methods that preserve
right censoring. Median and restricted mean time to resolution are reported.

### 19.4 Multiple comparisons

The non-inferiority and minimum-cost-reduction hypotheses are co-primary and
use a pre-registered family-wise error procedure. Secondary comparisons use
Holm correction within metric families or are labeled exploratory.

### 19.5 Clustered uncertainty

Confidence intervals and bootstrap resampling operate at the task and, where
possible, repository level. Treating repeated runs from the same issue as
independent benchmark tasks is prohibited.

### 19.6 Missingness and harness failures

Harness errors are diagnosed before unblinding aggregate policy results.
Exclusion requires a reason independent of model outcome and is reported by
policy.

Primary analysis follows intention-to-evaluate for every valid randomized run.
Per-protocol sensitivity analysis is allowed but cannot replace the primary
analysis.

## 20. Ablations and sensitivity analyses

Pre-registered ablations may include:

1. local-first clean fallback versus patch-and-trajectory handoff;
2. deterministic router versus learned router;
3. time-only versus verification-aware escalation;
4. public-tests-only versus public-tests-plus-static-analysis routing;
5. one local/cloud model pair versus a replication pair;
6. warm versus cold local model state;
7. repository-disjoint versus issue-disjoint analysis;
8. alternative complexity scoring rules;
9. alternative non-inferiority margins;
10. exclusion of tasks with possible temporal contamination;
11. exclusion of tasks disputed by post-hoc benchmark audit;
12. strict human-verified tasks versus the full executable task set;
13. bridge samples across minor harness revisions;
14. alternate treatment of harness failures and invalid tasks.

Ablations are secondary and cannot be used to redefine the primary policy after
confirmatory results are observed.

## 21. Validity threats

### Internal validity

- hidden provider changes during evaluation;
- imperfect independence across stochastic samples;
- harness or test-parser errors;
- router overfitting to calibration repositories;
- differential tool behavior across providers;
- thermal throttling or cache effects.
- unintended privilege, filesystem, shell, or version differences between
  task containers;
- scaffold changes that are incorrectly attributed to the underlying model.

### Construct validity

- repository tests may incompletely represent issue correctness;
- problem statements may be underspecified or reference tests may enforce
  requirements absent from the public task;
- CodeBLEU may penalize valid alternative implementations;
- static-analysis tools may produce false positives;
- maintainability metrics may not transfer across languages;
- blind reviewers may infer model origin from style.

### External validity

- open-source repositories may not represent proprietary systems;
- selected languages and issue types may not generalize;
- one hardware configuration may not represent other local deployments;
- one local/cloud pair cannot establish universal routing behavior;
- network-disabled execution excludes tasks requiring live services.

### Conclusion validity

- insufficient power for non-inferiority;
- optimistic margin selection;
- multiple testing;
- aggregation masking repository or complexity heterogeneity;
- survivorship bias from benchmark construction filters.
- benchmark saturation or task defects that change measured performance as
  systems become stronger.

## 22. Reproducibility and evidence

Every valid run retains:

- task and split identity;
- repository URL, base commit, and license;
- immutable container and harness digests;
- container user identity, privilege set, shell invocation, working directory,
  filesystem mounts, and network policy;
- model, quantization, runtime, and provider metadata;
- complete prompts and tool schemas;
- event stream, commands, stdout, stderr, status, and duration;
- initial state identity and final patch;
- router feature vector, decision, and reason;
- F2P, P2P, adversarial, security, and static-analysis results;
- token, monetary, energy, and hardware observations;
- final terminal disposition.

Successful and failed trajectories are published. Release manifests include
checksums for every artifact. Secrets, credentials, private repository paths,
customer data, and reviewer identities are excluded.

Analysis starts from immutable run artifacts and is fully scripted. Figures and
tables must be reproducible from the released manifest and result files.

Longitudinal tables include an explicit compatibility matrix. A new harness
series starts whenever a change can alter tool invocation, parsing, iteration,
or model-visible context. Historical scores are not rebased onto a newer task
set or scaffold without rerunning the historical condition.

## 23. Ethics and responsible release

The dataset construction process records repository licenses and preserves
required attribution. Maintainers are not contacted or burdened by automated
pull requests. Candidate patches are never submitted upstream as part of the
experiment.

Security findings in active projects follow coordinated disclosure when they
represent previously unknown vulnerabilities. Raw evidence is reviewed for
secrets and personal information before publication.

Human review requires informed participation, data minimization, and an
assessment of institutional or independent ethics-review obligations before
recruitment.

## 24. Go/no-go gates

### Benchmark readiness

Proceed only if:

- base and reference environments reproduce reliably;
- every retained task has at least one F2P test;
- selected P2P tests pass on the reference solution;
- hidden evaluation is inaccessible to agents and routers;
- repository-disjoint splits are frozen;
- licenses and contamination metadata are complete.

### Pilot readiness

Proceed only if:

- all three policies terminate and report status correctly;
- GPU utilization and provider token accounting are observable;
- the router uses only `X_route`;
- every trajectory produces an auditable evidence bundle;
- harness failures are distinguishable from model failures.

Model aliases such as `latest` are prohibited in calibration and confirmatory
runs. [`model-lock.json`](model-lock.json) records the immutable manifest digest,
runtime version, quantization, declared context, and experiment context. The
gateway must reject a request when the requested model or the locally resolved
manifest differs from that lock. Changing any locked model creates a new
treatment and requires a new campaign series.

The executable admission contract, including evaluator separation, frozen
patches, routing-policy isolation, and the failure taxonomy, is maintained in
[`construction/HARNESS_V2.md`](construction/HARNESS_V2.md). A change to those
semantics creates a new harness series and must not be presented as model-only
progress against results from an older series.

### Confirmatory readiness

Current decision (2026-08-19): **no-go**. Completed local-first calibration
invalidated the escalation-rate assumption and the checked-in 90-task power
design. No confirmatory trajectory may run until the study is explicitly scoped
as a pilot or a new powered design, benchmark, budget, and analysis package are
committed without inspecting confirmatory outcomes.

Proceed only if:

- routing thresholds and budgets are frozen from calibration data;
- non-inferiority and cost-reduction margins are fixed and justified;
- power analysis is committed;
- statistical code passes simulation and synthetic null tests;
- model identifiers and container digests are immutable;
- human-review rubric and sampling are frozen;
- no confirmatory outcome has been inspected.

## 25. Publication claims

A favorable result may support a claim of the form:

> On the specified repository-level benchmark, hardware, agent harness, and
> model pair, transparent local-first routing reduced hosted inference cost by
> X% while remaining within a pre-registered Y percentage-point
> non-inferiority margin for verified issue resolution.

It may not support claims that:

- local models are generally equivalent to frontier models;
- commercial providers use the same routing strategy internally;
- passing repository tests proves production safety;
- results transfer to untested languages, repositories, models, or hardware;
- local inference is free.

A negative result remains publishable if the protocol and evidence are intact.
It may establish that local attempts add latency or cost without avoiding enough
hosted work, or that the policy is useful only below a measurable complexity
boundary.

## 26. Relationship to prior evaluation work

### SWE-bench

SWE-bench establishes repository-level issue resolution as an execution-based
evaluation task. This protocol adopts its base-commit reconstruction,
issue-to-reference-patch construction, F2P/P2P test distinction, and resolved
rate while extending the object of evaluation from model patch generation to
dynamic inference-routing policies.

The evolution of SWE-bench also demonstrates why benchmark scores are system
measurements. The original full benchmark, the human-validated 500-task
SWE-bench Verified subset, and the Bash Only leaderboard differ in task set,
container harness, scaffold, prompt, and budget. Bash Only improves
contemporaneous model comparison by freezing mini-SWE-agent, but its own
documentation states that 1.x and 2.x releases are not necessarily comparable.
This protocol therefore does not use results produced by different scaffold
families as a continuous model-progress series.

Verified further motivates independent task audit: human review found
underspecified problem statements, overly specific tests, and unreliable
environments in the original benchmark. Later audits of frontier-model failures
show that static public benchmarks can become saturated, contaminated, or
dominated by defective tasks. We retain task-level adjudication, publish
exclusion sensitivity analyses, and treat benchmark validity as an empirical
object rather than a permanent assumption.

### HumanEval and Pass@k

HumanEval establishes functional correctness through tests and the unbiased
Pass@k estimator for repeated samples. This protocol uses Pass@k as a secondary
capability metric while separately measuring single-run reliability and
trajectory variance.

### CodeBLEU

CodeBLEU combines lexical, AST, and data-flow similarity. This protocol uses it
only diagnostically because repository-level issues may have many correct
solutions that differ from the historical reference patch.

### Security evaluation

Prior Copilot security evaluations demonstrate that functionally plausible
generated code can contain CWE-aligned vulnerabilities. This protocol therefore
keeps functional resolution and security findings as distinct outcomes.

### Human and LLM review

Prior productivity and code-quality studies motivate measuring patch acceptance
and maintainability beyond test execution. Human review remains the qualitative
reference. LLM judges are calibrated against blind human ratings rather than
treated as independent truth.

## 27. References

- Jimenez, C. E. et al. [SWE-bench: Can Language Models Resolve Real-World
  GitHub Issues?](https://arxiv.org/abs/2310.06770). ICLR 2024.
- SWE-bench team. [SWE-bench Verified and Bash Only
  methodology](https://www.swebench.com/verified.html).
- OpenAI. [Introducing SWE-bench
  Verified](https://openai.com/index/introducing-swe-bench-verified/). 2024.
- OpenAI. [Why SWE-bench Verified no longer measures frontier coding
  capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/).
- OpenAI. [Separating signal from noise in coding
  evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/).
- Chen, M. et al. [Evaluating Large Language Models Trained on
  Code](https://arxiv.org/abs/2107.03374). 2021.
- Ren, S. et al. [CodeBLEU: a Method for Automatic Evaluation of Code
  Synthesis](https://arxiv.org/abs/2009.10297). 2020.
- Pearce, H. et al. [Asleep at the Keyboard? Assessing the Security of GitHub
  Copilot's Code Contributions](https://arxiv.org/abs/2108.09293). IEEE
  Symposium on Security and Privacy, 2022.
- Ziegler, A. et al. [Productivity Assessment of Neural Code
  Completion](https://arxiv.org/abs/2205.06537). 2022.
- Farchi, E. et al. [Automatic Generation of Benchmarks and Reliable LLM
  Judgment for Code Tasks](https://arxiv.org/abs/2410.21071). 2024.

## 28. Venue planning note

ICLR 2027 currently lists an abstract deadline of 2026-09-18 AOE and a paper
deadline of 2026-09-25 AOE. The main submission is limited to nine pages before
references, with appendices and supplementary code permitted. Submission is
double blind and requires an AI-use statement; reproducibility and ethics
statements are recommended.

The conference explicitly welcomes datasets, benchmarks, infrastructure, and
hybrid AI systems. Meeting the deadline does not justify reducing the powered
design to an underpowered demonstration. If the confirmatory study cannot be
completed and audited in time, the correct outcome is a later venue or a pilot
paper, not weaker scientific claims.
