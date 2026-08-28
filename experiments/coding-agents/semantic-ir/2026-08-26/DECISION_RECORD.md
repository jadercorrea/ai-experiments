# Decision record: begin with a semantic core, not a surface language

## Context

The broader hypothesis combines several possible benefits: fewer representation
tokens, fewer invalid programs, explicit effects, stable identities, semantic
patches, and deterministic lowering. Attempting all of them in a new language
would make a positive or negative result uninterpretable.

## Options considered

1. Design a compact textual language immediately.
2. Build a general AST and TypeScript compiler.
3. Build a domain-bounded typed semantic core with an interpreter and one
   deterministic projection.
4. Extend the evidence-carrying handoff schema directly with program nodes.

## Decision

Choose option 3. The canonical object is a typed tree transported as JSON. It
supports one realistic control-and-effect path and has enough semantics to make
unknown symbols, type mismatches, undeclared effects, and incomplete option
handling rejectable before execution.

Keep this experiment separate from `evidence-carrying-handoffs`. The epistemic
IR and action IR may eventually share identity, provenance, and verification
primitives, but they answer different causal questions and must not share
outcome claims.

## Consequences

- The slice can test the trusted semantic boundary with no model dependency.
- The same object can be interpreted and projected, reducing backend ambiguity.
- JSON verbosity and model familiarity remain untested.
- Generality is intentionally absent; unsupported operations are visible rather
  than encoded through an unrestricted escape hatch.
- A future surface language or compact serialization can be compared without
  changing the core semantics.

Reconsider the boundary after one matched TypeScript task runs end to end. Add
an operation only when that task or a predeclared successor task requires it.

## Matched task boundary

### Context

A model-facing comparison requires both arms to begin from identical repository
state and terminate at the same executable evaluator. Letting each arm use a
different fixture or verifier would confound representation policy with task
difficulty or acceptance criteria.

### Decision

Construct one public, permanently non-confirmatory TypeScript task. Materialize
only its participant repository, allow exactly one target file to change, keep
mode instructions outside the workspace, and audit all non-target files against
a content lock before either evaluator runs. The semantic arm must start clean
and can modify the target only through validated deterministic lowering.

### Consequences

- Evaluator behavior is shared across arms and testable before model use.
- The public tree can demonstrate isolation mechanics but cannot itself provide
  secrecy; real runs require a separately mounted participant workspace.
- The full JSON schema is part of the semantic arm's context dose and must be
  counted rather than treated as free infrastructure.
- The construction task cannot contribute outcome data because its solution and
  hidden evaluator are already public.

## Model-facing interface freeze v0

### Context

The matched task alone does not define what an agent can observe or change.
Giving the source arm a normal repository shell while giving the semantic arm
only an IR submission endpoint would confound output representation with
repository access and feedback. Conversely, hiding the semantic schema from
token accounting would manufacture an efficiency advantage.

### Decision

Freeze an output-representation experiment. Both arms receive the same locked
workspace, list and read operations, public evaluator operation, and terminal
finish operation. Both may inspect public tests and rerun the public evaluator.
The only arm-specific mutation capability is:

- source: atomically write UTF-8 TypeScript to the frozen editable target;
- semantic IR: submit a complete program object that is validated and
  deterministically lowered to the same target.

Freeze the exact serialized contexts by byte length and SHA-256. Include the
full program schema and closed catalog in the semantic context and count them in
later provider-native token accounting. Permit the semantic arm to read its
generated TypeScript through the shared workspace interface.

Keep model identity, inference parameters, budgets, retry limits, token
accounting, and the calibration stopping rule outside this freeze. No model call
or efficacy claim is authorized by freezing these interfaces.

### Consequences

- A future comparison can attribute the principal treatment difference to
  direct source writing versus checked semantic submission.
- The semantic arm does not yet receive a semantic representation of repository
  state; this does not test the broader claim that transcripts or source text
  should be replaced as the agent's input persistence layer.
- Context sizes may legitimately differ, but their exact doses are auditable.
- The interface permits multiple writes, submissions, and public test runs;
  their numerical limits must be fixed by the later budget and retry policy.
- The checked freeze is deterministic, pins its schema and builder, and carries
  a self-digest. Any change requires an explicit regeneration and review.

## Semantic patch boundary v0

### Context

The single-shot and break-even observations regenerated whole programs. They did
not test the stronger claim that semantic state can persist across agent turns
and receive small, checked edits. A general graph rewrite system would introduce
multiple untested mechanisms at once.

### Decision

Add one transactional operation, `replace_subtree`, over the canonical program.
A patch identifies the exact program and canonical base digest. Each operation
identifies a stable target node, carries the expected canonical subtree digest,
and supplies a replacement whose root preserves that identity.

Validate every operation against the unchanged base before applying any of
them. Reject overlapping targets, replacement identity collisions, and any
result that fails the existing structural, symbol, type, or effect checks.
Non-overlapping operations must be order-independent at the canonical result
boundary.

Construct one matched local task where a staged unified diff and the semantic
patch begin from byte-corresponding source and semantic state, then face the
same public and hidden evaluators.

### Consequences

- Stale edits fail explicitly instead of being heuristically rebased.
- Patch application is all-or-nothing and leaves the caller's base object
  unchanged.
- Stable identities become active concurrency and audit primitives rather than
  projection markers only.
- The first source and semantic reference patches converge to byte-identical
  TypeScript under the same executable behavior.
- This v0 is not a merge language: it has no insert, delete, move, symbol-table,
  effect-declaration, or conflict-resolution operation.
- The local reference task is construction evidence only. It contains no model
  call and cannot support token-efficiency, efficacy, or generality claims.

The next gate is a frozen heterogeneous task set with at least one intentionally
unsupported task. Add a new patch operation only when a predeclared task cannot
be represented safely by `replace_subtree`.

## Heterogeneous candidate matrix v0

### Context

The local semantic-patch construction task exercises two string literals in one
program. Expanding directly from that result would permit task selection and IR
features to co-evolve, making later token or Pass@1 comparisons vulnerable to
support-set cherry-picking.

### Decision

Freeze six task families before constructing fresh instances: two small, two
medium, and two large across local literals, dataflow, control flow, effects,
and repository scope. Record current support disposition and required semantics
as content-addressed task identities.

Permit two requirement-driven extensions before the final task lock: pure
string equality and an explicit directory-read capability/effect. Forbid any
extension after the first model call. Keep the cross-module migration
intentionally unsupported rather than broadening the study into a repository IR.

Use two linked estimands. All-task utility includes every locked task and counts
a semantic unsupported outcome as failure. Conditional efficacy includes only
tasks supported by both arms at the final lock, but may never be reported
without the all-task result and semantic applicability rate.

### Consequences

- The support boundary becomes measured behavior rather than an implicit task
  filter.
- Task identities and objectives cannot change in response to model outcomes.
- Candidate disposition may change only through pre-model implementation of a
  frozen semantic requirement and must be locked again before execution.
- The candidate freeze does not authorize model calls: concrete repositories,
  sealed evaluators, contexts, model policy, budgets, order, and stopping rule
  remain deferred.
- Rejected construction candidates must be retained with predeclared reasons so
  task curation remains auditable.

## Additive catalog extension v1: pure string equality

### Context

The frozen `reserved-id-guard-001` family requires exact string equality before
an existing database effect. The v0 expression grammar already contains calls,
strings, variables, and typed conditionals, but its closed catalog has no such
predicate. The v0 schema and implementation are pinned by earlier observations,
so editing them would change a historical interface after measurement.

### Decision

Leave v0 byte-for-byte unchanged. Add program/catalog v1 as a thin layer over
the frozen v0 expression grammar and introduce exactly one symbol:
`string.equals(string, string) -> boolean`.

Define it as pure, exact, and case-sensitive. It requires no capability,
contributes no effect, executes directly in the interpreter, and lowers to
TypeScript strict equality. Keep semantic patch v0 unchanged; use a v1
application boundary that runs the same transactional checks and validates the
result as a v1 program.

Record the frozen suite commit and task digest beside the construction evidence.
Do not change the task's identity or its `extension_required` disposition at
candidate-freeze time, and do not authorize model calls.

### Consequences

- The extension is traceably requirement-driven rather than selected from model
  outcomes.
- Earlier v0 observations remain reproducible against identical files.
- The reference reserved-id guard is expressible and rejects `root` before I/O.
- JSON/tree shape was not the limiting factor in this task; the closed semantic
  instruction catalog was.
- Construction support is not final benchmark support. Concrete instances,
  hidden evaluators, and final dispositions remain to be sealed.
- The explicit directory-read capability/effect is still required before the
  final task lock.

## Additive catalog extension v2: directory fallback

### Context

The frozen `directory-fallback-001` family requires an ordered second lookup
with the explicit `network.read:directory` effect. The expression grammar can
already represent its nested option match, but v1 lacks the catalog symbol,
effect enum, interpreter capability, and target adapter.

One additional mismatch appears at the patch boundary. The frozen task requires
only `replace_subtree`, while the exact function-effect list is stored outside
the expression tree. A new effectful call makes that redundant summary stale.
Weakening exact validation would permit overdeclared authority; adding a second
patch operation would change the frozen task identity.

### Decision

Add program/catalog v2 with
`directory.get_by_id(string) -> option<user>` carrying
`network.read:directory`. Preserve the frozen v0 expression grammar and the v0
semantic patch operation.

Treat the function-effect list as canonical derived metadata during v2 patch
application. Validate the base and every patch precondition first, apply all
tree replacements to a copy, statically infer the resulting effects from the
closed catalog, store the sorted exact list, and then run complete v2 validation.
Direct program submissions continue to require exact declarations and reject
both missing and unused effects.

Interpret capabilities lazily and record only effects actually executed, in
order. Project both required adapters into the TypeScript capability contract
and execute the projected fallback as part of construction verification.

### Consequences

- The agent-facing patch remains the predeclared `replace_subtree` operation.
- The canonical result explicitly stores both effects without trusting the
  agent to synchronize redundant metadata.
- Empty input performs no effect; local success performs only the user-store
  read; local miss performs user-store then directory reads.
- Missing and invalid directory adapters fail only when the fallback is reached.
- Program/catalog v0 and v1 remain unchanged and reproducible.
- Both predeclared extensions are construction-supported, but final support
  dispositions still require fresh sealed task instances before model use.

## Final heterogeneous task lock v0

### Context

The candidate matrix fixed six semantic requirements and the all-task analysis
before concrete fixtures existed. Catalog v1 and v2 subsequently satisfied the
two permitted extension gates, but construction support alone did not establish
that fresh repositories, hidden evaluators, source patches, and semantic patches
formed matched tasks. The repository-scope family also needed an honest terminal
outcome rather than silent exclusion.

The frozen gate additionally required retained rejected candidates and a
contamination audit. Because hidden evaluators and references must remain
auditable in this repository, secrecy cannot be claimed against an unconstrained
process with host-repository or network access.

### Decision

Construct one content-addressed instance for every frozen family without
changing its candidate identity or analysis policy. Use the same repository,
objective, public evaluator, and external hidden evaluator for both arms. Keep
references, hidden evaluators, and publication metadata outside the participant
allowlist.

Require every unchanged baseline to fail hidden evaluation and every source
reference to pass public and hidden evaluation. For the five supported semantic
tasks, require the semantic reference to pass those same evaluators and lower to
editable files byte-identical to the source reference. Retain one deliberately
incomplete source candidate per task that passes public evaluation and fails
hidden evaluation.

Lock final semantic support at five tasks. Record
`cross-module-rename-001` as `semantic_unsupported`, mutate no workspace, and
count it as failure in all-task utility. Preserve the five-task conditional
estimand only as a companion to the six-task result and applicability rate.

Record contamination as `conditional_pre_model_clearance`: zero experimental
subject calls on the exact instances, known coding-agent development exposure,
known overlap with the public construction lineage, and no claim of universal
cleanliness. Require fresh subject contexts without the development thread and
an eventual runner that exposes only the assigned participant surface, denies
host-repository traversal and browsing, records exact context digests, and
repeats the model/provider audit before the first call.

### Consequences

- The concrete task, evaluator, and semantic applicability boundaries can no
  longer move in response to model outcomes.
- Applicability is 5/6; unsupported repository work remains visible in the
  primary all-task denominator.
- Public/hidden discrimination is executable rather than asserted: all six
  retained incomplete candidates pass public and fail hidden evaluation.
- Source and semantic references converge at the target byte boundary for all
  five supported tasks.
- Checked-in hidden material is auditable but only hidden under an isolated
  allowlisted runner; the suite does not claim otherwise.
- Model identity, inference parameters, budgets, exact arm contexts, execution
  order, stopping rule, and the runner itself remain deferred. This lock
  authorizes zero model calls and no efficacy claim.

## Calibration execution lock v0

### Context

The final heterogeneous suite fixed task content, evaluator behavior, semantic
applicability, and the analysis denominator, but it intentionally left the
experimental subject and orchestration policy unspecified. Running even one
cell before model identity, context construction, capabilities, budgets, order,
and stopping were fixed would permit outcome-dependent protocol changes.

### Decision

Reuse the locally locked Amazon Bedrock Sonnet 4.6 treatment identity, but not
the earlier one-request admission budget. Freeze a new calibration policy at
temperature zero with exact rendered context and tool-schema digests for each
cell. Give each subject only a fresh ephemeral workspace and a closed tool
surface; expose neither shell, host repository, external network, browsing,
hidden evaluator, nor references.

Execute six fixed pairs in a balanced nonadaptive order. Treat the unsupported
semantic repository task as an automatic zero-call terminal failure in the
all-task denominator. Allow at most 11 provider-call cells, 12 turns per such
cell, 132 requests globally, and USD 10 total estimated spend, reserving the
worst-case next request before dispatch. Do not retry provider failures, replace
runs, or stop for efficacy. Stop only for the spend rule or two consecutive
infrastructure-invalid cells.

Require a separate schema-valid launch record to bind explicit authorization,
the exact freeze and model-lock digests, a repeated contamination audit, fresh
context, credential and endpoint/IAM preflight, provider-retention-policy basis,
and zero prior experimental subject calls. The pre-execution freeze itself
continues to authorize no inference.

### Consequences

- The execution policy is content-addressed at
  `02bb16238584057e809d8bd2655a13b8b5d163a2317774735e4e636d18a83c05`.
- Eleven model-bearing cells and one automatic unsupported terminal are fixed;
  ordering and stopping cannot adapt to observed quality.
- Usage already incurred survives later cell interruption, and unsuccessful
  provider attempts consume the global request budget.
- The isolation claim is an allowlisted capability boundary, not an OS-process
  sandbox claim.
- The repeated contamination result remains conditional because the development
  agent saw host-side material and provider weight immutability is unverifiable.
- One gate remains: explicit launch after all launch assertions are checked
  again. Until then, experimental subject calls remain zero and no efficacy
  claim is authorized.

## Calibration 001 invalidation

### Context

The explicit prelaunch checks passed and calibration 001 completed the exact
12-cell schedule with 43 provider responses and USD 0.699015 estimated cost.
The frozen summarizer recorded three source hidden passes and zero semantic
hidden passes. All five supported semantic cells, however, ended before a
single mutation attempt.

### Finding

Each supported semantic subject called `workspace_read` with an artifact label
shown in its system context. Four requested `tasks/.../base/program.json`; one
first requested `tasks/.../participant-context/TASK.md`. Those artifacts were
embedded in the system message but were not mounted in the ephemeral repository
accepted by `workspace_read`.

The runner classified the unavailable path as terminal `tool_protocol_failure`
instead of returning the error to the subject for repair. The semantic arm
depended on embedded program, catalog, and schema artifacts while source files
were addressable through the workspace tool. The mismatch therefore censored
the treatment arm asymmetrically.

### Decision

Invalidate paired efficacy, semantic Pass@1, and cross-arm token comparisons.
Retain the raw 3/6 source and 0/6 semantic counts only as descriptions of this
frozen execution. Retain every request, response, cost, workspace, evaluator,
and failure; do not replace or rerun any cell under the same freeze.

### Consequences

- The lower semantic token total is early-censored and is not efficiency
  evidence.
- The run supports an interface finding: model-visible state needs an
  unambiguous addressable representation, not merely an embedded serialization.
- The next protocol must expose a read-only context surface and return invalid
  tool calls as recoverable observations within the trajectory budget.
- A new paired claim requires fresh sealed task instances because the provider
  has now seen the exact calibration-001 inputs.

## Recoverable addressable-context execution lock v1

### Context

Calibration 001 exposed embedded task artifacts under path-like labels that the
participant workspace could not read. A rejected read terminated the cell, so
all five supported semantic trajectories were censored before mutation. The old
instances were also no longer fresh after 43 provider responses.

### Decision

Create six new exact task instances from the same frozen strata while changing
identity namespaces, exported symbols, repository bytes, hidden evaluators, and
all content locks. Revalidate source references for all six tasks and semantic
reference convergence for the five supported tasks without calling a model.

Give every model-visible context artifact one allowlisted `context://` handle.
Expose immutable context only through `context_list` and `context_read`; keep
participant repository files in a disjoint workspace-relative namespace.

Return subject-originated tool protocol errors as typed recoverable results and
preserve every tool-call response inside the trajectory. Continue to classify
context drift, unexpected evaluator failures, and orchestrator failures as
infrastructure-invalid. Preserve the original schedule, model, sampling,
budgets, spend reservation, hidden-evaluation, unsupported-task, isolation, and
analysis rules.

Require a separately content-bound v1 launch record. The freeze itself
authorizes zero provider calls.

### Consequences

- The exact v0 calibration is neither rerun nor overwritten.
- The failure mode that invalidated calibration 001 is now executable as a
  passing recovery test.
- Wrong namespace, malformed tool input, and frozen-budget rejection consume
  trajectory opportunity but do not automatically terminate the experimental
  cell.
- Integrity failures remain distinguishable from correctable subject errors.
- The v1 suite remains calibration-grade: exact bytes are fresh, while its
  requirements and development lineage are deliberately disclosed.
- One gate remains before any new inference: explicit launch against the final
  v1 freeze and its artifact lock.

## Calibration 002 precondition-affordance invalidation

### Context

The explicitly authorized v1 calibration completed all twelve cells with 102
provider responses and USD 3.606831 estimated cost. Addressable context and
recoverable tool errors behaved as designed: no context-read failure recurred,
no cell was infrastructure-invalid, and every scheduled cell reached a frozen
terminal outcome.

The raw summarizer reported two source and one semantic hidden passes in the
six-task denominator. The semantic arm consumed 799,255 tokens versus 217,314
for source.

### Finding

Semantic submission required canonical base-program and target-subtree digests.
Those values were absent from participant context, while the visible context
manifest supplied a different byte-level artifact digest. The subject had no
hashing or semantic-inspection operation capable of producing the required
canonical values.

Subjects consequently learned preconditions through rejection feedback. Each
such discovery consumed the three-attempt mutation budget. Source submissions
had no equivalent cryptographic-precondition discovery step. This introduced a
treatment-asymmetric capability defect after the v1 addressability defect had
been removed.

### Decision

Retain the complete execution and its raw descriptive counts. Invalidate claims
comparing representation efficacy, token efficiency, and repair latency. Do not
replace or rerun cells under the same freeze.

Require the next protocol to return opaque canonical state and subtree
precondition tokens through a read-only semantic context operation. Selecting
or reading immutable concurrency state must not consume mutation budget, and
the model must never be asked to calculate a cryptographic digest.

Require fresh exact task instances before the next paired run.

### Consequences

- Context v1 passed its intended addressability and recovery test.
- The raw 2/6 source, 1/6 semantic, and 3.68× semantic-token observations
  describe v1 but do not isolate semantic representation quality.
- The next experimental-TDD layer is now explicit: semantic concurrency tokens
  must move from model-generated payload to deterministic infrastructure.
- Calibration 002 remains a completed, auditable infrastructure observation;
  it is not discarded or silently corrected.

## Capability-mediated semantic preconditions lock v2

### Context

Calibration 002 proved that addressable context and recoverable tool errors were
necessary but insufficient. Semantic subjects still had to submit canonical
program and subtree digests that were neither visible nor computable through
their frozen tool surface. Rejection feedback became a digest oracle and spent
the mutation budget asymmetrically.

### Decision

Replace model-generated digest preconditions with opaque infrastructure-issued
capabilities. Add a read-only `semantic_state_inspect` operation that accepts
selected stable node IDs and returns one state token plus node-bound target
tokens. Keep inspection outside the mutation budget. Require the semantic patch
wire format to carry those tokens and no digest fields.

Bind tokens to the issuer, canonical program state, target node identity, and
canonical subtree state. Resolve tokens only inside trusted infrastructure,
then translate to and reuse the existing atomic semantic patch implementation
for program IR v0, v1, or v2. A rejected submit remains atomic and consumes one
mutation attempt.

Create six fresh exact capability-v2 instances, revalidate all source and
supported semantic references locally, and freeze the unchanged paired
schedule, model, budgets, stopping rules, evaluator policy, and isolation
controls around the new interface. Do not authorize a provider call in this
checkpoint.

### Consequences

- The subject selects semantic intent by stable node identity but never computes
  a cryptographic digest.
- The model-facing patch schema contains no `sha256` or digest field.
- Cross-node replay, cross-store use, and stale state are rejected before
  persistent state changes.
- One wire format covers the v0/v1/v2 program backends in the frozen suite.
- The synthetic inspect-submit-finish trajectory passes hidden evaluation with
  exactly one mutation attempt.
- The fresh suite digest is
  `be3a565ac4aba5a618062dc2feb69cd8cc5f8b849c125ea72825dc19a6c9d3ab`.
- The execution freeze digest is
  `d8a3083ad2a08c5e66c5b10d61c390df6d75f42b7419a61f7906fe1896e8eab1`.
- Experimental subject calls remain zero. A separate explicit launch is the
  only remaining gate before calibration 003.

## Calibration 003 descriptive acceptance

### Context

The explicitly authorized capability-v2 calibration completed all twelve cells
with 78 successful provider responses and USD 2.101818 estimated cost. All five
supported semantic cells reached terminal submission. Six semantic inspections
issued the opaque state and target tokens used by eight subsequent patch
submissions.

The three rejected semantic patches violated stable target-node identity. No
rejection involved a missing, guessed, mismatched, or stale capability token.
The digest-precondition defect from calibration 002 did not recur, and no cell
was infrastructure-invalid.

The raw summarizer reported four semantic and two source hidden passes in the
six-task denominator. On the five supported pairs, it also reported four
semantic and two source passes. The semantic arm used 32 provider requests and
9,108 output tokens versus 46 requests and 19,887 output tokens for source. Its
larger input surface raised total use to 357,435 tokens versus 227,191 and cost
to USD 1.181601 versus USD 0.920217.

### Decision

Accept calibration 003 as a valid, complete descriptive comparison of the two
frozen interfaces. Accept capability v2 as resolving the specific unavailable
semantic-precondition defect identified by calibration 002.

Do not authorize an inferential, general efficacy, or general token-efficiency
claim. Do not replace or rerun cells under this freeze. Report all-task utility,
the 5/6 semantic applicability boundary, supported-task outcomes, provider
requests, input and output tokens separately, total tokens, and cost together.

Move the next red test to semantic input projection. Preserve the canonical
program and opaque capability semantics while testing compact typed slices,
stable graph handles, or progressive inspection. Require deterministic recovery
of omitted state and local whole-trajectory break-even before freezing a fresh
confirmatory task set.

### Consequences

- Capability-mediated preconditions are no longer the observed semantic-arm
  bottleneck.
- The semantic arm doubled hidden passes in this small suite and reduced
  provider requests by 30.4% and output tokens by 54.2%.
- The semantic arm still used 57.3% more all-task tokens and cost 28.4% more;
  supported-pair total-token overhead was 68.2%.
- The observed tension separates mutation efficiency from context efficiency.
- Calibration 003 advances the experimental-TDD sequence from context
  correctness to context density; it does not establish a language winner.

## Compact semantic context v1 construction

### Context

Calibration 003 used fewer semantic provider requests and output tokens but
more total tokens because each turn carried a complete canonical program,
catalog, program schema, patch schema, and sometimes a separate expression
grammar. State disclosure and mutation grammar were bundled into one large
input surface.

Three realistic options were considered: compress the entire canonical JSON,
introduce another compact AST as persistent state, or retain canonical state and
project only an addressable outline with exact expansion on demand.

### Decision

Keep canonical program IR as the sole persistent source of truth. Project a
deterministic preorder topology whose short handles carry operation, parent,
slot, and lexical hint but no canonical subtree or stable node ID. Add a
read-only `semantic_context_inspect` operation that maps selected handles to the
exact canonical subtree, lexical scope, stable node identity, and existing
opaque capability tokens.

Do not change `semantic_patch_submit`, its recursive expression schema,
capability resolution, validators, effects, or lowering in this slice. Measure
context and structured tools as canonical UTF-8 bytes, explicitly excluding any
provider-token claim.

### Consequences

- All five supported reference patches still pass their existing hidden
  evaluators through the compact projection.
- Initial semantic context falls from 81,171 to 13,647 bytes, an 83.19%
  reduction across the five tasks.
- Context plus tool definitions falls 56.63%, from 119,501 to 51,832 bytes.
- Compact semantic input remains 3.18 times the corresponding source surface;
  no task reaches local initial-surface break-even.
- Progressive inspection responses grow from 1,897 to 6,418 aggregate bytes
  because exact subtrees and scope move from eager to on-demand disclosure.
- Unchanged tool definitions now account for 73.67% of the compact surface,
  isolating recursive patch grammar as the next dominant cost.
- Deterministic construction issuer keys make fixture tokens reproducible and
  are not treated as authorization credentials.
- The next red test is a compact finite motion/patch instruction surface that
  deterministically reconstructs the same canonical replacement and preserves
  all validation boundaries.
