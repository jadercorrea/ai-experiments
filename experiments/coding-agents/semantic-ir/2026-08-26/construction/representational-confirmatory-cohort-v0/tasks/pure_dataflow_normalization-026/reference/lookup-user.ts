// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA70b043ca9d408d4c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-70b043ca9d408d4c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-70b043ca9d408d4c-normalizer */ rawId;
    return /* ir:node:fresh-70b043ca9d408d4c-validation */ (/* ir:node:fresh-70b043ca9d408d4c-is-empty */ (/* ir:node:fresh-70b043ca9d408d4c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-70b043ca9d408d4c-invalid */ { error: /* ir:node:fresh-70b043ca9d408d4c-invalid-code */ "invalid_input_70b043ca9d408d4c" })
      : (/* ir:node:fresh-70b043ca9d408d4c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-70b043ca9d408d4c-get-user */ capabilities.users.getById(/* ir:node:fresh-70b043ca9d408d4c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-70b043ca9d408d4c-missing */ { error: /* ir:node:fresh-70b043ca9d408d4c-missing-code */ "not_found_70b043ca9d408d4c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-70b043ca9d408d4c-found */ { ok: /* ir:node:fresh-70b043ca9d408d4c-user-ref */ user };
        })());
  })();
}
