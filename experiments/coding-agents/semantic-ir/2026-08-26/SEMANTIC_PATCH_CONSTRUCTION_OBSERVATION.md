# Semantic patch construction observation

## Result

The persistent semantic program can now be edited transactionally and lowered
back to the existing TypeScript target. On the local reference task:

- the unchanged baseline failed both executable evaluators;
- the source patch and semantic patch passed the same public and hidden tests;
- both arms produced byte-identical TypeScript;
- reversing the two non-overlapping semantic operations produced the same
  canonical result digest;
- stale program or subtree preconditions were rejected without mutating the
  persistent program or participant workspace; and
- a source diff that changed a protected file was rejected in staging and did
  not mutate the participant workspace.

This establishes construction feasibility for checked edits over persistent
semantic state. It does not establish that a model generates those edits more
reliably or cheaply.

## Frozen boundary

Semantic patch v0 intentionally has one operation:

```text
replace_subtree(
  target_node_id,
  expected_subtree_sha256,
  replacement
)
```

The patch also identifies the target program and exact canonical base-program
digest. Application is all-or-nothing. Replacement roots preserve the target's
stable node identity; overlapping targets and node-identity collisions are
rejected; the complete result is run through the existing schema, symbol, type,
and effect validator before it can replace source code.

This is optimistic concurrency for semantic state, not a merge algorithm. A
patch based on a different state fails visibly instead of being guessed onto the
new tree.

## Matched local task

The task changes two independently located error literals in the existing user
lookup program:

- empty ASCII-normalized input: `invalid_user_id` → `empty_user_id`;
- completed lookup with no user: `not_found` → `user_not_found`.

The public evaluator exposes the first change and successful lookup behavior.
The hidden evaluator checks the second change, ASCII-only normalization, and all
empty ASCII representations. A deliberately public-only semantic patch passes
the public evaluator and fails the hidden one.

The reference source patch is 1,238 UTF-8 bytes; the reference semantic JSON
patch is 1,009 bytes, 18.50% smaller for this particular generated source. That
is a payload-byte description, not a token result: there were no model calls and
no tokenizer measurement in this slice.

Machine-readable evidence is locked with the task in
[`observation.json`](construction/patch-task-001-error-codes/observation.json).

## What this changes

The earlier comparisons asked a model to regenerate a complete source or IR
program. This slice makes the semantic object persistent. The treatment for a
future experiment can now be the edit itself:

```text
source state + textual diff
          versus
semantic state + checked graph edit
```

That is closer to the original hypothesis that the transcript and source text
need not be the agent's only persistence layers.

## Next gate

Freeze several fresh, heterogeneous patch tasks before making more model calls.
The set should include at least literal/local changes, control-flow changes,
effect changes, and one intentionally unsupported task. Each task needs matched
visibility, mutation scope, evaluator behavior, context accounting, and a
predeclared unsupported-task classification.

Only after that freeze should source patches and semantic patches be compared on
provider-native tokens, hidden Pass@1, validation failures, repair cycles, and
unsupported-task rate.
