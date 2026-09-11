# Final heterogeneous task suite: pre-model sealing observation

## Status

**Six concrete matched patch tasks are content-locked before model use. Five
have a supported semantic path and one has an explicit unsupported terminal.
No model calls or efficacy claims are authorized.**

Observation date: **2026-08-27**

Suite: `semantic-ir-final/heterogeneous-patches-v0`

Suite self-digest:
`6582c37cbc7d7a1acfaef9768809ad4b6d6360e0c47babd11666583f9d9eb914`

## What was sealed

The candidate identities and analysis policy from
`semantic-ir-candidates/heterogeneous-patches-v0` remain unchanged. Each family
now has one concrete repository, participant objective, public evaluator,
external hidden evaluator, retained public-only rejected candidate, reference
source patch, runtime identity, editable-path boundary, and artifact lock.

The five supported tasks additionally carry a versioned persistent IR base and
a checked semantic reference patch. The repository-scope task carries an
explicit `semantic_unsupported` record instead of a fake semantic solution.

| Task | Size | Semantic disposition | Backend |
| --- | --- | --- | --- |
| `error-taxonomy-001` | small | supported | v0 |
| `normalization-policy-001` | small | supported | v0 |
| `raw-id-retry-001` | medium | supported | v0 |
| `reserved-id-guard-001` | medium | supported | v1 |
| `directory-fallback-001` | large | supported | v2 |
| `cross-module-rename-001` | large | unsupported | none |

The final applicability boundary is therefore **5/6 (83.33%)**. The
unsupported task remains a failure in the six-task all-task denominator; the
five-task conditional denominator may only be reported beside that result.

## Construction controls

The executable pre-model checks establish:

- all six unchanged baselines fail their hidden evaluators;
- all six source references pass the same public and hidden contract;
- all five semantic references pass both evaluators and lower to target files
  byte-identical to their source-reference counterparts;
- all six retained incomplete source candidates pass the public evaluator but
  fail the hidden evaluator;
- participant allowlists exclude hidden evaluators, references, and publication
  metadata;
- task and suite locks, candidate identities, dependency hashes, hidden-test
  hashes, and the suite self-digest verify;
- the unsupported semantic outcome mutates no workspace and is counted as an
  all-task failure.

These checks demonstrate fixture discrimination, arm convergence for reference
solutions, isolation mechanics, and a locked semantic applicability boundary.
They do not measure model performance.

## Contamination boundary

The hidden evaluators and references are checked into the research repository
for auditability. They are hidden only from the materialized participant
surface, not from the repository owner or an unconstrained process. The suite
therefore records `conditional_pre_model_clearance`, not a universal
cleanliness claim.

There have been zero **experimental subject** calls on these exact instances.
The coding agent that assisted their construction has seen the builder,
evaluators, and references; the audit records that development exposure
explicitly. Later use is conditional on fresh subject contexts without this
development thread, a runner that exposes only the repository and assigned-mode
context, denial of host-repository traversal and external browsing, exact
context digests, and a repeated model/provider audit immediately before the
first call. Known overlap with the public candidate objectives and the earlier
lookup-user construction is retained rather than hidden.

## Claim boundary

This is a final **task/evaluator/support** lock, not a final execution protocol.
It authorizes neither model calls nor an efficacy claim. Still deferred are the
model identity, inference parameters, tool and retry budgets, exact arm-context
digests, execution order, and calibration stopping rule.

The next gate is to freeze those execution variables and implement the isolated
runner. Only that later lock may authorize the first paired model call.

## Reproduce

From the repository root:

```bash
.venv/bin/python -m unittest tests.test_semantic_final_task_suite
```

The suite manifest is
[`construction/final-patch-tasks-v0/suite.json`](construction/final-patch-tasks-v0/suite.json),
the contamination record is
[`construction/final-patch-tasks-v0/publication/contamination-audit.json`](construction/final-patch-tasks-v0/publication/contamination-audit.json),
and the outer content lock is
[`construction/final-patch-tasks-v0/publication/artifact-lock.json`](construction/final-patch-tasks-v0/publication/artifact-lock.json).
