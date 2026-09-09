// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAabb29bcb2472149c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-abb29bcb2472149c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-abb29bcb2472149c-normalizer */ (/* ir:node:fresh-abb29bcb2472149c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-abb29bcb2472149c-validation */ (/* ir:node:fresh-abb29bcb2472149c-is-empty */ (/* ir:node:fresh-abb29bcb2472149c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-abb29bcb2472149c-invalid */ { error: /* ir:node:fresh-abb29bcb2472149c-invalid-code */ "invalid_input_abb29bcb2472149c" })
      : (/* ir:node:fresh-abb29bcb2472149c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-abb29bcb2472149c-get-user */ capabilities.users.getById(/* ir:node:fresh-abb29bcb2472149c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-abb29bcb2472149c-retry-guard */ (/* ir:node:fresh-abb29bcb2472149c-raw-equals-normalized */ (/* ir:node:fresh-abb29bcb2472149c-raw-for-guard */ rawId) === (/* ir:node:fresh-abb29bcb2472149c-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-abb29bcb2472149c-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-abb29bcb2472149c-retry-user */ capabilities.users.getById(/* ir:node:fresh-abb29bcb2472149c-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-abb29bcb2472149c-retry-missing */ { error: /* ir:node:fresh-abb29bcb2472149c-retry-missing-code */ "not_found_abb29bcb2472149c" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-abb29bcb2472149c-retry-found */ { ok: /* ir:node:fresh-abb29bcb2472149c-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-abb29bcb2472149c-missing */ { error: /* ir:node:fresh-abb29bcb2472149c-missing-code */ "not_found_abb29bcb2472149c" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-abb29bcb2472149c-found */ { ok: /* ir:node:fresh-abb29bcb2472149c-user-ref */ user };
        })());
  })();
}
