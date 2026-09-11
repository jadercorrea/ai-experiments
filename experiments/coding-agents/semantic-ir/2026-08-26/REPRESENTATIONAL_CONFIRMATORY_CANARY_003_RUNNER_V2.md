# Representational confirmatory canary 003 runner v2

## Status

**The sequence-3-only runner, launch schema, and result schema are implemented
and pass a provider-free regression of the exact lexical trajectory that broke
canary 002. No launch artifact exists and external execution remains blocked.**

## Content boundary

The runner accepts only the materialized canary-003 plan. A future launch must
bind all of the following:

- the exact plan file and canonical plan digests;
- the protocol v2 freeze and artifact lock;
- the runner, launch-schema, and result-schema digests;
- immutable schedule sequence 3;
- `capability_lookup_fallback-001 / opaque_table`;
- `SESSION_STATE/v1` with observation codec v1;
- one authorized cell, two prior observed cells, and 957 blocked cells; and
- 12 requests, zero retries, and a USD 4.00 ceiling.

The launch schema fixes retry authority for sequences 1 and 2 and remaining
campaign release to `false`. Drift in the cell, runner, plan, protocol,
provider, runtime, limits, or hashes is rejected before inference.

## Provider-free lexical regression

The runner was exercised with deterministic local inference responses carrying
the same three inspection instructions recorded from canary 002:

```text
I [n0,n3,n8,n11,n12,n13,n14]
I [n11,n12]
I [n8,n9,n10,n11,n12,n13,n14]
F
```

Under protocol v2 and opaque-table packaging:

- all three inspections execute;
- the fourth request contains `k32`;
- the fourth request does not expose `arguments[0]`;
- the session reaches terminal `F`;
- the operational gate passes; and
- the result validates against the new result schema.

The four responses were local test doubles. They are not provider observations
and support no behavioral claim.

## Authorization and credential boundary

Freezing this runner does not materialize a launch. The default launch path is
absent. The command that prepares a launch requires a new authorization message
before checking credential presence. Credential values are never recorded or
placed in model context.

Only an already validated, content-bound launch can reach the execution path.
The external gateway remains cloud-only, model-locked, request-bounded,
zero-retry, and spend-bounded.

## Claim boundary

- The runner can represent and continue past the known canary-002 lexical
  failure under deterministic local inference.
- Launch and result contracts reject the known scope-expansion paths.
- No credential was read during this checkpoint.
- No provider request was made and no cost was incurred.
- No model behavior, efficacy, or generalization claim is supported.

## Evidence

- [`representational_confirmatory_canary_runner_v2.py`](scripts/representational_confirmatory_canary_runner_v2.py)
  implements launch validation, bounded execution, and evidence capture.
- [`representational-confirmatory-canary-launch-v2.schema.json`](protocol/representational-confirmatory-canary-launch-v2.schema.json)
  seals the one-cell authorization boundary.
- [`representational-confirmatory-canary-result-v2.schema.json`](protocol/representational-confirmatory-canary-result-v2.schema.json)
  seals result and operational-gate accounting.
- [`test_representational_confirmatory_canary_runner_v2.py`](../../../../tests/test_representational_confirmatory_canary_runner_v2.py)
  replays the lexical failure locally and exercises scope rejection.

## Next red test

Freeze this runner checkpoint. A later external launch requires a new explicit
authorization naming the canary-003 plan, followed by current credential and
pricing checks. That authorization may materialize one launch for sequence 3;
it cannot retry sequences 1 or 2 or release the other 957 cells.
