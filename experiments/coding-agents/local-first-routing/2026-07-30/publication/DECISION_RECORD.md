# Decision record: publish the pilot and validate a successor

Date: 2026-08-19

Status: accepted and authorized for release `2026.08.20.1`

## Context

The completed six-task calibration produced a scientifically useful no-go for
the original confirmatory design. A standalone general-effect paper would
overstate the sample, while waiting for an unbounded successor risks hiding a
valid negative feasibility result.

## Options considered

1. Submit the six-task calibration as a full general-effect paper.
2. Keep the calibration private until a successor series finishes.
3. Release the calibration as a bounded pilot artifact and reserve the main
   manuscript for a separately named prospective successor.

## Decision

Choose option 3. The pilot will be made independently citable as calibration
evidence. A later paper may present the pilot as development and the successor
as prospective validation, provided their policies, samples, and estimates
remain separate.

## Consequences

- Negative and invalidated outcomes remain visible rather than entering a file
  drawer.
- The pilot can support method, infrastructure, and feasibility claims but not
  population non-inferiority claims.
- Any router, model, prompt, timeout, budget, or harness change creates a new
  treatment or series.
- The two series must not be pooled unless a preregistered bridge study proves
  compatibility on every treatment-defining dimension.
- External publication is versioned independently from any successor-series
  calibration or confirmatory result.

## Reconsideration trigger

Reconsider the combined-paper strategy only if the successor cannot obtain a
repository-disjoint sample, cannot be funded within a declared budget, or
fails its prospective calibration gate. In that event, the pilot remains a
standalone technical report or workshop artifact rather than being withdrawn.
