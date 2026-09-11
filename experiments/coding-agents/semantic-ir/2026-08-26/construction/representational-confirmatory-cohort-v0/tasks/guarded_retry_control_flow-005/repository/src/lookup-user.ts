// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6b8df1f85c2fff65(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6b8df1f85c2fff65-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6b8df1f85c2fff65-normalizer */ (/* ir:node:fresh-6b8df1f85c2fff65-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-6b8df1f85c2fff65-validation */ (/* ir:node:fresh-6b8df1f85c2fff65-is-empty */ (/* ir:node:fresh-6b8df1f85c2fff65-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6b8df1f85c2fff65-invalid */ { error: /* ir:node:fresh-6b8df1f85c2fff65-invalid-code */ "invalid_input_6b8df1f85c2fff65" })
      : (/* ir:node:fresh-6b8df1f85c2fff65-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6b8df1f85c2fff65-get-user */ capabilities.users.getById(/* ir:node:fresh-6b8df1f85c2fff65-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6b8df1f85c2fff65-missing */ { error: /* ir:node:fresh-6b8df1f85c2fff65-missing-code */ "not_found_6b8df1f85c2fff65" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6b8df1f85c2fff65-found */ { ok: /* ir:node:fresh-6b8df1f85c2fff65-user-ref */ user };
        })());
  })();
}
