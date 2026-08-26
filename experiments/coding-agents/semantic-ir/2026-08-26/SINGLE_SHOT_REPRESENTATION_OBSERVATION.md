# Construction observation: source, JSON IR, and compact IR in one shot

## Outcome

The compact tuple/opcode representation preserved the checked semantic core and
passed the same public and hidden behavior as direct TypeScript and canonical
JSON IR. It reduced output tokens by **55.04%** and solution transport bytes by
**73.08%** relative to TypeScript. On this small task, however, total tokens were
effectively tied: compact IR used **2,022** tokens versus **2,009** for source,
a **0.65% increase**.

Canonical JSON IR was the clear loser. It used **4,487 total tokens**, 2.23 times
the source arm and 2.22 times the compact arm.

| Metric | TypeScript | Canonical JSON IR | Compact IR |
| --- | ---: | ---: | ---: |
| Provider requests | 1 | 1 | 1 |
| Input tokens | 1,751 | 3,542 | 1,906 |
| Output tokens | 258 | 945 | 116 |
| Total tokens | 2,009 | 4,487 | 2,022 |
| Cached input tokens | 0 | 0 | 0 |
| Solution transport | 650 bytes | 1,764 bytes | 175 bytes |
| Tool-argument envelope | 707 bytes | 1,776 bytes | 187 bytes |
| Tool schema | 126 bytes | 4,794 bytes | 137 bytes |
| Provider latency | 3.774 s | 10.480 s | 3.388 s |
| Estimated hosted cost | $0.009123 | $0.024801 | $0.007458 |
| Public evaluator | pass | pass | pass |
| Hidden evaluator | pass | pass | pass |

The lower estimated cost for compact IR despite near-identical total tokens is
not contradictory: output tokens cost more than input tokens under the frozen
pricing, and compact IR moved the balance sharply toward input.

These are descriptive measurements from one contaminated construction task and
one trajectory per arm. They do not estimate a population effect or authorize
an efficacy claim.

## Controlled boundary

Every arm received byte-identical messages containing the task, initial public
workspace, public tests, and closed symbol catalog. Each arm used the same
Claude Sonnet 4.6 endpoint, temperature zero, and output budget. There were no
navigation tools, test results, correction turns, or retries. The only changed
surface was one forced terminal tool:

- TypeScript submitted the complete replacement source;
- JSON IR submitted the canonical checked program tree;
- compact IR submitted a task-bounded tuple/opcode tree.

The compact decoder supplied fixed ABI metadata and stable identities, decoded
the tuple tree into the canonical JSON IR, and then invoked the same semantic
validator and deterministic TypeScript lowerer used by the JSON arm. It did not
bypass types, effects, lexical resolution, or the closed catalog.

## What the result distinguishes

### JSON is useful, but it is not the agent-native wire format

The JSON object remains valuable as a canonical interchange, debugging, and
evidence representation. Its named fields make every semantic distinction
inspectable. Those same field names, repeated node headers, IDs, and general
schema definitions are expensive to transmit through a text-token API.

The compact form represented the same accepted program in 175 bytes instead of
1,764 bytes and required 116 output tokens instead of 945. The large loss in the
earlier experiment therefore came substantially from serialization and schema
envelope, not from semantic structure itself.

### Compact output density is real; whole-request savings are not established

The compact arm's fixed request was 417 bytes larger than the source request
because it still had to explain the opcode grammar. The provider charged 155
more input tokens before generation began. The 142-token output saving nearly,
but not completely, repaid that fixed input cost on this tiny function.

This is the crucial break-even result. A compact semantic representation can be
denser than source while the complete interaction is not yet smaller. Grammar
amortization, server-side contracts, prompt caching, larger outputs, semantic
patches, or tokenizer-native opcodes could move that boundary. This observation
does not assume that they will.

### Cost and latency moved before total tokens did

Compact IR cost 18.25% less and returned 10.23% faster than source in this one
run. JSON IR cost 2.72 times as much and took 2.78 times as long as source. These
single latency and cost samples are descriptive and especially unsuitable for
generalization, but they show which measurements a larger experiment should
retain alongside raw token totals.

## Invalid observation 001

The first single-shot execution is preserved and explicitly invalidated. The
source arm completed, but the JSON model added `capabilities` as a second
semantic parameter. The lowerer reserves that name because capabilities are
compiler-supplied. Since the protocol permitted one attempt and no repair, the
runner stopped before compact IR.

This was an output-contract defect rather than behavioral evidence. For
observation 002, the JSON tool schema fixed the task ABI: `rawId` is the only
semantic parameter, while capabilities remain a lowering concern. The failed
run was not pooled into the valid comparison.

## Interpretation

For this slice, the answer is:

> JSON IR serves as the canonical semantic object, while a compact graph/tree
> encoding serves better as the model-facing transport.

A graph database or binary format is not yet required. The compact object is
still a tree encoded in JSON arrays because that is what the provider tool API
accepts. The architectural separation matters more than the container:

```text
model-facing compact transport
             ↓ decode
canonical typed semantic graph/tree
             ↓ validate + lower
TypeScript / WASM / native targets
```

The next experiment should test the break-even curve rather than add arbitrary
language features: use several fresh tasks with increasing solution size,
freeze the compact grammar once, and measure when its fixed input overhead is
amortized. A semantic-patch arm should then test whether editing a persistent
graph is cheaper than retransmitting complete programs.

## Evidence

- [`single-shot-representations-001`](observations/single-shot-representations-001)
  contains the invalid ABI-underspecification run.
- [`single-shot-representations-002`](observations/single-shot-representations-002)
  contains the valid requests, responses, gateway events, final workspaces, and
  evaluator results.
- [`single-shot-comparison-v0-002.json`](construction/single-shot-comparison-v0-002.json)
  freezes the valid observation protocol.
- [`single_shot_comparison.py`](scripts/single_shot_comparison.py) implements the
  one-request runner.
- [`compact_ir.py`](scripts/compact_ir.py) implements the compact-to-canonical
  decoder.
- [`user-lookup.compact.json`](examples/user-lookup.compact.json) is the compact
  example for this construction task.
