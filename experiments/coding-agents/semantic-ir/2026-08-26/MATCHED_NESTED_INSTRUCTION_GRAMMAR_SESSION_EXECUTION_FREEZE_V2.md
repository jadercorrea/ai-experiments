# Matched Nested Instruction-Grammar Session Execution Freeze v2

## Result

Calibration 008 now has a provider-admissible, content-bound execution freeze.
The package derives from the prior Instruction-Grammar freeze, preserves every
task, model, sampling, limit, accounting, isolation, schedule, memory, progress,
and static-context variable, and changes only the reserved-phase grammar
surface and its deterministic runtime inversion.

The freeze digest is
`e72c87ff0141913dfa48f391c63ada9a6669e410a302c690da778c958a48d943`.
It contains no launch artifact, authorizes no provider call, and leaves
`explicit_launch_008` as the sole execution gate.

## Frozen intervention

Turns in the work phase retain the exact existing `x({i,a})` request and
dispatch path. Commit and finish requests use Grammar v3's single required
envelope, `{"v": instruction}`. The runtime validates the complete advertised
schema before extracting `v`, then dispatches only the inner instruction. The
inner object is bijective with Grammar v2; the envelope is a provider-target
lowering, not a new semantic instruction language.

The exact reserved schemas are bound by digest:

- commit:
  `bc482f59403f07e1174683c839a60571b8e042dd04981ebeb0774038aabc225d`;
- finish:
  `cb1ce59a749115ddb203dc2588ab6ac8db914f85a48aa05619cafd13a3c63a83`.

Probe 003 is incorporated only as endpoint-admission evidence. Its two
synthetic requests prove that these exact nested-union schema objects reached
generation on the frozen provider endpoint. They do not prove constrained
decoding, future adherence, or Calibration 008 efficacy.

## Local preflight

The deterministic preflight reports:

- 11 callable cells;
- 110/110 work-phase requests byte-identical to the predecessor;
- 11/11 reference mutations accepted at commit;
- 11/11 reference sessions terminated at finish;
- 6/6 source and 5/5 supported semantic hidden references passed;
- zero top-level unions and 22 nested-union reserved schemas;
- valid `F[]` dispatched once;
- an extra-argument `F` and a missing `v` envelope rejected with zero
  underlying dispatches;
- exact schema preservation through the local Bedrock adapter;
- zero model calls during construction and preflight.

The one unsupported semantic cell remains in the twelve-cell schedule and is
still resolved administratively without a provider call.

## Contamination and claim boundary

The audit separates 127 prior experimental-subject responses from the two
synthetic Probe 003 requests, for 129 prior provider responses in total. The
instances therefore remain a within-instance follow-up rather than a fresh
benchmark. A prelaunch repeat of the audit is mandatory.

The newly registered Representational Dependence Hypothesis is explicitly
outside Calibration 008. It adds no model-visible variable here and may be
designed only in a later calibration, after this one is completed or formally
abandoned. This preserves Calibration 008's estimand: whether the already
constructed complete reserved-phase instruction grammar changes agent behavior
when expressed through its provider-admissible v3 envelope.

No efficacy, Pass@1, token-efficiency, latency, constrained-decoding, or general
coding-agent claim follows from this freeze.
