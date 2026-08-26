# Directory capability and effect extension observation

## Result

Semantic IR catalog v2 adds:

```text
directory.get_by_id(string) -> option<user>
effect: network.read:directory
```

The reference patch expresses the frozen `directory-fallback-001` family with
one `replace_subtree`: query the existing user store first, call the directory
only after a miss, and preserve empty-input, local-success, and double-miss
behavior. The interpreter's effect trace and an executable TypeScript projection
both confirm the order `db.read:users` then `network.read:directory`.

## The effect-header problem

The frozen task required only `replace_subtree`, while semantic IR stores an
exact function-effect declaration outside the expression tree. Adding an
effectful call therefore changes two representations of the same fact:

```text
expression symbol: directory.get_by_id
catalog effect:    network.read:directory
function summary:  [db.read:users, network.read:directory]
```

There were three plausible responses:

1. weaken effect checking so declarations become permissive upper bounds;
2. change the frozen task to require another patch operation; or
3. treat the function summary as canonical derived metadata during checked
   patch application.

Catalog v2 chooses the third. The submitted patch still contains only the
frozen operation. After all identity, digest, overlap, and collision guards pass,
the v2 applicator infers the result's effects from the closed catalog, stores
them in sorted canonical form, and runs final exact validation. Direct program
submissions still reject both missing and unused effects.

This avoids weakening the language invariant or rewriting the task identity.
It also identifies a useful distinction for an agent-native IR: some explicit
state should be authored, while redundant summaries are safer when derived.

## Version and compatibility boundary

The new effect expands the structural function schema, so this is program and
catalog v2. Its expression grammar remains the frozen v0 grammar. Catalog v1's
pure `string.equals` remains available through the additive catalog chain, and
the pinned v0/v1 implementations are unchanged.

The TypeScript projection exposes two typed adapters only when their effects are
declared:

```text
capabilities.users.getById
capabilities.directory.getById
```

Capabilities are resolved lazily by the interpreter. A local hit succeeds even
when the directory adapter is absent; a local miss reports the missing adapter
rather than silently skipping the declared fallback.

## Chronology and claim boundary

The candidate family, required semantics, operation set, and extension gate were
frozen in commit `16d29a5`. This implementation starts from `2218188`, after the
separate pure-equality extension. No concrete benchmark instance, hidden
evaluator, model policy, or model call is introduced here.

The evidence establishes construction support for the required capability,
effect, ordering, patch atomicity, interpreter behavior, and projected runtime.
It does not establish comparative efficacy or token savings.

Machine-readable evidence is in
[`construction/extensions/directory-get-by-id-001/observation.json`](construction/extensions/directory-get-by-id-001/observation.json).

## Next gate

Both predeclared extensions are now construction-supported. The next step is to
construct one fresh repository instance per frozen family, seal shared hidden
evaluators, and lock the final support dispositions before any model call.
