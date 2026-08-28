# Matched Session ISA Source Control v1

## Status

**Construction valid and the shared-infrastructure confound removed. Source and
semantic arms now use the exact same 269-byte tool definition, `{i,a}` envelope,
system line, common opcodes, dispatcher, task text, evaluator boundary, and
finish semantics. The semantic arm begins 125.48% larger but submits reference
changes in 75.47% fewer bytes. A partial transport proxy favors source by
47.73%, but it includes semantic inspection while excluding source workspace
reads and is not a treatment comparison. No model call is authorized.**

The deterministic bundle contains 22 files with tree digest
`193f0776b1aba773038b7b9c5255807abe730382ea08d4f00148bf3f803ac60e`.
It binds Session Instruction ISA v1 after the shared-dispatch extension, whose
tree digest is
`1464db33d471ea0ae827649581dbe18f1d36f8caa1965e1ffc953bbd6720b15f`.

## Why this control was necessary

Session ISA v1 measured 14,442 semantic bytes against a frozen 16,277-byte
source comparator. That crossed an engineering gate, but 90.58% of the reduction
from Motion v1 came from collapsing shared tool definitions. The source arm had
not received the same infrastructure improvement.

Comparing those interfaces in Calibration 004 would have attributed shared
protocol compression to semantic representation. This slice removes that
confound before any new inference.

## Matched and treatment-specific surfaces

Both arms now share exactly:

- one `x({i,a})` tool and JSON Schema;
- opcodes `C`, `R`, `L`, `W`, `E`, and `F`;
- the dispatcher implementation and positional envelope;
- system instruction and task text;
- workspace, public-evaluator, atomic-publication, and finish boundaries.

Only representation-specific operations differ:

```text
source:   S[unified-diff]
semantic: I[node-handles] → S[patch-id,state-token,motions]
```

Source `S` writes the submitted diff to an ephemeral artifact and invokes the
unchanged staged, editable-path-restricted, atomic source backend. Semantic
`I/S` retain the unchanged compact-context, Motion v1, capability, type, effect,
and atomic patch backends.

All five source references and all five semantic references pass the same hidden
evaluators. Invalid source arity, empty patches, and malformed diffs reject
without changing the workspace.

## Static surface result

The measurement counts exact UTF-8 context plus the same canonical tool
definition for each task.

| Surface across five tasks | Source session | Semantic session | Semantic change |
| --- | ---: | ---: | ---: |
| Context | 5,060 B | 13,097 B | +158.83% |
| Identical tool definitions | 1,345 B | 1,345 B | 0% |
| Initial context + tool | 6,405 B | 14,442 B | +125.48% |
| Reference submit payloads | 9,337 B | 2,290 B | −75.47% |

Every individual semantic initial surface is larger, and every semantic submit
payload is smaller. This is the trade-off the prior unpaired comparator had
hidden: semantic state costs more to disclose, while semantic change intent is
substantially denser than a unified diff.

## The deliberately incomplete transport proxy

For diagnostic purposes, the slice also adds initial surface and known-reference
submission costs. The semantic side includes its `I` instruction and 6,418 bytes
of inspection responses; the source side includes no `W` instruction or
workspace-read response:

| Partial known-reference proxy | Bytes |
| --- | ---: |
| Source lower bound | 15,742 B |
| Semantic with inspection | 23,256 B |
| Semantic overhead | +47.73% |

All five tasks have the same direction under this partial proxy. It is not a
matched trajectory and cannot support a representation claim. A source agent
cannot construct these diffs from task text alone; it must observe repository
content. Charging semantic observation while assigning zero bytes to source
observation intentionally produces a lower bound for source, not a fair result.

## What this checkpoint establishes

- The one-tool ISA is not a semantic-only optimization.
- Shared delivery infrastructure is now matched exactly.
- Semantic initial state is the dominant static overhead.
- Semantic mutation payload is the dominant output advantage.
- Both mutation paths retain their previous atomicity and evaluator behavior.
- The earlier 11.27% win survives only as an engineering comparison to the
  obsolete verbose interface, not as evidence against a matched source arm.

## Claim boundary

- No model/provider call occurred or is authorized.
- UTF-8 bytes are not provider tokens.
- Known reference patches were used to construct both submission instructions.
- Source observation, model reasoning, repair, history, provider wrappers, and
  runtime latency remain unmeasured.
- The partial transport proxy is asymmetric by construction and is not an
  efficacy or efficiency comparison.
- The unsupported cross-module task remains outside the five supported pairs.

## The next red test

Match observation cost before deciding whether the interface is ready to freeze.
For each known reference, construct the minimum deterministic source observation
through `L/W` needed to recover the editable inputs and compare it with the
existing semantic `I` request/response. Count instruction and response bytes on
both sides, then combine:

```text
initial surface + observation exchange + reference submit
```

The test must preserve identical tool schema and evaluators, disclose the
reference-informed read policy, and report sensitivity to reading one editable
file versus the whole workspace. No model call is authorized.

Only a matched observation surface can determine whether the next step is an
execution freeze, further state/inspection compaction, or an amortization curve.

The sequence advances to:

`session ISA → matched source ISA → matched observation surface`.

### Subsequent result

Matched Observation Surface v1 now charges source `L/W` and semantic `I` on
both sides. Under the favorable source policy of listing once and reading only
the reference-touched editable file, semantic totals 23,256 versus 27,762
bytes, a 16.23% reduction, and is smaller in all five pairs. Whole-workspace
source reading increases the semantic margin to 32.34%. The construction gate
therefore advances to a fresh execution freeze; no model-efficacy claim follows.
