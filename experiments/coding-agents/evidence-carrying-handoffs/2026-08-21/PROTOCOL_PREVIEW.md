# Public protocol preview v0.1

## Evidence-carrying recovery after coding-agent failure

Snapshot date: **2026-08-24**

| Claim boundary | State at this snapshot |
| --- | --- |
| Publication type | Public protocol preview for critique |
| Protocol status | Design under review; not frozen or preregistered |
| Study-model trajectories | 0 |
| Outcome data observed | No |
| Calibration authorized | No |
| Confirmatory execution authorized | No |
| Model selection | Intentionally unfrozen |
| Funding | Credit applications planned, not submitted |
| Sponsor or vendor endorsement | None |

This document is the public entry point for the study. The detailed design
remains in [README.md](README.md), unresolved confirmatory decisions remain in
[PREREGISTRATION_DRAFT.md](PREREGISTRATION_DRAFT.md), and the scoped scientific
map is in [RELATED_WORK.md](RELATED_WORK.md). The machine-readable
[preview manifest](publication/preview-manifest.json) makes the no-results and
no-execution boundary executable.

## Abstract

When a coding agent fails, a successor can restart without history, inherit the
failed raw trajectory, or receive a compact account of repository-backed
evidence. These policies may change both recovery and failure propagation. We
propose a recovery harness that creates a fresh receiver workspace, assigns one
of those three context policies, and uses an independent executable evaluator
to determine whether the task was resolved. The structured policy separates
language-independent propositions from linguistic realizations and requires
each factual claim to reference normalized events protected by content hashes.
The design preserves invalid and failed trajectories and classifies failures as
model, harness, runtime/infrastructure, evaluator, or product/workflow failures.
Primary estimates will compare context policies within a locked receiver
provider; provider comparisons are exploratory unless separately powered. This
snapshot publishes the causal design and implemented integrity primitives for
critique before tasks, models, power, assignment, and analysis are frozen. It
contains no study outcomes and supports no efficacy claim.

## Research question

For a repository-level task ending in a qualifying first-agent failure, does
the information given to a fresh successor agent change the probability of a
hidden, executable, independently verified resolution?

The proposed intervention has three arms:

1. **Clean restart:** original task and immutable repository state only.
2. **Raw trajectory:** the clean inputs plus the complete allowed, redacted,
   chronologically serialized failed attempt.
3. **Structured evidence:** the clean inputs plus a versioned handoff whose
   factual claims must link to repository or execution evidence.

The study changes inherited information, not inherited filesystem state. Every
receiver begins from the same immutable source commit. Sender patches,
untracked files, caches, and process state are prohibited unless represented by
the assigned context artifact.

## Why this is a harness experiment

The object under test is the recovery layer between model and product:

```text
qualifying sender failure
          |
          v
normalize events + classify failure
          |
          v
clean receiver workspace + assigned context policy
          |
          v
locked receiver harness
          |
          v
independent executable evaluator
          |
          v
auditable trajectory, evidence graph, patch, cost, and result
```

The model is a controlled component of this system, not the sole explanatory
variable. The harness must make context delivery, isolation, identity,
resources, telemetry, retries, redaction, and evaluation observable enough to
distinguish model behavior from system failure.

## Proposed causal estimands

Within each locked receiver-provider stratum, the primary proposed estimand is
the difference in hidden-verified resolution probability between structured
evidence and clean restart. A second proposed contrast compares structured
evidence with the raw trajectory. Whether the raw-versus-clean contrast is
confirmatory or exploratory remains open.

The hypotheses are deliberately two-sided at this preview stage. Structured
evidence may improve recovery by preserving verified discoveries, or harm it by
omitting decisive details, amplifying an incorrect claim, or inducing anchoring.
Directionality, estimands, and multiplicity handling must be frozen before any
calibration outcome is observed.

## Experimental unit and pairing

The conceptual cell is:

```text
task × qualifying sender failure × receiver provider × context policy × repeat
```

The same qualifying sender failure is reused across applicable receiver arms.
This pairing holds the failed attempt constant while context policy varies.
Repeats are required because agent trajectories can diverge even under nominally
fixed configurations. The statistical unit, dependence structure, number of
sender traces per task, repeat count, and assignment schedule remain to be
frozen.

## Eligibility of sender failures

A sender run may enter the receiver study only after an automated eligibility
audit confirms its source commit, task identity, public evaluator availability,
termination reason, patch digest, resource use, absence of hidden-evaluator
access, and deterministic redaction. Candidate qualifying categories include:

- budget or timeout without verified resolution;
- a material patch that fails public verification;
- no patch on a task that passed the construction audit;
- a clean exit with an incorrect completion claim.

Provider, harness, and infrastructure failures will not silently enter the
ordinary model-failure stratum. Included categories and invalidation rules must
be declared before calibration.

## Treatment integrity

The harness must prove, for every receiver start:

- an identical source snapshot and allowed baseline artifact set;
- absence of sender-derived artifacts in the clean arm;
- an exact raw-trace digest in the raw arm;
- an exact bundle and referenced-event digest set in the structured arm;
- no hidden evaluator material in any participant-visible context;
- frozen prompt, tools, budgets, retry policy, runtime, and adapter identity.

The implemented workspace and context audits already reject unexpected files,
changed source content, duplicate artifacts, digest mismatches, and sender
metadata in a clean treatment. They are construction evidence, not evidence
that future experimental deliveries passed.

## Evidence-carrying handoff

The structured handoff is a versioned data object rather than a persuasive
summary. Its current schema records:

- task, source, trace, sender, harness, and generator identities;
- inspected files and commands with evidence references;
- observations, rejected hypotheses, and unresolved failures;
- failed-patch and public-evaluator status;
- language and translation policy;
- redactions;
- event and bundle SHA-256 digests.

Every factual observation, rejected hypothesis, and unresolved failure requires
at least one evidence reference. References must resolve to normalized trace
events, and recorded event hashes must match their canonical content. The
validator rejects private reasoning fields and prevents hidden-evaluator events
from becoming participant-visible.

This integrity design does not prove that a proposition is semantically true.
It proves a narrower and necessary claim: the proposition is attributable to
specific, untampered observed material. Independent evaluators remain the
authority for task resolution.

## Language as a treatment-integrity variable

Semantic propositions and their linguistic realizations are separate objects.
A proposition keeps stable subject, predicate, object, and evidence references;
a realization declares the language used to express it. Task language, sender
output language, trace languages, mixed-language events, translation method,
review status, and token accounting are recorded.

This design responds to two bodies of evidence. Motion-event lexicalization and
*thinking for speaking* show that languages can package event components
differently, while multilingual LLM evaluations show that prompt language and
language mixing can alter measured behavior. Protocol v0.1 therefore controls
and records language but does not test language as a causal factor. A future
multilingual ablation must hold the proposition/evidence graph fixed and receive
its own preregistration, equivalence audit, power analysis, and multiplicity
plan.

## Outcomes and independent evaluation

The proposed primary outcome is binary hidden-verified issue resolution: the
receiver produces a patch that passes a deterministic frozen executable
evaluator without prohibited evidence access. No model or LLM judge decides the
primary outcome.

Proposed secondary outcomes include time, tokens, cost, tool calls, public
evaluator status, time to novel action, time to new evidence, repeated failed
commands, adoption of rejected hypotheses, patch similarity, regressions,
changed-file count, context language, and prohibited-access attempts. A
secondary metric becomes confirmatory only if its extraction rule, missing-data
behavior, and analysis are frozen.

## Failure taxonomy

Each attempted trajectory must receive one primary operational classification:

- **model failure:** the locked agent receives a valid treatment and runtime
  but fails the task under its resource limits;
- **harness failure:** orchestration, context delivery, state reset, identity,
  or telemetry violates the protocol;
- **runtime/infrastructure failure:** sandbox, network, dependency, provider,
  rate-limit, or machine failure prevents a valid attempt;
- **evaluator failure:** the evaluator is nondeterministic, unavailable,
  contaminated, or inconsistent with the task contract;
- **product/workflow failure:** the interaction is technically valid but the
  recovery policy, observability, or operator experience is unusable.

The frozen invalidation policy must define precedence for multiple failures,
rerun eligibility, retry ceilings, and missing cells. All scheduled, attempted,
invalid, failed, and timed-out trajectories remain in the ledger.

## Analysis commitments before execution

The current planning ceiling is six confirmatory tasks, three treatments, two
receiver providers, and two repeats, for at most 72 receiver trajectories plus
sender attempts and handoff generation. This is a cost envelope, not a sample
size justification. Six tasks may be insufficient for the minimum effect of
interest.

Before calibration, the protocol must define the minimum operationally
meaningful effect, candidate analysis methods, candidate model set,
calibration assignment, invalidation and stopping rules, and an
outcome-independent rule that maps calibration variance and cost to a final
sample size, model lock, or no-go. After calibration and before confirmatory
execution, the exact unit and clustering, schedule seed, primary analysis,
uncertainty intervals, multiplicity, missing-data policy, and resource locks
must be frozen. Calibration cannot be pooled into confirmatory inference. If
the available budget cannot support an informative design, the correct
disposition is no-go or redesign under a new version.

## Threats to validity

- **Task representativeness:** a small, fresh task set cannot establish broad
  coding-agent reliability.
- **Task leakage:** public repository history or issue text may expose a
  solution; freshness and leakage audits reduce but cannot eliminate this risk.
- **Interference:** one sender trace reused across arms creates dependence that
  must be modeled rather than treated as independent observations.
- **Provider asymmetry:** Codex and Claude tool semantics are not naturally
  exchangeable; within-provider estimates are primary.
- **Context dose:** raw and structured arms may differ in token count as well as
  organization. Token use is measured; a dose-matched ablation is a possible
  successor study, not an implicit claim in v0.1.
- **Generator error:** evidence references constrain attribution but do not
  guarantee complete or unbiased selection.
- **Evaluator construct validity:** passing tests may not capture every intended
  requirement; task audits and reviewed reference resolutions are required.
- **Researcher degrees of freedom:** outcome exposure before locks would
  invalidate confirmatory interpretation.

## Security, privacy, and responsible publication

Agent outputs, external repositories, tool results, and archives are untrusted.
Before release, publishable artifacts must be scanned for credentials, personal
data, proprietary content, unsafe paths, terminal controls, and provider fields
that cannot be redistributed. Raw chain-of-thought is excluded. Redaction
events record category and count without preserving removed values.

Confirmatory task identities and hidden evaluator contents are excluded from
this preview because early disclosure could contaminate the study. Their hashes
may be committed at freeze while content remains sealed. Source licenses must
be recorded per task before any evidence is redistributed.

## What is implemented today

- JSON Schema contracts for normalized events and structured handoffs;
- canonical event and bundle hashing;
- semantic validation of evidence references and language metadata;
- rejection of hidden-evaluator leakage and private-reasoning fields;
- deterministic workspace snapshots and treatment-context audits;
- unit tests for valid and adversarial cases;
- a schema-validated preview manifest and deterministic artifact-tree lock.

No sender adapter, receiver adapter, task suite, evaluator suite, run explorer,
power decision, model lock, or confirmatory schedule is claimed complete.

## Freeze gates

No calibration trajectory may start until the calibration-entry lock in
[PREREGISTRATION_DRAFT.md](PREREGISTRATION_DRAFT.md) is reviewed, encoded, and
checksummed. No confirmatory trajectory may start until every remaining freeze
item is resolved and a second go/no-go is signed. The highest-risk open gates
across those two milestones are:

1. task partitions, licenses, solvability, leakage audit, and sealed evaluators;
2. exact sender failure policy and sender-generation process;
3. raw serialization, overflow, redaction, and structured generator locks;
4. receiver model, adapter, runtime, tools, budgets, and parity audit;
5. minimum effect, power, assignment, analysis, multiplicity, and missing data;
6. append-only ledger, secret scan, schedules, hashes, and signed authorization.

Publishing this preview does not satisfy those gates. It creates a public
record against which later changes can be compared.

## Cautious contribution claim

Prior work separately establishes repository-level executable evaluation,
linguistic reflection and agent memory, prompt compression, evidence
attribution, and error propagation from stored experiences. As of the scoped
review through 2026-08-24, we have not identified a controlled repository-level
study that combines all of the following: the same qualifying failed trajectory
across clean/raw/evidence-linked treatments; clean receiver workspaces;
independent executable outcomes; and explicit model/harness/runtime/evaluator/
workflow failure attribution. This is a review-bounded gap statement, not a
claim of priority. It will be revised if contrary work is identified.

## Change control and citation

This snapshot is `preview_version: 0.1`. Its file tree is protected by
`publication/artifact-lock.json`. Changes receive a new preview snapshot or, at
confirmatory freeze, a separately identified preregistration. Superseded artifacts
remain available. Formal experiment releases use the repository's CalVer
contract only after the relevant publication package exists.

Until a citable archive or DOI is minted, cite the repository path, experiment
identifier `evidence-carrying-handoffs-2026-08-21`, preview version `0.1`,
snapshot date `2026-08-24`, and commit hash. Feedback that identifies prior art,
an unmeasured confound, an invalid estimator, or a broken integrity invariant is
particularly useful.
