# Construction task 001: user lookup

## Claim boundary

This is a harness-construction task, not an experimental observation. No model
has attempted it under either treatment.

The task is permanently ineligible for confirmatory use because its semantic
program, reference source solution, public evaluator, and hidden evaluator are
present in this public construction tree. It exists to test treatment
materialization, evaluator parity, and contamination controls before selecting
fresh calibration tasks.

## Matched contract

Both submission modes begin from the locked contents of `repository/`. Only
`src/lookup-user.ts` may differ at evaluation time.

- `source`: the participant edits that TypeScript file directly.
- `semantic_ir`: the participant emits a program object; the harness requires a
  clean baseline, validates the object, and atomically projects the target file.

The task behavior and mode instructions are supplied out of band from
`participant-context/`. The materialized workspace contains only `repository/`.
It does not contain `evaluator/`, `reference/`, the artifact lock, or either
mode's instructions.

## Shared evaluation boundary

The public and hidden evaluators import the same target module and accept the
same API. Evaluation first audits the workspace against the artifact lock:

- the editable target may change;
- every other baseline file must retain its recorded digest;
- missing, unexpected, and symlinked files are rejected;
- the evaluator is pinned to Deno 2.7.13, receives no network permission, and
  refuses remote and npm module resolution;
- the hidden evaluator receives only permission to read the target workspace
  and the environment variable containing the target module URL.

Construction checks establish the following expected separation:

| Artifact | Public evaluator | Hidden evaluator |
| --- | --- | --- |
| Baseline stub | fail | fail |
| Reference TypeScript solution | pass | pass |
| Deterministically projected semantic example | pass | pass |
| Deliberately public-only TypeScript solution | pass | fail |

This table records test-fixture behavior, not agent performance.

## Integrity

`publication/artifact-lock.json` records every file in this task tree except the
lock itself. Repository materialization refuses a stale lock. After any
intentional task change, rebuild the lock before running construction checks.
`task.json` additionally pins the external task schema, harness, program schema,
and semantic lowerer by SHA-256 so those dependencies cannot drift while the
task tree still appears unchanged.

The lock establishes artifact identity. It does not make the hidden evaluator
secret from a process that can inspect this parent repository. Any future agent
run must mount only the materialized participant workspace and its assigned
out-of-band context.
