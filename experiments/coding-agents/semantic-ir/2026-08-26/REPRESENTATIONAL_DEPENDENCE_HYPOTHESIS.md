# Representational Dependence Hypothesis

## Status

**Registered for a future calibration. It is not part of Calibration 008, does
not alter any frozen estimand, and authorizes no model or provider call.**

## Motivation

Separating a canonical semantic object from its linguistic or source-code
realizations does not make the canonical representation semantically neutral.
Human-readable labels contribute one set of commitments, while graph topology,
node categories, operand order, granularity, and omitted distinctions contribute
another. Replacing `call`, `let`, or `match` with opaque opcodes removes lexical
cues but preserves the ontology encoded by the structure.

For a language model, the canonical IR is therefore not assumed to expose a
language-independent internal state. It is an engineered interface between a
probabilistic model and deterministic infrastructure. The useful empirical
question is which properties remain invariant across realizations and which
properties change model behavior.

## Future empirical hypothesis

Given model-facing realizations that decode deterministically to the same
canonical semantic object and expose identical capabilities, evidence, budgets,
and verification, lexicalization and structural packaging can systematically
change coding-agent behavior.

The corresponding null hypothesis is that any observed differences are
compatible with sampling variation once canonical meaning, disclosed
information, and execution controls are matched.

This is an engineering hypothesis about coding agents. It is not a claim about
human cognition, a language-independent mental representation, linguistic
determinism, or an artificial equivalent of *thinking for speaking*.

## Required isolation

The first future study should separate two factors rather than combining them:

1. **Lexical factor:** identical topology and operands, with meaningful words
   such as `call`, `let`, and `match` versus opaque symbols or opcodes.
2. **Structural factor:** different model-facing organizations that lower to
   the same canonical object, with lexical cues held as constant as practical.

Every condition must pass through a deterministic decoder to one canonical IR.
The shared validator, capability resolver, effect checker, mutation backend,
target projection, evaluators, model, sampling, context policy, tool budget,
and stopping rule must remain unchanged.

Byte equality of decoded canonical objects is a construction gate, not an
empirical result. Conditions that cannot represent the same task remain in the
applicability denominator rather than being silently removed.

## Candidate conditions

| Condition | Model-facing realization | Isolated question |
| --- | --- | --- |
| Source control | Existing source-code workflow | Baseline only |
| Meaningful lexicon | Current semantic words and stable references | Combined semantic treatment |
| Opaque lexicon | Same topology and operands with arbitrary opcodes | Effect of lexical cues |
| Alternate packaging | Different structure, same canonical decode | Effect of structural packaging |

The factorial comparisons are the meaningful tests. The source condition
remains useful context but does not by itself identify lexical or structural
dependence.

## Outcomes

At minimum, report hidden-evaluator Pass@1, valid terminal rate, provider input
and output tokens, repair cycles, schema and runtime rejections, time to valid
terminal, unsupported-task rate, and total estimated cost. Retain the complete
trajectory and decoded canonical object for every attempt.

Round-trip preservation, type/effect validity, capability authorization, stable
identity, evidence references, and evaluator outcomes are candidate operational
invariants. Salience, attention, chosen decomposition, action order, and repair
strategy are explicitly allowed to vary and are part of the empirical subject.

## Sequencing gate

This hypothesis must not be folded into Calibration 008. That calibration asks
whether the already constructed complete reserved-phase instruction grammar
changes behavior under its provider-admissible v3 envelope. Adding lexical or
structural conditions now would change the estimand after construction and
confound the next comparison.

A later calibration may be designed only after Calibration 008 is completed or
formally abandoned, its evidence is frozen, and a separate power, contamination,
cost, and launch decision is recorded.
