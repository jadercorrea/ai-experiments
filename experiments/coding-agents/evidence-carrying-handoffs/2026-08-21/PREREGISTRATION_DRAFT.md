# Preregistration draft: evidence-carrying handoffs for coding agents

## Administrative status

- Experiment family: `coding-agents/evidence-carrying-handoffs`
- Draft date: `2026-08-21`
- Public preview snapshot: `2026-08-24`, version `0.1`
- Protocol version: `0.1-draft`
- Status: **not frozen**
- Calibration authorized: **no**
- Confirmatory execution authorized: **no**
- Outcome data observed under this protocol: **none**

Every item marked `TO FREEZE` must be resolved, encoded where applicable,
reviewed, and checksummed before confirmatory execution. Before the first
calibration trajectory, the narrower calibration-entry gate below must pass.
Confirmatory execution requires a second explicit freeze and go/no-go after
calibration. Calibration data never enter confirmatory inference.
Publication of [PROTOCOL_PREVIEW.md](PROTOCOL_PREVIEW.md) does not freeze any
open item or authorize model execution.

## Research question

When a first-stage coding agent fails on a repository-level issue, does the
information supplied to a fresh successor agent change the probability of an
executable hidden-verified resolution?

The three information policies are:

- clean restart with no failed-attempt context;
- full redacted raw trajectory from the failed attempt;
- structured evidence-carrying handoff generated from that trajectory.

## Confirmatory hypotheses

### Primary hypothesis

`H1 TO FREEZE:` A structured evidence-carrying handoff changes the probability
of hidden-verified resolution relative to a clean restart within a locked
receiver provider.

The direction must be frozen as either two-sided or directional before
calibration. The conservative recommendation is a two-sided test because a
structured handoff can omit decisive evidence or amplify a false hypothesis.

### Secondary confirmatory hypothesis

`H2 TO FREEZE:` A structured evidence-carrying handoff changes the probability
of hidden-verified resolution relative to a raw trajectory within a locked
receiver provider.

### Mechanism hypotheses

These are secondary unless the annotation and measurement procedure is frozen
and powered:

- structured handoffs reduce repeated failed commands compared with raw traces;
- structured handoffs reduce time to first novel relevant action compared with
  raw traces;
- raw trajectories increase adoption of unsupported sender hypotheses compared
  with clean restarts;
- structured handoffs reduce rediscovery cost compared with clean restarts;
- effects vary by sender termination reason and task failure mode.

### Provider interpretation

Codex and Claude estimates are separate strata. A treatment × provider
interaction is exploratory unless a larger design, sample-size justification,
and multiplicity plan are frozen before confirmatory execution.

## Experimental units and assignment

### Unit

`TO FREEZE:` Define the primary unit as a receiver trajectory nested in a
task × qualifying-sender-failure block. Repetitions and use of the same sender
trace create dependence that must be handled by the analysis model.

### Blocking

At minimum, block or stratify by:

- task;
- qualifying sender trace;
- receiver provider;
- receiver repetition.

### Assignment

`TO FREEZE:` Generate a deterministic randomized schedule from a recorded seed.
Balance treatment order within task, sender trace, and provider. The schedule
must be generated and checksummed before confirmatory task identities are
unsealed to the execution harness.

### Repetitions

Initial planning value: 2 per task × treatment × provider cell.

`TO FREEZE:` Confirm or replace this value after a calibration-only variance,
power, and cost assessment. Calibration outcomes may determine feasibility but
must not be mixed with confirmatory inference.

## Task population

### Target population

Repository-level software engineering issues requiring investigation, code
changes, and executable verification under a bounded agent environment.

### Inclusion criteria

- immutable, license-compatible pre-fix repository commit;
- issue not used in previous experiments;
- task specification understandable without hidden evaluator access;
- deterministic local setup under the locked runtime;
- public verification useful but incomplete;
- hidden deterministic evaluator with no model judgment;
- reviewed reference resolution;
- solvability confirmed independently;
- no known contamination from experiment development.

### Exclusion criteria

- task requires unavailable credentials, live proprietary services, or
  irreproducible external state;
- task depends on unstable network access during evaluation;
- hidden evaluator cannot distinguish the target behavior from superficial
  patches;
- reference resolution is disputed or non-deterministic;
- source license or publication terms prevent evidence release;
- task was used to tune the sender, receiver, handoff generator, or evaluator;
- issue or fix was knowingly exposed to a study model during construction.

### Partitions

`TO FREEZE:` Record disjoint construction, calibration, and confirmatory task
IDs and source digests. Confirmatory materials must be sealed from execution
agents until the go/no-go gate.

Initial target: 6 confirmatory tasks, subject to power and feasibility review.

## Stage-one sender

### Purpose

Produce a realistic failed coding-agent trajectory that can be paired across
receiver treatments. The sender is not an outcome competitor.

### Identity and resources

`TO FREEZE:` Record:

- provider and exact model/version/digest;
- inference parameters;
- harness and adapter commits;
- system, policy, and task prompts;
- available tools and permissions;
- network policy;
- context, token, wall-clock, tool-call, and cost limits;
- retry and backend-fallback behavior;
- runtime image and hardware;
- price table and capture timestamp.

### Qualifying failure categories

`TO FREEZE:` Choose categories from:

1. wall-clock or resource timeout with no hidden pass;
2. material patch that fails the public evaluator;
3. material patch that passes public but fails hidden evaluation;
4. no material patch despite valid setup and task solvability;
5. clean exit with an incorrect completion claim;
6. recoverable provider/harness failure, analyzed in a separate stratum.

Category 3 risks consuming hidden evaluator results before receiver execution.
If used, only eligibility—not hidden failure details—may reach the handoff
generator or receiver, and evaluator leakage must be audited.

### Non-qualifying runs

- sender hidden pass;
- invalid setup or evaluator;
- contaminated task or workspace;
- prohibited evidence access;
- unclassified infrastructure failure;
- missing trace required to construct all arms.

Non-qualifying runs remain in the sender ledger with a disposition and are not
silently discarded.

## Receiver treatments

### Shared receiver input

All arms receive:

- identical original task text;
- a clean checkout of the same immutable source commit;
- identical public repository artifacts;
- the same provider-specific system and policy prompt;
- the same resource limits within a receiver provider.

### Clean restart

No sender-derived context. Input-context audit must demonstrate absence of
sender trace, sender patch, handoff bundle, and sender-failure metadata.

### Raw trajectory

`TO FREEZE:` Define exact serialization, ordering, redaction, size limits,
truncation policy, delivery mechanism, and failure label. Recommended policy:

- chronological normalized event stream plus publishable raw fields;
- explicit statement that this is a failed attempt;
- deterministic removal of secrets and binary/control data;
- no semantic summarization;
- deterministic context-window overflow behavior declared before runs;
- failed patch included as an evidence artifact but not applied to workspace.

### Structured evidence bundle

Construction status: `handoff-bundle-v1.schema.json` and its evidence validator
are implemented and tested. `TO FREEZE:` lock their exact revisions and the
generator contract. The bundle must include source and trace identity,
termination reason, inspected files, commands with outcomes, evidence-backed
observations, falsified hypotheses, unresolved failures, patch digest, resource
usage, redactions, and integrity metadata.

Normative rules:

- every factual claim references captured evidence;
- machine-readable propositions and evidence references are stored separately
  from their linguistic realizations;
- every realization declares its BCP 47 language tag, and alternate
  realizations reuse the same proposition identifiers and evidence graph;
- evidence reference targets exist and their digests verify;
- hypotheses and observations are distinct types;
- confidence is explicit and cannot be silently upgraded;
- recommendations without evidence are rejected;
- hidden evaluator facts are prohibited;
- raw chain-of-thought is neither required nor published;
- the failed patch is referenced, not applied;
- the bundle is immutable once assigned to a run.

### Language and linguistic realization

`TO FREEZE:` Task language, sender-visible language instructions, permitted
trace languages, structured-realization language, mixed-language policy,
translation method and reviewer, and language-specific token accounting.

Language is a treatment-integrity variable. If the raw arm and structured arm
differ in language, the experiment changes both information packaging and
linguistic realization; prompt interpretation, lexical salience, and
tokenization may then confound the handoff contrast. The bundle therefore
represents each evidence-bearing assertion as a stable proposition
(`subject`, `predicate`, `object`, epistemic status, and evidence references)
plus one or more explicitly tagged linguistic realizations. Translation may
change a realization, but must not silently change the proposition or its
evidence graph.

Motion-event lexicalization and the broader *thinking for speaking* literature
motivate this control because languages package event components differently
([Talmy, 1985](https://dingo.sbs.arizona.edu/~hharley/courses/PDF/TalmyLexicalizationPatterns.pdf);
[Slobin, 1991](https://benjamins.com/catalog/prag.1.1.01slo)). Evidence that
these differences alter non-linguistic event cognition is mixed
([Papafragou et al., 2002](https://www.sciencedirect.com/science/article/pii/S0010027701001664);
[Papafragou & Selimis, 2010](https://doi.org/10.1080/01690960903017000)), so
this literature is a theoretical motivation rather than evidence that the
present handoff effect exists. More directly, multilingual LLM studies report
performance differences under different prompt and reasoning languages
([Huang et al., 2023](https://aclanthology.org/2023.findings-emnlp.826/);
[Behzad et al., 2024](https://aclanthology.org/2024.findings-emnlp.916/)).
Language mixing in reasoning traces is also an empirically observed model
behavior whose performance effects remain context dependent
([Wang et al., 2025](https://aclanthology.org/2025.emnlp-main.132/)).

Protocol v0.1 contains no confirmatory multilingual contrast. All causal
conclusions are restricted to the frozen language policy, and equivalence
between two realizations must not be inferred merely because they reference
the same proposition.

### Handoff generator

`TO FREEZE:` Select deterministic extraction or deterministic extraction plus a
constrained summarizer. If a model participates, freeze its identity, prompt,
parameters, budget, and evidence validator. Record bundle-generation cost
separately and include it in treatment-cost analysis.

The same finalized bundle must be delivered to all repetitions for the same
task × sender-failure block unless the protocol explicitly treats generator
stochasticity as another factor.

## Receiver configurations

### Codex stratum

`TO FREEZE:` model, service tier, reasoning effort, CLI/SDK/app version, harness
commit, prompt, tools, sandbox, network policy, retry policy, resource ceilings,
and telemetry adapter.

### Claude stratum

`TO FREEZE:` model, service tier, reasoning mode, Claude Code or Agent SDK
version, harness commit, prompt, tools, sandbox, network policy, retry policy,
resource ceilings, and telemetry adapter.

### Parity audit

Before calibration, document every material provider difference. The audit
must verify semantic parity for repository reset, command execution, public
evaluator access, prohibited paths, time accounting, cost accounting, and
termination classification.

## Outcomes

### Primary outcome

Binary `hidden_verified_resolution`:

- `1`: final receiver workspace passes the frozen hidden executable evaluator,
  preserves prohibited-path constraints, and has no evaluator leakage;
- `0`: otherwise, unless the run is invalid under the frozen invalidation
  policy.

The evaluator version and checksum must be frozen before confirmatory runs.

### Secondary outcomes

`TO FREEZE:` exact definitions and extraction procedures for:

- public evaluator pass;
- wall-clock seconds;
- input, output, cached, and reasoning tokens where available;
- normalized cost and provider-billed cost;
- tool calls and shell commands;
- first novel relevant action latency;
- first new evidence latency;
- repeated failed commands;
- repeated rejected hypotheses;
- failed-sender/final-receiver patch similarity;
- regression count;
- patch size and changed-file count;
- prohibited access attempts;
- final confidence/calibration;
- task, trace, and realization languages plus mixed-language event counts;
- provider-native token use stratified by recorded language where available;
- infrastructure failures and retries.

Provider telemetry that lacks semantic equivalence must be reported separately
rather than forced into a false common metric.

## Failure-inheritance annotation

`TO FREEZE:` Create a rubric and test it on construction data only.

Proposed categories:

- `repeated_failed_action_without_new_evidence`;
- `sender_hypothesis_adopted_without_support`;
- `sender_hypothesis_independently_confirmed`;
- `sender_rejected_hypothesis_avoided`;
- `sender_rejected_hypothesis_repeated`;
- `novel_investigation_branch`;
- `failed_patch_reused_substantially`;
- `failed_patch_repaired_with_new_evidence`.

Prefer deterministic event comparisons. If humans annotate semantic hypotheses,
treatment labels and executable outcomes should be blinded where practical,
with at least two reviewers and a frozen disagreement procedure.

## Invalidation and infrastructure failures

`TO FREEZE:` Commit an invalidation policy before calibration.

Candidate invalid reasons:

- source or task checksum mismatch;
- dirty or leaked starting workspace;
- missing or corrupted assigned context;
- hidden evaluator exposure;
- provider outage before material task work;
- harness crash not attributable to the agent;
- telemetry loss affecting primary-outcome integrity;
- execution beyond resource limits due to harness error.

Principles:

- invalidation is about experimental integrity, not poor performance;
- invalid runs remain in manifests and cost totals;
- retry eligibility and maximum attempts are frozen;
- agent-caused tool misuse is generally an outcome, not infrastructure invalidity;
- backend/harness failure rates are reported separately even when retried.

## Analysis plan

### Primary estimands

Within each receiver provider:

1. difference in hidden-pass probability: Structured − Clean;
2. difference in hidden-pass probability: Structured − Raw.

`TO FREEZE:` Decide whether Raw − Clean is confirmatory or exploratory.

### Statistical model

`TO FREEZE:` Select a model appropriate for paired task/sender blocks and small
samples. Candidate approaches include exact paired randomization inference,
hierarchical logistic regression with task and sender-trace effects, or a
predeclared combination with one designated primary analysis.

Do not choose the model after viewing confirmatory outcomes. Report effect
sizes and uncertainty intervals, not only thresholded significance.

### Multiplicity

`TO FREEZE:` Define how two provider strata and two primary contrasts are
handled. A hierarchical testing order or adjusted interval procedure is
preferred to unqualified multiple claims.

### Missing and invalid data

`TO FREEZE:` Specify:

- whether invalid trajectories are rerun;
- maximum reruns per scheduled cell;
- treatment of provider refusals and safety stops;
- how partial telemetry affects secondary metrics;
- whether a missing cell stops the paired block.

### Exploratory analyses

Clearly label analyses by sender failure category, task type, receiver provider,
patch similarity, context size, or cost efficiency as exploratory unless they
are separately powered and frozen.

### Deferred multilingual ablation

`H-LANG (future; not part of protocol v0.1):` Holding the task, repository,
evidence graph, receiver configuration, evaluator, and resource limits fixed,
changing only the handoff realization language may change hidden-verified
resolution and evidence use.

This hypothesis must receive a separate protocol version, translation and
semantic-equivalence audit, power analysis, assignment schedule, and
multiplicity plan. No multilingual outcomes may be inspected under v0.1 and
then presented as confirmatory evidence for this hypothesis.

## Sample size, power, and budget

Planning ceiling:

- 6 confirmatory tasks;
- 3 treatments;
- 2 providers;
- 2 repetitions;
- maximum 72 receiver trajectories plus sender attempts and handoff generation.

`TO FREEZE:` Use construction/calibration-only data to estimate whether this
design can distinguish an operationally meaningful effect. Define the minimum
effect of interest before confirmatory execution.

Proposed all-in spend ceiling: USD 750.

`TO FREEZE:` Per-run token, time, tool-call, and cost caps; provider price-table
snapshot; stopping behavior at 50%, 80%, and 100% of budget. Budget exhaustion
stops new starts but never erases completed outcomes.

## Calibration gate

Exactly one calibration block may be authorized after the calibration-entry
lock. That lock must include:

- immutable calibration tasks, evaluators, assignment, and success criteria;
- a sealed, disjoint candidate confirmatory task pool;
- candidate study models and an outcome-independent rule for selecting or
  rejecting their confirmatory configurations;
- treatment serialization and delivery, workspace and context audits, event
  normalization, redaction, and telemetry;
- provisional identity, runtime, resource, retry, invalidation, security, and
  cost ceilings for calibration;
- the minimum operationally meaningful effect, candidate analysis methods, and
  the rule by which calibration variance and cost determine confirmatory sample
  size or a no-go;
- an append-only calibration schedule and ledger, artifact hashes, and signed
  calibration authorization.

Confirmatory execution remains prohibited until a written go/no-go review.

Calibration passes only if all are true:

- source reset and context delivery audits pass in every arm;
- hidden evaluator remains inaccessible;
- at least one non-trivial qualifying sender failure is produced;
- structured bundle validation has zero unsupported factual claims;
- raw trace handling is deterministic and fits the declared policy;
- primary outcome is deterministic across evaluator repeats;
- all primary and required secondary telemetry fields are captured;
- no treatment suffers an obvious prompt or resource asymmetry;
- projected confirmatory spend fits the ceiling;
- no severe floor or ceiling effect makes the comparison uninformative.

Any protocol change prompted by calibration must increment the protocol version,
follow the predeclared decision rule, regenerate schedules and hashes, and
retain superseded artifacts. Looking at confirmatory task contents to make that
change invalidates their sealed status.

## Confirmatory stop rules

Stop new runs and quarantine the affected block when:

- evaluator leakage or workspace contamination is detected;
- task or reference solution is shown invalid;
- provider/model identity changes;
- an adapter changes treatment semantics;
- the frozen budget is exhausted;
- repeated infrastructure failures cross the frozen threshold;
- a security or secret-handling issue is discovered.

Do not stop early because results appear favorable, unfavorable, or null unless
an outcome-independent sequential rule was preregistered.

## Reporting commitments

Report:

- every scheduled and attempted run;
- success, failure, timeout, invalidity, and infrastructure failure;
- deviations from protocol;
- primary contrasts before exploratory analyses;
- effect sizes and uncertainty;
- provider strata separately;
- cost and wall time inclusive of handoff generation;
- the frozen language policy, detected language mixing, translation metadata,
  and language-specific token accounting;
- the strongest alternative explanations;
- negative and null findings;
- task, model, harness, adapter, evaluator, and runtime identities;
- checksums for released evidence.

Do not report this as a Codex-versus-Claude benchmark and do not infer broad
coding-agent reliability from six tasks.

## Security, privacy, and publication review

Before any release:

- scan traces and patches for credentials, personal data, proprietary content,
  terminal escape sequences, and unsafe files;
- record deterministic redactions without exposing removed values;
- confirm repository and issue licenses;
- exclude raw chain-of-thought and non-publishable provider fields;
- verify archives before extraction and publish SHA-256 checksums;
- make hidden evaluator release timing explicit so it cannot contaminate active
  confirmatory runs.

## Freeze checklist

### Protocol

- [ ] Experiment ID and protocol/schema versions frozen
- [ ] Hypotheses and directionality frozen
- [ ] Primary unit, blocking, and assignment frozen
- [ ] Primary and secondary outcomes operationalized
- [ ] Statistical model and multiplicity plan frozen
- [ ] Invalidation, retry, and missing-data policies frozen
- [ ] Budget, stopping, and resource rules frozen
- [ ] Task, trace, realization, translation, and language-mixing policies frozen

### Tasks and evaluators

- [ ] Construction, calibration, and confirmatory task lists disjoint
- [ ] Source commits and licenses recorded
- [ ] Reference patches independently reviewed
- [ ] Public and hidden evaluators deterministic
- [ ] Solvability and leakage audits complete
- [ ] Confirmatory tasks and evaluators sealed

### Treatments

- [ ] Raw trajectory serialization and overflow policy frozen
- [x] Handoff schema and evidence validator committed
- [ ] Handoff generator identity and prompt frozen
- [ ] Proposition/realization separation and language metadata audited
- [ ] Clean-arm absence audit implemented
- [ ] Receiver workspaces reset and verified identically

### Models and harnesses

- [ ] Sender identity and resources frozen
- [ ] Codex receiver identity and resources frozen
- [ ] Claude receiver identity and resources frozen
- [ ] Provider parity audit reviewed
- [x] Normalized event schema committed
- [ ] Cost tables and telemetry adapters frozen
- [ ] Language-aware token accounting limitations documented

### Reproducibility

- [ ] Schedule generated from recorded seed
- [ ] Protocol and schedule checksums recorded
- [ ] Append-only run ledger implemented
- [ ] Secret-redaction and publication checks implemented
- [x] Dry-run validation passes without study-model calls
- [ ] Repository worktree and revision recorded

### Authorization

- [ ] Calibration-entry lock reviewed and signed
- [ ] One calibration block explicitly authorized
- [ ] Calibration disposition written
- [ ] Confirmatory freeze and go/no-go explicitly signed

Until the relevant authorization boxes are complete, the next agent may build
infrastructure and construction artifacts but must not execute study-model
trajectories.
