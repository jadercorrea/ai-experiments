# Representational confirmatory cohort v0

## Status

**All 240 predeclared confirmatory task units and their 960 exact initial
requests passed the complete provider-free construction pipeline. Participant
execution and behavioral claims remain blocked.**

The cohort contains 48 tasks in each of the five frozen mechanism families.
Every accepted task has one baseline repository, transactional reference,
public and hidden evaluators, canonical observation, and four lossless
factorial realizations.

## Selection result

Construction followed the immutable first-eligible rule in slot order:

- 235 previously untouched slots selected attempt 0;
- the five `*-001` slots exposed by the engineering smoke selected their
  predeclared attempt 1;
- zero candidates were rejected;
- zero slots were exhausted, manually substituted, or reallocated; and
- all 240 selected candidates passed local eligibility.

The absence of rejections is an observed construction result, not permission to
skip the rejection machinery. The builder retains failed candidates and their
reason if a later deterministic rebuild encounters one.

## Local eligibility

Every task passed the same checks proven by the smoke slice:

1. deterministic materialization from its frozen slot and attempt seed;
2. program, catalog, type, effect, and Session ISA vocabulary closure;
3. reference success and baseline discrimination on public and hidden cases;
4. byte-identical canonical round-trip across all four realizations;
5. meaningful/opaque lexical-skeleton equality within each packaging level;
6. participant-context isolation and cross-task uniqueness; and
7. an individual content lock over the complete retained task evidence.

The outer cohort lock recursively covers all 240 task locks and the construction
checkpoint.

## Exact-request audit

The frozen constructor generated all 960 initial requests and translated each
through the frozen Bedrock Converse adapter. The audit found:

- 960 unique canonical request digests;
- zero matches against 867 historical request artifacts representing 832
  unique canonical requests;
- zero matches against the twenty development-smoke requests;
- zero duplicates inside the confirmatory cohort;
- no visible factorial condition identifier; and
- exact preservation of the shared `x` tool schema in every translation.

All request fields outside the condition-specific system content are identical.
This isolates the intended observation realization while holding model,
sampling, instructions, tool transport, limits, and workspace semantics fixed.

## Evidence by reconstruction

The first complete build retained every OpenAI-compatible request, Bedrock
translation, and four replicated participant trees. It occupied 134,236 KiB
and 12,963 files. Those copies are deterministic products of already locked
task inputs.

The accepted artifact therefore retains the input files plus both exact
digests, not duplicate payloads. The test suite reconstructs all 960 participant
requests and all 960 Bedrock translations and checks them against those hashes.
This reduces the artifact to 49,652 KiB and 4,323 files—a 63.01% checkout
reduction—without weakening request identity or reproducibility.

An interrupted build is also resumable. Each task is moved into the cohort only
after its nested lock passes, and the checkpoint advances atomically afterward.
Resume rejects source drift and verifies the exact completed protocol prefix
before constructing the next slot.

## Claim boundary

- Confirmatory tasks created: 240.
- Confirmatory condition realizations and exact initial requests created: 960.
- Behavioral outcomes observed: 0.
- Model calls, provider requests, and provider cost: 0.
- Lexical, packaging, interaction, efficacy, and generalization claims: none.
- Launch authorization: absent.

## Evidence

- [`result.json`](construction/representational-confirmatory-cohort-v0/result.json)
  records selection, request audits, gates, and all task/request identities.
- [`tasks`](construction/representational-confirmatory-cohort-v0/tasks) contains
  the 240 individually locked task evidence trees.
- [`checkpoint.json`](construction/representational-confirmatory-cohort-v0/checkpoint.json)
  records the exact completed protocol prefix.
- [`build_representational_confirmatory_cohort.py`](scripts/build_representational_confirmatory_cohort.py)
  implements resumable selection, materialization, compaction, reconstruction,
  request audit, and nested verification.
- [`test_representational_confirmatory_cohort_v0.py`](../../../../tests/test_representational_confirmatory_cohort_v0.py)
  reconstructs every request and translation and tests interrupted resume.

## Next red test

Implement and content-lock the confirmatory session runner against this exact
cohort. Its provider-free preflight must reconstruct and match all 960 request
digests, prepare fresh workspaces and empty histories for every scheduled cell,
exercise tool dispatch and evaluator boundaries without inference, and prove
the USD 350 pre-dispatch stop. Bedrock access and rates must then be rechecked,
followed by a separate explicit launch record before the first model call.
