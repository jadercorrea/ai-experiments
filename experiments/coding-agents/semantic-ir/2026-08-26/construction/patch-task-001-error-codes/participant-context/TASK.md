# Task

Change `lookupUser` so an empty ASCII-normalized identifier returns
`empty_user_id`, while a completed lookup with no matching user returns
`user_not_found`.

Preserve successful lookup behavior, ASCII-only normalization, and the rule
that empty identifiers perform no database read. Only `src/lookup-user.ts` may
change. Public and hidden evaluators run without network access.
