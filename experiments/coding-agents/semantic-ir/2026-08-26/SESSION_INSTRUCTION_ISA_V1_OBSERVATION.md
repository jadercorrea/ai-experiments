# Semantic Session Instruction ISA v1

## Status

**Construction valid and local initial-surface break-even achieved. One
model-facing session instruction preserves the eight required operations,
delegates semantic inspection and submission to the unchanged Motion v1 and
canonical backends, passes all five hidden references, and measures 11.27%
below the corresponding source surface. No provider-token, model-efficacy, or
whole-trajectory claim is authorized.**

The deterministic construction bundle contains 21 files with tree digest
`6e2fa6ac16ec29960347ab9e9332670a33abdef9f9d43dd0cea7c0068e4e3641`.
It consumes the Motion Lexicalization v1 bundle with tree digest
`50257fa1bd03d4f9868e6bf8bd7b791edb2fc9aa3e011c9a01e59edbd4228bac`.

## The isolated change

Motion v1 made replacement intent compact, but the model still received eight
verbose tool definitions and English instructions describing how they fit
together. This slice changes only the delivery interface:

```text
one x instruction: {i: opcode, a: positional operands}
      ↓ strict session decoder
legacy context/workspace/evaluator adapters OR semantic I/S path
      ↓ unchanged Motion v1 decoder
canonical capability patch and validators
```

The session instruction set is:

| Opcode | Operands | Existing operation |
| --- | --- | --- |
| `C` | none | list context artifacts |
| `R` | context handle | read context artifact |
| `I` | node handles | inspect semantic targets |
| `L` | none | list workspace files |
| `W` | path | read workspace file |
| `E` | none | run public evaluator |
| `S` | patch ID, state token, positional operations | submit semantic motion patch |
| `F` | none | finish submission |

`I` and `S` execute through the compact-context and Motion v1 stores. The six
remaining opcodes dispatch to the same legacy operation adapters. One tool
schema constrains the opcode and outer operand array; the complete per-opcode
arity and Motion grammar is disclosed in the context and enforced by the
trusted decoder.

The persistent program, outline, target and state capabilities, lexical scope,
catalog, types, effects, atomicity, evaluators, and lowering remain unchanged.
This is an instruction-set boundary between agent and infrastructure, not a new
general-purpose programming language and not machine code for the target CPU.

## Experimental-TDD result

The construction gate required:

1. the same five reference patches and negative semantic fixtures;
2. unchanged target, scope, catalog, type, effect, capability, and atomicity
   checks;
3. task + outline + full ISA legend + complete callable interface below the
   16,277-byte source surface;
4. explicit accounting for grammar or wrappers outside the prompt; and
5. zero model calls until a separate execution freeze.

All five parts pass at the construction boundary. Every task independently
crosses its source comparator, rather than relying on one small task to offset
another.

The decoder rejects invalid envelope shape, opcode arity, malformed positional
operations, stale target capabilities, and every error already rejected by
Motion v1. All eight opcodes have an executable dispatch path. All five
semantic references preserve target-root identity and pass their existing
hidden evaluators.

## Local byte-surface measurement

The measurement counts exact UTF-8 context bytes plus canonical JSON tool
definitions. It is not provider tokenization.

| Surface across five tasks | Motion v1 | Session ISA v1 | Source comparator |
| --- | ---: | ---: | ---: |
| Context | 14,937 B | 13,097 B | included below |
| Tool definitions | 19,035 B | 1,345 B | included below |
| Context + complete tools | 33,972 B | 14,442 B | 16,277 B |
| Submit payloads | 3,032 B | 2,290 B | — |

Session ISA reduces the Motion v1 initial surface by 57.49% and crosses local
source break-even with an aggregate margin of 1,835 bytes, or 11.27%. Individual
session surfaces range from 2,824 to 2,990 bytes; their source comparators range
from 3,227 to 3,279 bytes. Positional submission reduces Motion v1 payload bytes
by another 24.47%.

This is the first construction checkpoint in the sequence where the complete
semantic initial surface is smaller than its local source comparator.

## Comparability boundary

The source comparator is the previously frozen capability-v2 source interface.
It was not rewrapped in the same one-tool session ISA. Of the 19,530-byte
reduction from Motion v1 to Session ISA v1, 17,690 bytes, or 90.58%, come from
tool-definition consolidation that could also benefit a source-editing arm.

The 11.27% break-even is therefore a valid engineering feasibility gate: a
semantic interface can be made smaller than the existing source interface
without removing its grammar or capabilities. It is not evidence that semantic
IR is smaller than source under matched delivery infrastructure.

A model comparison between the new semantic ISA and the old source tool surface
would confound representation with shared protocol compaction. That comparison
must not be launched.

## Nothing was hidden for the byte win

The measured initial surface includes:

- system instruction;
- exact task text;
- canonical compact outline and catalog tuples;
- the complete eight-opcode legend and operand grammar;
- the one callable tool definition; and
- context delimiters.

The decoder implementation is trusted infrastructure and is not model input,
just as the legacy tool implementations and source patch applicator were not
model input. The slice explicitly excludes provider request wrappers,
conversation history, tool responses, and future turns. The provider's unknown
serialization overhead has not been silently assigned a zero-byte causal
effect; it is outside this local construction metric.

Progressive semantic inspection responses total 6,418 bytes across the five
reference trajectories. They are dynamic output and are not part of the
initial-surface gate. A whole-trajectory provider comparison must count them,
repeated static context, errors, and every subsequent request.

## The decisive trade-off

The previous recursive tool schema could constrain much of the output grammar
during generation. Session ISA v1 moves opcode-specific operand validation from
the provider-visible JSON Schema into the deterministic decoder, while keeping
the grammar visible as compact context.

This produces the measured byte reduction, but it may increase malformed first
attempts if the model benefits substantially from schema-guided decoding. The
construction cannot decide that trade-off. Pass@1, repair calls, input/output
tokens, and latency require a frozen model-facing run.

## Claim boundary

- No model or provider call occurred or is authorized.
- The exact five references were known during construction.
- The eight opcodes are executable, but no model selected or emitted them.
- Local UTF-8 break-even is not provider-token or whole-trajectory break-even.
- The generic operand array weakens provider-side grammar masking; its observed
  reliability is unknown.
- The unsupported cross-module task remains outside semantic applicability.

## The next red test

Construct a matched source session control before freezing any new execution.
The source arm must use the same `x({i,a})` envelope, compact common opcode
legend, dispatcher, task text, workspace operations, evaluator boundary, and
finish semantics. Only the mutation-specific operands may differ: positional
source replacement versus semantic inspect plus Motion submission.

That construction must report both arms' complete initial surfaces and prove
their existing reference patches still pass the same hidden evaluators. If the
semantic arm does not beat the rewrapped source arm, retain that result rather
than comparing against the obsolete verbose control.

Only after a matched control exists should an execution freeze bind fresh task
bytes, exact renderers, tool contracts, model and inference policy, budgets,
schedule, provider wrapper accounting, evaluator boundary, and stopping rule.
A separately authorized Calibration 004 can then test whether any construction
result survives complete trajectories:

- hidden-evaluator outcomes in the six-task denominator;
- invalid instruction and repair rates;
- provider-native input and output tokens;
- dynamic inspection cost;
- requests, latency, and cost; and
- source versus session-ISA whole-trajectory break-even.

The Experimental TDD sequence is now:

`compact context → motion lexicalization → session ISA → matched source ISA → execution freeze`.
