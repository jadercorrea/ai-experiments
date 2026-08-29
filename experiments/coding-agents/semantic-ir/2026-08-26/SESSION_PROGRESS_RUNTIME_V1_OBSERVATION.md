# Session Progress Runtime v1

## Status

**The Terminal Reserve contract now has a parallel executable request and
dispatch path. It preserves all 110 frozen work-phase requests byte for byte,
accepts all eleven known-reference mutations in the commit phase, terminates
all eleven callable sessions in the reserved finish phase, and preserves the
existing 6/6 source plus 5/5 supported semantic hidden-reference passes. A
synthetic finish-phase `I` escape is returned as the typed recoverable error
`session_progress_opcode_unavailable` without dispatching the instruction.
No provider or model call occurred.**

The 12-file evidence package is content-locked with tree digest
`4e3855cdb29651868f6bf321f421e1af894d06f530ba556ab6230e1a572145d1`.
It depends on the exact Calibration 006 freeze while leaving its runner and
all frozen assets unchanged.

## What was implemented

The candidate path is a parallel adapter, not a mutation of the Calibration
006 runner:

1. build the existing coverage-compacted request;
2. derive a progress contract from the trusted session snapshot for the
   current turn;
3. project that contract into the `x.i` enum before sampling;
4. validate the returned instruction against the same contract before
   dispatch; and
5. return an escaped opcode as a typed recoverable tool result.

Internal contract corruption is not recoverable. A malformed or
self-inconsistent progress contract propagates as an infrastructure error
instead of being misclassified as a subject mistake.

## The surface correction found by the gate

The first replay implementation described source and semantic as having
different open-phase opcode sets. That was the logical runtime distinction,
not the frozen wire distinction. Calibration 006 deliberately used one exact
shared tool schema:

`C R I L W E S F`

Source cannot execute `I`, but the provider saw it in the matched interface.
The work-phase equality gate therefore failed until the progress contract
preserved the shared enum in both arms. The rebuilt replay retains all original
conflict counts: ten commit-phase cell conflicts, ten finish-phase cell
conflicts, 26 conflicting recorded instructions, and first divergence at turn
eleven in all ten exhausted cells.

## Local gates

| Gate | Result |
| --- | ---: |
| Callable cells | 11 |
| Frozen work requests projected, turns 1–10 | 110 |
| Byte-identical work requests | 110 / 110 |
| Reference mutations accepted at turn 11 | 11 / 11 |
| Sessions terminated with `F` at turn 12 | 11 / 11 |
| Source hidden-reference passes | 6 / 6 |
| Supported semantic hidden-reference passes | 5 / 5 |
| Unsupported semantic cells retained | 1 |
| Reference failures | 0 |
| Model calls | 0 |

The reference trajectory deliberately delays the known valid mutation until
turn eleven and `F` until turn twelve. Semantic references perform their
required inspection during the still-open work phase. References and hidden
evaluators are trusted local gate inputs only; neither is projected into a
provider request.

## Typed schema escape

The request-time enum is the primary control, but provider adherence remains
an open assumption. The local negative gate injects `I` after presenting an
`F`-only finish schema. The backstop:

- records the attempted tool as `x`;
- returns `session_progress_opcode_unavailable`;
- marks the result recoverable;
- performs no instruction dispatch; and
- leaves the session unfinished.

This demonstrates containment after an escaped sample. It does not recover the
provider turn already consumed by that sample. Calibration 007 must therefore
record schema escapes separately from ordinary tool-request errors.

## What this establishes

1. The state-dependent vocabulary is executable against the existing session
   state and dispatcher.
2. Its open phase does not introduce an accidental model-visible delta.
3. Both representations can still carry their exact known references through
   the two reserved phases.
4. Request-time masking and runtime validation agree on the terminal surface.
5. The frozen Calibration 006 implementation remains reproducible and
   unchanged.

## Claim boundary

- This is a local known-reference construction gate.
- No provider choice or schema adherence was observed.
- The use of references proves runtime reachability, not model reachability.
- No Pass@1, token, latency, cost, or convergence improvement is claimed.
- The source and semantic workspaces are evaluated locally with the existing
  hidden evaluators.
- Calibration 007 is not yet frozen or authorized.

## The next red test

Freeze a matched Calibration 007 package around a new runner that consumes
this adapter. It must preserve Calibration 006 task, context, model, sampling,
limits, schedule, accounting, memory policies, and stopping rule while changing
only the progress projection and its typed escape accounting. The 110-request
work-surface equality gate and all eleven terminal-reference trajectories must
be repeated from the candidate freeze itself.

Only after the freeze, contamination audit, artifact lock, and separate launch
contract pass should a provider execution be considered. The empirical
question remains narrow:

`does the provider use a structurally reserved terminal opportunity
productively?`
