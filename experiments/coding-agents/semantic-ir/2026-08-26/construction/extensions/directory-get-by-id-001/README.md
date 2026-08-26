# Directory lookup extension

This construction adds one effectful closed-catalog intrinsic to semantic IR:

```text
directory.get_by_id(string) -> option<user>
effect: network.read:directory
```

The reference semantic patch still contains only the frozen `replace_subtree`
operation. After the checked tree replacement, the v2 applicator derives the
canonical function-effect list from the resulting symbols and validates that
the stored declaration is exact. It does not accept missing or unused effects
in directly submitted programs.

The fallback executes only after `users.get_by_id` returns none. Empty input and
local success never invoke the directory capability. This is construction
evidence only: no benchmark instance is sealed and no model call is authorized.

See [`observation.json`](observation.json) for content-addressed chronology and
behavior evidence.
