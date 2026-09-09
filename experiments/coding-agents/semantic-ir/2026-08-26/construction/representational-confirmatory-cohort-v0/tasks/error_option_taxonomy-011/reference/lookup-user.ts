// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA29745df5089c9cd3(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-29745df5089c9cd3-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-29745df5089c9cd3-normalizer */ rawId;
    return /* ir:node:fresh-29745df5089c9cd3-validation */ (/* ir:node:fresh-29745df5089c9cd3-is-empty */ (/* ir:node:fresh-29745df5089c9cd3-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-29745df5089c9cd3-invalid */ { error: /* ir:node:fresh-29745df5089c9cd3-invalid-code */ "empty_identifier_29745df5089c9cd3" })
      : (/* ir:node:fresh-29745df5089c9cd3-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-29745df5089c9cd3-get-user */ capabilities.users.getById(/* ir:node:fresh-29745df5089c9cd3-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-29745df5089c9cd3-missing */ { error: /* ir:node:fresh-29745df5089c9cd3-missing-code */ "unknown_user_29745df5089c9cd3" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-29745df5089c9cd3-found */ { ok: /* ir:node:fresh-29745df5089c9cd3-user-ref */ user };
        })());
  })();
}
