// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc5d6d7d202e4c1f9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c5d6d7d202e4c1f9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c5d6d7d202e4c1f9-normalizer */ (/* ir:node:fresh-c5d6d7d202e4c1f9-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c5d6d7d202e4c1f9-validation */ (/* ir:node:fresh-c5d6d7d202e4c1f9-is-empty */ (/* ir:node:fresh-c5d6d7d202e4c1f9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c5d6d7d202e4c1f9-invalid */ { error: /* ir:node:fresh-c5d6d7d202e4c1f9-invalid-code */ "empty_identifier_c5d6d7d202e4c1f9" })
      : (/* ir:node:fresh-c5d6d7d202e4c1f9-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c5d6d7d202e4c1f9-get-user */ capabilities.users.getById(/* ir:node:fresh-c5d6d7d202e4c1f9-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c5d6d7d202e4c1f9-missing */ { error: /* ir:node:fresh-c5d6d7d202e4c1f9-missing-code */ "unknown_user_c5d6d7d202e4c1f9" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c5d6d7d202e4c1f9-found */ { ok: /* ir:node:fresh-c5d6d7d202e4c1f9-user-ref */ user };
        })());
  })();
}
