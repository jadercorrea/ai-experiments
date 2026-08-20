# Calibration pilot report: local-first coding-agent routing

Status: released calibration-only report; not a confirmatory result

Calibration completed: 2026-08-18

Post-calibration analysis completed: 2026-08-19

## Executive result

The frozen local-first policy reduced observed hosted inference cost by 45.56%
relative to the paired Sonnet 4.6 cloud-only calibration, but resolved 2/6 tasks
versus 3/6 for cloud-only. The descriptive resolution-rate difference was
-16.67 percentage points, outside the frozen -10 percentage-point
non-inferiority margin. With only six calibration tasks, this is a design gate,
not a treatment-effect estimate.

The original 90-task powered design did not survive completed local-first
calibration. Joint simulated power fell from 91.28% under the frozen planning
assumptions to 25.92% after substituting the observed escalation rate and to
1.18% after also substituting the observed resolution estimates. No
confirmatory trajectory has been run.

## Calibration outcomes

| Policy | Resolved | L1 | L2 | L3 | Hosted cost | Total wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Local-only | 3/6 | 2/2 | 0/2 | 1/2 | USD 0 | 9,479.207 s |
| Cloud-only Sonnet 4.6 | 3/6 | 2/2 | 1/2 | 0/2 | USD 7.417368 | 2,365.354 s |
| Local-first clean fallback | 2/6 | 2/2 | 0/2 | 0/2 | USD 4.037955 | 10,627.930 s |

Hosted cost excludes local hardware, electricity, and opportunity cost. Wall
time includes the agent stages and evaluation recorded by each valid
trajectory and is descriptive only.

The local-first router accepted two tasks locally and escalated four. Escalation
triggers were two hard timeouts, one local backend failure, and one
no-material-patch outcome. The two locally accepted tasks split: Echo resolved,
while Fiber passed observable routing checks but failed the held-out evaluator.
This is expected evidence about router precision, not a harness invalidation.

The valid local-first stages recorded 257 successful local inference calls, two
failed local calls, and 82 successful cloud calls. Every successful cloud event
used `us.anthropic.claude-sonnet-4-6`; no model-identity failure was recorded.

## Departures from the planning projection

The routing lock's retrospective check projected 2/6 escalations and 4/6
resolutions after clean fallback. The executed calibration observed 4/6
escalations and 2/6 resolutions. The discrepancy came from actual trajectories,
not manual fallback decisions or changed routing thresholds.

Two earlier attempts remain invalidated and excluded from outcome counts:

- Validator failed before inference because Docker's metadata database returned
  an input/output error.
- Zerolog was intentionally interrupted outside the overnight compute window
  and restarted from the immutable base during an admissible window.

Both evidence bundles and their `invalidation.json` files remain preserved.

## Power and feasibility

The checked-in 90-task design reproduces exactly at 91.28% joint power under its
pre-local-first assumptions. Post-calibration sensitivity gives:

| Scenario | Resolution power | Cost power | Joint power | Three-policy runs |
| --- | ---: | ---: | ---: | ---: |
| Frozen design reproduction | 91.28% | 100.00% | 91.28% | 1,350 |
| Observed escalation rate | 91.28% | 28.64% | 25.92% | 1,350 |
| Observed resolution and escalation | 3.80% | 28.64% | 1.18% | 1,350 |
| Exploratory powered candidate | 92.68% | 100.00% | 92.68% | 48,600 |

The exploratory candidate contains 1,080 tasks from 270 repositories and 15
trajectories per task-policy pair. It is a tested feasibility point, not an
optimized minimum or preregistered design.

Using the frozen lognormal cloud-cost assumptions, that candidate implies an
expected USD 20,482 for the cloud-only arm and USD 13,655 for local-first cloud
fallback, approximately USD 34,137 total hosted inference before attrition or
invalid repetitions. Applying the observed mean wall times to 16,200
trajectories per policy implies roughly 16,854 serial hours across all three
arms, or 702 days on one execution slot. These are planning projections, not
observed campaign consumption.

## Decision

The confirmatory gate is **no-go**. Three paths remain scientifically honest:

1. Publish the completed work as a calibration pilot, emphasizing router
   behavior, failure taxonomy, evidence integrity, and feasibility limits.
2. Change the routing rule or treatment, creating a new named series and
   repeating calibration before any confirmatory claims.
3. Construct, budget, and preregister a substantially larger benchmark before
   running the current treatment confirmatorily.

The recommended next step is path 1. The available evidence supports a useful
pilot report; it does not justify the expense or claimed precision of path 3.

## Reproduction and evidence

- Machine-readable local-first summary:
  [`calibration/local-first-summary.json`](calibration/local-first-summary.json)
- Power sensitivity and candidate:
  [`calibration/local-first-power-sensitivity.json`](calibration/local-first-power-sensitivity.json)
- Routing lock:
  [`calibration/routing-policy-lock.json`](calibration/routing-policy-lock.json)
- Frozen power inputs:
  [`power-assumptions.json`](power-assumptions.json) and
  [`power-result.json`](power-result.json)

From the repository root:

```bash
.venv/bin/python scripts/summarize_local_first_calibration.py
.venv/bin/python scripts/analyze_local_first_power.py
env PATH="$PWD/.venv/bin:$PATH" scripts/validate
```

The second command intentionally takes several minutes because it confirms the
48,600-run candidate across 5,000 simulated campaigns.
