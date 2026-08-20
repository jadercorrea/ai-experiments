# Calibration campaign

Calibration estimates routing thresholds, execution budgets, complexity cut
points, escalation behavior, and variance components. Its tasks and outcomes
are excluded from confirmatory estimates.

The initial screen contains six post-lock candidate changes from six repositories.
The `provisional_stratum` labels are scheduling aids, not final complexity
labels. A candidate becomes a calibration task only after its separated test
patch fails at the base commit, its reference solution passes the focal and
regression suites, and its container is reproducible without network access.

The campaign began with `local-only`. The strong hosted reference is now frozen
in [`hosted-treatment.json`](hosted-treatment.json): Claude Sonnet 4.6 through
the US Amazon Bedrock inference profile `us.anthropic.claude-sonnet-4-6`, with
no provider router and a USD 50 calibration cap. The Bearer Token is recovered
from one exact macOS Keychain item inside the temporary host gateway process;
it is never mounted into the agent container or written to a file. The gateway
translates the frozen OpenAI-compatible scaffold to Bedrock Converse while
retaining the same client-visible prompt, tools, and tool-result loop.

Bedrock Converse does not return the requested model identifier in its response.
Model identity is therefore evidenced by the locked inference-profile endpoint,
the exclusive IAM scope reported for that key, request/response hashes, and the
absence of provider-managed intelligent routing. This is weaker than a returned
provider fingerprint and is reported as a limitation rather than synthesized as
provider evidence.

The formal Sonnet admission passed on 2026-08-12 with the required
`record_admission` tool call, 685 input tokens, 33 output tokens, and estimated
cost USD 0.00255. Its content-free evidence is retained under
`cloud-admission-bedrock-sonnet-4-6`. The earlier Groq treatment, lock, admission,
and six trajectories remain an immutable low-cost ablation and are never pooled
with the Sonnet series.

The first admission attempt was invalidated before inference because GroqCloud
rejected Python's default `urllib` User-Agent with HTTP 403. A control request
to the non-inference model inventory returned 403 with default `urllib` and 200
with curl using the same credential. The failed result, hash-chain log, and
invalidation rationale are retained in
`cloud-admission-invalid-python-urllib-user-agent`. The gateway now sends the
explicit `ai-experiments-gateway/1` User-Agent; this transport correction does
not alter prompts, model parameters, routing, or evaluation.

The first cloud-only Echo trajectory was also invalidated as a harness failure.
OpenCode replayed a provider-specific `reasoning_content` field in the assistant
history after a successful tool call, and GroqCloud rejected request sequence 3
with HTTP 400. Both preceding responses returned the locked model identity. The
gateway adapter now strips only that nonportable history field for Groq-bound
requests. The trajectory, its USD 0.00145725 estimated cost, and its hash-chain
evidence remain under
`calibration-aborted-runs/echo-3056-cloud-groq-reasoning-content-incompatibility`.
No local outcome may be used to remove a task that passed the construction
criteria.

Run order was generated from a committed seed after retained tasks were known.
Each run gets a clean workspace, a new gateway, the locked model from
`../model-lock.json`, and a separate evidence directory.

## Local-only calibration result

The six-task local-only schedule completed with three resolved trajectories:
L1 2/2, L2 0/2, and L3 1/2. These are calibration-only descriptive results,
not confirmatory estimates of model performance.

One Fiber P2P evaluator was invalidated after unrelated network-style tests
timed out under the full race suite. The original result and logs remain
preserved; the same frozen patch, without rerunning the agent, passed a revised
race-enabled regression family covering IP and proxy-header behavior. One
initial go-git trajectory was also aborted before any patch after the public
prompt was found to expose hidden-test names. Its evidence is retained under
`calibration-aborted-runs`, and the valid trajectory restarted from the base
commit with public and hidden commands separated.

See `local-only-summary.json` for machine-readable outcomes and the per-run
evidence directories under `calibration-runs` for frozen patches, gateway event
chains, agent output, evaluator logs, and hashes.

The local-only trajectories consumed 4,874,339 reported input tokens and 21,319
reported output tokens. Applying the frozen Groq price schedule to the same
token volume would cost approximately USD 0.744; this is only a planning bound,
not a prediction of hosted token use. The USD 5 calibration cap leaves margin
for different hosted trajectories while bounding financial exposure.

## GroqCloud cloud-only calibration result (historical ablation)

The direct GroqCloud `openai/gpt-oss-120b` arm completed all six eligible
trajectories with 1/6 verified resolutions: L1 1/2, L2 0/2, and L3 0/2. Only
two trajectories produced patches. Four stopped after the model emitted an
invalid or unparseable tool generation; the remaining non-resolving patch
failed both hidden evaluator transitions. No successful provider response
substituted the locked model identity.

This treatment is retained as an informative low-cost cloud ablation, not as
the primary cloud baseline. Using it as the sole fallback would make the
local-first comparison answer whether routing beats an unreliable cloud
scaffold/model pairing, rather than whether routing preserves the reliability
of a strong hosted coding system.

The eligible trajectories cost USD 0.11346315 after applying Groq's cached-input
rate. Original result files remain immutable and contain the deliberately
conservative full-input-rate estimate; `cloud-cost-accounting-revision.json`
records the non-destructive accounting correction. See
`cloud-only-summary.json` for machine-readable outcomes.

## Bedrock Sonnet 4.6 cloud-only calibration result

The strong-reference `us.anthropic.claude-sonnet-4-6` arm completed all six
eligible trajectories with 3/6 verified resolutions: L1 2/2, L2 1/2, and L3
0/2. The primary outcomes were three passes, one functional failure, one
functional no-op, and one agent timeout. This is a calibration-only descriptive
result, not a confirmatory comparison or a model leaderboard estimate.

The six valid trajectories used 2,364,011 reported input tokens and 21,689
reported output tokens across 123 successful inference calls. Their frozen-price
cost was USD 7.417368. One operator-interrupted Fiber trajectory was invalidated
and repeated under the original 1,800-second timeout; its 24 calls and USD
1.420866 remain accounted but are not an outcome. Total benchmark consumption,
including that invalidated attempt, was USD 8.838234. The earlier formal
admission cost USD 0.00255 separately, and the eight-token direct preflight cost
approximately USD 0.002166. Total known Bedrock consumption for this work was
therefore USD 8.842950. Every successful inference event records the locked
endpoint model and no identity failure.

Fiber's valid repetition reached the preregistered timeout with no patch. The
initial interruption is retained at
`calibration-aborted-runs/fiber-4568-cloud-sonnet-operator-inactivity-interrupt`.
It is not counted as a second model sample.

Validator and Testify initially encountered evaluator infrastructure errors:
the agent-added public tests and hidden tests inserted hunks into the same test
files, so the hidden patches did not apply after the frozen patches. The agent
was not rerun. For each trajectory, the original frozen patch and error logs
remain preserved; the evaluator excluded only the agent-added test file from
the frozen patch, applied the unchanged production patch and hidden patch, and
reran offline. Validator passed both transitions. Testify executed and failed
the focal behavior, so it remains a functional failure. Both `result.json`
files explicitly identify the infrastructure rerun and excluded path.

See `cloud-only-sonnet-4-6-summary.json` for machine-readable trajectories,
outcomes, token/latency totals, costs, evaluation sources, and evidence hashes.

## Local-first calibration result

The frozen clean-fallback local-first schedule completed all six tasks with 2/6
verified resolutions: L1 2/2, L2 0/2, and L3 0/2. Two trajectories were
accepted locally and four escalated to the clean cloud stage: two hard timeouts,
one backend failure, and one no-material-patch outcome. Every valid cloud event
used the locked Bedrock Sonnet 4.6 inference profile with no identity failure.

Valid local-first trajectories cost USD 4.037955 in hosted inference versus USD
7.417368 for the paired cloud-only calibration, a descriptive reduction of
45.56%. Resolution was 33.33% versus 50.00%, a -16.67 percentage-point
difference that is outside the frozen -10 percentage-point non-inferiority
margin at the point estimate. These six calibration tasks do not support a
confirmatory treatment-effect claim.

The observed router behavior also contradicted the frozen retrospective check:
4/6 tasks escalated and 2/6 resolved, versus the projected 2/6 escalations and
4/6 resolutions. See `local-first-summary.json` for the machine-readable
outcomes, routing triggers, costs, token totals, hashes, and invalidations.

Post-calibration sensitivity in `local-first-power-sensitivity.json` reproduces
the original 91.28% joint-power calculation, then shows 25.92% joint power when
only the observed escalation rate is substituted and 1.18% when the observed
resolution and escalation estimates are both substituted. An exploratory
candidate with 1,080 tasks, 270 repositories, and 15 trajectories per
task-policy pair reaches 92.68% across 5,000 simulations, but requires 48,600
three-policy runs. It is explicitly not frozen or preregistered.

## Current go/no-go gate

Local-first calibration is complete. Do not execute confirmatory trajectories.
The calibration gate closed as follows:

1. ~~a direct, version-pinned hosted coding treatment strong enough to serve as
   the non-inferiority reference~~ — Sonnet 4.6 frozen on 2026-08-12;
2. ~~a one-request admission result covering identity evidence, tool use, token
   accounting, and the campaign spending cap~~ — passed on 2026-08-12;
3. ~~a cloud-only calibration schedule for that treatment~~ — completed 3/6
   with USD 8.838234 total benchmark consumption;
4. ~~deterministic routing thresholds derived without confirmatory outcomes~~;
5. ~~a campaign runner that implements the clean fallback boundary: freeze
   local evidence, restore the base repository, then start a separate cloud
   stage~~;
6. the original power design did not survive completed local-first calibration.

No further inference-consuming campaign is admitted until one path is chosen
and committed: either report this work as a calibration pilot, or construct and
preregister a new powered benchmark. The current powered candidate requires
1,080 tasks across 270 repositories and 48,600 three-policy runs; feasibility,
budget, statistical null tests, and human-review materials remain open gates.

The gateway must preserve local HTTP failures instead of silently replaying a
request against the cloud backend. Provider failover inside one conversation
does not satisfy the clean-fallback protocol.
