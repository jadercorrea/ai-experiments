# Evidence-carrying handoffs for coding agents

## Status

**Public protocol preview v0.1. The design is not frozen and no experimental
runs are authorized.**

Start with [PROTOCOL_PREVIEW.md](PROTOCOL_PREVIEW.md) for the public scientific
summary and claim boundaries. See [RELATED_WORK.md](RELATED_WORK.md) for the
scoped primary-source review and
[publication/preview-manifest.json](publication/preview-manifest.json) for the
machine-readable no-results contract.

This directory is an execution handoff for a future agent. It records the
research rationale, the intended comparison, the invariants that must survive
implementation, and the gates that must pass before any calibration or
confirmatory trajectory is started.

The study is separate from both generations of the local-first-routing work:

- `local-first-routing/2026-07-30` tested routing and established a published
  calibration pilot followed by a confirmatory no-go;
- `local-first-routing-v2/2026-08-19` is a separate design draft;
- this study asks what context a successor agent should inherit after a failed
  coding-agent attempt.

Results from those studies must not be pooled with this one. Their artifacts
may inform construction choices, but they are prior work rather than outcome
data for this protocol.

## Working title

> **When Should a Coding Agent Forget? A planned preregistered study of raw
> traces, clean restarts, and evidence-carrying handoffs.**

The title is intentionally a research question rather than a product claim.
The experiment remains useful if structured handoffs do not help, help only
under specific failure modes, or actively harm recovery.

## Why this experiment exists

Long-running coding-agent systems frequently split work across attempts,
sessions, models, or providers. When an attempt fails, the next agent can be
given:

1. no history and a clean task restart;
2. the full raw trajectory from the failed attempt; or
3. a compact, structured bundle of claims backed by repository evidence.

Each choice carries a different risk.

- A clean restart discards useful investigation and repeats work.
- A raw trace preserves evidence but also preserves noise, fixation, stale
  assumptions, accidental secrets, and misleading hypotheses.
- A structured handoff may preserve useful discoveries while filtering noise,
  but the compression step can omit the one detail the receiver needed or can
  turn an uncertain hypothesis into an apparently authoritative fact.

The central engineering question is therefore not simply whether more context
helps. It is:

> After a coding agent fails, what information should the next agent inherit to
> maximize verified recovery without inheriting the first agent's failure?

This is a workflow and harness question. It is not a model leaderboard.

## Intended external relevance

The design deliberately targets problems discussed by teams building coding
agents and their evaluation infrastructure:

- OpenAI's Codex work emphasizes agent orchestration, harness design, safe
  execution, task quality, and separating evaluator signal from infrastructure
  noise.
- Anthropic's agent-engineering publications emphasize long-running harnesses,
  context engineering, managed-agent boundaries, and infrastructure noise.

Relevant public references:

- [OpenAI — AI Systems Engineer, Codex Agents](https://openai.com/careers/ai-systems-engineer-codex-agents-san-francisco/)
- [OpenAI — Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [OpenAI — Harness engineering](https://openai.com/index/harness-engineering/)
- [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Anthropic — Managed agents](https://www.anthropic.com/engineering/managed-agents)
- [Anthropic — Infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise)
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

These references motivate the question; they do not endorse this protocol.

## Decision frame

### Outcome

Determine whether a structured, evidence-carrying handoff improves a successor
coding agent's hidden-verified resolution rate relative to a clean restart and
to the failed attempt's raw trajectory.

### Hard constraints

- The repository and task start from the same immutable commit in every arm.
- Receiver workspaces are reset; no patch or untracked file from the sender may
  leak into a receiver unless the protocol explicitly represents it as data.
- Hidden evaluator material is never visible to sender, receiver, compressor,
  or handoff generator.
- The primary outcome is executable and deterministic; no LLM judge decides
  whether a task passed.
- Models, tools, harness revisions, prompts, budgets, timeouts, and runtime
  identities are frozen before confirmatory execution.
- Invalid and failed runs are retained and reported.
- Within-provider comparisons are primary. Cross-provider comparisons are
  exploratory unless separately powered and preregistered.
- Existing local-first-routing outcomes are not pooled into this experiment.

### Risks the design must expose

- **Anchoring:** the receiver repeats the sender's wrong hypothesis.
- **Action imitation:** the receiver repeats failed commands or near-identical
  patches without obtaining new evidence.
- **Authority inflation:** compression turns uncertainty into a false fact.
- **Evidence loss:** compression removes a detail necessary for recovery.
- **Workspace leakage:** one arm inherits state outside its assigned context.
- **Evaluator leakage:** task construction reveals hidden acceptance criteria.
- **Harness confounding:** provider adapters expose materially different tools,
  prompts, budgets, or repository state.
- **Infrastructure noise:** network, sandbox, rate limit, setup, or runtime
  failures are incorrectly counted as agent failures.
- **Researcher degrees of freedom:** treatments, exclusions, or metrics change
  after seeing outcomes.

## Experimental flow

```text
immutable task + source commit
            |
            v
locked first-stage sender, fixed budget
            |
            v
      qualifying failure
       /       |       \
      /        |        \
clean restart  raw trace  structured evidence bundle
      \        |        /
       \       |       /
       reset receiver workspace
            |
            v
  Codex receiver or Claude receiver
            |
            v
hidden executable evaluator + telemetry
```

The same qualifying sender failure should be reused across all applicable
receiver arms. This paired construction reduces variance and makes the context
treatment—not a different first-stage failure—the causal contrast.

## Unit of analysis

The conceptual unit is a **task × sender-failure × receiver-provider × handoff
mode** cell. Repetitions within a cell estimate stochastic variability.

The exact statistical unit, clustering strategy, and handling of repeated
sender traces must be frozen in `PREREGISTRATION_DRAFT.md` before any outcome is
observed.

## Stage 1: producing a qualifying failure

### Sender requirements

The sender must be a locked, relatively inexpensive agent configuration. A
local model is preferred if it can produce non-trivial repository work at an
acceptable rate, but the sender identity is a design variable that must be
frozen after calibration.

Freeze at minimum:

- model provider, exact model identifier, and model digest where available;
- harness revision and adapter revision;
- system and task prompts;
- tool inventory and permissions;
- wall-clock, token, tool-call, and cost budgets;
- retry policy;
- runtime image, hardware, and dependency lock;
- source commit and task manifest checksum.

### Qualifying failures

A sender trace may enter the receiver study only when it ends in one of the
predeclared categories:

- timeout without hidden-verified resolution;
- a material patch that fails public verification;
- no patch despite a task that passed the construction audit;
- clean exit with an unverified or incorrect claim of completion;
- a recoverable provider or harness failure, if that failure class is included
  as a separate preregistered stratum.

Infrastructure failures must not silently enter the ordinary task-failure
stratum. They are retained, labeled, and either analyzed separately or declared
invalid according to the frozen rules.

### Failure eligibility audit

Before material is passed to a receiver, an automated audit must verify:

- the source commit and task identity;
- that public evaluator commands were available and executable;
- that the sender did not access hidden evaluator material;
- the termination reason and resource use;
- whether a patch existed and its digest;
- whether the failure matches an allowed category;
- that secrets and personal data are absent or redacted reproducibly.

## Stage 2: receiver treatments

### Arm A — Clean restart

The receiver receives only the original task specification and the normal
repository checkout. It receives no sender trace, summary, patch, or signal that
another agent attempted the task.

Purpose: measure the value of a fully independent second attempt and establish
the baseline cost of rediscovery.

### Arm B — Raw trajectory

The receiver receives the complete allowed sender trajectory in chronological
order, using a stable serialization. It may include messages, tool calls,
command output, inspected paths, and patch diffs, subject to deterministic
redaction and size rules.

Questions that must be frozen:

- Is the raw trace injected into the initial prompt or exposed as an artifact?
- How are outputs larger than the context window handled?
- Are binary data and terminal control characters removed?
- Are failed patch contents included?
- Does the receiver know the trace belongs to a failed attempt?

The default recommendation is to label the trace explicitly as a failed
attempt. Hiding that fact would test a different question.

### Arm C — Structured evidence bundle

The receiver receives the original task plus a versioned, machine-readable
handoff. The handoff is not a free-form narrative and must not include the
sender workspace itself.

Minimum proposed fields:

```text
schema_version
experiment_id
task_id
source_commit
sender_identity
termination_reason
resource_usage
language_policy
  task_language
  sender_output_language
  trace_languages[]
  realization_language
  mixed_language_policy
files_inspected[]
commands_run[]
  command
  exit_code
  output_digest
  evidence_ref
observations[]
  claim_id
  proposition
    subject
    predicate
    object
  confidence
  evidence_refs[]
  realizations[]
    language
    text
hypotheses_rejected[]
  hypothesis_id
  proposition
  falsifying_evidence_refs[]
  realizations[]
unresolved_failures[]
  failure_id
  proposition
  evidence_refs[]
  realizations[]
failed_patch
  present
  diff_digest
  evaluator_summary
redactions[]
integrity
  bundle_digest
  generator_revision
```

Every factual claim must point to evidence captured during the sender run.
Unsupported recommendations and persuasive prose should be prohibited. The
bundle may say what was observed and falsified; it should not tell the receiver
what conclusion to reach.

The schema must be committed and versioned before calibration. Any schema
change after outcome inspection creates a new protocol version.

### Language is part of the treatment

The evidence layer and its linguistic realization are distinct protocol
objects. A proposition records stable semantic roles and evidence references;
a realization records how that proposition is expressed in a declared
language. Alternate realizations must preserve proposition identifiers and the
same evidence graph rather than being treated as independent summaries.

This control is scientifically motivated but deliberately conservative.
Motion-event lexicalization and *thinking for speaking* show that languages can
package event components differently
([Talmy, 1985](https://dingo.sbs.arizona.edu/~hharley/courses/PDF/TalmyLexicalizationPatterns.pdf);
[Slobin, 1991](https://benjamins.com/catalog/prag.1.1.01slo)), while empirical
effects beyond language are mixed
([Papafragou et al., 2002](https://www.sciencedirect.com/science/article/pii/S0010027701001664);
[Papafragou & Selimis, 2010](https://doi.org/10.1080/01690960903017000)). More
directly relevant multilingual LLM evaluations find that prompt language can
affect task performance
([Huang et al., 2023](https://aclanthology.org/2023.findings-emnlp.826/);
[Behzad et al., 2024](https://aclanthology.org/2024.findings-emnlp.916/)), and
language mixing in reasoning traces has measurable, context-dependent effects
([Wang et al., 2025](https://aclanthology.org/2025.emnlp-main.132/)).

Protocol v0.1 therefore freezes task, trace, and realization languages and
records language mixing and token use. It does not test multilingual effects
or claim that two translations are causally equivalent. A future ablation may
vary realization language while holding the proposition/evidence graph fixed,
but it requires a separate preregistration and power analysis.

### Handoff generator

The experiment must freeze how the bundle is produced. Candidate mechanisms:

1. deterministic extraction from normalized trace events;
2. deterministic extraction plus a constrained model summarizer;
3. sender-authored handoff validated against trace evidence.

The recommended first confirmatory protocol is deterministic extraction where
possible, with a constrained summarizer only for observations and rejected
hypotheses. A validator must reject claims whose evidence references are
missing. Generator model identity, prompt, budget, and revision are part of the
manifest.

## Receivers and provider comparisons

Run the three arms separately with:

- a locked Codex configuration;
- a locked Claude Code or Claude Agent SDK configuration.

Primary estimates are Clean vs Raw vs Structured **within Codex** and separately
**within Claude**. Differences between providers are exploratory because their
harnesses, tool semantics, and model families are not naturally exchangeable.

Adapter parity must be audited. Each receiver should have equivalent:

- repository state and task prompt;
- shell and filesystem permissions;
- network policy;
- public evaluator access;
- token, time, and tool-call ceilings;
- retry policy;
- event normalization;
- cost accounting;
- secret-redaction behavior.

Provider-native features may be used only when recorded and justified. Perfect
surface symmetry is neither possible nor desirable if it makes one provider
artificial, but material asymmetry must be visible in the report.

## Outcomes

### Primary outcome

**Hidden-verified issue resolution:** the receiver produces a patch that passes
the frozen hidden executable evaluator without prohibited evidence access.

One task should map to one binary primary outcome per receiver trajectory. If
partial credit is desired, it must be a secondary metric defined before runs.

### Secondary outcomes

- public evaluator result;
- wall-clock time;
- provider-reported and normalized token use;
- estimated cost under frozen price tables;
- tool calls and command executions;
- time to first novel, task-relevant action;
- time to first new piece of evidence;
- repeated failed command count;
- repeated rejected-hypothesis count;
- similarity between sender and receiver patches;
- regression count;
- changed-file count and patch size;
- prohibited evidence access attempts;
- infrastructure failures and retries;
- task, trace, and realization languages and mixed-language event counts;
- provider-native token use by recorded language where available;
- receiver's final confidence and whether it matches executable outcome.

### Failure-inheritance metrics

The study should operationalize, before execution:

- **repeated action:** normalized command or edit substantially equivalent to a
  failed sender action without intervening new evidence;
- **inherited hypothesis:** receiver adopts a sender hypothesis before obtaining
  independent supporting evidence;
- **recovery from rejected hypothesis:** receiver avoids or explicitly rejects
  a sender path documented as falsified;
- **novel action latency:** time from receiver start to first action absent from
  the sender trace;
- **patch inheritance:** structural or textual similarity between failed sender
  patch and final receiver patch.

Automated metrics are preferred. Any qualitative annotation must use a frozen
rubric, blinded treatment labels where possible, and independent review.

## Task construction

### Required properties

Use fresh repository-level tasks that are disjoint from previous experiment
tasks and not present in public model-training artifacts where reasonably
verifiable. Each task must provide:

- an immutable pre-fix source commit;
- a license record;
- a natural-language issue specification;
- a public verification surface that helps agents work but does not reveal all
  acceptance criteria;
- a hidden executable evaluator;
- a reviewed reference patch or reference resolution;
- a solvability audit under the frozen environment;
- a leakage audit;
- a difficulty rationale;
- a checksum manifest.

### Partitions

Tasks must be separated before outcome runs:

- **construction:** unrestricted protocol and tooling development;
- **calibration:** used to validate telemetry, budgets, failure production, and
  treatment delivery; never reported as confirmatory evidence;
- **confirmatory:** frozen and untouched until every gate passes.

Calibration tasks and trajectories must never be promoted into confirmatory
data after their outcomes are known.

### Initial scale proposal

The first bounded design target is:

- 6 fresh confirmatory tasks;
- 3 handoff modes;
- 2 receiver providers;
- 2 repetitions per cell;
- at most 72 receiver trajectories, plus qualifying sender trajectories.

This is a planning ceiling, not yet a justified sample size. A variance and
power analysis based only on construction/calibration data must decide whether
the confirmatory design is informative. If it is not, the experiment stops or
is redesigned under a new protocol version before confirmatory runs.

Suggested total spend ceiling: **USD 750**, inclusive of sender, handoff
generation, receiver, and evaluator costs. Freeze a lower per-cell budget where
possible. Reaching the ceiling stops new trajectories; it does not justify
discarding completed failures.

## Execution phases

### Phase 0 — Fixture-only construction

Use synthetic events, deterministic fixtures, and non-study executors to
develop the sender harness, handoff generator, receiver adapters, event model,
evaluators, and run explorer. This phase makes no candidate study-model calls.

### Phase 1 — Calibration-entry lock

Before the first calibration trajectory:

- freeze calibration tasks, evaluators, assignment, and pass/fail criteria;
- seal a disjoint candidate confirmatory task pool without exposing its
  contents to execution agents;
- freeze the candidate model set and an outcome-independent selection rule;
- lock treatment delivery, adapters, redaction, telemetry, provisional resource
  limits, retries, and invalidation for the calibration block;
- version and validate schemas, hash artifacts, and sign one explicit
  calibration authorization.

Calibration identities and budgets are not automatically the final
confirmatory locks. Any permitted post-calibration change must follow the
predeclared selection rule, increment the protocol version, and retain the
superseded artifacts.

### Phase 2 — Calibration

Run one complete calibration block end to end. Audit:

- whether sender failures are frequent enough and substantively useful;
- whether all arms receive exactly their permitted context;
- whether workspaces reset identically;
- whether hidden evaluators remain hidden;
- whether telemetry supports every preregistered metric;
- whether budgets create floor or ceiling effects;
- whether raw traces overflow context;
- whether the structured bundle retains verifiable evidence;
- whether cost and runtime fit the ceiling.

Publish the calibration disposition even if it produces a no-go.

### Phase 3 — Confirmatory freeze and go/no-go review

Proceed only if the calibration demonstrates treatment integrity, evaluator
integrity, task solvability, usable variance, and feasible cost. Use only the
predeclared calibration decision rule to finalize model identities, sample
size, resource locks, estimands, analysis, multiplicity, missing-data policy,
confirmatory schedule, and hashes. Sign a go/no-go before unsealing
confirmatory tasks to the execution harness.

### Phase 4 — Confirmatory execution

Execute from a precomputed schedule. Append every attempted run to the ledger.
Never overwrite a run directory. Preserve invalid, failed, timed-out, and
successful trajectories.

### Phase 5 — Analysis and publication

Run only the frozen primary analysis first. Exploratory analysis must be clearly
separated. Publish regardless of whether structured handoffs win.

## Repository layout to implement

```text
2026-08-21/
  README.md
  PREREGISTRATION_DRAFT.md
  protocol/
    handoff-bundle-v1.schema.json
    normalized-event-v1.schema.json
    treatments.json
    resource-lock.json
    identity-lock.json
    invalidation-policy.json
    analysis-plan.json
  adapters/
    sender/
    codex/
    claude/
  tasks/
    construction/
    calibration/
    confirmatory/
  schedules/
  runs/
  analysis/
  publication/
  manifests/
```

Large generated evidence belongs in immutable release assets rather than Git
history, following the repository publication contract.

## Required run artifacts

Each attempted trajectory must have a unique, append-only run directory with:

- run manifest and experiment/schema version;
- task, source, evaluator, harness, adapter, model, and runtime identities;
- assigned treatment and schedule position;
- input-context digest;
- normalized event trace;
- raw provider trace when licensing and privacy permit;
- stdout/stderr and command digests;
- starting and final repository state;
- patch and patch digest;
- public and hidden evaluator results;
- tokens, cost, wall time, and tool counts;
- termination and invalidation classification;
- secret-redaction report;
- checksums for all artifacts.

## Agent execution handoff

A future agent implementing this study must proceed in this order:

1. Read this file, the preregistration, the repository publication contract,
   and the existing local-first experiment protocols in full.
2. Inspect the worktree and preserve unrelated or untracked work.
3. Do not start a trajectory or inspect a confirmatory evaluator.
4. Turn each calibration-entry item into an explicit decision with a rationale
   and manifest field; keep confirmatory-only decisions visibly open.
5. Implement schemas and validators before provider adapters.
6. Implement a deterministic workspace-reset audit and a context-diff audit.
7. Build sender and receiver adapters with normalized telemetry.
8. Create construction tasks, then calibration tasks, then seal confirmatory
   tasks. Never reuse a task across partitions.
9. Run static validation and dry runs that do not call study models.
10. Execute one calibration block only after the calibration-entry checklist
    passes and its artifacts are hashed.
11. Resolve every remaining `TO FREEZE` item and produce a written confirmatory
    go/no-go before any confirmatory run.
12. If protocol changes are needed after calibration, increment the version,
    regenerate manifests and schedules, and keep the superseded artifacts.

The agent must not optimize the protocol for a result favorable to GPTCode,
Codex, Claude, OpenAI, Anthropic, local models, or any commercial narrative.

## Publication plan

The public protocol preview was prepared before model selection or outcome
exposure. It is intended for prior-art discovery and methodological criticism;
it is not the frozen preregistration or a result release. Its machine-readable
manifest prohibits result claims and study execution, and its deterministic
artifact lock makes this snapshot comparable with later revisions.

If the study reaches publication, produce four complementary artifacts:

1. **One-screen result page on `gptcode.dev`:** question, design, primary result,
   confidence/uncertainty, cost, and the strongest limitation.
2. **Run explorer:** task, provider, treatment, repetition, events, patch,
   evaluator result, cost, and invalidation reason.
3. **Short manuscript (approximately 5–7 pages):** rationale, protocol,
   estimands, results, limitations, and operational implications.
4. **Immutable GitHub Release:** protocol, schedules, manifests, traces where
   publishable, patches, evaluator outputs, analysis code, and SHA-256 checksums.

The repository and blog should read as a chronological laboratory notebook:
each study states what changed, why it changed, what was frozen, what failed,
and what the next experiment may legitimately conclude.

## Outreach after publication

Do not lead with an offer to work for free and do not contact CEOs with an
unvalidated idea. After a credible artifact exists, contact technical authors,
evaluation engineers, coding-agent infrastructure leads, or relevant hiring
managers with:

- one specific finding or unresolved question;
- one link to the result page;
- one link to reproducible evidence;
- one sentence connecting the result to their published work;
- an invitation to challenge the protocol or identify a missing failure mode.

The artifact must provide value even if no one replies.

## Success and stop conditions

### Success

Success means producing a trustworthy answer or a trustworthy statement that
the bounded design cannot answer the question. A null result, a harmful effect
from raw traces, a harmful effect from structured handoffs, or a calibration
no-go are all legitimate outcomes.

### Stop or redesign when

- task solvability cannot be demonstrated;
- sender failures are trivial or too rare;
- treatment contamination cannot be excluded;
- evaluator or repository leakage is detected;
- provider adapters are materially incomparable within the intended estimand;
- context-window limits make the raw arm undefined;
- telemetry cannot support the primary or failure-inheritance metrics;
- the projected study exceeds the frozen budget;
- confirmatory task integrity is compromised.
- the frozen language, translation, or mixed-language policy changes after
  outcome exposure.

Any redesign after outcome exposure receives a new protocol version and must
not be presented as the original confirmatory study.

## Non-goals

- ranking Codex against Claude;
- proving that GPTCode is superior;
- claiming general agent reliability from one successful run;
- using subjective code quality as the primary outcome;
- hiding infrastructure failures;
- merging this study with earlier local-first results;
- claiming cross-language equivalence or generalization from a single-language
  protocol;
- manufacturing a favorable result for job outreach.

## Initial decision log

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-08-21 | Create a separate experiment family for evidence-carrying handoffs | The causal question differs from local-first routing and must not inherit or pool its outcomes |
| 2026-08-21 | Compare clean, raw, and structured context | These are the three operationally plausible recovery policies and isolate the value and cost of inherited context |
| 2026-08-21 | Reset the receiver workspace in every arm | The treatment is information, not accidental filesystem or patch state |
| 2026-08-21 | Use executable hidden verification as the primary outcome | Avoids persuasive but ungrounded model or human judgments |
| 2026-08-21 | Estimate treatment effects within each receiver provider | Codex and Claude harnesses are not naturally exchangeable; cross-provider results remain exploratory |
| 2026-08-21 | Require evidence references in structured handoffs | Prevents a compressed narrative from turning unsupported hypotheses into facts |
| 2026-08-21 | Preserve invalid and failed runs | Infrastructure noise and failure modes are part of the evidence, not disposable inconvenience |
| 2026-08-21 | Prohibit any model run while the protocol is a draft | Prevents early outcomes from silently shaping confirmatory design decisions |
| 2026-08-24 | Separate evidence propositions from linguistic realizations | Prevents translation or lexicalization choices from silently changing the evidence layer |
| 2026-08-24 | Treat language as a treatment-integrity variable and defer the multilingual causal contrast | Avoids confounding the v0.1 handoff comparison or expanding it into an unpowered language study |
| 2026-08-24 | Publish a protocol preview before confirmatory freeze | Enables external criticism and prior-art discovery without pretending that open model, task, power, and analysis decisions are resolved |
| 2026-08-24 | Split calibration-entry lock from confirmatory freeze | Removes the circular requirement to choose final sample size before calibration can estimate operational variance and cost |
| 2026-08-24 | Encode the preview's no-results boundary in a schema-validated manifest | Makes publication status, exclusions, and lack of authorization executable rather than editorial |
