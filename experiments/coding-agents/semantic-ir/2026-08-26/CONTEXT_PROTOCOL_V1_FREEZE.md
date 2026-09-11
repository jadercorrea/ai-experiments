# Experimental TDD for agent infrastructure: context protocol v1

## Status

**Fresh task instances and a recoverable, addressable context protocol are
sealed before model execution. No model call is authorized or observed. No
efficacy or token-efficiency claim is made.**

The sealed suite self-digest is
`8d88feb0c30f7fc041fa8d938dd351d1db7e0226ace985f9bfad9a615f4bf6d5`.
The execution freeze self-digest is
`2fdc21e5ead53e466ac64048b081d51f7a8077de3f03a2a2340e14b59514b05a`.

Calibration 001 did not falsify semantic patching. It exposed an
infrastructure defect: artifacts visible in the transcript looked like paths,
but were not readable through the workspace tool. The runner then converted
that correctable tool mistake into a terminal failure. Because semantic tasks
depended more heavily on those artifacts, the defect censored that arm
asymmetrically.

This checkpoint treats the failure as a red test for agent infrastructure.

## The v1 boundary

The new protocol separates two namespaces:

| Namespace | Meaning | Operations |
| --- | --- | --- |
| `context://...` | Immutable, allowlisted task artifacts | `context_list`, `context_read` |
| workspace-relative paths | Files in the ephemeral participant repository | `workspace_list`, `workspace_read` |

Every artifact embedded in the system context has one stable handle, role,
byte count, and SHA-256 digest in a cell-specific manifest. Source cells expose
the task and source-mode contract. Supported semantic cells additionally expose
the persistent program, catalog, and applicable schemas. Hidden evaluators,
references, publication metadata, host files, shell, network, and browsing
remain outside the subject surface.

Tool-request errors are now typed observations inside the trajectory. Invalid
JSON, malformed calls, unknown handles, wrong namespaces, schema-invalid
arguments, exhausted public-evaluation or mutation budgets, and excess calls in
a turn produce a recoverable tool result. Every provider tool-call ID receives
a response, while the frozen four-executed-call and twelve-turn limits remain
unchanged. Context drift and unexpected evaluator/orchestrator failures remain
infrastructure-invalid; they are not blamed on the model.

## Fresh instances

The v1 suite preserves the six predeclared task strata, the 5/6 semantic
applicability boundary, the shared public/hidden evaluator contract, and the
all-task denominator. It changes exact task bytes before any new subject call:

- program, patch, node, local, and parameter identities use a new namespace;
- exported function and cross-module contract names change;
- repository and hidden-evaluator bytes change;
- task and suite locks are rebuilt; and
- all reference solutions are revalidated locally.

All six source references pass hidden evaluation. All five supported semantic
references pass hidden evaluation and lower to editable files byte-identical to
their paired source references. The unsupported cross-module semantic task
remains an explicit zero-call failure in the primary denominator.

These are fresh exact instances, not a claim of universal contamination
cleanliness. They are deterministically derived from the same public semantic
requirements and have known development-agent exposure. A future execution is
therefore calibration evidence.

## Tests that failed before the implementation

The implementation was built as an experimental TDD sequence:

1. importing the addressable context protocol failed;
2. a recoverable wrong-namespace trajectory failed because no v1 runner
   existed;
3. fresh-suite construction failed until references, semantic preconditions,
   evaluator hashes, and locks were regenerated; and
4. review exposed a missing epistemic distinction between a bad subject request
   and context-integrity drift, which received separate error classes before
   freeze.

The resulting tests prove deterministic suite and freeze construction,
reference convergence, exact context-handle coverage, namespace separation,
recoverable continuation after a wrong read, non-recoverable context drift,
launch binding, and zero prelaunch calls.

## Claim boundary and next gate

This checkpoint establishes that the revised infrastructure can represent and
recover from the failure mode observed in calibration 001. It does not establish
that models will use the new interface correctly, that semantic IR will improve
Pass@1, or that it will reduce tokens.

The freeze continues to declare:

- `model_calls_authorized: false`;
- `experimental_subject_calls_observed: 0`;
- `efficacy_claim_authorized: false`; and
- `remaining_before_launch: [explicit_launch]`.

A launch requires a separate v1 authorization record binding the exact freeze,
artifact lock, model lock, repeated contamination audit, fresh subject context,
credential and endpoint preflight, and zero prior calls. Until that explicit
gate is crossed, the experiment stops here.
