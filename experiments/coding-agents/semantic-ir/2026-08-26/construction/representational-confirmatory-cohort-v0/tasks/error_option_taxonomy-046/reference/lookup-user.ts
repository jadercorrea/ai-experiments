// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA021a3bb286e9c725(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-021a3bb286e9c725-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-021a3bb286e9c725-normalizer */ rawId;
    return /* ir:node:fresh-021a3bb286e9c725-validation */ (/* ir:node:fresh-021a3bb286e9c725-is-empty */ (/* ir:node:fresh-021a3bb286e9c725-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-021a3bb286e9c725-invalid */ { error: /* ir:node:fresh-021a3bb286e9c725-invalid-code */ "empty_identifier_021a3bb286e9c725" })
      : (/* ir:node:fresh-021a3bb286e9c725-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-021a3bb286e9c725-get-user */ capabilities.users.getById(/* ir:node:fresh-021a3bb286e9c725-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-021a3bb286e9c725-missing */ { error: /* ir:node:fresh-021a3bb286e9c725-missing-code */ "unknown_user_021a3bb286e9c725" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-021a3bb286e9c725-found */ { ok: /* ir:node:fresh-021a3bb286e9c725-user-ref */ user };
        })());
  })();
}
