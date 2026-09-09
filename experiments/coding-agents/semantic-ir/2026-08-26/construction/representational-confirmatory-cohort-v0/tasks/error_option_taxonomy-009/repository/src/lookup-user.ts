// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5eb6e7732fb61639(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5eb6e7732fb61639-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5eb6e7732fb61639-normalizer */ rawId;
    return /* ir:node:fresh-5eb6e7732fb61639-validation */ (/* ir:node:fresh-5eb6e7732fb61639-is-empty */ (/* ir:node:fresh-5eb6e7732fb61639-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5eb6e7732fb61639-invalid */ { error: /* ir:node:fresh-5eb6e7732fb61639-invalid-code */ "invalid_input_5eb6e7732fb61639" })
      : (/* ir:node:fresh-5eb6e7732fb61639-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5eb6e7732fb61639-get-user */ capabilities.users.getById(/* ir:node:fresh-5eb6e7732fb61639-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5eb6e7732fb61639-missing */ { error: /* ir:node:fresh-5eb6e7732fb61639-missing-code */ "not_found_5eb6e7732fb61639" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5eb6e7732fb61639-found */ { ok: /* ir:node:fresh-5eb6e7732fb61639-user-ref */ user };
        })());
  })();
}
