# Semantic Motion Lexicalization v1

## Status

**Construction valid; break-even gate failed. A flat eight-word motion
vocabulary reconstructed semantically equivalent canonical patches for all five
supported tasks, passed all five hidden evaluators, reduced patch payload bytes
by 61.27%, and reduced tool-definition bytes by 50.15%. Context plus tools still
measured 2.09 times the source surface. No model or provider-token claim is
authorized.**

The deterministic bundle contains 21 files with tree digest
`50257fa1bd03d4f9868e6bf8bd7b791edb2fc9aa3e011c9a01e59edbd4228bac`.
It consumes the frozen Compact Context v1 bundle with tree digest
`fab0f9be5d526b44b1f4849620846d32d602512ae712da092ec127fec9a62bb9`.

## The isolated change

Compact Context v1 changed state disclosure but deliberately retained the
recursive `semantic_patch_submit` grammar. This slice changes only the
model-facing realization of replacement intent:

```text
flat motion words
      ↓ deterministic decoder
canonical replacement AST
      ↓ unchanged capability resolver
checked atomic semantic patch
      ↓ unchanged validator/lowerer
target program
```

The persistent program, catalog semantics, stable target identity, opaque state
and target preconditions, type/effect validation, atomicity, and target lowering
remain unchanged.

The finite vocabulary is:

| Word | Arguments | Canonical realization |
| --- | --- | --- |
| `str` | value | string literal |
| `var` | scope or binding slot | stable symbol reference |
| `call` | catalog symbol, argument refs | checked catalog call |
| `let` | binding, value, continuation | lexical binding |
| `if` | condition, then, else | total conditional |
| `match` | value, binding, none, some | total option match |
| `ok` | value | successful result |
| `err` | error | error result |

Motions form a flat, reference-addressed tree rather than recursively nested
JSON expressions. `s0...` addresses exact external scope slots returned by
inspection; `b0...` names local bindings whose stable symbol identities are
created by trusted infrastructure. Replacement root identity is always derived
from the inspected target. Descendant node and binding identities are generated
deterministically.

“Lexicalization” is used here in a deliberately narrow engineering sense: a
semantic event structure is packaged into a small set of realization words.
The analogy follows the earlier handoff protocol's separation of propositions
from linguistic realizations. This construction makes no claim about natural-
language cognition or multilingual model behavior.

## Experimental-TDD result

The preregistered construction gate had four parts:

1. round-trip all five supported references;
2. reject invalid opcode, arity, type, scope, effect, and target precondition
   before mutation;
3. cross local source initial-surface break-even; and
4. authorize no model call before a separate freeze.

Parts 1, 2, and 4 pass. Part 3 fails.

All reference motions resolve through the existing capability protocol and pass
the existing hidden evaluators. The negative fixtures reject an unknown word,
wrong word arity, a binding used outside its branch, an invalid result type, a
stale effect declaration, and a mismatched target capability. Rejection leaves
the immutable canonical base unchanged.

## Local byte-surface measurement

The measurement canonicalizes structured values and counts exact UTF-8 bytes.
It is a transport proxy, not provider tokenization.

| Surface across five tasks | Recursive patch | Motion v1 | Change |
| --- | ---: | ---: | ---: |
| Context | 13,647 B | 14,937 B | +9.45% |
| Tool definitions | 38,185 B | 19,035 B | −50.15% |
| Context + tools | 51,832 B | 33,972 B | −34.46% |
| Patch payloads | 7,828 B | 3,032 B | −61.27% |
| Corresponding source context + tools | — | 16,277 B | Motion is 2.09× |

The context grew because a usable motion vocabulary and addressing rules had to
be disclosed. The mutation tool shrank from 5,613 to 1,784 canonical bytes per
task; the remaining seven tools occupy 2,023 bytes per task. Every task reduced
its full recursive semantic surface by roughly 34%, and none reached source
break-even.

The result is stronger than “JSON IR is verbose.” The motion payload itself is
compact. The remaining initial cost is protocol disclosure:

- motion context: 14,937 aggregate bytes;
- tools excluding motion submission: 10,115 bytes; and
- motion submission definition: 8,920 bytes.

Even a zero-byte submission schema would leave context plus the other tools at
25,052 bytes, 53.91% above the entire source surface. Motion lexicalization is
therefore necessary for this design but mathematically insufficient to satisfy
the current break-even gate.

## Claim boundary

- No model call occurred or is authorized.
- The five exact reference patches were known during construction.
- UTF-8 byte reductions are not token reductions.
- A deterministic encoder produced the observed motions; model production,
  repair, Pass@1, latency, and comprehension remain unmeasured.
- Semantic equivalence is bounded to the existing five hidden evaluators and
  canonical validators, not all possible programs.
- The unsupported cross-module task remains outside semantic applicability.

## The next red test

Do not widen the canonical language. Compress the end-to-end interaction
protocol while preserving this decoder and all checked semantics. The next
slice should test a session-level semantic instruction interface that avoids
repeating English mode prose and multiple verbose JSON tool contracts on every
turn.

The next gate should require:

1. the same five lexicalized reference patches and negative fixtures;
2. the same exact target, scope, type, effect, and atomicity boundaries;
3. context plus the complete callable interface below 16,277 aggregate bytes;
4. explicit accounting for any grammar, tokenizer, or provider wrapper moved
   outside the measured prompt; and
5. zero model calls until a separately frozen interface passes construction.

This advances the sequence without hiding the failed assertion:

`compact context → motion lexicalization → session instruction ISA`.
