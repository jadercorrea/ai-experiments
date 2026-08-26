# Semantic IR for coding agents — construction slice v0

## Status

**Executable construction artifact with one matched task fixture and two valid
descriptive token observations. No efficacy claim is supported.**

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
- One declared external effect: `db.read:users`.
- A closed catalog with three callable symbols.
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
- Branches are total for the supported `if` and `Option` forms and must agree on
  their result type.
- Interpretation and lowering both require the same validation pass.
- The interpreter records an effect only when the effect is actually executed.
- The TypeScript projection is deterministic for a canonical IR object.

## The semantic core

The canonical representation is JSON for this construction slice. JSON is a
transport and inspection format, not a proposed final AI-native surface syntax.
The important boundary is the typed tree and its operational semantics.

| Symbol | Input | Output | Effect |
| --- | --- | --- | --- |
| `string.trim_ascii` | `string` | `string` | pure |
| `string.is_empty` | `string` | `boolean` | pure |
| `users.get_by_id` | `string` | `option<user>` | `db.read:users` |

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
- [`test_semantic_ir.py`](../../../../tests/test_semantic_ir.py) exercises the
  construction invariants.
- [`test_semantic_task.py`](../../../../tests/test_semantic_task.py) proves the
  expected baseline/reference/semantic/public-only evaluator separation.
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

Run the focused construction checks:

```bash
.venv/bin/python -m unittest \
  tests.test_semantic_ir \
  tests.test_semantic_task \
  tests.test_semantic_interface_freeze
```

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

## Limitations and next gate

This slice is closer to a typed domain kernel than to a programming language.
It has one domain type, one effect, no modules, no recursion, no collections,
no semantic patch operation, and no adapter to an existing repository. Its JSON
encoding is verbose and is not evidence for token efficiency. Generated
TypeScript has node markers, not a standards-compliant source map, and has not
yet been compiled as part of the repository verification path. Capability
adapter exceptions remain runtime failures rather than typed IR values, and the
v0 projection is synchronous; both boundaries must be made explicit in any
task fixture that uses this core.

The next gate is not “add more syntax.” The forced single-shot comparison showed
that compact IR can make the generated solution substantially denser while the
fixed grammar/context cost keeps whole-request tokens at parity on a tiny task.
The next slice should measure that break-even curve across fresh tasks of
increasing solution size, with the grammar frozen once. A later semantic-patch
arm should test persistent graph editing instead of full-program retransmission.
