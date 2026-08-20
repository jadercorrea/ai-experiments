# When Should a Coding Agent Go to the Cloud?

Release: `2026.08.20.1`

This bounded calibration-pilot release contains the protocol, harness, valid
and invalidated trajectories, machine-readable summaries, analysis, and pilot
manuscript for a six-task comparison of local-only, cloud-only, and clean
fallback local-first coding-agent policies.

The observed local-first policy reduced hosted inference cost by 45.56% versus
the paired Sonnet 4.6 cloud-only calibration, while resolving 2/6 tasks versus
3/6. The result triggered a no-go for the original confirmatory design. It is
calibration evidence, not a population estimate or a claim that local-first
routing is generally inferior.

The release archive preserves the reviewed experiment tree except for release
control files whose checksums depend on the archive itself. Runtime Unix
sockets, operating-system metadata, and Python caches are also excluded.
`manifest.json`, `SHA256SUMS`, and `publication/artifact-lock.json` remain
available in the Git tag. The complete repository tag also contains the
analysis and harness source.

Read `CALIBRATION_PILOT_REPORT.md` and `publication/PILOT_MANUSCRIPT.md` before
interpreting or citing the result.
