# Compact Semantic Context v1

## Status

**Construction valid and complete. A short-handle outline plus exact progressive
inspection preserved all five supported reference patches and reduced the
aggregate initial semantic context by 83.19%. The full initial surface did not
reach source break-even because the unchanged recursive semantic patch tool
schema now dominates the remaining input. No model or provider-token claim is
authorized.**

The deterministic construction bundle contains 21 files with tree digest
`fab0f9be5d526b44b1f4849620846d32d602512ae712da092ec127fec9a62bb9`.
It is bound to capability suite
`be3a565ac4aba5a618062dc2feb69cd8cc5f8b849c125ea72825dc19a6c9d3ab`
and execution freeze
`d8a3083ad2a08c5e66c5b10d61c390df6d75f42b7419a61f7906fe1896e8eab1`.

## The isolated change

Capability v2 embedded the complete canonical program, catalog, program schema,
patch schema, and optional expression grammar in initial context. Compact
Context v1 changes only how immutable semantic state is disclosed:

1. Initial context contains a short-handle topology with operation, parent,
   slot, and a small lexical hint for each node.
2. Catalog signatures and function effects remain visible in compact tuples.
3. `semantic_context_inspect` accepts selected handles and returns exact node
   identities, lexical scope, canonical subtrees, and the unchanged opaque state
   and target capabilities.
4. `semantic_patch_submit`, canonical program IR, validators, effects, lowering,
   and atomic mutation semantics remain unchanged.

Handles such as `n8` are projection-local addresses. They never replace stable
node identity in persistent state or patch application.

## Sufficiency evidence

All five supported capability-v2 references were rebuilt through the compact
surface and passed their existing hidden evaluators:

| Task | Nodes in outline | Inspected handles | Hidden result |
| --- | ---: | --- | --- |
| Error taxonomy | 15 | `n7`, `n12` | Pass |
| Normalization policy | 15 | `n1` | Pass |
| Raw-ID retry | 15 | `n8` | Pass |
| Reserved-ID guard | 15 | `n8` | Pass |
| Directory fallback | 15 | `n8` | Pass |

Inspection returned the exact canonical target subtree and every external
symbol visible at that lexical position. Reference patches then reused the
unchanged capability resolver and semantic backends. No digest entered the
model-facing outline or inspection response.

This proves deterministic representational sufficiency for the five known
references. It does not prove that a model can select the right handle or
construct the same replacement from this context.

## Local byte-surface measurement

The measurement canonicalizes structured tool definitions and counts context
text exactly as UTF-8. It is a local transport proxy, not provider tokenization.

| Surface across five tasks | Capability v2 | Compact v1 | Change |
| --- | ---: | ---: | ---: |
| Initial semantic context | 81,171 B | 13,647 B | −83.19% |
| Tool definitions | 38,330 B | 38,185 B | −0.38% |
| Context + tools | 119,501 B | 51,832 B | −56.63% |
| Corresponding source context + tools | — | 16,277 B | Compact is 3.18× |
| First inspection responses | 1,897 B | 6,418 B | +238.32% |

Every individual task reduced its initial context by more than 82% and its
complete initial semantic surface by more than 55%. None reached source
break-even.

The transfer is intentional: exact subtrees and lexical scope leave the static
context and appear only when requested. Progressive responses are therefore
larger, but static context is paid on every provider turn. A real trajectory
comparison is still required to determine whether that timing wins in tokens.

## What the failure teaches

After compaction, unchanged tool definitions account for 73.67% of the compact
initial surface. Almost all of that semantic-only overhead is the recursive
expression grammar embedded in `semantic_patch_submit`.

The result separates two costs that Calibration 003 had conflated:

- **state disclosure** can be made substantially smaller without abandoning
  canonical semantic state; and
- **mutation grammar disclosure** remains expensive even when state disclosure
  is compact.

Compact Context v1 therefore passes its construction test while deliberately
failing whole-surface break-even. Replacing the patch grammar inside this same
comparison would prevent attribution of the observed reduction.

## Claim boundary

- No model call occurred or is authorized by this construction artifact.
- UTF-8 bytes are not Claude or provider-native tokens.
- The five exact references were known during implementation.
- Handle selection, repair behavior, output tokens, latency, and Pass@1 remain
  unmeasured.
- Conversation-history accumulation and provider request wrappers are excluded.
- Deterministic issuer keys make the checked bundle reproducible; its opaque
  tokens are test fixtures and make no authorization or secrecy claim.
- The cross-module task remains outside semantic applicability.

## The next red test

Lexicalize the semantic patch protocol without changing canonical IR or checked
mutation semantics. The next candidate should replace the recursively expanded
model-facing expression schema with a compact, finite instruction surface that
deterministically constructs the same canonical replacement.

The test must require:

1. all five existing reference replacements round-trip to byte-identical or
   semantically identical canonical subtrees;
2. invalid opcodes, arity, types, scope, effects, and target identity are rejected
   before mutation;
3. the compact patch surface plus Compact Context v1 crosses local source
   initial-surface break-even; and
4. no model call is authorized until that interface is separately frozen.

This is the next Experimental TDD transition:

`capabilities → compact context → motion lexicalization`.
