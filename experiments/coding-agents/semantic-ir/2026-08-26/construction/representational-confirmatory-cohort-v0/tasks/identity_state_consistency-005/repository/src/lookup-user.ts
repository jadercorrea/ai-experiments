// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA3bec53dff281a882(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-3bec53dff281a882-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-3bec53dff281a882-normalizer */ (/* ir:node:fresh-3bec53dff281a882-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-3bec53dff281a882-validation */ (/* ir:node:fresh-3bec53dff281a882-is-empty */ (/* ir:node:fresh-3bec53dff281a882-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-3bec53dff281a882-invalid */ { error: /* ir:node:fresh-3bec53dff281a882-invalid-code */ "invalid_input_3bec53dff281a882" })
      : (/* ir:node:fresh-3bec53dff281a882-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-3bec53dff281a882-get-user */ capabilities.users.getById(/* ir:node:fresh-3bec53dff281a882-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-3bec53dff281a882-missing */ { error: /* ir:node:fresh-3bec53dff281a882-missing-code */ "not_found_3bec53dff281a882" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-3bec53dff281a882-found */ { ok: /* ir:node:fresh-3bec53dff281a882-user-ref */ user };
        })());
  })();
}
