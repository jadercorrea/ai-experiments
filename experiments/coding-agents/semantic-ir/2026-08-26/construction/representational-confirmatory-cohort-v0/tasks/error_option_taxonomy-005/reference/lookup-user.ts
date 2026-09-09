// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA63290d366c6a1ffc(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-63290d366c6a1ffc-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-63290d366c6a1ffc-normalizer */ (/* ir:node:fresh-63290d366c6a1ffc-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-63290d366c6a1ffc-validation */ (/* ir:node:fresh-63290d366c6a1ffc-is-empty */ (/* ir:node:fresh-63290d366c6a1ffc-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-63290d366c6a1ffc-invalid */ { error: /* ir:node:fresh-63290d366c6a1ffc-invalid-code */ "empty_identifier_63290d366c6a1ffc" })
      : (/* ir:node:fresh-63290d366c6a1ffc-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-63290d366c6a1ffc-get-user */ capabilities.users.getById(/* ir:node:fresh-63290d366c6a1ffc-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-63290d366c6a1ffc-missing */ { error: /* ir:node:fresh-63290d366c6a1ffc-missing-code */ "unknown_user_63290d366c6a1ffc" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-63290d366c6a1ffc-found */ { ok: /* ir:node:fresh-63290d366c6a1ffc-user-ref */ user };
        })());
  })();
}
