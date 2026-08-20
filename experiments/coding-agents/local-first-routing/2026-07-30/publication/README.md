# Pilot publication release candidate

Status: release candidate; not yet published or peer reviewed.

This package turns the completed `2026-07-30` calibration into a bounded pilot
publication. It does not upgrade calibration outcomes into confirmatory
evidence and it does not authorize the exploratory 48,600-run campaign.

## Publication claim

The defensible claim is:

> On six calibration tasks, the frozen local-first policy reduced observed
> hosted inference cost by 45.56% relative to the paired Sonnet 4.6 cloud-only
> condition, while resolving 2/6 tasks versus 3/6. The calibration therefore
> rejected the current confirmatory design and identified routing, reliability,
> and feasibility constraints for a prospective successor series.

The words *observed*, *calibration*, and *current design* are required. This
package does not claim that local-first routing is generally inferior or that
the observed percentages estimate population effects.

## Package contents

- [`PILOT_MANUSCRIPT.md`](PILOT_MANUSCRIPT.md) is the pilot-paper draft.
- [`DECISION_RECORD.md`](DECISION_RECORD.md) records why the pilot is released
  separately while the main paper waits for a prospective successor series.
- [`RELEASE_REVIEW.md`](RELEASE_REVIEW.md) records the automated secret, path,
  symlink, and license-metadata triage performed on the release candidate.
- [`artifact-lock.json`](artifact-lock.json) checksums the complete experiment
  tree, excluding only itself and generated operating-system/Python cache files.
- [`../CALIBRATION_PILOT_REPORT.md`](../CALIBRATION_PILOT_REPORT.md) is the
  concise analysis report from which the manuscript is derived.
- [`../calibration/local-first-summary.json`](../calibration/local-first-summary.json)
  and
  [`../calibration/local-first-power-sensitivity.json`](../calibration/local-first-power-sensitivity.json)
  are the machine-readable primary summaries.

Valid runs, failed runs, and invalidation records remain in their original
directories. The release must preserve them rather than publishing only the
summary tables.

## Verify the release candidate

From the repository root:

```bash
.venv/bin/python scripts/build_artifact_lock.py \
  experiments/coding-agents/local-first-routing/2026-07-30 \
  experiments/coding-agents/local-first-routing/2026-07-30/publication/artifact-lock.json \
  --verify

.venv/bin/python scripts/summarize_local_first_calibration.py
.venv/bin/python scripts/analyze_local_first_power.py
git diff --check
scripts/validate
```

The two analysis commands must reproduce their checked-in JSON outputs before
the artifact lock is regenerated. Regenerating the lock is an explicit release
operation, not an automatic formatting step.

## Remaining external publication steps

The local release candidate is complete only after these external steps:

1. complete human review of raw evidence for secrets, personal data, and
   third-party attribution obligations; automated triage is recorded in
   `RELEASE_REVIEW.md`;
2. commit the complete study so the harness and analysis have an immutable Git
   revision;
3. assign a CalVer release identifier, create a release archive, and record its
   checksum in the repository release manifest;
4. update `CITATION.cff` to the new release without erasing the earlier
   publication history;
5. publish the archive and tag to the selected public destination.

No file in this directory represents a completed external publication until
those steps have occurred.
