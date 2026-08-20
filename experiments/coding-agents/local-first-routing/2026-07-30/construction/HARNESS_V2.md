# Evaluation harness v2

## Purpose

The pilot evaluates routing policies, not memorable agent demonstrations. The
harness must therefore keep the task, evaluator, execution environment, and
measurement policy constant while changing only the declared routing policy.

The current GPTCode evidence runner is useful for recording executions, but it
cannot be used as the experimental authority without the changes below. It
copies the complete fixture into the agent workspace, executes verification
commands from that same visible fixture, and does not independently enforce the
container, network, identity, or routing-policy contract specified by this
experiment.

This document defines the minimum compatible harness. Any material change to
these rules creates a new harness series; results from different major series
must not be pooled as if they measured model progress alone.

## Non-negotiable invariants

### Evaluator separation

1. Prepare the agent workspace from the immutable `base_commit`.
2. Expose only `public_problem` and `router_view` while the agent is running.
   Mount the working tree read-write but overlay its `.git` metadata read-only;
   the agent may inspect repository history but cannot rewrite configuration,
   refs, index state, or filters before the host freezes the patch.
3. Keep `hidden_evaluator.test_patch` outside the workspace and outside every
   model context, tool response, log, and retry prompt.
4. Stop the agent and freeze its final patch before evaluation begins.
5. Apply the hidden test patch only to an evaluator copy of that frozen state.
6. Run the declared F2P and P2P commands in the evaluator, not through the
   agent.

Any run in which hidden evaluator material reaches the agent is invalid, not a
failed task.

### Environment identity

Every run must record and enforce:

- task schema version and task-manifest SHA-256;
- repository URL and immutable base commit;
- container image name and digest;
- harness version and source commit;
- operating system, architecture, and non-root UID/GID;
- network policy for the agent and evaluator phases;
- routing-policy identifier and immutable policy configuration;
- provider, model, model digest or release identifier, context limit, and
  sampling parameters;
- separate hashes and byte counts for the client request and the normalized
  upstream payload actually sent to the selected backend;
- wall-clock, model-reported token counts, retry counts, and termination cause;
- local accelerator backend, device identity, and sampled utilization when a
  local model is used.

Missing identity data makes a run non-comparable. It must never be inferred
after the fact.

### Policy isolation

The three arms share the same task order, public inputs, tools, limits, and
evaluator:

- `local-only`: no hosted inference is permitted;
- `cloud-only`: no local inference is permitted;
- `local-first`: begins locally and may invoke the preregistered fallback only
  after an objective trigger.

Fallback cannot be an informal human decision. Each trigger must be machine
observable and preregistered, such as a hard timeout, exhausted attempt budget,
repeated verification plateau, or explicit model failure. The harness records
the trigger, local work already consumed, payload transferred to the cloud
model, and all subsequent cost and latency.

The inference gateway enforces the backend allowed within a stage; it does not
perform the primary policy transition. The campaign runner must stop the local
stage, freeze its evidence, restore the immutable base, and start a separate
cloud-only stage. In-conversation provider failover is a distinct ablation.

### Frozen outcome

The agent phase ends before hidden evaluation. The harness records:

- the final Git diff and its SHA-256;
- changed paths and repository status;
- the complete event stream and tool commands;
- the termination reason;
- any policy transition and its trigger.

The evaluator operates on a copy. It must not allow a model to react to hidden
test output. An evaluator crash is an infrastructure error and is rerun under
the preregistered rule; a completed failing test is an agent failure.

## Execution state machine

```text
validate manifest
      |
materialize immutable base
      |
apply public task material only
      |
start isolated agent phase
      |
local-only | cloud-only | local-first policy
      |
freeze patch and trajectory
      |
clone frozen state for evaluator
      |
apply hidden test patch
      |
run F2P, P2P, static and security checks
      |
classify outcome and seal evidence bundle
```

No arrow returns from the evaluator to the agent.

## Failure taxonomy

The runner emits exactly one primary outcome and may attach secondary labels.

Primary outcomes:

- `pass`: all required evaluator commands pass;
- `functional_failure`: evaluator completed and functional tests failed;
- `regression`: F2P passes but a P2P command fails;
- `agent_timeout`: the agent exceeded its declared budget;
- `agent_error`: the agent or inference backend failed before producing a
  frozen result;
- `policy_violation`: a forbidden provider, network action, or fallback was
  attempted;
- `invalid_run`: evaluator leakage or missing comparability metadata;
- `infrastructure_error`: construction or evaluator infrastructure failed.

Secondary labels include security-boundary violation, incomplete patch,
non-compiling patch, no-op, malformed tool call, context exhaustion, repeated
patch, fallback trigger, and telemetry loss.

## Randomization and repetition

- Build repository-disjoint blocks by task complexity.
- Randomize policy order within each block from a recorded seed.
- Never run all tasks from one policy in a temporal batch.
- Preserve unsuccessful trajectories; do not replace them with hand-selected
  retries.
- A rerun is allowed only for a classified infrastructure error and retains a
  link to the invalidated attempt.
- Pilot runs validate the apparatus and variance assumptions. They are not
  merged silently into the confirmatory sample.

## Minimum implementation order

1. Add a public-workspace materializer and a physically separate hidden
   evaluator store.
2. Add the frozen-patch boundary and evaluator-copy workflow.
3. Enforce pinned containers, non-root execution, and phase-specific network
   policies.
4. Add structured run manifests, event logs, telemetry, and outcome taxonomy.
5. Implement the three routing policies, including objective clean-fallback
   triggers.
6. Add randomized block scheduling and resumable campaign state.
7. Run a zero-inference smoke test with scripted mock agents.
8. Run the construction pilot locally before authorizing hosted inference.

## Pilot admission criteria

For the Amazon Bedrock treatment, the host gateway is the only process allowed
to retrieve the scoped Bearer Token from macOS Keychain. The token must not be
written to an authorization file or passed to Docker. The agent container keeps
`--network none` and communicates only over the mounted Unix socket. The
OpenAI-to-Converse adapter and its reverse tool-call translation must pass unit
tests before provider admission.

The harness is ready for model runs only when automated tests prove that:

- an agent cannot read the hidden patch by path traversal, command output,
  environment variable, mounted directory, or evidence bundle;
- the evaluator receives the exact frozen patch and cannot mutate the original
  trajectory;
- local-only and cloud-only reject forbidden backends;
- local-first falls back exactly once and only on registered triggers;
- timeouts terminate descendants and report the correct final status;
- an interrupted campaign resumes without duplicating a trial;
- all required identity, cost, timing, and accelerator fields are present;
- a known-good solution passes and three intentionally defective solutions are
  classified correctly.

Only after these checks pass should the pilot consume Qwen, Kimi, Gemini,
OpenAI, or other inference budgets.
