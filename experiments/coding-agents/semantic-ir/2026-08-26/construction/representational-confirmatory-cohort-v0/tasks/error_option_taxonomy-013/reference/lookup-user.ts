// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd25553e07a600857(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d25553e07a600857-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d25553e07a600857-normalizer */ rawId;
    return /* ir:node:fresh-d25553e07a600857-validation */ (/* ir:node:fresh-d25553e07a600857-is-empty */ (/* ir:node:fresh-d25553e07a600857-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d25553e07a600857-invalid */ { error: /* ir:node:fresh-d25553e07a600857-invalid-code */ "empty_identifier_d25553e07a600857" })
      : (/* ir:node:fresh-d25553e07a600857-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d25553e07a600857-get-user */ capabilities.users.getById(/* ir:node:fresh-d25553e07a600857-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d25553e07a600857-missing */ { error: /* ir:node:fresh-d25553e07a600857-missing-code */ "unknown_user_d25553e07a600857" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d25553e07a600857-found */ { ok: /* ir:node:fresh-d25553e07a600857-user-ref */ user };
        })());
  })();
}
