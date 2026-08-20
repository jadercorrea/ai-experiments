# Construction set

This directory contains three repository-disjoint Go tasks used only to build
and test the benchmark harness. They are excluded from calibration,
confirmatory estimates, and publication claims about routing performance.

The tasks were reconstructed from merged pull requests in Bubble Tea, Cobra,
and Chi. Each retained task has:

- an immutable base and reference commit;
- separate test and solution patches;
- at least one observed fail-to-pass transition;
- a full regression run under the Go race detector;
- an OSI-approved source license;
- a non-root container built from a digest-pinned Go image;
- network-disabled evaluation.

`candidates.json` records the manually curated candidate metadata. Files under
`artifacts/<task>/` contain the separated patches and the validated benchmark
task record.

## Verify repository contracts

```bash
python3 -m venv .venv
.venv/bin/pip install --requirement requirements-dev.txt
PATH="$PWD/.venv/bin:$PATH" ./scripts/validate
```

## Re-run the executable transitions

Build the three local images from their immutable base commits, then run the
transitions:

```bash
PATH="$PWD/.venv/bin:$PATH" python3 scripts/build_construction.py
PATH="$PWD/.venv/bin:$PATH" python3 scripts/verify_construction.py
```

The verifier checks artifact hashes, runs the focal test with only the hidden
test patch and expects failure, then applies the reference solution and requires
the pass-to-pass regression command to succeed. Every runtime uses
`--network none`, a read-only evidence mount, and a non-root user.

The experimental runner has a stricter contract than this construction
verifier. [HARNESS_V2.md](HARNESS_V2.md) defines evaluator separation, frozen
outcomes, policy isolation, telemetry, failure classification, randomization,
and the admission tests required before any model budget is consumed.

Image IDs in the current records identify the locally validated construction
images. They are not yet published OCI artifacts. A release candidate must
publish or archive the exact images and replace local-only identity with
portable OCI provenance before confirmatory execution.

## Construction findings

The construction process found three harness defects before model execution:

1. a login shell removed the Go toolchain from `PATH`;
2. excluding Git metadata changed repository behavior and agent-visible state;
3. running as root invalidated a Cobra permission test.
4. Docker Desktop's `--internal` networks still allowed an agent container to
   reach `host.docker.internal`, so the final design uses `--network none` and
   a Unix socket connected to the policy gateway;
5. a background relay could keep a container alive after the command runner
   reported completion, so the runner now names containers, redirects relay
   descriptors, traps termination, and uses Docker state as the lifecycle
   authority;
6. mutable model aliases are not treatment identities. The local treatment is
   locked by Ollama runtime version, public quantization-specific tag, and full manifest digest
   in [`../model-lock.json`](../model-lock.json). The gateway verifies all three
   at the start of every run and rejects `latest` requests.

These are harness failures, not model failures. They motivate recording shell,
Git state, user identity, filesystem ownership, and privileges as experimental
environment variables.

## First contained local pilot

The first post-lock construction pilot used Chi task 1045, the `local-only`
policy, OpenCode 1.18.9, Ollama 0.32.5, and the locked Qwen3 Coder manifest. It
made 11 auditable inference calls on the GPU but produced no material patch
before the 300-second hard timeout. The outcome is `agent_timeout`; the hidden
evaluator was intentionally not opened.

This is a harness and feasibility observation, not a benchmark estimate. It is
excluded from calibration, confirmatory analysis, and model-performance claims.
