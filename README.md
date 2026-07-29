# AI Experiments

Reproducible evaluations of AI models, agents, and inference systems.

This repository publishes protocols, manifests, summaries, and verification
tools. Large or generated evidence bundles are attached to immutable GitHub
Releases instead of being committed to Git history.

The goal is not to collect favorable demonstrations. Every publication should
retain failed runs, state what the executable contract proves, and distinguish
capability from repeatability.

## Published experiments

| Release | Experiment | Result |
| --- | --- | --- |
| `2026.07.29.1` | Local coding agents: filesystem containment | One reviewed capability pass; subsequent repeatability batch 0/3 |

See
[coding-agents/filesystem-containment](experiments/coding-agents/filesystem-containment/2026-07-29)
for the protocol, limitations, and release manifest.

## Publication contract

Each experiment must provide:

- a stable experiment identifier;
- an explicit schema version;
- source and harness revisions;
- model and runtime identity;
- hardware and execution constraints;
- exact verification commands;
- success, failure, and timeout results;
- known limitations;
- checksums for every released asset.

Releases use CalVer:

```text
YYYY.MM.DD.N
```

The final component is a sequence number for multiple publications on the same
day. Published release tags and assets are never replaced. Corrections receive
a new release.

## Verify a release

Download a release archive and its checksum file into the same directory:

```bash
./scripts/verify-release \
  SHA256SUMS \
  ai-experiment-coding-agents-filesystem-containment-2026.07.29.1.tar.gz
```

The script verifies the checksum and inspects the archive before extraction.

## Scope

The repository is intentionally independent from any single model or harness.
An experiment may use GPTCode, Codex, OpenCode, Gemini, a custom evaluator, or
another system, provided the manifest records the dependency precisely.

## License

Repository-authored code, metadata, and documentation are available under the
[MIT License](LICENSE). Evidence bundles may contain third-party or generated
material; each experiment must record the applicable source licenses.
