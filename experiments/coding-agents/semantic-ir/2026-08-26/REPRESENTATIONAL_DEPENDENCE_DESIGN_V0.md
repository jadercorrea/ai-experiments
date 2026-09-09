# Representational Dependence factorial design v0

## Status

**Call-free construction valid; empirical launch blocked. A 2x2 design now
isolates the lexicon of semantic inspection results from their structural
packaging while keeping the Session ISA, mutation backend, capabilities,
evaluators, model policy, and budgets fixed. Twenty construction realizations
decode to byte-identical canonical observations, and meaningful/opaque pairs
have identical structure after applying the frozen label map. The five fixtures
already reached the provider during Calibration 008 and are ineligible as
confirmatory subjects. A separate 64-scenario sensitivity now exposes a
16-to-920-task range, and a subsequent scientific freeze selects a 240-task
asymptotic candidate. Finite-sample validation, spend ceiling, execution
freeze, launch artifact, authorization, and model calls remain absent.**

The materialized construction contains 28 files with tree digest
`1ed3881fa29a5b1edb451c16ee80035aa72127841f4936008c4c5247b7cdae0e`.
Its artifact-lock file digest is
`d6ddf239dfccdf14cb9e3f2716bc86ec495ecd166e6094322ccfab5a6e755013`.

## The bounded question

Calibration 008 showed that an exact action grammar can reject invalid model
output without making the model use the semantic representation productively.
The next question must not change that action grammar again. It is:

> Given the same detailed semantic observation, does changing its lexical or
> structural realization change subsequent coding-agent behavior?

This v0 design varies only results returned by semantic inspection. The compact
outline and handle-selection interface before the first inspection remain
common. Once treatment begins, later inspection choices may diverge as part of
the agent trajectory; every returned observation is encoded by the assigned
condition. The model-facing payload contains neither a condition name nor the
evaluator-only codebook.

## Factorial conditions

| Condition | Lexicon | Packaging |
| --- | --- | --- |
| `meaningful_nested` | Existing semantic control words | Recursive node records |
| `opaque_nested` | Frozen arbitrary labels | Recursive node records |
| `meaningful_table` | Existing semantic control words | Flat node table and references |
| `opaque_table` | Frozen arbitrary labels | Flat node table and references |

The lexical comparison is made twice, once inside each packaging. After the
opaque labels are deterministically normalized, each meaningful/opaque pair is
structurally byte-identical. The packaging comparison is likewise made inside
each lexicon. Every condition decodes through trusted infrastructure to the
same canonical `compact-inspection/v1` object.

The first factorial intentionally omits a source-code arm. Source remains a
useful engineering comparator, but it identifies neither the lexical nor the
packaging main effect and would add a fifth provider cell per task.

## Fixed and varying surfaces

| Surface | Policy |
| --- | --- |
| Task requirement | Fixed |
| Compact outline and handle-selection interface | Fixed |
| Detailed inspection realization | **Varied 2x2 treatment** |
| Session ISA and phase grammar | Fixed |
| Semantic mutation backend | Fixed |
| Catalog, capabilities, types, and effects | Fixed |
| Public and hidden evaluators | Fixed |
| Model and sampling policy | Fixed before launch |
| Turn, mutation, repair, and accounting limits | Fixed before launch |

This boundary avoids the earlier source-versus-semantic confound. The output
language, mutation semantics, and observation realization do not change
together.

## Executable equivalence gate

The codec represents JSON values as typed, identity-bearing nodes. Nested
packaging embeds child records recursively; table packaging stores every node
once and uses explicit references. A closed label map replaces transport keys,
canonical field names, expression operators, slots, and the schema identifier
in the opaque conditions. Domain values, capability tokens, stable identities,
symbol names, and types remain unchanged.

Surface serialization preserves condition-independent construction order
instead of sorting keys by their meaningful or opaque spelling. After label
normalization, each lexical pair is therefore byte-identical in order as well
as topology.

The decoder rejects:

- unknown lexical or transport labels;
- a payload decoded under the wrong lexicon or packaging;
- duplicate node identities and object keys;
- dangling, repeated, cyclic, or unreachable table nodes;
- scalar values with the wrong declared JSON type; and
- collisions between domain literals and the reserved opaque namespace.

The construction uses the five supported Calibration 008 programs and includes
each function body plus its reference targets solely as grammar-coverage
fixtures. These reference-selected observations are not future participant
inputs. Across the fixtures:

| Measure | Observed |
| --- | ---: |
| Supported construction tasks | 5 |
| Factorial conditions | 4 |
| Realizations | 20 |
| Exact canonical round-trips | 20 / 20 |
| Lexical skeleton matches | 10 / 10 pairs |
| Current expression operators covered | 8 / 8 |
| Model/provider calls | 0 |

## Surface accounting

These bytes measure deterministic canonical UTF-8, not provider tokens:

| Surface, five fixtures | Bytes | Change from canonical |
| --- | ---: | ---: |
| Canonical observations | 16,905 | — |
| `meaningful_nested` | 41,524 | +145.6% |
| `opaque_nested` | 36,288 | +114.7% |
| `meaningful_table` | 45,427 | +168.7% |
| `opaque_table` | 40,181 | +137.7% |

Opaque labels make nested fixtures 12.6% smaller and table fixtures 11.5%
smaller than their meaningful counterparts. Table packaging adds 9.4% over
meaningful nested and 10.7% over opaque nested.

This is treatment accounting, not an optimization result. The generic typed
node carrier deliberately repeats identities and type tags so factor boundaries
are auditable. It is an experimental instrument, not a proposed production
wire format. Provider tokenization, caching, trajectory growth, and behavioral
effects remain unobserved.

## Power gate

The experimental unit is a fresh task instance. Repeated stochastic requests
for one task can improve within-task precision but cannot manufacture new task
units or justify generalization.

The primary estimands are the marginal lexical and packaging effects on hidden
Pass@1. The design reserves a familywise alpha of 0.05 with Holm correction
across those two main effects and targets power of 0.80. The interaction is
secondary and estimation-first.

A deterministic sensitivity curve now crosses baseline Pass@1 values 0.20 to
0.80, absolute effects 0.05 to 0.20, and null within-task ICC values 0.00 to
0.75. It plans from the more expensive of equal-magnitude rescue and harm
alternatives, uses the smallest Holm threshold, and rounds upward to four-task
counterbalancing blocks. Results range from 16 to 920 fresh tasks. This is a
normal-approximation sensitivity, not a selected or simulation-validated power
design.

A separate pre-outcome selection now fixes these inputs:

1. the smallest effect size of interest for each main effect;
2. baseline success probability;
3. within-task cross-condition outcome correlation; and
4. the mixture of fresh task families to which the result should generalize.

Both primary SESOIs are 0.10; the planning envelope spans baseline 0.20–0.80
and null ICC 0.00–0.75; five mechanism families receive equal weight. The
resulting 240-task value remains an asymptotic candidate until finite-sample
simulation passes. See
[`REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md`](REPRESENTATIONAL_POWER_SELECTION_FREEZE_V0.md).

Choosing a convenient number of requests before those inputs would create the
appearance of power rather than power.

## Contamination gate

All five construction fixtures were sent to the provider in Calibration 008.
They are valid codec fixtures and invalid confirmatory subjects. A future suite
must contain fresh participant bytes and must reject equality with every prior
provider-request artifact before launch. References and hidden evaluators remain
outside participant context and require their own content lock.

The four conditions will use independent sessions. Their temporal order is
assigned through a balanced four-period sequence family after task freeze; no
history crosses conditions.

## Cost gate

Calibration 008's five supported semantic cells provide only a descriptive
rate basis:

| Basis | Observed |
| --- | ---: |
| Mean cost per semantic cell | USD 0.245715 |
| Maximum observed cell cost | USD 0.294795 |
| Maximum requests per cell | 12 |
| Five-task, four-condition mean-rate projection | USD 4.914300 |
| Five-task projection at observed maximum rate | USD 5.895900 |
| Five-task maximum-request projection | 240 |

Those five tasks are not launch-eligible, and a powered task count does not yet
exist. The projections therefore set scale only. No spend ceiling or provider
request ceiling is authorized.

## Interpretation boundary

- Byte equality proves codec preservation, not equal model interpretation.
- Lexical normalization proves that the lexical pair differs only by the
  frozen codebook at the serialized-surface level.
- Structural conditions preserve decoded information but necessarily differ in
  reference layout, repetition, byte length, and likely tokenization; those are
  constituents of the packaging treatment, not hidden controls.
- The common pre-inspection outline means this first study estimates dependence
  on detailed semantic observations, not every model-visible representation.
- The construction fixtures cover the current eight-expression vocabulary, not
  future language extensions.
- No behavioral, token, cost-efficiency, inferential, cognitive, or general
  language claim is authorized.

## Next red test

The deterministic finite-sample campaign later selected 240 tasks under the
frozen inputs. The next red test is to freeze their construction protocol before
creating fresh instances, auditing contamination, freezing exact contexts and
evaluators, projecting a cost ceiling, or requesting launch. See
[`REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_OBSERVATION_V0.md`](REPRESENTATIONAL_FINITE_SAMPLE_SIMULATION_OBSERVATION_V0.md).
