# Semantic submission policy

Do not edit TypeScript. Emit semantic IR matching the supplied program schema
and closed catalog. Set `program_id` to exactly `program:user-lookup`. The
deterministic backend will validate the object and materialize
`src/lookup-user.ts`. An unknown symbol, unresolved identity, type mismatch,
undeclared effect, or unsupported operation invalidates the submission before
evaluation.
