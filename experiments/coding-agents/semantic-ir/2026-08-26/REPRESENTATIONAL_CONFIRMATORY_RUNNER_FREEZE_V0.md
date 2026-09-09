# Representational confirmatory runner freeze v0

## Status

**One condition-agnostic Session ISA runtime is now sealed against the exact
240-task confirmatory cohort. All 960 cells passed a complete provider-free
reference replay. Bedrock access, current rates, explicit authorization, and
the first model dispatch remain deliberately blocked.**

This checkpoint turns the execution contract into an operational boundary. It
does not measure model behavior. The “participant” in the preflight is a
deterministic reference trajectory used to prove that every frozen condition
can traverse the same infrastructure before money or confirmatory evidence is
at risk.

## What the runner now does

For each scheduled cell, the runner creates a new session and copies only the
sealed baseline repository into a new ephemeral workspace. The session begins
with empty history and exposes one shared positional `x` instruction surface:

1. `C` lists two participant-visible context artifacts;
2. `R` reads the frozen catalog or public cases by stable handle;
3. `I` returns the requested semantic targets in that cell's observation
   realization;
4. `L` and `W` list and read only the ephemeral workspace;
5. `S` validates and atomically applies a Motion v1 semantic submission;
6. `E` evaluates only the public cases; and
7. `F` closes the session before the runner invokes the hidden evaluator once,
   without returning its result to the participant.

Condition identity remains orchestration metadata. It selects one frozen codec
configuration, but never appears in participant requests or tool results. The
same dispatcher, mutation path, evaluator implementation, limits, and opcode
trajectory are used for all four cells.

## Provider-free replay result

The replay executed the fixed sequence `C R R I L W S E F` in every cell. Its
aggregate result is:

- 960/960 initial requests reconstructed to their frozen canonical digest;
- 2,880 turn requests built and translated locally, including 1,920
  post-turn-one requests carrying authoritative typed state instead of a chat
  transcript;
- 960 unique session identities and 960 unique fresh workspace identities;
- 960/960 observation surfaces decoded back to the canonical inspection;
- 960/960 reference submissions accepted through Motion v1;
- 960/960 public evaluations passed;
- 960/960 hidden evaluations passed after `F`;
- zero hidden evaluations admitted before `F`;
- zero factorial condition labels found in participant-facing tool results;
- zero factorial condition labels and zero tool-schema drift across all 2,880
  locally translated turn requests;
- four-condition final-program, workspace, public-evidence, and
  hidden-evidence equivalence in all 240 tasks; and
- zero model calls, provider requests, or provider cost.

The preflight persists one compact result row per cell. Ephemeral workspaces
are deleted after their digest and evaluation evidence are recorded, so the
locked artifact is about 1.9 MB rather than another full replication of the
cohort.

## Cost stop

The executable pre-dispatch guard was replayed with the frozen rates and token
limits. A maximum-size first request reserves USD 0.258048 beneath the USD 350
ceiling. The same request beginning at USD 349.75 is rejected before dispatch.

This proves the local arithmetic and stop behavior only. The ceiling is not a
launch authorization, and the frozen rates must be checked again against the
provider immediately before launch.

## Claim boundary

- Provider-free reference trajectories observed: 960.
- Behavioral participant outcomes observed: 0.
- Model calls, provider requests, and provider cost: 0.
- Lexical, packaging, interaction, efficacy, and generalization claims: none.
- Bedrock access recheck: absent.
- Current-rate recheck: absent.
- Explicit launch record: absent.

## Evidence

- [`freeze.json`](construction/representational-confirmatory-runner-freeze-v0/freeze.json)
  binds the runtime, source freezes, preflight digest, gates, and claim boundary.
- [`preflight/result.json`](construction/representational-confirmatory-runner-freeze-v0/preflight/result.json)
  records the 960 compact cell results and aggregate invariants.
- [`representational_confirmatory_session.py`](scripts/representational_confirmatory_session.py)
  implements the isolated Session ISA boundary.
- [`build_representational_confirmatory_runner_freeze.py`](scripts/build_representational_confirmatory_runner_freeze.py)
  reconstructs requests, replays every cell, audits equivalence, and locks the
  artifact.
- [`test_representational_confirmatory_runner_freeze_v0.py`](../../../../tests/test_representational_confirmatory_runner_freeze_v0.py)
  tests the hidden boundary, full replay, deterministic rebuild, and content
  lock.

## Next red test

Recheck Bedrock access and the current rate card, then bind both observations
to a separate explicit launch record. Only after that record exists may a
zero-cost or minimum-cost single-cell dispatch canary test the provider path;
the remaining 959 scheduled cells stay blocked until the canary is accepted.
