# Semantic context calibration 002

## Status

**Execution valid and complete; representation efficacy, token-efficiency, and
repair-latency comparisons invalidated by a treatment-asymmetric semantic
precondition affordance. Raw evidence is retained. No replacement run is
authorized under this freeze.**

Calibration 002 executed all twelve cells under context freeze
`2fdc21e5ead53e466ac64048b081d51f7a8077de3f03a2a2340e14b59514b05a`.
The evidence lock contains 282 files with tree digest
`fc919cda119b33bb36746477b4d26a11fe881efe5c2d39f243cd02b528a89b8e`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 102 |
| Input tokens | 970,142 |
| Output tokens | 46,427 |
| Total tokens | 1,016,569 |
| Estimated cost | USD 3.606831 |
| Public evaluator runs | 15 |
| Repair cycles | 14 |
| Recoverable tool errors | 34 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 102 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. Provider usage sums, cell costs, schedule
identities, launch and freeze bindings, request exclusions, and the artifact
lock reconcile. No request contains a hidden-evaluator path, reference path,
credential identifier, bearer value, or Keychain reference.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 2 | 1 |
| Supported-task hidden Pass@1, denominator 5 | 2 | 1 |
| Provider requests | 45 | 57 |
| Input tokens | 200,909 | 769,233 |
| Output tokens | 16,405 | 30,022 |
| Total tokens | 217,314 | 799,255 |
| Estimated cost | USD 0.848802 | USD 2.758029 |

Under the frozen v1 protocol, the semantic arm used 3.68 times the all-task
tokens of source patching. Excluding the automatic zero-call unsupported cell,
it used 4.04 times the tokens of the corresponding five source cells.

Four source cells reached terminal submission; normalization-policy and
reserved-id-guard passed hidden evaluation, while error-taxonomy and
cross-module-rename failed it. Two source cells exhausted twelve turns.

One semantic cell, normalization-policy, reached terminal submission and passed
hidden evaluation. Four supported semantic cells exhausted twelve turns. The
cross-module semantic cell remained the predeclared automatic unsupported
failure.

These are true descriptions of this execution. They are not isolated evidence
that semantic structure itself is less accurate or intrinsically more
token-expensive.

## What v1 fixed

The defect from calibration 001 did not recur. Every embedded artifact had a
readable `context://` handle. No tool error involved an unavailable context path,
unknown context handle, or workspace/context namespace confusion. No cell was
classified as infrastructure-invalid.

The 34 recoverable tool errors were budget observations:

- 21 semantic mutation-attempt-limit rejections;
- 11 source mutation-attempt-limit rejections;
- one public-evaluation-limit rejection; and
- one per-turn tool-call-limit rejection.

This establishes the intended infrastructure result: a subject error now
remains evidence inside the trajectory rather than terminating the cell.

## Why the representation comparison is invalid

`semantic_patch_submit` requires the model to provide:

1. a canonical SHA-256 of the base program; and
2. a canonical SHA-256 of every target subtree.

Neither value was present in the initial semantic context. The context manifest
did expose a SHA-256 for the program artifact, but that digest covered the UTF-8
file bytes and differed from the canonical JSON digest required by the patch
validator. No exposed operation could calculate canonical program or subtree
digests.

The trajectories show the consequence directly. Subjects stated that they
could not compute the digest, submitted zeros or the visible byte digest, and
used rejection messages to discover the expected values. Those discovery
attempts consumed the same three-mutation budget intended for candidate repair.
The source arm had no equivalent cryptographic-precondition discovery burden.

For a one-operation semantic task, discovering the canonical program digest and
the subtree digest can consume two attempts before the first semantically
checkable mutation. A subsequent identity, type, effect, or behavioral repair
then requires a fourth attempt that the freeze forbids. Multi-operation tasks
can require still more discovery rejections. The comparison therefore mixes
representation quality with a treatment-specific missing capability.

Calibration 002 is valid as a test of the complete v1 interface and as evidence
that the addressability fix worked. It cannot isolate the semantic IR from its
incomplete optimistic-concurrency interface.

## The next red test

Cryptographic state preconditions belong to the deterministic execution layer,
not to model reasoning. The next protocol must expose opaque, exact precondition
tokens through the context surface—for example:

- a program-state token returned with `context://state/program`;
- node handles carrying the exact current subtree token; or
- a read-only semantic inspection operation returning target identity and
  concurrency token together.

The agent should select a target and construct a replacement. It should not
calculate, guess, or learn SHA-256 values by failing mutations. Reading immutable
preconditions must not consume mutation budget.

A new paired representation claim also requires another set of fresh exact task
instances because the provider has now seen the v1 inputs. Until that protocol
and suite are separately frozen, calibration 002 supports an infrastructure
finding, not a representation winner.
