// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb9f03dd500f6fcd4(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b9f03dd500f6fcd4-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b9f03dd500f6fcd4-normalizer */ (/* ir:node:fresh-b9f03dd500f6fcd4-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b9f03dd500f6fcd4-validation */ (/* ir:node:fresh-b9f03dd500f6fcd4-is-empty */ (/* ir:node:fresh-b9f03dd500f6fcd4-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b9f03dd500f6fcd4-invalid */ { error: /* ir:node:fresh-b9f03dd500f6fcd4-invalid-code */ "invalid_input_b9f03dd500f6fcd4" })
      : (/* ir:node:fresh-b9f03dd500f6fcd4-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b9f03dd500f6fcd4-get-user */ capabilities.users.getById(/* ir:node:fresh-b9f03dd500f6fcd4-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b9f03dd500f6fcd4-missing */ { error: /* ir:node:fresh-b9f03dd500f6fcd4-missing-code */ "not_found_b9f03dd500f6fcd4" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b9f03dd500f6fcd4-found */ { ok: /* ir:node:fresh-b9f03dd500f6fcd4-user-ref */ user };
        })());
  })();
}
