# Local coding agents and filesystem containment

This publication records two sequential campaigns against a strengthened Go
filesystem-containment fixture:

1. a capability check in which Devstral Small 2 passed once;
2. a three-run repeatability campaign in which every run timed out.

The campaigns are reported separately. The result is not presented as a 1/4
success rate because they served different experimental purposes and were not
planned as one randomized batch.

## Question

Can a fully local coding model implement bounded filesystem writes while
preserving legitimate nested paths and rejecting traversal, absolute paths,
and a pre-existing symlink escape?

## Environment

- Apple M1 Pro
- 32 GB unified memory
- 16 GPU cores
- Ollama
- Devstral Small 2 24B
- 16,384-token context
- 17 GB runtime footprint reported by Ollama
- 100% GPU residency reported by Ollama

## Contract

Every passing run must satisfy:

```text
go test -count=1 -race ./...
go vet ./...
```

The fixture also prevents public API changes and rejects the earlier shortcut
of prohibiting every filename containing two adjacent dots.

## Results

| Campaign | Runs | Passed | Timed out | Median |
| --- | ---: | ---: | ---: | ---: |
| Capability check | 1 | 1 | 0 | 26m08s |
| Repeatability | 3 | 0 | 3 | 30m01s |

The first campaign establishes bounded capability. The second does not support
a reliability claim.

## Provenance limitation

The historical runs were executed from a precursor working tree that was
subsequently incorporated into GPTCode revision
`8fe858b81c72625c214308a8aa72f6d25d14c2cb`. The exact transient build commit
was not retained.

This limits source-level reproducibility of the historical binary and is
recorded rather than repaired after the fact. Future publications require a
clean, immutable harness revision before execution.

## Human-review boundary

The successful patch passed the declared fixture. Its symlink check and final
write remained separate filesystem operations, leaving a possible TOCTOU
window against an actively hostile concurrent process.

The result is not evidence of a general race-free filesystem primitive.

## Source material

- [GPTCode fixture](https://github.com/jadercorrea/gptcode/tree/main/benchmarks/fixtures/go-safe-store)
- [Suite configuration](https://github.com/jadercorrea/gptcode/blob/main/benchmarks/suites/local-devstral-small-2-safe-store.json)
- [Published result notes](https://github.com/jadercorrea/gptcode/blob/main/benchmarks/results/2026-07-29-local-filesystem.md)
- [Engineering essay](https://gptcode.dev/blog/2026-07-29-one-successful-agent-run-proves-almost-nothing)
