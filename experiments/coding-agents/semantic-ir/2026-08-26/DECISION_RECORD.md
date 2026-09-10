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

## Semantic motion lexicalization v1 construction

### Context

Compact Context v1 reduced state disclosure by 83.19%, but its unchanged
recursive patch grammar occupied 5,613 canonical bytes per task. The next red
test required a finite mutation surface, semantic round-trip for all five
references, unchanged validation boundaries, and local source break-even.

### Decision

Keep canonical program IR and capability-mediated patch application unchanged.
Represent replacement intent as a flat tree of eight words:
`str`, `var`, `call`, `let`, `if`, `match`, `ok`, and `err`.

Address motion nodes with short `r` references, inspected external symbols with
ordered `s` slots, and lexical bindings with `b` slots. Derive the replacement
root identity from the inspected target and generate descendant node and symbol
identities deterministically inside trusted infrastructure. Reject malformed
graphs, invalid words and arity, scope escapes, catalog mismatches, stale
capabilities, types, and effects before applying the unchanged atomic patch.

Measure both the flat output payload and the complete initial context/tool
surface. Preserve a failed break-even assertion as a result rather than widening
the language or removing required protocol disclosure.

### Consequences

- All five supported references reconstruct semantically equivalent canonical
  patches and pass their existing hidden evaluators.
- Patch payloads fall from 7,828 to 3,032 aggregate bytes, a 61.27% reduction.
- Tool definitions fall from 38,185 to 19,035 bytes, a 50.15% reduction.
- Full semantic initial surface falls 34.46%, from 51,832 to 33,972 bytes.
- The 16,277-byte source break-even gate still fails; motion v1 is 2.09 times
  the source surface.
- Context plus non-submission tools alone occupy 25,052 bytes, proving that no
  further optimization of only the motion schema can satisfy the frozen gate.
- No model call is authorized. The next red test moves to a session-level
  instruction ISA that reduces repeated prose and tool-contract disclosure
  without weakening the semantic decoder or checked backend.

## Semantic session instruction ISA v1 construction

### Context

Motion Lexicalization v1 cut replacement payload and schema size, but the model-
facing interface still repeated eight independently described tools. Even a
zero-byte semantic submit schema could not cross the source gate because context
plus the remaining tool definitions already occupied 25,052 aggregate bytes.

### Decision

Preserve Compact Context v1, Motion v1, canonical state, and all validation
backends. Replace the model-facing tool collection with one session instruction
`x({i, a})`: a finite opcode plus positional operands.

Assign eight opcodes to the existing context list/read, semantic inspect,
workspace list/read, public evaluation, semantic submit, and finish operations.
Disclose the complete opcode, operand, binding, and motion grammar in compact
context. Keep only the opcode and outer array in the provider-facing schema;
enforce exact per-opcode shapes and all semantic invariants in the deterministic
decoder. Dispatch nonsemantic opcodes to their unchanged adapters and route
inspection/submission through the existing semantic stores.

Count the system line, task, canonical outline, full ISA legend, delimiters, and
single complete tool definition. Explicitly exclude and report provider wrappers,
conversation history, dynamic responses, and decoder implementation bytes.

### Consequences

- All eight operations retain an executable dispatch path through one tool.
- All five semantic references preserve root identity and pass hidden evaluation.
- Initial surface falls from 33,972 Motion v1 bytes to 14,442 bytes, a 57.49%
  reduction.
- The local source comparator is 16,277 bytes; Session ISA v1 crosses the gate
  by 1,835 bytes, or 11.27%, and every individual task also crosses.
- The source comparator still uses its frozen verbose tool surface. Because
  90.58% of the Motion-to-Session reduction is shared tool consolidation, the
  break-even is an engineering gate and not a matched treatment effect.
- Positional submit payloads fall another 24.47%, from 3,032 to 2,290 bytes.
- Provider-side JSON grammar masking is weaker because operand validation moves
  into the decoder. Whether this increases repair loops is deliberately unknown.
- Dynamic inspection responses remain outside the initial gate and must be
  charged in a complete trajectory.
- No model call is authorized. The next red test applies the same session
  transport to the source arm; only a matched pair may proceed to a fresh
  execution freeze and separately authorized Calibration 004.

## Matched source session-ISA control v1

### Context

Session ISA v1 crossed the old source initial-surface gate, but 90.58% of its
Motion-to-Session reduction came from collapsing shared tool definitions. The
frozen source comparator still used seven verbose tools. Launching that pair
would confound representation with infrastructure compression.

### Decision

Wrap source operation in the exact same `x({i,a})` schema, system line, common
opcodes, and dispatcher as the semantic arm. Define only the source-specific
submit operand as `S[unified-diff]`; retain semantic `I` and Motion `S` as its
treatment-specific path. Route the source payload through the unchanged staged,
editable-path-restricted, atomic source patch backend.

Measure context/tool and reference-submit bytes separately. Also publish a
partial reference transport proxy, but label it explicitly as a source lower
bound because it includes semantic inspection and excludes source workspace
reads.

### Consequences

- The two arms share the exact 269-byte tool definition and common dispatcher.
- All five source and five semantic references pass hidden evaluation.
- Semantic initial surface is 14,442 versus 6,405 source bytes, a 125.48%
  overhead under matched static infrastructure.
- Semantic submits are 2,290 versus 9,337 source bytes, a 75.47% reduction.
- The asymmetric partial proxy is 23,256 semantic versus 15,742 source bytes,
  but cannot support a treatment claim because source observation is uncharged.
- The prior 11.27% win is retained as an engineering result against the verbose
  interface and withdrawn as a candidate matched comparison.
- No model call is authorized. The next red test must match `L/W` source
  observation against semantic `I` before any execution freeze.

## Matched observation surface v1

### Context

The matched source Session ISA removed the shared-tool confound, but its partial
transport proxy charged semantic inspection while assigning zero bytes to
source workspace observation. That source lower bound favored source by 47.73%
and could not determine whether to freeze execution or compact the semantic
state again.

### Decision

Charge both arms for deterministic known-reference observation through the
frozen one-tool ISA. For the primary source policy, issue `L[]` and read only
the editable paths parsed from the reference unified diff. Preserve the exact
path/bytes/SHA-256 listing and path/content/SHA-256 read responses. Compare this
with the frozen semantic `I[reference handles]` exchange.

Count initial surface, observation instructions and responses, and reference
submit. Report a separate sensitivity that reads every listed source workspace
file. Mark both policies as oracle-informed construction trajectories and keep
model calls unauthorized.

### Consequences

- Source targeted observation costs 12,020 bytes; semantic inspection costs
  6,524 bytes.
- The complete targeted known-reference surface is 27,762 source versus 23,256
  semantic bytes, a 16.23% semantic reduction.
- Semantic is smaller in all five supported pairs; margins range from 6.73% to
  23.12%.
- Reading all three source workspace files raises the source total to 34,370
  bytes and the semantic construction margin to 32.34%.
- Semantic still pays an 8,037-byte initial-state penalty. Observation saves
  5,496 bytes and submit saves 7,047 bytes, producing the 4,506-byte net result.
- No provider tokens, model choices, repair behavior, latency, cost, or general
  efficacy are established.
- The local construction gate now passes. The next red test is a fresh matched
  execution freeze with a separate explicit launch gate for Calibration 004.

## Matched Session execution freeze v1

### Context

The matched observation surface crossed local construction break-even, but its
reference trajectories could not establish whether a model would choose useful
files, handles, instructions, or repairs. The capability-v2 tasks had already
been experimental model inputs during Calibration 003 and could not be reused as
fresh exact instances.

### Decision

Deterministically derive `session-patch-tasks-v3` from the same six frozen task
families while changing exported names, semantic identities, repository bytes,
reference tokens, hidden-evaluator bytes, and content locks. Record that these
instances are exact-byte fresh but remain family-derived and exposed to
development agents.

Freeze a twelve-cell paired schedule with three source-first and three semantic-
first pairs. Keep the unsupported cross-module semantic cell as an automatic
all-task failure, so eleven cells may call the provider. Give every callable
cell the exact same one-tool `x({i,a})` bytes and preserve the same source diff
and checked semantic backends behind it. Make invalid envelopes and instructions
recoverable and count them separately.

Inherit the Calibration 003 model, temperature, output, turn, mutation,
evaluation, request, timeout, and spend controls. Bind complete evidence and
provider-native accounting into the runtime. Keep execution authorization in a
separate schema and require a content-bound launch record that repeats the
contamination, digest, credential, endpoint/IAM, and retention checks.

### Consequences

- The exact six task instances have zero experimental subject calls, but no
  universal contamination-clean claim is available.
- All six source references and all five supported semantic references pass the
  hidden evaluator through the shared Session ISA runtime; supported projections
  converge byte-for-byte.
- The schedule contains twelve cells and eleven possible calls, with balanced
  pair order and unchanged applicability accounting.
- Every callable cell uses byte-identical `tools/session.json`; treatment now
  differs in state and mutation semantics, not in outer tool transport.
- Opcode use, envelope and instruction rejections, recoverable errors, repairs,
  provider tokens, requests, latency, cost, and evaluator results are frozen as
  required outputs.
- The suite digest is
  `30e4a58a578b4b18c7a07b43cb04db1d97c0b7f8b93ae06d97b6c8ef28efa1ca`;
  the freeze digest is
  `c2e49b3b32c2e9af6c577cab70c425a6ab74637744a01b9557535c6eca3f6232`.
- No launch record was created and no model call is authorized. The only next
  gate is explicit Calibration 004 launch after repeated prelaunch checks.

## Calibration 004 descriptive acceptance

### Context

The matched execution freeze pre-registered fresh exact instances, one shared
Session ISA tool, balanced order, budgets, accounting, and a separate launch.
The user subsequently authorized the eleven provider-call cells. Prelaunch
checks reverified every digest, fresh-context boundary, credential presence,
endpoint/model identity, and current public provider policy. The inference-
scoped credential again could not read the effective account retention mode;
the launch records that limitation and makes no account-specific ZDR claim.

### Decision

Accept Calibration 004 as a valid and complete descriptive observation. Bind
the result to freeze
`c2e49b3b32c2e9af6c577cab70c425a6ab74637744a01b9557535c6eca3f6232`
and retain all twelve scheduled outcomes without replacement or rerun.

Report both all-task and supported-task comparisons. Treat the unsupported
semantic cross-module cell as a failure in all-task utility and as zero-call
resource use. Use the five supported pairs for treatment resource ratios. Keep
inferential and general efficacy claims unauthorized.

### Consequences

- All twelve cells completed with 101 successful responses from the locked
  model, no infrastructure-invalid cell, and USD 2.006349 estimated cost.
- Source passed 2/6 hidden evaluations and semantic 1/6; supported-task counts
  were 2/5 and 1/5.
- On supported pairs, semantic used 20.9% more requests, 86.8% more input,
  18.0% less output, 78.6% more total tokens, and 55.5% more cost.
- Semantic reached two supported terminals and exhausted three turn budgets;
  source reached three supported terminals and exhausted two.
- Semantic recorded more recoverable errors, rejected instructions, rejected
  mutations, and repair cycles. The run does not isolate the causal share of
  instruction opacity versus repeated state and transcript growth.
- The prior 16.23% known-reference byte advantage is retained as a construction
  fact and rejected as a predictor of model-driven whole-trajectory efficiency.
- The next red test uses the frozen trajectories for deterministic session-state
  replay and transcript compaction before considering another model call.

## Explicit Session State Replay v1

### Context

Calibration 004 showed that a dense instruction format can still induce an
expensive transcript. The five supported semantic cells used 86.8% more input
tokens than source while generating less output. Before another model call, the
frozen evidence permits a construction question: how much accumulated history
can be replaced by explicit state without changing the observable result of the
actions already taken?

### Decision

Replay every provider-call cell from its frozen baseline. Before each of the 101
requests, derive a typed snapshot containing namespace separation, current
workspace, read context, inspected semantic handles, bounded errors, latest
evaluation and submission, and exact budgets/counters. Replace every prior
assistant/tool message with that snapshot while preserving the initial system,
initial user, exact tool, model, and sampling fields.

Execute all 131 recorded `x` actions against the reconstructed runtime and
require result equality. Canonicalize only evaluator workspace paths,
cache-dependent Deno `Check` lines, and millisecond durations; compare every
other result byte exactly. Measure complete canonical request bytes and keep
provider-native tokens explicitly unclaimed.

### Consequences

- All 131 actions reproduce their normalized original results across 101 turns
  and eleven call cells; no model call occurs.
- Explicit state removes 260,646 canonical bytes, a 17.73% aggregate reduction.
- Source falls 41.64%; semantic falls 4.56%. Source state is smaller in 37/43
  post-initial requests and semantic state in 23/47.
- State materialization costs 43.14% at turn two. Aggregate break-even arrives
  at turn four and the reduction reaches 38.64% at turn twelve.
- Every source cell improves. Three of five semantic cells become larger, so the
  aggregate result is not a universal compact-state win.
- Full semantic inspections consume 394,439 repeated snapshot bytes, 2.28 times
  semantic workspace state, and become the next measured bottleneck.
- Recorded-action result equivalence does not establish that a model would
  choose the same action from compact state.
- The next red test separates persistent capability identity from an evictable
  semantic subtree working set and requires reconstruction through explicit
  deterministic re-fetch without next-action oracle knowledge.

## Representational Dependence Hypothesis registration

### Context

Discussion of motion lexicalization exposed a broader question: even when two
model-facing surfaces decode to one canonical semantic object, lexical labels
and structural packaging may change what a language model attends to, selects,
or repairs. Adding that question to Calibration 008 would change its estimand
after its instruction grammar and provider-admission probes were already built.

### Decision

Register the Representational Dependence Hypothesis as a future calibration.
Separate lexical cues from structural packaging, require deterministic equality
of the decoded canonical IR, and hold capabilities, evidence, budgets,
verification, model, and sampling constant. Do not add any such condition or
model-visible variable to Calibration 008.

### Consequences

- The hypothesis will not be lost, but it cannot contaminate the current test.
- A later design must isolate lexical and structural factors rather than treat
  source versus semantic representation as a causal identification strategy.
- Calibration 008 must complete or be formally abandoned before power, cost,
  contamination, and launch decisions for the new hypothesis are made.

## Matched Nested Instruction-Grammar Session execution freeze v2

### Context

Grammar v3 proved local bijection with Grammar v2 and moved the complete union
below `{"v": instruction}`. Probe 003 then established that the exact commit
and finish schema objects are accepted by the frozen Bedrock endpoint. The
previous Calibration 008 freeze still referenced the provider-rejected
top-level union and could not be launched as written.

### Decision

Derive a parallel Calibration 008 freeze from the previous instruction-grammar
freeze. Preserve every task, context, static tool, model, sampling, limit,
accounting, isolation, schedule, stopping, analysis, memory, and progress
variable. Keep work requests unchanged. In commit and finish, advertise the
exact Grammar v3 schemas, validate the envelope before dispatch, and pass only
the inner instruction to the frozen Session runtime.

Bind Probe 003 as admission evidence while explicitly denying a constrained-
decoding claim. Distinguish its two synthetic requests from the 127 earlier
experimental-subject responses. Retain launch as a separate, content-bound
artifact and create none during the freeze.

### Consequences

- The local preflight preserves 110/110 work requests byte for byte, accepts
  11/11 reference mutations and terminals, and passes 6/6 source plus 5/5
  supported semantic hidden references.
- Zero of 22 reserved schemas has a top-level union. Missing envelopes and an
  extra-argument finish instruction are rejected before underlying dispatch.
- The freeze digest is
  `e72c87ff0141913dfa48f391c63ada9a6669e410a302c690da778c958a48d943`.
- No launch record exists, no Calibration 008 subject call occurred, and the
  only next execution gate is `explicit_launch_008`.

## Calibration 008 descriptive acceptance

### Context

The provider-admissible freeze bound Nested Grammar v3 to the unchanged
Calibration 008 subjects after Probe 003 established endpoint admission. The
user subsequently authorized transmission of synthetic participant contexts
and artifacts, excluding references and hidden evaluators, across at most 132
Bedrock requests with zero retries and USD 10 maximum estimated spend.
Prelaunch checks repeated content, credential, endpoint, model, contamination,
and current public service-policy controls. The inference-scoped credential
could not read effective account retention, so no account-specific ZDR claim is
made.

### Decision

Accept Calibration 008 as a valid and complete repeated within-instance
descriptive observation. Bind the result to freeze
`e72c87ff0141913dfa48f391c63ada9a6669e410a302c690da778c958a48d943`
and launch
`b021e97e3284caa2b586327fabc8bec56c0f0f923e6f8e4dcd3eb4f45a9235fa`.
Retain all twelve scheduled outcomes without replacement or rerun.

Interpret Grammar v3 as a pre-dispatch safety boundary. Do not interpret
provider admission as constrained decoding, the five valid terminals as five
completed tasks, or realized differences from Calibration 007 as a causal
effect. Keep inferential and general efficacy claims unauthorized.

### Consequences

- All twelve cells completed with 126 successful responses from the locked
  model, no infrastructure-invalid cell, and USD 1.914876 estimated cost.
- Source passed 1/6 hidden evaluations and semantic 0/6; supported-task counts
  were 1/5 and 0/5.
- Sixteen reserved-phase calls failed exact grammar validation before dispatch:
  eight during commit and eight during finish. No missing `v` envelope was
  observed; two samples used a string-valued `v`, and fourteen object-valued
  instructions violated the active opcode, arity, or payload union.
- Valid provider-call terminals rose from four to five relative to Calibration
  007, but four failed hidden evaluation and three semantic terminals contained
  no mutation.
- Provider requests fell by one, total tokens by 0.67%, and estimated cost by
  1.36%. Independent sampling and changed trajectories preclude an efficiency
  attribution.
- The supported semantic arm still used 126.0% more total tokens and 108.7%
  more estimated cost than source while producing no hidden pass.
- Grammar v3 has satisfied its runtime-safety purpose. The next call-free red
  test is design of the registered Representational Dependence calibration,
  with lexical and structural factors isolated over one decoded canonical IR.

## Representational Dependence factorial design v0

### Context

Calibration 008 established pre-dispatch grammar safety but left semantic
representation use unreliable. Comparing source with semantic IR cannot
identify whether model behavior depends on operator labels, structural
packaging, action grammar, or mutation semantics because those surfaces move
together.

### Options

1. Cross lexicalization and packaging across the entire input and output
   language, accepting multiple simultaneous treatment changes.
2. Hold detailed observation structure fixed and test lexicalization alone.
3. Cross lexicalization and packaging only for detailed semantic inspection
   results while keeping outline, action, mutation, and evaluation surfaces
   fixed.

### Decision

Choose option 3 as the thinnest identifiable first study. Define four
conditions: meaningful/nested, opaque/nested, meaningful/table, and
opaque/table. Apply treatment only after semantic inspection. Keep the compact
outline, handle-selection interface, Session ISA, Grammar v3 runtime backstop,
semantic mutation backend, capabilities, evaluators, and future execution
policy fixed.

Use the five supported Calibration 008 tasks only as codec-coverage fixtures.
Materialize their function bodies and reference targets in all four conditions,
require exact canonical round-trip, and keep the codebook outside participant
visibility. Do not include source in the first factorial because it identifies
neither main effect.

### Consequences

- All 20 realizations decode to canonical byte equality and all ten lexical
  pairs share an exact normalized structural skeleton.
- The fixtures cover all eight current expression operators. Duplicate,
  dangling, repeated, cyclic, unreachable, wrong-condition, and reserved-label
  failures are rejected locally.
- The carrier costs 36,288 to 45,427 bytes across the five fixtures versus
  16,905 canonical bytes. It is an auditable experimental instrument, not a
  wire-format optimization.
- The experimental unit is a fresh task instance. Repeated requests cannot
  substitute for task-level sample size.
- The primary estimands are marginal lexical and packaging effects on hidden
  Pass@1, with Holm correction across both at familywise alpha 0.05 and target
  power 0.80. Interaction is secondary.
- Power remains blocked until smallest effects of interest, baseline success,
  within-task correlation, and task-family mixture are specified.
- The five construction fixtures are provider-exposed and confirmatory-
  ineligible. Fresh instances and a prior-request equality audit are required.
- Calibration 008 rates project approximately USD 4.91 at the mean and USD
  5.90 at its observed maximum for a five-task, four-condition illustration;
  no powered cell count or spend ceiling exists.
- No execution freeze, launch, authorization, or model call exists. The next
  call-free red test is a deterministic power-sensitivity curve.

## Representational power-sensitivity curve v0

### Context

The factorial design identified task, not request, as the experimental unit but
left baseline success, smallest relevant effects, within-task dependence, task
mixture, and sample size unresolved. Choosing a convenient request count would
create apparent precision without supporting generalization across fresh tasks.

### Options

1. Pick a small affordable task count and report detectable effects afterward.
2. Choose one unverified point estimate for baseline and correlation, then
   calculate one nominal sample size.
3. Freeze a broad deterministic sensitivity grid, make every assumption and
   cost consequence visible, and leave scientific selection to a later gate.

### Decision

Choose option 3. Cross baseline hidden Pass@1 values 0.20, 0.40, 0.60, and
0.80 with absolute main-effect SESOIs 0.05, 0.10, 0.15, and 0.20 and null
within-task ICC values 0.00, 0.25, 0.50, and 0.75. For each of the 64
scenarios, calculate a task-level paired factorial contrast under proportional
rescue and harm alternatives, retain the more expensive direction, use the
smallest two-primary Holm threshold at familywise alpha 0.05, target power
0.80, and round upward to four-task counterbalancing blocks.

Do not select a row. Treat Calibration 008 cell rates only as descriptive
linear cost scales. Keep the interaction estimation-first and all provider
gates red.

### Consequences

- The grid requires 16 to 920 fresh task units, or 64 to 3,680 four-condition
  cells.
- At Calibration 008 rates, descriptive mean-cost scale ranges from USD 15.73
  to USD 904.23 and observed-maximum-rate scale from USD 18.87 to USD 1,084.85.
- The calculation uses a normal approximation with model-based moments. It is
  deterministic but not exact or finite-sample validated.
- Positive null ICC reduces paired-contrast variance in this model; correlated
  cells are never counted as independent task units.
- No SESOI, baseline/ICC envelope, task-family mixture, task count, request
  ceiling, spend ceiling, fresh subject, execution freeze, or launch is chosen.
- No model call occurred and no provider cost was incurred.
- The next red test is a pre-outcome scientific selection record followed by
  deterministic simulation of the selected finite-sample design.

## Representational power-selection freeze v0

### Context

The sensitivity curve exposed a 16-to-920-task range but intentionally could
not choose which effect mattered or which tasks defined the population. Leaving
those choices open until after new provider outcomes would permit post hoc
movement of the scientific target.

### Options

1. Select the cheapest feasible grid point and accept sensitivity only to large
   effects.
2. Use the five provider-exposed construction fixtures to estimate assumptions
   and extrapolate from them.
3. Freeze an operationally material SESOI, a broad conservative planning
   envelope, and a bounded equal task-family mixture before new outcomes.

### Decision

Choose option 3. Set both lexical and packaging absolute Pass@1 SESOIs to 0.10.
Use baseline 0.20–0.80 and null within-task ICC 0.00–0.75 as the planning
envelope. Under the frozen proportional rescue/harm model, zero ICC is the
conservative boundary at this SESOI. Maximize the directional asymptotic task
count over the continuous baseline interval.

Define five equally weighted task families within the frozen Session ISA and
semantic inspection vocabulary: capability lookup/fallback, error/option
taxonomy, guarded retry/control flow, identity/state consistency, and pure
dataflow normalization. Round the worst envelope result upward to the least
common multiple of four counterbalancing sequences and five families.

### Consequences

- The worst point is baseline 0.486251052, zero ICC, and an increasing effect,
  requiring 236.503122 tasks before rounding.
- The asymptotic candidate is 240 fresh tasks: 48 per family, 960 condition
  cells, and at most 11,520 requests at the Calibration 008 cell maximum.
- Descriptive Calibration 008 rates project USD 235.8864 at the mean and USD
  283.0032 at the observed maximum; neither value is a budget or ceiling.
- Equal family weights define this bounded target population and make no claim
  about real-world workload prevalence.
- The five construction fixtures remain provider-exposed coverage material and
  contribute no confirmatory unit or empirical parameter estimate.
- If finite-sample simulation fails, scientific inputs remain frozen and task
  count may only increase in complete 20-task blocks.
- The candidate does not establish power. No task, contamination audit, cost
  ceiling, execution freeze, launch, model call, or provider spend exists.
- The next red test is a frozen deterministic finite-sample simulation protocol
  that evaluates null type-I behavior and both effect directions.

## Representational finite-sample simulation protocol v0

### Context

The power curve and scientific selection fixed task-level moments and an
asymptotic candidate, but moments alone do not define a reproducible Monte Carlo
experiment. Choosing a latent distribution, null sentinels, replication count,
uncertainty rule, or passing threshold after seeing simulation results would
reintroduce researcher degrees of freedom before any provider call.

### Options

1. Treat 240 tasks as final from the normal approximation alone.
2. Simulate from a convenient generator and tune scenarios until 240 passes.
3. Complete the frozen moment model explicitly and freeze the entire simulation
   and escalation protocol before observing a Monte Carlo result.

### Decision

Choose option 3. Preserve the latent-task mean/ICC model, conditional Bernoulli
sampling, proportional rescue/harm alternatives, marginal task contrasts, and
two-primary Holm family used by the curve. For ICC above zero, complete the
moments with a Beta latent probability; use the degenerate baseline when ICC is
zero. Permit only one nonzero primary at a time rather than inventing an
unidentified interaction/composition rule.

Freeze nine global-null baseline/ICC sentinels and four isolated-primary
worst-point alternatives. Use 20,000 replications per scenario, independent
SHA-256-derived streams rooted at seed 24121980, and 95% Wilson intervals. A
candidate passes only when every global-null familywise Type I upper bound and
every inactive-primary upper bound are at most 0.06, and every active-primary
power lower bound is at least 0.80. Evaluate 240 through 400 in ascending
20-task blocks and select the first complete pass.

### Consequences

- The simulation can no longer silently change the generator, test, scenarios,
  random streams, uncertainty method, or acceptance rule after seeing output.
- The Beta family is a declared distributional completion, not evidence that
  real task difficulty is Beta-distributed.
- The protocol tests aggregate equal-mixture behavior and does not model
  family-specific baseline, ICC, or effect heterogeneity.
- A failure may only increase task count through the frozen schedule; failure
  at 400 leaves the experiment blocked.
- Freezing the protocol runs no simulation, constructs no fresh task, and
  authorizes no model call, provider request, cost, execution freeze, or launch.
- The next red test is the local campaign aggregator and its execution against
  this content-locked protocol.

## Representational finite-sample campaign runner v0

### Context

One candidate contains thirteen long-running streams. A runner that retained
results only at process exit could lose hours of deterministic work after an
interruption, while an informal resume could repeat streams or combine results
from different protocol or source versions.

### Options

1. Run the entire campaign in memory and write one result at exit.
2. Parallelize immediately and accept process-local progress as operational
   state.
3. Execute sequential independent streams with canonical atomic checkpoints,
   strict resume validation, and a final content lock.

### Decision

Choose option 3 for v0. Verify the protocol tree and every recorded source
dependency before simulation. Derive each stream solely from the frozen base
seed, scenario identity, and task count. After each scenario, atomically store
its counts, Wilson intervals, criteria, and seed as the next exact campaign
prefix. On resume, recompute every summary and reject any ordering, source,
runner, or result mismatch.

Finalize only after the first fully passing candidate or the frozen 400-task
maximum. A complete checkpoint can repair the narrow crash window before lock
creation without repeating simulation. A valid final result must match both
the checkpoint and its artifact lock.

### Consequences

- An interruption loses at most the currently running scenario.
- Completed streams are never rerun during a valid resume.
- Code or protocol changes invalidate partial state instead of silently mixing
  simulation versions.
- Sequential execution is simpler and deterministic but does not yet exploit
  independent-stream parallelism.
- Synthetic aggregation and a five-replication smoke test validate wiring but
  are not scientific outcomes.
- The next red test is execution of the unchanged 20,000-replication campaign
  beginning at 240 tasks.

## Representational finite-sample simulation result v0

### Observation

Execute the thirteen frozen scenario streams at the initial 240-task candidate.
All nine global-null sentinels satisfy the Type I criterion and all four
isolated-primary scenarios satisfy both active-power and inactive-primary
criteria. The stop rule therefore selects 240 without evaluating larger
candidates.

The largest global-null Wilson upper bound is 0.05665 against a 0.06 ceiling.
The smallest active-power lower bound is 0.80172 against a 0.80 floor, in the
packaging/decrease scenario. The largest inactive-primary upper bound is
0.05100 against a 0.06 ceiling.

### Consequences

- The final finite-sample design contains 240 fresh tasks, 48 in each of five
  mechanism families and 960 four-condition cells.
- The simulation gate is green under the exact frozen generator and criteria.
- The narrowest power margin is 0.00172; no downstream safeguard may be relaxed
  on the theory that the design is generously overpowered.
- Individual Wilson intervals were predeclared; simultaneous coverage across
  all event rates is not claimed.
- No behavioral effect, empirical task distribution, general prevalence,
  provider budget, or launch is established.
- No model call, provider request, fresh task, or spend occurred.
- The next red test is a pre-construction freeze for the 240 fresh instances,
  followed by local generation, equivalence, evaluator, and contamination
  checks before any provider authorization.

## Representational fresh-task construction protocol v0

### Context

Finite-sample simulation selected 240 fresh task units, but a sample-size result
does not define the tasks. Constructing them informally would leave room to
change family composition, choose convenient candidates, reuse exposed bytes,
or let a task-generating model introduce uncontrolled lexical and structural
preferences before the representational comparison begins.

### Options

1. Generate 240 tasks immediately and describe the construction afterward.
2. Use the future participant model to generate tasks, then evaluate that same
   model on their four realizations.
3. Freeze stable slots, deterministic attempt streams, acceptance rules, and
   red downstream gates before implementing or running a non-LLM constructor.

### Decision

Choose option 3. Create 48 immutable slots in each of the five selected
mechanism families. Cycle the four already frozen balanced sequences within
each family, yielding twelve tasks per sequence per family and 60 per sequence
overall.

Give every slot eight ordered, domain-separated attempt seeds rooted at
`24121980`. Only the first candidate passing the complete eligibility pipeline
may occupy a slot. Retain all rejections and reasons. Manual substitution,
family reallocation, and skipping an eligible candidate are forbidden. Eight
failures block construction and require an explicit new design decision.

Specify task construction as deterministic and non-LLM. Its family templates
must be implemented, tested, and content locked before materialization. The
future participant model remains a separate role: one exact identity, inference
policy, tool runtime, and accounting policy must be frozen and held equal across
all four conditions before launch. Each condition runs in a fresh independent
context with no cross-condition memory; the sequence balances temporal order,
not conversational carryover.

### Consequences

- The protocol freezes 240 slots and 1,920 attempts while creating zero tasks.
- Every accepted task must be expressible by the frozen Session ISA and
  semantic vocabulary; an unsupported candidate is rejected, not patched by an
  unplanned extension.
- Baseline/reference discrimination, four-condition canonical byte equality,
  normalized lexical-skeleton equality, participant-context isolation,
  contamination checks, duplicate checks, and a task artifact lock are all
  mandatory eligibility gates.
- The provider-exposed construction fixtures remain codec coverage and cannot
  become confirmatory units.
- Constructor implementation, task materialization, equivalence, evaluator,
  contamination, cost, execution-freeze, launch, and authorization gates remain
  red.
- No model call, provider request, task, behavioral claim, or spend occurred.
- The next red test is implementing and content locking the deterministic
  five-family task generator without materializing the full cohort.

## Representational fresh-task generator freeze v0

### Context

The construction protocol fixed 240 slots and 1,920 attempt seeds, but a seed
alone does not define task semantics. A generator could still hide arbitrary
choices in prose, emit invalid IR for untested profiles, depend on treatment
order, or write the entire cohort before its family contracts were auditable.

### Options

1. Generate repository directories directly for all 240 first attempts.
2. Freeze only abstract profile names and defer executable semantics.
3. Implement a pure semantic-blueprint generator, audit every frozen attempt,
   execute one representative of every profile, and defer persistence.

### Decision

Choose option 3. For each slot and attempt, deterministically produce a complete
in-memory blueprint: participant objective, typed program IR v2 baseline,
transactional reference patch, public/hidden value-and-effect cases, and the
family invariant contract. Derive all variable task material from the already
frozen seed without a language model or provider response.

Give every family twelve profiles from a `3 × 2 × 2` matrix. Assign one profile
to four consecutive slots so it crosses all four cyclic counterbalance
sequences. Do not consume the condition-order field during generation.

Generate all 1,920 blueprints in frozen order and require unique byte and
semantic-signature digests. Semantically execute attempt zero for the first slot
of every profile: 60 validations. A profile passes only if the baseline and
patched programs type/effect check and project, the reference passes every
public and hidden case, the baseline is discriminated by both evaluator
partitions, and stale base state rejects the patch.

### Consequences

- The construction-generator gate is green and content locked.
- The audit produced 384 unique blueprints per family, 1,920 overall, with no
  semantic-signature collision.
- Validation spans all 60 profiles rather than only the five family exemplars.
- The generated population is explicitly synthetic and balanced; it does not
  estimate naturally occurring task prevalence or contain 1,920 different
  algorithms.
- In-memory generation is not task materialization. No participant repository,
  context, condition realization, persistent reference, provider request, or
  model call exists.
- Materialization, complete local eligibility, four-condition equivalence,
  contamination, cost, execution-freeze, launch, and authorization gates remain
  red.
- The next red test is materializing one predeclared attempt-zero smoke task per
  family and running the complete local eligibility pipeline without provider
  calls.

## Representational fresh-task smoke v0

### Context

The locked generator proved all 1,920 candidate blueprints were deterministic
and unique, but it had never composed persistent repositories, participant
boundaries, detailed observation realizations, evaluator evidence, duplicate
checks, and an artifact lock in one end-to-end construction.

### Decision

Materialize exactly attempt zero of the first frozen slot in each of the five
families. Run the complete local eligibility pipeline and persist all four
factorial realizations for each task without making a model or provider call.

Treat persistence and development inspection as exposure. Retain each attempt
zero as an engineering fixture, mark it ineligible for the confirmatory cohort,
and require the corresponding slot to resume at its already frozen attempt 1.
Do not substitute another candidate, revise the family generator, or count the
fixture among the 240 experimental units.

### Consequences

- Five task repositories and twenty condition realizations pass deterministic
  materialization, frozen-vocabulary, evaluator, equivalence, isolation,
  duplicate, and artifact-lock checks.
- All four realizations per task decode to identical canonical observation
  bytes, and meaningful/opaque skeletons match within each packaging level.
- No participant tree matches the provisional inventory of 867 historical
  provider request artifacts; the audit must be repeated once exact future
  request framing is frozen.
- The smoke fixtures establish infrastructure composition only. Confirmatory
  task count, behavioral evidence, model calls, provider requests, and spend
  remain zero.
- The next red test is freezing the exact participant request envelope, model,
  inference policy, independent-session runner, and provider cost ceiling.

## Representational participant execution freeze v0

### Context

The local smoke proved that task generation and four-condition realization
compose, but participant execution was still underspecified. Model identity,
request framing, provider translation, session independence, and a binding
cost stop could otherwise be chosen after seeing confirmatory task bytes or
outcomes. At the same time, exact requests for unmaterialized tasks cannot be
honestly frozen in advance.

### Options

1. Materialize the confirmatory cohort first and decide execution details
   afterward.
2. Freeze placeholder request hashes for task bytes that do not yet exist.
3. Freeze the deterministic request constructor and every invariant field,
   prove it on exact smoke envelopes, schedule independent sessions, and defer
   confirmatory request hashes until eligible tasks exist.

### Decision

Choose option 3. Reuse the Calibration 008 participant identity through Amazon
Bedrock: `us.anthropic.claude-sonnet-4-6` in `us-east-1`, temperature zero,
4,096 output tokens per turn, and no provider substitution. Lock the one-tool
request surface and local Bedrock adapter. Assemble each initial system message
from task, outline, observation state, and Session ISA without passing the
condition identifier to the constructor.

Assign all 960 condition cells unique session and workspace identities with
empty histories and no cross-condition parent. Preserve the frozen within-task
condition order only as counterbalancing. Advance the five development-exposed
slots to attempt 1; retain attempt 0 for the other 235 slots.

Set USD 350 as the hard experiment ceiling. It exceeds the descriptive USD
283.0032 maximum-observed-rate projection by USD 66.9968 but is not permission
to spend. Require a rate recheck and reservation guard at launch.

### Consequences

- Twenty exact smoke requests and Bedrock translations prove constructor and
  tool-schema composition without a provider call.
- Their non-system fields are invariant, condition labels are absent, and none
  matches 867 historical request artifacts.
- Exact confirmatory requests remain correctly nonexistent until their 240
  task units pass local eligibility.
- The execution-freeze and cost-ceiling gates are green; confirmatory-task,
  exact-request, access/rate recheck, explicit-launch, and authorization gates
  remain red.
- The next red test is materializing all 240 confirmatory task units and
  auditing all 960 exact requests before provider execution.

## Representational confirmatory cohort v0

### Context

The scientific design, deterministic task generator, participant execution
contract, and five exposed attempt-zero slots were frozen. What remained was
to select and persist the actual 240-task sample without adaptive candidate
choice, then replace the smoke audit with exact request identities for every
factorial cell.

A direct implementation also exposed an evidence-storage choice. Persisting
four complete participant trees plus both request formats for every task
produced 134,236 KiB and 12,963 files, although those payloads were deterministic
products of smaller locked inputs.

### Options

1. Commit all replicated trees and 1,920 complete request payloads.
2. Keep only aggregate counts and discard exact request identity.
3. Retain canonical task inputs and every exact digest, reconstruct all payloads
   during verification, and lock each task plus the full cohort.

### Decision

Choose option 3. Traverse the 240 frozen slots in protocol order and accept only
the first locally eligible predeclared attempt. Start the five smoke-exposed
slots at attempt 1 and all other slots at attempt 0. Advance an atomic
checkpoint only after the accepted task's individual artifact lock verifies.
Reject source drift or a non-prefix resume.

For every accepted task, generate all four exact participant requests through
the frozen constructor, translate them through the frozen Bedrock adapter, and
audit historical equality, smoke equality, within-cohort equality, condition
labels, invariant fields, and tool-schema preservation. Retain canonical
OpenAI and Bedrock digests. Remove only the derived request bodies and duplicate
participant trees; reconstruct them from blueprint, canonical outline,
condition realization, repository, evaluators, and execution freeze in tests.

### Consequences

- All 240 slots selected their first permitted candidate: 235 at attempt 0 and
  five at attempt 1, with zero rejection or exhaustion.
- All 960 realizations pass local eligibility and all 960 exact requests are
  unique, condition-blind, schema-preserving, and novel against both historical
  and development-smoke requests.
- Tests reconstruct every request and Bedrock translation and recover the
  recorded digests.
- Evidence by reconstruction reduces the retained artifact to 49,652 KiB and
  4,323 files, 63.01% below the direct materialization size.
- No model call, provider request, behavioral outcome, or spend occurred.
- The next red test is a content-locked confirmatory runner and complete
  provider-free replay of the 960-cell schedule before access/rate checks and a
  separate explicit launch decision.

## Representational lexicalization totality v0

### Context

Confirmatory canary 002 followed a legal inspection trajectory outside the
reference replay and reached `slot="arguments[0]"`. The opaque codec lacked
that scalar label and stopped after three successful provider responses. The
observation was infrastructure-invalid, and both retry and campaign release
remained blocked.

### Options

1. Add the label to the existing codec and invalidate the hashes that preserve
   prior construction and execution evidence.
2. Patch only the observed canary path and test the same handles again.
3. Preserve the historical codec, create a one-entry versioned extension, and
   exhaustively test all nodes of all frozen tasks under all four conditions.

### Decision

Choose option 3. Keep the v0 codec byte-identical and add `arguments[0] -> k32`
in a successor v1 codec. Enumerate every handle in each of the 240 frozen task
outlines, request one legal full-node inspection per task, and require all four
meaningful/opaque by nested/table realizations to decode to the identical
canonical bytes. Also require each lexical pair to normalize to the same
surface and every observed structural label to belong to the evaluator-only
codebook.

### Consequences

- The original red test reproduced the same missing label in all 240 tasks.
- The successor codec passes 960/960 round trips over 3,552 reachable nodes.
- All observed keys, slots, scope fields, operations, and schema values are
  covered; meaningful and opaque skeletons match within each packaging.
- The claim is totality for the frozen cohort and grammar, not for future ASTs,
  catalogs, schemas, or positional arities.
- The proof is local and deterministic: zero provider requests and zero cost.
- Canary 002 is not retried. A successor runtime freeze and provider-free replay
  are the next red test before planning a new immutable schedule cell.
