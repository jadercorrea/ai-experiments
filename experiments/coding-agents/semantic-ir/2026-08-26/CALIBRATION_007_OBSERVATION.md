# Matched Progress-Session calibration 007

## Status

**Execution valid and complete as a repeated within-instance descriptive
calibration. Terminal Reserve v1 changed action selection but did not make
convergence reliable. `F` calls rose from one in Calibration 006 to seven,
valid terminals rose from one to four, and the source arm added one hidden
pass. Yet the five supported semantic cells still produced zero valid
terminals and zero hidden passes. Of ten cells reaching the reserved final
turn, six selected `F`: three were accepted and three were rejected because
the model attached arguments to the zero-argument instruction. The other four
did not select `F`. Total tokens rose 8.72% and estimated cost rose 9.26%. The
result rejects the strong hypothesis that opcode lexicalization alone makes a
terminal opportunity productive. The next red test is instruction-shape
lexicalization: phase-specific schemas must encode opcode arity and payload,
not only the opcode enum.**

Calibration 007 executed all twelve scheduled cells under freeze
`46f33d10f32dc3f5b3e523b9bf369eeffcb1ec9f0659ccae73ee3515f85f4551`.
Eleven cells called the locked model; the unsupported semantic cell remained a
zero-call local result. The evidence lock contains 458 files with tree digest
`6cf4e2cef1a4e8198562c232953ccab159f0a3f1bed21412591951307ec8fb4d`.

## Execution facts

| Measure | Observed |
| --- | ---: |
| Scheduled/completed cells | 12 / 12 |
| Provider-call cells | 11 |
| Successful provider responses | 127 |
| Input tokens | 447,457 |
| Output tokens | 39,927 |
| Total tokens | 487,384 |
| Estimated cost | USD 1.941276 |
| Public evaluator runs | 3 |
| Repair cycles | 4 |
| Infrastructure-invalid cells | 0 |
| Missing cells | 0 |

All 127 responses reported the locked model
`us.anthropic.claude-sonnet-4-6`. Provider usage, cell costs, schedule
identities, launch and freeze bindings, progress contracts, the exact shared
`x` tool, message roles, and the artifact lock reconcile. Request and evidence
scans found no reference, hidden-evaluator, keychain identity, bearer token, or
credential-shaped value.

The account-level Amazon Bedrock retention mode remains unreadable by the
inference-scoped credential and is not claimed. The launch records the current
public service-policy basis and this limitation.

## Raw outcomes

| Estimand | Source | Semantic |
| --- | ---: | ---: |
| All-task hidden Pass@1, denominator 6 | 2 | 0 |
| Supported-task hidden Pass@1, denominator 5 | 1 | 0 |
| Semantic applicability | — | 5 / 6 |
| Provider requests, all-task accounting | 67 | 60 |
| Input tokens, all-task accounting | 150,019 | 297,438 |
| Output tokens, all-task accounting | 16,761 | 23,166 |
| Total tokens, all-task accounting | 166,780 | 320,604 |
| Estimated cost, all-task accounting | USD 0.701472 | USD 1.239804 |

The automatic unsupported semantic cell costs zero, so the all-task resource
comparison understates the semantic overhead. Across only the five supported
pairs:

| Supported-task resource | Source | Semantic | Semantic change |
| --- | ---: | ---: | ---: |
| Provider requests | 55 | 60 | +9.1% |
| Input tokens | 128,942 | 297,438 | +130.7% |
| Output tokens | 13,850 | 23,166 | +67.3% |
| Total tokens | 142,792 | 320,604 | +124.5% |
| Estimated cost | USD 0.594576 | USD 1.239804 | +108.5% |
| Sum of cell durations | 209.08 s | 490.75 s | +134.7% |

## What terminal reserve changed

Calibration 007 changed only the request-time instruction surface shared by
both arms. Turns one through ten retained the complete `C/R/I/L/W/E/S/F`
vocabulary. Turn eleven exposed the still-budgeted `E/S` subset plus `F`.
Turn twelve exposed only `F`. Runtime validation remained authoritative when
the provider escaped the advertised schema.

| Measure | Calibration 006 | Calibration 007 | Realized change |
| --- | ---: | ---: | ---: |
| Provider requests | 128 | 127 | -0.78% |
| Total tokens | 448,311 | 487,384 | +8.72% |
| Estimated cost | USD 1.776825 | USD 1.941276 | +9.26% |
| `F` instructions | 1 | 7 | +6 |
| Valid provider-call terminals | 1 | 4 | +3 |
| Source all-task hidden passes | 1 / 6 | 2 / 6 | +1 |
| Semantic supported hidden passes | 0 / 5 | 0 / 5 | 0 |
| Repair cycles | 5 | 4 | -1 |

The unchanged source arm used 1.59% fewer total tokens than in Calibration
006, while the semantic arm used 14.98% more. Across both arms, total tokens
rose 8.72%. The reserve therefore did not pay for itself as a transport or cost
optimization in this run.

Because the trajectories are independently sampled, these deltas are realized
run differences rather than a causal decomposition. The added hidden pass came
from the source cross-module task; the source reserved-ID task had already
passed in Calibration 006 and again finished early in Calibration 007.

## The final-turn split

One source cell finished and passed hidden evaluation at turn seven. The other
ten provider cells reached the reserved turn-twelve surface:

| Final-turn outcome | Cells | Hidden passes |
| --- | ---: | ---: |
| `F` accepted | 3 | 1 |
| `F` rejected | 3 | 0 |
| Forbidden opcode rejected | 3 | 0 |
| Malformed instruction envelope rejected | 1 | 0 |

All three rejected `F` calls carried arguments even though `F` is a
zero-argument instruction. The dynamic tool schema advertised `i: enum [F]`
but described `a` only as an array. The provider therefore satisfied the
coarse JSON shape while violating the instruction's arity, which the runtime
correctly rejected.

The run also recorded twelve typed progress-schema escapes: nine during
`commit` and three during `finish`. Commit rejected six `W`, two `I`, and one
`S` instruction. Finish rejected one `I` and two `S` instructions. A fourth
non-`F` final response failed the ordinary instruction-envelope validator
rather than the progress-opcode gate.

Runtime validation protected the workspace from every invalid action. It did
not recover the already consumed provider turn. On the final turn, a
recoverable error is behaviorally terminal because no budget remains.

## Paired task observations

| Task | Source | Semantic |
| --- | --- | --- |
| Error taxonomy | `F` accepted; hidden fail | `F` rejected with arguments |
| Normalization policy | Final `S` blocked | `F` rejected with arguments |
| Raw-ID retry | `F` accepted; hidden fail | Final `I` blocked |
| Reserved-ID guard | Early hidden pass | `F` rejected with arguments |
| Directory fallback | Final `S` blocked | Malformed final envelope |
| Cross-module rename | Reserved `F`; hidden pass | Unsupported by construction |

Terminal validity and task correctness separated cleanly. Error taxonomy and
raw-ID retry both reached accepted `F` but failed hidden evaluation. The
cross-module source cell reached the forced terminal surface, survived several
commit-phase escapes, then submitted a valid `F` and became the only new hidden
pass relative to Calibration 006.

No supported semantic cell reached a valid terminal. Three selected `F` with
an invalid payload, and two selected non-terminal work. Opcode availability
changed what the model tried, but it did not solve semantic motion
construction or finalization.

## Interpretation

The experiment makes four boundaries sharper:

1. **A phase contract can change model action selection.** The exact repeated
   tasks produced seven `F` calls rather than one and four valid terminals
   rather than one.
2. **An opcode is not a complete instruction grammar.** Advertising `F`
   without its zero-argument shape left enough freedom for half of the forced
   `F` attempts to fail validation.
3. **Runtime safety is not sampling efficiency.** Typed rejection prevented
   invalid dispatch, but the rejected final request still consumed tokens,
   latency, and the last turn.
4. **Termination is not correctness.** Two newly terminal source trajectories
   still failed hidden evaluation.

This is another Experimental-TDD split result. The test that the terminal
opportunity reaches the provider turned green. The stronger test that the
provider can use that opportunity reliably stayed red.

## Interpretation boundary

- Calibration 007 reuses the exact Calibration 006 instances to isolate the
  progress-policy change. It is not a fresh benchmark.
- This is one unreplicated schedule over six family-derived tasks and one model
  endpoint.
- Provider-native model identity is verified; model weights are not
  cryptographically pinned.
- Hidden Pass@1 is descriptive, not a powered statistical comparison.
- Independent sampling means run-to-run outcome differences cannot be assigned
  solely to the progress policy.
- The source and semantic arms share progress control but retain different
  representations and memory projections.
- Provider-side tool-schema adherence is observed, not guaranteed by the
  runtime.

No cell will be replaced or rerun under this freeze. Both inferential and
general efficacy claims remain unauthorized.

## The next red test

Before another provider launch, turn the instruction envelope itself into a
phase-specialized discriminated grammar. At minimum:

- `finish` must expose `i: const F` and an exactly empty `a` array;
- `commit` must use an opcode-specific union whose `E`, `S`, and `F` branches
  encode their own arity and payload shape;
- exhausted budgets must remove both the opcode branch and its payload grammar;
- recorded extra-argument `F`, blocked `W/I/S`, and malformed-envelope samples
  must fail locally at schema validation; and
- all eleven known reference transitions must remain accepted.

The next hypothesis is:

`motion lexicalization must cover instruction shape, not only opcode choice`.
