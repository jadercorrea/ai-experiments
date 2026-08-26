# Construction observation: token consumption on one matched task

## Outcome

The current semantic-IR v0 consumed **4.25 times as many total provider tokens**
as direct TypeScript on the construction task.

Both valid observation arms used the same `us.anthropic.claude-sonnet-4-6`
endpoint with temperature zero, made exactly one candidate mutation, and passed
the same public and hidden executable behavior.

| Metric | Direct TypeScript | Semantic IR v0 | Semantic / source |
| --- | ---: | ---: | ---: |
| Provider requests | 4 | 5 | 1.25× |
| Input tokens | 7,812 | 34,359 | 4.40× |
| Output tokens | 587 | 1,301 | 2.22× |
| Total tokens | 8,399 | 35,660 | 4.25× |
| Cached input tokens | 0 | 0 | — |
| Provider latency | 11.821 s | 26.590 s | 2.25× |
| Estimated hosted cost | $0.032241 | $0.122592 | 3.80× |
| Public evaluator | pass | pass | — |
| Hidden evaluator | pass | pass | — |

These are descriptive measurements from one public construction task and one
trajectory per arm. They are not estimates of a population effect and do not
authorize an efficacy claim.

## What was measured

The observation used the frozen output-interface policy:

- both arms could list and read the same locked workspace;
- both could run the same public evaluator and finish the submission;
- the source arm could call `workspace_write_target` once;
- the semantic arm could call `ir_submit` once;
- all provider-native `inputTokens`, `cacheReadInputTokens`, and `outputTokens`
  were summed across the complete tool trajectory;
- the hidden evaluator ran only after `submission_finish` and its output was not
  returned to the model.

The model, order, sampling, limits, accounting policy, interface digest, task
tree, and upstream model configuration were fixed before the valid calls.

## Why semantic IR lost this comparison

### 1. The static semantic contract dominated input

The first direct-source request contained 3,530 serialized characters and was
reported as 1,325 input tokens. The first semantic request contained 17,879
characters and was reported as 5,791 input tokens.

| Initial request component | Direct TypeScript | Semantic IR v0 |
| --- | ---: | ---: |
| Mode system context | 894 characters | 9,260 characters |
| Tool definitions | 2,129 characters | 7,014 characters |
| Complete request | 3,530 characters | 17,879 characters |

The complete program schema appears once in the semantic system context and
again inside the `ir_submit` tool schema. Because the provider reported zero
cached tokens, that static material was charged again on every turn as the
conversation grew.

### 2. The JSON tree was larger than the TypeScript answer

The source mutation call used 732 serialized argument bytes and generated 316
output tokens on that turn. The semantic mutation used 1,568 argument bytes and
generated 1,038 output tokens. The canonical JSON AST is an inspection format,
not a dense agent-native encoding, and on this small task it was more verbose
than the source it represented.

### 3. The semantic trajectory took one additional request

The source arm combined listing and its first read in one response, then wrote,
tested, and finished in four requests. The semantic arm listed, read, submitted,
tested, and finished in five. Its final finish request alone added 7,923 input
tokens and 49 output tokens. Even excluding that final request, however, the
semantic trajectory had already used 27,688 tokens, 3.30 times the source
arm's complete total.

## Invalid observation 001

The first attempted pair is retained but invalidated. The semantic backend
required `program_id = "program:user-lookup"`, while that task-specific value
was absent from every participant-visible artifact. The model submitted
`prog:lookup-user`, received the rejection, and corrected the identifier on the
next turn, but the single-mutation policy correctly blocked a second attempt.

That was an interface specification defect. The required identifier was exposed,
the task and interface locks were rebuilt, and the corrected execution received
the separate identifier `token-consumption-002`. No evidence from observation
001 is pooled into the valid comparison.

## Interpretation

This observation rejects a narrow proposition: **the current schema-heavy JSON
IR and current tool envelope are not token-efficient for this task**.

It does not reject the broader AI-native-language hypothesis. This slice has no
custom vocabulary, tokenizer-aligned opcodes, compact serialization, semantic
patches, prompt caching, or persistent server-side grammar. It repeats a large
general JSON Schema through a text-oriented provider API and emits an entire
program tree for a small function. In other words, this measured the cost of an
auditable prototype representation, not the proposed dense representation.

That distinction does not rescue v0: a future design must demonstrate the
savings rather than assume them.

## Follow-up discriminating experiment

The subsequent single-shot representation observation removed three known
confounders before adding language features:

1. expose the program grammar exactly once rather than duplicating it in the
   prompt and tool definition;
2. preload the identical repository evidence and force one terminal submission
   call per arm, eliminating navigation-turn variance; and
3. compare JSON AST against a compact serialization of the same semantic tree,
   while preserving the same validator and evaluator.

That three-way comparison found that compact IR cut solution output tokens by
55.04% relative to source and canonical JSON IR by 87.72%, while total compact
tokens remained within 0.65% of source because fixed input context dominated the
small task. See
[`SINGLE_SHOT_REPRESENTATION_OBSERVATION.md`](SINGLE_SHOT_REPRESENTATION_OBSERVATION.md).

## Evidence

- [`token-consumption-001`](observations/token-consumption-001) contains the
  invalidated first execution and its explicit invalidation record.
- [`token-consumption-002`](observations/token-consumption-002) contains the
  valid requests, responses, gateway usage events, tool transcripts, final
  workspaces, per-arm results, and paired result.
- [`token-comparison-v0.json`](construction/token-comparison-v0.json) is the
  checked protocol used for observation 002.
- [`token_comparison.py`](scripts/token_comparison.py) is the bounded runner.
