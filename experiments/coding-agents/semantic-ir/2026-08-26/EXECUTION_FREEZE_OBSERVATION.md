# Semantic patch calibration — execution freeze observation

## Status

The heterogeneous semantic-patch calibration is now completely specified but
not launched. The freeze authorizes zero model calls, contains no efficacy
result, and leaves one explicit gate: a separately recorded launch after the
prelaunch checks are repeated.

Freeze identity:
`02bb16238584057e809d8bd2655a13b8b5d163a2317774735e4e636d18a83c05`.

## What is frozen

The execution manifest fixes the following before any experimental subject sees
the six task instances:

- Amazon Bedrock `us.anthropic.claude-sonnet-4-6` in `us-east-1`, with provider
  substitution forbidden;
- temperature `0`, at most 4,096 output tokens per turn, 12 model turns and four
  tool calls per call-bearing cell;
- three mutation attempts, two public evaluations, one hidden evaluation, and
  zero provider retries per cell;
- 132 provider requests globally, with a USD 10 ceiling reserved against the
  worst-case next request before it is sent;
- exact rendered context and tool-schema digests for every arm;
- one fresh ephemeral participant workspace per cell and a closed tool surface
  without shell, browsing, network, or host-repository access;
- a fixed, nonadaptive order balanced across three source-first and three
  semantic-first pairs;
- twelve terminal outcomes but eleven provider-call cells, because the locked
  unsupported semantic repository task terminates automatically and remains a
  failure in the all-task denominator;
- no efficacy early stop, no replacement runs, and a stop after two consecutive
  infrastructure-invalid cells or before the next worst-case request could
  exceed the spend ceiling.

The runner records complete request/response and tool evidence, provider-native
usage, estimated spend, validation failures, public evaluations, repair cycles,
time to terminal submission, payload bytes, workspace digest, and one external
hidden evaluation. A failed provider or evaluator step preserves any usage
already incurred; unsuccessful provider attempts also consume the global
request budget.

## Isolation boundary

This is capability isolation implemented by an allowlisted orchestration layer,
not a claim that the Python process itself is an operating-system sandbox. The
experimental subject receives only the rendered context and five closed tools:
workspace listing, workspace reading, public evaluation, its assigned mutation
operation, and terminal submission. Host-side reference solutions and hidden
evaluators remain auditable in the repository but are absent from the subject
surface.

The orchestrator alone may contact the locked Bedrock endpoint. Credentials are
read from macOS Keychain and are not placed in model context. Evidence from a
future run will contain provider payloads and must pass a secret scan before
publication.

## Contamination boundary

The repeated preflight audit still has the honest status
`conditional_pre_model_clearance`:

- experimental subject calls on the exact instances: `0`;
- the coding agent used to build and inspect the fixtures has seen host-side
  materials;
- the hosted provider does not expose a cryptographically immutable weight
  snapshot;
- the frozen participant surface excludes hidden tests, references, shell,
  browsing, network, and the host repository.

Immediately before launch, a fresh subject context, exact endpoint/IAM scope,
provider retention policy, credential availability, artifact digests, and the
zero-prior-call count must be checked again. Those assertions belong in an
`execution-launch-v0` document tied to this exact freeze and artifact-lock hash.
Creating such a document without an explicit launch decision is not authorized.

## Analysis boundary

The primary descriptive metric is hidden Pass@1 over all six locked tasks. The
unsupported semantic outcome counts as failure. A five-task conditional result
may be reported only beside all-task utility and semantic applicability. Token
accounting includes all trajectory requests and repair turns reported by the
provider. This small calibration does not authorize an inferential or benchmark
claim, even after execution.

## Verification

From the repository root:

```bash
.venv/bin/python experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_execution_freeze.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/execution-freeze-v0 \
  --verify

.venv/bin/python experiments/coding-agents/semantic-ir/2026-08-26/scripts/semantic_patch_calibration.py \
  experiments/coding-agents/semantic-ir/2026-08-26/construction/execution-freeze-v0 \
  --preflight

.venv/bin/python -m unittest tests.test_semantic_execution_freeze
```

The builder was also reproduced into a second directory: both `freeze.json`
files and both artifact locks were byte-identical. Preflight performs no model
call. The execution command remains deliberately gated by a schema-valid launch
document and a new output directory.

## Claim

The execution variables and participant surface are frozen and reproducible.
No model has received these exact experimental inputs through this protocol, no
calibration cell has run, and no efficacy claim is supported.
