# Matched Observation Surface v1

## Status

**The previously asymmetric known-reference proxy is now matched. Both arms are
charged for initial context and tool disclosure, deterministic observation, and
reference submission through the same one-tool Session ISA. Against a source
policy that lists the workspace and reads only the reference-touched editable
file, semantic totals 23,256 bytes versus 27,762 source bytes: a 16.23%
reduction. Semantic is smaller in all five supported tasks. Reading the entire
source workspace increases the construction margin to 32.34%. No model call is
authorized, and this is not a provider-token or agent-performance result.**

The deterministic bundle contains 17 files with tree digest
`ded3bc94bd9eb5f37f2bd2730efe28140b9e22f27431a21db319cb61f651d5f6`.
It binds the 22-file Matched Session ISA Control v1 bundle without changing its
tool, envelope, dispatcher, context renderer, mutation paths, or evaluators.

## The matched observation policy

The previous checkpoint charged semantic `I` but assigned zero source
observation bytes. This slice replaces that source lower bound with two explicit
policies.

The primary, deliberately favorable source policy is reference-informed:

```text
L[] → W[each reference-touched editable path]
```

`L` returns the unchanged workspace-list records: path, byte count, and SHA-256.
`W` returns the unchanged path, UTF-8 content, and SHA-256 response. The five
known source references each touch only `src/lookup-user.ts`, so this policy
performs one listing and one targeted read per task.

The sensitivity policy reads every listed file:

```text
L[] → W[deno.json] → W[src/lookup-user.ts] → W[tests/public.test.ts]
```

The semantic policy is the exact frozen reference inspection:

```text
I[reference target handles]
```

Both policies are oracle-informed construction trajectories. Neither represents
which files or nodes a model would choose to inspect.

## Primary result

All counts are canonical UTF-8 bytes. Each total is:

```text
initial context and tool + observation instructions and responses + submit
```

| Component across five tasks | Source targeted | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Initial context + tool | 6,405 B | 14,442 B | +8,037 B |
| Observation exchange | 12,020 B | 6,524 B | −5,496 B |
| Reference submit | 9,337 B | 2,290 B | −7,047 B |
| **Known-reference total** | **27,762 B** | **23,256 B** | **−4,506 B (−16.23%)** |

The semantic initial-state penalty remains real. It is overcome only after
charging both the narrower semantic inspection and the denser semantic mutation.
The result is therefore a composition property of state, observation, and
change representation—not evidence that the initial semantic prompt is smaller.

## Per-task result

| Task | Source targeted | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Directory fallback | 5,731 B | 5,097 B | −11.06% |
| Error taxonomy | 5,465 B | 4,381 B | −19.84% |
| Normalization policy | 4,850 B | 3,916 B | −19.26% |
| Raw-ID retry | 5,214 B | 4,863 B | −6.73% |
| Reserved-ID guard | 6,502 B | 4,999 B | −23.12% |

Every pair has the same direction. The smallest margin is 6.73%, so the
aggregate result is not produced by one unusually favorable task.

## Whole-workspace sensitivity

The source observation exchange grows from 12,020 to 18,628 bytes when it reads
all three visible workspace files. Its total becomes 34,370 bytes:

| Sensitivity total | Bytes |
| --- | ---: |
| Source, target file only after listing | 27,762 B |
| Source, entire listed workspace | 34,370 B |
| Semantic, reference handles | 23,256 B |
| Semantic reduction versus whole-workspace source | 32.34% |

This is not the primary estimate because it assigns a broader observation scope
to source. It demonstrates how strongly the result depends on an agent's file-
selection behavior without using that behavior to inflate the main claim.

## What this checkpoint establishes

- Source and semantic observation are both charged through the frozen Session
  ISA and canonical response shapes.
- Every measured semantic inspection carries the exact state and target tokens
  consumed by its frozen reference submit.
- The semantic representation crosses local known-reference transport break-even
  even against a favorable one-editable-file source policy.
- The break-even holds independently in all five supported task pairs.
- The semantic advantage comes from observation and submit density, not a
  smaller initial state.
- Further interface compaction is no longer required before an execution freeze.

## Claim boundary

- No model/provider call occurred or is authorized.
- UTF-8 bytes are not provider-native tokens.
- Both read policies use knowledge from the exact reference solution.
- Model file selection, node selection, reasoning, invalid instructions,
  repairs, conversation history, provider wrappers, latency, and cost remain
  unmeasured.
- Five supported single-file task pairs cannot establish general repository or
  long-horizon efficacy.
- The unsupported cross-module task remains outside semantic applicability and
  would remain in an all-task execution denominator.

## The next red test

Freeze a fresh matched Session ISA execution package before any new inference.
It must bind new reference-hidden task bytes, the exact one-tool schema and
renderers, source `L/W/S`, semantic `I/S`, response accounting, model and
sampling policy, paired schedule, budgets, evaluator boundary, repair limits,
stopping rule, and a separate explicit launch authorization.

Calibration 004 must retain complete provider-native trajectories and answer a
different question: whether models can realize the construction advantage when
they must choose their own observations and instructions. Its analysis must
report hidden-evaluator outcomes, applicability, invalid-instruction and repair
rates, input/output tokens, requests, latency, and cost. Construction break-even
must remain a prior result, not be relabeled as model efficacy.

The sequence advances to:

`matched source ISA → matched observation surface → fresh execution freeze`.

## Subsequent result

The fresh freeze is now complete. `session-patch-tasks-v3` changes the exact
repository, identity, reference, and hidden-evaluator bytes for all six task
families. `matched-session-execution-freeze-v1` binds those tasks into twelve
paired cells, eleven possible provider calls, the exact shared `x` tool, the
runtime, model and sampling controls, accounting, stopping rules, and a
separate launch contract. Local references pass 6/6 source and 5/5 supported
semantic cells. No inference has occurred; explicit launch remains the only
open gate. See
[`MATCHED_SESSION_EXECUTION_FREEZE_V1_OBSERVATION.md`](MATCHED_SESSION_EXECUTION_FREEZE_V1_OBSERVATION.md).
