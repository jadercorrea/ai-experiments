# Semantic IR for coding agents — construction slice v0 + catalog extensions v1/v2

## Status

**Executable construction artifact with matched whole-program and patch task
fixtures, two valid single-task model observations, one valid five-point
break-even curve, one local semantic-patch observation, two invalidated
heterogeneous calibrations, and one valid descriptive capability-v2
calibration. Calibration 003 observed semantic hidden passes of 4/6 versus 2/6
for source, with fewer calls and output tokens but more total tokens and cost.
Compact Context v1 now preserves all five supported references while reducing
initial semantic context by 83.19%; the unchanged recursive patch tool schema
still prevented whole-surface source break-even. Motion Lexicalization v1 now
replaces that recursive grammar with eight flat words, passes the same five
hidden references, cuts tool definitions by 50.15%, and deliberately records
that the complete semantic surface still misses source break-even by 2.09×.
Neither construction nor the small calibration authorizes an inferential or
general efficacy claim.**

Snapshot date: **2026-08-26**

This is the first deliberately narrow implementation behind the hypothesis in
[*The Transcript Is Not the State: Toward a Semantic IR for Coding
Agents*](https://gptcode.dev/blog/2026-08-25-the-transcript-is-not-the-state).
It asks whether a coding agent can target a checked semantic object that is
interpreted directly or lowered deterministically to an existing language.

It does not yet ask whether a model performs better when using that object.

## Decision frame

### Outcome

Establish the smallest executable boundary at which one canonical program can:

1. be rejected before execution when it references an unavailable symbol,
   violates a type, duplicates a stable identity, or omits an effect;
2. run through an IR interpreter with observable capability use; and
3. lower deterministically to a readable TypeScript projection whose generated
   expressions remain traceable to IR node identities.

Passing those checks establishes construction feasibility only. It does not
establish token savings, higher Pass@1, lower latency, better model reasoning,
or sufficient expressiveness for repository work.

### Constraints

- One target projection: TypeScript.
- One domain operation: user lookup by a normalized identifier.
- One v0 external effect, `db.read:users`; additive v2 introduces
  `network.read:directory` for the frozen fallback family.
- A v0 closed catalog with three callable symbols; additive v1 adds one pure
  equality predicate and additive v2 adds one effectful directory lookup.
- `Option` is represented by `user | none`; errors are explicit `Result`
  values rather than exceptions.
- No model calls, source-to-source editing, custom tokenizer, theorem prover,
  optimizer, or general-purpose syntax in this slice.

### Invariants

- Every expression has a unique stable node identity.
- Every parameter and local binding has a unique stable symbol identity.
- Source names reserved for backend capabilities and generated temporaries are
  rejected before projection.
- References resolve lexically; spelling a plausible name is insufficient.
- Calls resolve only through the versioned closed catalog.
- Inferred effects must equal declared effects. Missing and unused capabilities
  are both rejected.
- After a v2 semantic tree patch, the redundant function-effect header is
  derived canonically before the same exact validation.
- Branches are total for the supported `if` and `Option` forms and must agree on
  their result type.
- Interpretation and lowering both require the same validation pass.
- The interpreter records an effect only when the effect is actually executed.
- The TypeScript projection is deterministic for a canonical IR object.

## The semantic core

The canonical representation is JSON for this construction slice. JSON is a
transport and inspection format, not a proposed final AI-native surface syntax.
The important boundary is the typed tree and its operational semantics.

| Symbol | Input | Output | Effect | Introduced |
| --- | --- | --- | --- | --- |
| `string.trim_ascii` | `string` | `string` | pure | v0 |
| `string.is_empty` | `string` | `boolean` | pure | v0 |
| `users.get_by_id` | `string` | `option<user>` | `db.read:users` | v0 |
| `string.equals` | `string, string` | `boolean` | pure | v1 |
| `directory.get_by_id` | `string` | `option<user>` | `network.read:directory` | v2 |

The v0 expression set is intentionally small:

- string literals and stable symbol references;
- catalog calls;
- lexical `let` bindings;
- typed `if`;
- total `option_match`;
- explicit `ok` and `err` values.

The example program trims an identifier, rejects an empty identifier without
performing I/O, performs one user-store lookup otherwise, and returns either a
user or a declared error. Whitespace normalization is explicitly limited to
ASCII whitespace so the interpreter and TypeScript projection do not inherit
different Unicode definitions from their host languages.

## Artifacts

- [`program-ir-v0.schema.json`](protocol/program-ir-v0.schema.json) defines the
  structural grammar.
- [`semantic_ir.py`](scripts/semantic_ir.py) implements semantic validation,
  direct interpretation, effect telemetry, and deterministic TypeScript
  projection.
- [`user-lookup.program.json`](examples/user-lookup.program.json) is the first
  canonical program.
- [`task-001-user-lookup`](construction/task-001-user-lookup) is the first
  immutable matched TypeScript construction task. It contains separated
  participant context, repository, evaluators, and reference material.
- [`semantic-patch-v0.schema.json`](protocol/semantic-patch-v0.schema.json)
  defines checked, transactional subtree replacement over persistent IR.
- [`semantic_patch.py`](scripts/semantic_patch.py) validates patch and state
  preconditions, rejects overlapping or colliding edits, and applies all
  operations or none.
- [`patch-task-001-error-codes`](construction/patch-task-001-error-codes) is the
  locked local comparison between a staged unified diff and a semantic patch.
- [`semantic_patch_task.py`](scripts/semantic_patch_task.py) materializes the
  shared baseline, audits both mutation paths, and runs identical evaluators.
- [`SEMANTIC_PATCH_CONSTRUCTION_OBSERVATION.md`](SEMANTIC_PATCH_CONSTRUCTION_OBSERVATION.md)
  reports byte-identical target convergence and the strict construction-only
  claim boundary.
- [`semantic-patch-suite-v0.json`](construction/semantic-patch-suite-v0.json)
  freezes six task families, size balance, support dispositions, estimands, and
  the gate for fresh sealed instances.
- [`semantic_patch_suite.py`](scripts/semantic_patch_suite.py) deterministically
  builds and verifies the matrix, per-task digests, dependency digests, and
  suite self-digest.
- [`SEMANTIC_PATCH_SUITE_FREEZE.md`](SEMANTIC_PATCH_SUITE_FREEZE.md) explains why
  unsupported work remains in the all-task denominator and which two pre-model
  extensions are permitted.
- [`final-task-suite-v0.schema.json`](protocol/final-task-suite-v0.schema.json)
  and [`final-patch-task-v0.schema.json`](protocol/final-patch-task-v0.schema.json)
  define the final suite and per-instance contracts.
- [`final-patch-tasks-v0`](construction/final-patch-tasks-v0) contains the six
  content-locked repositories, evaluators, retained rejected candidates,
  references, final support dispositions, and conditional contamination audit.
- [`semantic_final_task.py`](scripts/semantic_final_task.py) materializes the
  participant boundary, applies source or semantic patches transactionally,
  records unsupported outcomes, audits workspaces, and runs shared evaluators.
- [`FINAL_TASK_SUITE_OBSERVATION.md`](FINAL_TASK_SUITE_OBSERVATION.md) records
  the 5/6 applicability boundary, construction controls, and remaining
  pre-execution lock.
- [`execution-freeze-v0.schema.json`](protocol/execution-freeze-v0.schema.json),
  [`execution-launch-v0.schema.json`](protocol/execution-launch-v0.schema.json),
  and [`execution-freeze-v0`](construction/execution-freeze-v0) freeze the
  model, inference policy, exact contexts and tools, budgets, schedule, stopping
  rule, runner, analysis, and conditional contamination status.
- [`semantic_execution_freeze.py`](scripts/semantic_execution_freeze.py)
  deterministically builds and verifies that content-addressed package.
- [`semantic_patch_calibration.py`](scripts/semantic_patch_calibration.py)
  provides the launch-gated closed-tool runner. Its preflight path makes no
  provider call.
- [`EXECUTION_FREEZE_OBSERVATION.md`](EXECUTION_FREEZE_OBSERVATION.md) records
  the isolation and claim boundaries and the final explicit-launch gate.
- [`semantic-patch-calibration-001`](observations/semantic-patch-calibration-001)
  retains the complete 12-cell execution, launch record, USD 0.699015 cost,
  provider payloads, workspaces, evaluators, artifact lock, and explicit
  invalidation record.
- [`CALIBRATION_001_OBSERVATION.md`](CALIBRATION_001_OBSERVATION.md) explains
  why all five supported semantic trajectories were early-censored by an
  unreadable context-artifact path and why the raw 3/6 versus 0/6 counts cannot
  support a representation comparison.
- [`context-recovery-tasks-v1`](construction/context-recovery-tasks-v1) contains
  six fresh exact instances with changed identities, symbols, repository and
  hidden-evaluator bytes, locally revalidated before any new model call.
- [`context-execution-freeze-v1`](construction/context-execution-freeze-v1),
  [`context-execution-freeze-v1.schema.json`](protocol/context-execution-freeze-v1.schema.json),
  and [`context-execution-launch-v1.schema.json`](protocol/context-execution-launch-v1.schema.json)
  freeze the successor context protocol and its separate explicit-launch gate.
- [`semantic_context_protocol.py`](scripts/semantic_context_protocol.py),
  [`semantic_context_execution_freeze.py`](scripts/semantic_context_execution_freeze.py),
  and [`semantic_context_calibration.py`](scripts/semantic_context_calibration.py)
  implement immutable `context://` addressing, recoverable subject tool errors,
  deterministic freezing, and the launch-gated runner.
- [`CONTEXT_PROTOCOL_V1_FREEZE.md`](CONTEXT_PROTOCOL_V1_FREEZE.md) records the
  experimental-TDD sequence, fresh-instance boundary, and remaining claim gate.
- [`semantic-context-calibration-002`](observations/semantic-context-calibration-002)
  retains the complete 12-cell v1 execution: 102 provider responses, USD
  3.606831 estimated cost, workspaces, transcripts, evaluators, invalidation
  record, and content lock.
- [`CALIBRATION_002_OBSERVATION.md`](CALIBRATION_002_OBSERVATION.md) records why
  context v1 succeeded operationally while unavailable canonical program and
  subtree preconditions invalidate the next representation comparison.
- [`capability-semantic-patch-v1.schema.json`](protocol/capability-semantic-patch-v1.schema.json)
  and [`semantic_capability_protocol.py`](scripts/semantic_capability_protocol.py)
  replace model-generated canonical digests with store- and node-bound opaque
  precondition tokens resolved inside trusted infrastructure.
- [`capability-patch-tasks-v2`](construction/capability-patch-tasks-v2) contains
  six fresh exact task instances with locally verified source references and
  five supported semantic capability references.
- [`capability-execution-freeze-v2`](construction/capability-execution-freeze-v2),
  [`capability-execution-freeze-v2.schema.json`](protocol/capability-execution-freeze-v2.schema.json),
  and [`capability-execution-launch-v2.schema.json`](protocol/capability-execution-launch-v2.schema.json)
  freeze the capability interface and its separate explicit-launch gate.
- [`semantic_capability_execution_freeze.py`](scripts/semantic_capability_execution_freeze.py)
  and [`semantic_capability_calibration.py`](scripts/semantic_capability_calibration.py)
  provide deterministic freezing, preflight, and launch-gated execution without
  changing the prior context-v1 artifacts.
- [`CAPABILITY_PROTOCOL_V2_FREEZE.md`](CAPABILITY_PROTOCOL_V2_FREEZE.md) records
  the next experimental-TDD failure, the version-neutral fix, exact digests, and
  construction-only claim boundary.
- [`capability-execution-launch-003.json`](construction/capability-execution-launch-003.json)
  and its
  [`preflight`](construction/capability-execution-launch-003.preflight.json)
  bind the explicit authorization to the exact v2 freeze, suite, model, budget,
  and provider-policy audit.
- [`semantic-capability-calibration-003`](observations/semantic-capability-calibration-003)
  retains the complete 12-cell execution: 78 provider responses, USD 2.101818
  estimated cost, workspaces, transcripts, evaluator results, and a 233-file
  content lock.
- [`CALIBRATION_003_OBSERVATION.md`](CALIBRATION_003_OBSERVATION.md) records the
  valid descriptive comparison, the resolved capability defect, the opposing
  output- and input-token results, and the next compact-context red test.
- [`compact-semantic-outline-v1.schema.json`](protocol/compact-semantic-outline-v1.schema.json),
  [`compact-semantic-inspection-v1.schema.json`](protocol/compact-semantic-inspection-v1.schema.json),
  and [`semantic_compact_context.py`](scripts/semantic_compact_context.py)
  define a short-handle topology over canonical semantic state and exact
  progressive subtree/scope recovery.
- [`compact-context-v1`](construction/compact-context-v1) is the deterministic
  five-task construction bundle and byte-surface measurement. Its 21-file lock
  has tree digest
  `fab0f9be5d526b44b1f4849620846d32d602512ae712da092ec127fec9a62bb9`.
- [`COMPACT_CONTEXT_V1_OBSERVATION.md`](COMPACT_CONTEXT_V1_OBSERVATION.md)
  records the 83.19% context reduction, five hidden-reference passes, failed
  total-surface break-even, and next motion-lexicalization red test.
- [`motion-semantic-patch-v1.schema.json`](protocol/motion-semantic-patch-v1.schema.json)
  and [`semantic_motion_patch.py`](scripts/semantic_motion_patch.py) define the
  flat `str/var/call/let/if/match/ok/err` realization, lexical scope slots, and
  deterministic reconstruction of canonical replacement trees.
- [`motion-lexicalization-v1`](construction/motion-lexicalization-v1) contains
  five generated motion patches, resolved canonical patches, model-facing
  contexts and tools, hidden-evaluator evidence, and a 21-file content lock.
- [`MOTION_LEXICALIZATION_V1_OBSERVATION.md`](MOTION_LEXICALIZATION_V1_OBSERVATION.md)
  records the 61.27% patch-payload reduction, 50.15% tool-definition reduction,
  five hidden passes, and failed 2.09× whole-surface break-even gate.
- [`program-ir-v1.schema.json`](protocol/program-ir-v1.schema.json) and
  [`semantic_ir_v1.py`](scripts/semantic_ir_v1.py) add exact pure string
  equality without changing the pinned v0 schema or implementation.
- [`semantic_patch_v1.py`](scripts/semantic_patch_v1.py) applies the unchanged
  semantic patch v0 protocol transactionally to v1 programs.
- [`STRING_EQUALS_EXTENSION_OBSERVATION.md`](STRING_EQUALS_EXTENSION_OBSERVATION.md)
  records the chronology, compatibility boundary, and local guard construction.
- [`program-ir-v2.schema.json`](protocol/program-ir-v2.schema.json),
  [`semantic_ir_v2.py`](scripts/semantic_ir_v2.py), and
  [`semantic_patch_v2.py`](scripts/semantic_patch_v2.py) add the typed directory
  capability, explicit network effect, ordered runtime telemetry, and canonical
  derivation of the exact effect header after checked tree edits.
- [`DIRECTORY_EXTENSION_OBSERVATION.md`](DIRECTORY_EXTENSION_OBSERVATION.md)
  records the effect-header decision and ordered fallback construction.
- [`semantic_task.py`](scripts/semantic_task.py) materializes isolated
  workspaces, audits treatment integrity, lowers semantic submissions, and runs
  the shared evaluators.
- [`interface-freeze-v0.schema.json`](protocol/interface-freeze-v0.schema.json)
  defines the machine-readable model-facing contract.
- [`interface-freeze-v0.json`](construction/interface-freeze-v0.json) freezes
  the exact contexts, workspace snapshot, operations, mutation scope, evaluator
  visibility, and integrity dependencies for the construction comparison.
- [`interface_freeze.py`](scripts/interface_freeze.py) deterministically builds
  and verifies that freeze, including its self-digest.
- [`token-comparison-v0.json`](construction/token-comparison-v0.json) freezes the
  bounded model, sampling, retry, ordering, and provider-native accounting
  policy for the first construction observation.
- [`token_comparison.py`](scripts/token_comparison.py) executes the isolated
  tool trajectories and retains request, response, usage, workspace, and
  evaluator evidence.
- [`TOKEN_CONSUMPTION_OBSERVATION.md`](TOKEN_CONSUMPTION_OBSERVATION.md) reports
  why semantic IR v0 consumed 4.25× the tokens of direct TypeScript on this
  task, while keeping the result inside its one-task claim boundary.
- [`compact_ir.py`](scripts/compact_ir.py) decodes a task-bounded tuple/opcode
  transport into the same canonical checked program.
- [`single_shot_comparison.py`](scripts/single_shot_comparison.py) forces one
  terminal provider call for each source, JSON IR, and compact IR arm.
- [`SINGLE_SHOT_REPRESENTATION_OBSERVATION.md`](SINGLE_SHOT_REPRESENTATION_OBSERVATION.md)
  reports that compact IR reduced output tokens by 55.04% versus source while
  total tokens remained within 0.65% on this small task.
- [`break-even-comparison-v0.json`](construction/break-even-comparison-v0.json)
  freezes a nonadaptive `[1, 2, 4, 8, 16]` repeated-body size grid.
- [`break_even_comparison.py`](scripts/break_even_comparison.py) implements the
  paired body assemblers, fixed tool contracts, evaluators, and curve rule.
- [`BREAK_EVEN_OBSERVATION.md`](BREAK_EVEN_OBSERVATION.md) reports sustained
  observed total-token break-even at eight bodies.
- [`test_semantic_ir.py`](../../../../tests/test_semantic_ir.py) exercises the
  construction invariants.
- [`test_semantic_task.py`](../../../../tests/test_semantic_task.py) proves the
  expected baseline/reference/semantic/public-only evaluator separation.
- [`test_semantic_patch.py`](../../../../tests/test_semantic_patch.py) exercises
  atomicity, optimistic-concurrency guards, identity safety, and operation-order
  independence.
- [`test_semantic_patch_task.py`](../../../../tests/test_semantic_patch_task.py)
  proves matched evaluator behavior and workspace isolation for both patch arms.
- [`test_semantic_patch_suite.py`](../../../../tests/test_semantic_patch_suite.py)
  proves coverage, size balance, support accounting, extension discipline, and
  content-addressed freeze integrity.
- [`test_semantic_string_equals_extension.py`](../../../../tests/test_semantic_string_equals_extension.py)
  proves exact pure equality, pre-effect guarding, v0 rejection, deterministic
  TypeScript lowering, transactional patching, and evidence integrity.
- [`test_semantic_directory_extension.py`](../../../../tests/test_semantic_directory_extension.py)
  proves exact effect declarations, ordered lazy fallback, runtime adapter
  checking, executable TypeScript parity, and evidence integrity.
- [`test_semantic_final_task_suite.py`](../../../../tests/test_semantic_final_task_suite.py)
  proves baseline/reference discrimination, source/semantic convergence,
  isolation, unsupported accounting, contamination-boundary recording, and
  final content-lock integrity across all six tasks.
- [`test_semantic_interface_freeze.py`](../../../../tests/test_semantic_interface_freeze.py)
  proves that the only arm-specific mutation operation is the intended output
  representation boundary.

## Reproduce

From the repository root:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_ir.py \
  validate \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.program.json
```

Interpret the IR directly:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_ir.py \
  interpret \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.program.json \
  --arguments '{"rawId":" 42 "}' \
  --users '{"42":{"id":"42","name":"Ada"}}'
```

Project the same object to TypeScript:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_ir.py \
  project-typescript \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.program.json
```

Pass `--output <path>` to write the deterministic projection for compilation or
execution by a target toolchain.

Apply the checked reference patch to persistent semantic state:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_patch.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/patch-task-001-error-codes/base/user-lookup.program.json \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/patch-task-001-error-codes/reference/semantic.patch.json \
  /tmp/user-lookup.patched.program.json
```

Verify the heterogeneous candidate matrix:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_patch_suite.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/semantic-patch-suite-v0.json \
  --verify
```

Verify the sealed final task suite and all pre-model controls:

```bash
.venv/bin/python -m unittest tests.test_semantic_final_task_suite
```

Apply the reference reserved-identifier guard with catalog v1:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_patch_v1.py \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.catalog-v1.program.json \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.reserved-id-guard.patch.json \
  /tmp/user-lookup.reserved-id-guard.program.json
```

Apply the ordered directory fallback with catalog v2:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_patch_v2.py \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.catalog-v2.program.json \
  experiments/coding-agents/semantic-ir/2026-08-26/examples/user-lookup.directory-fallback.patch.json \
  /tmp/user-lookup.directory-fallback.program.json
```

Run the focused construction checks:

```bash
.venv/bin/python -m unittest \
  tests.test_semantic_ir \
  tests.test_semantic_task \
  tests.test_semantic_patch \
  tests.test_semantic_patch_task \
  tests.test_semantic_patch_suite \
  tests.test_semantic_string_equals_extension \
  tests.test_semantic_directory_extension \
  tests.test_semantic_interface_freeze
```

Verify the capability protocol, fresh suite, and frozen synthetic trajectory:

```bash
.venv/bin/python -m unittest \
  tests.test_semantic_capability_protocol \
  tests.test_semantic_capability_task_suite \
  tests.test_semantic_capability_execution \
  tests.test_semantic_capability_calibration_observation \
  tests.test_semantic_compact_context_v1 \
  tests.test_semantic_motion_lexicalization_v1

.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_capability_calibration.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/capability-execution-freeze-v2 \
  --preflight
```

The preflight performs no provider call. Calibration 003 used a separately
authorized, content-bound launch record; reproducing preflight does not
authorize another execution.

Verify the checked model-facing interface freeze:

```bash
.venv/bin/python \
  experiments/coding-agents/semantic-ir/2026-08-26/scripts/interface_freeze.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/task-001-user-lookup \
  --verify \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/interface-freeze-v0.json
```

## Frozen model-facing interface v0

The first freeze isolates **output representation**, not the agent's entire
input representation. Both arms receive the same locked participant workspace
and can perform the same four operations:

- list workspace files;
- read a UTF-8 workspace file;
- run the shared public evaluator; and
- finish the candidate, after which the orchestrator audits the workspace and
  runs the withheld evaluator.

Exactly one mutating operation differs:

| Source arm | Semantic-IR arm |
| --- | --- |
| `workspace_write_target({path, content})` | `ir_submit({program})` |
| Writes TypeScript to a frozen editable path | Validates and deterministically lowers a program to the same path |

Both operations have the same mutation scope. Protected files remain immutable
and neither arm can invoke or inspect the hidden evaluator. A valid semantic
submission produces an ordinary TypeScript target, which the semantic arm may
then inspect through the shared read operation. An invalid semantic submission
returns structured validation errors and leaves the workspace unchanged.

The contexts are not byte-identical because the treatment itself must be
described. Their exact UTF-8 byte lengths and SHA-256 digests are frozen. The
semantic context includes the complete catalog and program schema; their input
tokens must be charged to that arm in later accounting.

The interface freeze alone does not authorize model calls or efficacy claims.
The separate construction-observation protocol authorizes only its recorded
pair and fixes model identity, inference parameters, limits, and token
accounting. A calibration stopping rule and confirmatory design remain deferred.

## Planned first comparison

The first model-facing comparison will use matched repository tasks under two
policies:

```text
A — source policy
    inspect and edit ordinary TypeScript

B — semantic policy
    inspect a closed symbol catalog and emit validated IR
    that is interpreted and projected deterministically
```

The construction fixture and output-representation interfaces are frozen. The
first bounded construction observation additionally froze model identity,
inference parameters, budgets, token accounting, retry policy, telemetry, and
invalidation rules. A future calibration still requires fresh tasks and an
outcome-independent stopping rule. Direct-source and semantic outputs must
continue to be judged by the same hidden executable behavior.

Candidate measurements are:

- hidden-evaluator Pass@1;
- total model input and output tokens using provider-native accounting;
- validation failures by category;
- repair cycles and time to verified resolution;
- unsupported-task rate;
- projection size and deterministic-build status;
- human comprehension of a semantic diff, treated as a separate study unless
  its procedure is independently frozen.

The unsupported-task rate is mandatory: a small IR must not appear reliable
merely because it cannot express difficult changes.

### Construction task status

`task-001-user-lookup` now exercises the full pre-model path:

```text
locked task tree
      ↓
participant-only workspace + mode-specific context
      ↓
source edit OR validated semantic lowering
      ↓
workspace integrity audit
      ↓
the same public and hidden executable behavior
```

The baseline fails both evaluators. Independent reference TypeScript and the
semantic projection pass both. A deliberately incomplete source solution passes
the public tests and fails the hidden evaluator, establishing that the hidden
contract adds discriminating behavior rather than duplicating the public suite.

This task is construction-only and permanently contaminated for confirmatory
use: its example IR, reference solution, and hidden evaluator are public in this
tree. A real run must use a fresh locked task and expose only the materialized
workspace plus the assigned mode context to the model.

### Semantic patch construction status

`patch-task-001-error-codes` changes two independent literals over persistent
IR. The unchanged source projection fails both evaluators. The staged source
diff and transactional semantic patch pass the same public and hidden tests and
produce byte-identical TypeScript. A public-only semantic patch passes the
public test and fails the hidden evaluator; stale semantic state and protected
source changes are rejected without mutating the participant workspace.

The semantic JSON patch is 1,009 bytes versus 1,238 bytes for the unified diff
on this generated source. This is a local payload measurement, not token or
model evidence. The reference solutions and hidden tests are checked in, so the
task is permanently non-confirmatory.

### Heterogeneous final task status

Six concrete task instances are now sealed across local literals, dataflow,
control flow, effects, and repository scope, with exactly two tasks in each size
band. Three use v0, the reserved-identifier guard uses catalog v1, the directory
fallback uses catalog v2, and the cross-module migration is explicitly
unsupported. Candidate identities and the frozen analysis policy are unchanged.

The final semantic applicability boundary is 5/6. Unsupported semantic outcomes
count as failures in all-task utility; a conditional supported-task result is
allowed only beside all-task utility and applicability. All baseline, reference,
public/hidden-discrimination, participant-isolation, and content-lock controls
pass. The conditional contamination audit records zero experimental subject
calls and known coding-agent development exposure; it requires fresh isolated
contexts, an offline allowlisted runner, and a repeated pre-call model/provider
audit.

## Limitations and next gate

This slice is closer to a typed domain kernel than to a programming language.
It has one domain type, two effects in v2, no modules, no recursion, no
collections, and only one semantic patch operation. There is no insert, delete, move, merge,
or repository adapter beyond deterministic replacement of one generated target.
Its JSON encoding remains verbose and the local patch bytes are not evidence for
token efficiency. Generated TypeScript has node markers, not a
standards-compliant source map. Capability adapter exceptions remain runtime
failures rather than typed IR values, and the v0 projection is synchronous;
both boundaries must be explicit in every task fixture.

The synthetic repeated-body curve crossed at eight bodies and remained below
source at sixteen, but it does not represent heterogeneous repository work.
Calibration 001 exposed a treatment-asymmetric addressability failure.
Calibration 002 fixed addressability but exposed model-inaccessible digest
preconditions. Capability v2 moved those preconditions into trusted
infrastructure, and calibration 003 completed without either defect.

Calibration 003 is valid descriptive evidence, not a confirmatory result. On
six frozen tasks, semantic hidden passes were 4/6 versus 2/6 for source. The
semantic arm used 30.4% fewer provider requests and 54.2% fewer output tokens,
but 57.3% more total tokens and 28.4% more estimated cost because its input
surface was larger.

Compact Context v1 preserves checked state and opaque preconditions while
reducing the five-task initial semantic context from 81,171 to 13,647 canonical
UTF-8 bytes. Including tool definitions, the reduction is 56.63%, but the
compact semantic surface remains 3.18 times the corresponding source surface.
The recursively expanded expression grammar now occupies 73.67% of compact
input. These are local byte measurements, not provider tokens. The next gate is
a compact, finite patch instruction surface that lowers to the unchanged
canonical patch and crosses local source break-even before any new model call or
fresh confirmatory freeze.
