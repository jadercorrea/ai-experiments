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
