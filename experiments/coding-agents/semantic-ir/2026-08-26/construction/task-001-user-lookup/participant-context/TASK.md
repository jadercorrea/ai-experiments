# User lookup task

Implement `lookupUser` under the contract already declared in
`src/lookup-user.ts`.

Required behavior:

1. Remove ASCII whitespace (`space`, `tab`, `LF`, `VT`, `FF`, and `CR`) from
   both ends of `rawId`.
2. If the normalized identifier is empty, return
   `{ error: "invalid_user_id" }` without reading the user store.
3. Otherwise call the available user lookup exactly once with the normalized
   identifier.
4. Return `{ error: "not_found" }` when no user exists.
5. Return `{ ok: user }` when a user exists.

Expected failures are values, not thrown exceptions. Do not change public APIs,
test files, runtime configuration, or any file other than the declared target.
