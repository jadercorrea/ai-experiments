# Heterogeneous semantic-patch candidate matrix v0

## Status

**Six task families and their analysis policy were frozen before construction.
Their concrete instances, evaluators, and final 5/6 semantic applicability
boundary are now separately sealed. No model calls or efficacy claims are
authorized.**

This is a candidate-matrix freeze, not a final experiment lock. It fixes what
types of work must be represented and how unsupported work will be counted. It
does not pretend that repositories, hidden evaluators, model policy, or arm
contexts have already been sealed.

## Why freeze the matrix first

The earlier local task proved that a checked semantic patch can modify
persistent IR and converge with a source diff. Selecting only more literal
replacement tasks would make the IR appear broadly applicable without testing
the boundaries that matter: dataflow, control flow, new effects, and
repository-wide changes.

The matrix therefore precedes IR expansion. Two extensions may now be built
because participant requirements demand them, but task identities and
objectives cannot be changed after seeing model behavior.

## Frozen task families

| Family | Stratum | Size | Candidate disposition | Required boundary |
| --- | --- | --- | --- | --- |
| `error-taxonomy-001` | local literal | small | supported v0 | two checked literal replacements |
| `normalization-policy-001` | dataflow | small | supported v0 | replace a `let` value with an existing symbol reference |
| `raw-id-retry-001` | control flow | medium | supported v0 | nested option match and a repeated declared effect |
| `reserved-id-guard-001` | control flow | medium | extension required | pure `string.equals` catalog intrinsic |
| `directory-fallback-001` | effect | large | extension required | directory capability and explicit network-read effect |
| `cross-module-rename-001` | repository scope | large | intentionally unsupported | multi-file identities, exports, and symbol references |

Post-freeze construction status: the pure equality gate is implemented in
catalog v1 and the directory capability/effect gate is implemented in catalog
v2. These additions did not rewrite the table's historical dispositions or task
digests. The final task lock records five supported tasks and keeps the
cross-module family unsupported.

There are exactly two small, two medium, and two large families. Every family
has a content digest over its objective, semantic requirements, size,
disposition, and construction expectations.

## Support is part of the result

The deliberately unsupported cross-module migration remains in the denominator
of the all-task utility estimate. A semantic `unsupported` terminal result
counts as failure there. This prevents the system from increasing apparent
reliability by declining hard tasks.

A conditional hidden Pass@1 may also be reported for tasks supported by both
arms at the final lock, but only beside the all-task result. The mandatory
applicability rate exposes how much of the candidate matrix the semantic
representation can actually cover.

## Outcome-independent extension rule

Before the final task lock, the IR may gain only extensions directly required
by a frozen family:

1. a pure string-equality catalog intrinsic for the reserved-identifier guard;
2. a directory lookup capability with an explicit
   `network.read:directory` effect for the fallback task.

Those changes may not alter task identities or participant objectives. They are
forbidden after the first model call, and model outcomes may never justify
them. The multi-file task stays unsupported in this study rather than triggering
an unbounded repository-IR redesign.

## Frozen analysis boundary

The independent variable is patch representation over persistent state:

```text
source patch arm                    semantic patch arm
locked repository source           locked canonical semantic IR
unified diff                        checked patch or unsupported result
```

Both arms must share the concrete repository instance, participant objective,
visible files, public and hidden evaluators, runtime, model/sampling policy, and
tool/retry budget.

The primary views are:

- all-task hidden Pass@1, with unsupported semantic outcomes counted as
  failures;
- conditional hidden Pass@1 over tasks supported by both arms at the final
  lock, always reported with the all-task view.

Provider-native token accounting must include system/task context, persistent
state, schemas and catalogs, all tool traffic, repair turns, and the terminal
submission. Applicability, validation failures, public evaluator runs, repair
cycles, time, and terminal payload bytes are mandatory secondary metrics.

## Final gate outcome and what remains before model use

The separate final suite now provides one concrete repository task per family
and satisfies the gate with:

- baseline failure and reference-solution success on the hidden evaluator;
- a public evaluator that does not duplicate the entire hidden contract;
- the same instance and hidden evaluator for both arms;
- content locks, sealed hidden tests, and references excluded from participant
  trees;
- predeclared rejection reasons, retained rejected candidates, and a
  contamination audit;
- final support dispositions locked before any model call.

The task/evaluator/support portion is complete. The contamination audit is
conditional because the auditable repository contains hidden and reference
material outside the participant allowlist; the later runner must deny access to
that host tree and to external browsing, then repeat the model/provider audit.

Those formerly deferred execution variables are now frozen, together with the
closed-tool runner and a repeated conditional contamination audit, in
[`execution-freeze-v0`](construction/execution-freeze-v0). The freeze authorizes
zero model calls. Only an explicit launch tied to its exact digests remains; the
boundary is documented in
[`EXECUTION_FREEZE_OBSERVATION.md`](EXECUTION_FREEZE_OBSERVATION.md).

The machine-readable freeze is
[`semantic-patch-suite-v0.json`](construction/semantic-patch-suite-v0.json),
generated and verified by
[`semantic_patch_suite.py`](scripts/semantic_patch_suite.py).
