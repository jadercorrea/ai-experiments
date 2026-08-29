# Session Progress Control v1

## Status

**Local fixed-trace replay complete. Calibration 006 did not lack a turn
budget: every compact state after turn one already exposed
`remaining_turns`. The missing layer was authority. Nothing converted that
fact into a smaller legal action surface as exhaustion approached. Terminal
Reserve v1 leaves both arms unchanged through turn ten, restricts turn eleven
to the still-budgeted subset of `E` and `S` plus `F`, and restricts turn twelve
to `F`. Applied to the recorded trace, the candidate finds 26 incompatible
instructions across the ten turn-limit cells and would first diverge at turn
eleven in all of them. This
proves that the policy is relevant to the observed failure mode. It does not
predict what the model would choose after divergence or that a valid terminal
submission would result.**

The replay is bound to Calibration 006's result and 333-file evidence lock. It
reads all 128 recorded provider turns, makes no model call, uses neither hidden
evaluator output nor reference patches, and writes a 13-file evidence package
with tree digest
`1be4425581976344a0b1949823140d4fba0e1d3af87c39d1bfa87cdc8eac8dbe`.

## The corrected diagnosis

The Calibration 006 state already carried these counters:

- current and next turn;
- remaining model turns;
- mutation attempts and remaining mutation attempts;
- public evaluations and remaining public evaluations;
- validation failures and whether the session had finished.

The model saw `remaining_turns: 1` in the final request of every full-length
cell and still emitted no `F`. Information alone was insufficient because the
tool schema continued advertising the complete opcode vocabulary.

This distinction matters for an agent-native ISA. A budget represented as data
is advisory. A budget represented as a state-dependent instruction set is
operational.

## Observed trace

| Measure | Calibration 006 |
| --- | ---: |
| Provider-call cells | 11 |
| Recorded provider turns | 128 |
| Turn-limit cells | 10 |
| Turn-limit cells ending with `F` | 0 |
| Supported semantic turn-limit cells | 5 / 5 |
| Source turn-limit cells | 5 / 6 |

One source cell finished at turn eight and never entered the reserve. The
unsupported semantic cell made no provider call. The remaining ten cells used
all twelve turns.

## The candidate contract

Terminal Reserve v1 applies identically to both matched arms:

| Remaining turns, including current | Phase | Allowed opcodes |
| ---: | --- | --- |
| 3 or more | `work` | Frozen arm-specific surface |
| 2 | `commit` | budgeted subset of `E`/`S`, plus `F` |
| 1 | `finish` | `F` |

The restriction is projected into the `i.enum` field of the existing `x` tool
before the request reaches the provider. Runtime validation repeats the check
as a backstop. This is not a new model-facing tool, a new patch language, or a
prompt telling the model to hurry. It is a dynamic ISA surface derived from
already-visible, trusted counters.

The commit phase advertises `S` only while mutation attempts remain and `E`
only while public evaluations remain. `F` is always available. This prevents
an already-exhausted effect from consuming the penultimate turn. The finish
phase removes inspection, workspace reading, context reading, evaluation, and
submission from the advertised vocabulary. It leaves only the terminal opcode.

## Fixed-trace conflicts

| Arm | Cells conflicting at `commit` | Cells conflicting at `finish` | Recorded instruction conflicts |
| --- | ---: | ---: | ---: |
| Source | 5 | 5 | 16 |
| Semantic | 5 | 5 | 10 |
| Total | 10 | 10 | 26 |

All ten trajectories first conflict with the candidate at turn eleven. Two
emit an `S` after their mutation-attempt budget has already reached zero; the
effect-aware commit surface excludes those calls. Every turn-limit trajectory
also conflicts with the finish-phase `F`-only surface.

The source conflicts are important. Terminal exhaustion is not peculiar to
semantic IR: five source cells also failed to finish. Applying the policy only
to the semantic arm would introduce exactly the kind of treatment asymmetry
this experiment has repeatedly learned to avoid.

Only the first disallowed action in each cell identifies a meaningful
counterfactual boundary. Recorded actions after that point belong to the
original trajectory and are retained only as diagnostics. The total of 26 is
therefore a surface-conflict count, not a claim that 24 future calls disappear.

## What this establishes

1. **The red test is about control, not observability.** Remaining budget was
   already visible and was ignored.
2. **The candidate intersects the failure before exhaustion.** Eight of ten
   full-length cells would receive a different action vocabulary while two
   turns still remain.
3. **Progress semantics belong in the ISA.** The legal vocabulary can depend
   on trusted execution state without asking the model to reconstruct policy
   from prose.
4. **The control must remain matched.** Source and semantic trajectories both
   exhibit terminal-budget violations.

This construction does not establish improved Pass@1, fewer provider turns,
lower cost, or provider compliance with the narrowed schema. Those are runtime
and provider questions.

## Relationship to the AI-native language hypothesis

The experiment adds a second meaning to “dense vocabulary.” It is not enough
for one token to mean `inspect` or `finish`. The set of tokens that can legally
follow must itself be a function of typed state.

Traditional source languages usually accept any syntactically valid statement
until a later checker rejects it. An agent-native ISA can make temporal
affordances first-class:

`vocabulary = f(phase, remaining budget, effects already consumed)`

That is closer to an instruction set with privilege levels than to a prompt.
The model does not merely read the control state; the runtime projects it into
the model's action space.

## Claim boundary

- This is a fixed-action replay over the exact Calibration 006 instances.
- No model or provider call occurs.
- The candidate trajectory is unknown after the first disallowed action.
- The request schema reserves an `F`-only opportunity; it does not guarantee
  that the provider emits a conforming call or that the workspace passes.
- Runtime validation can reject an escaped opcode but cannot recover a turn
  already consumed by sampling.
- No hidden-pass, latency, token, or cost improvement is claimed.
- The policy uses current counters only and has no future-action input.

## The next red test

Implement the contract as a parallel request projection without changing the
frozen Calibration 006 runner. Before any provider launch it must pass four
local gates:

1. preserve the complete source and semantic tool surfaces through turn ten;
2. mask both arms to the still-budgeted subset of `E/S` plus `F` at turn
   eleven, and `F` at turn twelve;
3. replay all known-reference patches with a mutation in the commit phase and
   a terminal instruction in the reserved phase;
4. record schema escape as a typed recoverable protocol error while keeping
   provider schema adherence an explicit open assumption.

Only then should a matched Calibration 007 freeze be constructed. Its narrow
hypothesis will be:

`a state-dependent ISA can reserve a terminal opportunity; whether the model
uses that opportunity productively remains an empirical provider question`.
