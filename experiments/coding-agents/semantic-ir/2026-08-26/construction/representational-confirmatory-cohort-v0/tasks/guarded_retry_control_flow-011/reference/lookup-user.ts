// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA88df68f82edd2818(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-88df68f82edd2818-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-88df68f82edd2818-normalizer */ (/* ir:node:fresh-88df68f82edd2818-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-88df68f82edd2818-validation */ (/* ir:node:fresh-88df68f82edd2818-is-empty */ (/* ir:node:fresh-88df68f82edd2818-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-88df68f82edd2818-invalid */ { error: /* ir:node:fresh-88df68f82edd2818-invalid-code */ "invalid_input_88df68f82edd2818" })
      : (/* ir:node:fresh-88df68f82edd2818-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-88df68f82edd2818-get-user */ capabilities.users.getById(/* ir:node:fresh-88df68f82edd2818-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-88df68f82edd2818-retry-guard */ (/* ir:node:fresh-88df68f82edd2818-raw-equals-normalized */ (/* ir:node:fresh-88df68f82edd2818-raw-for-guard */ rawId) === (/* ir:node:fresh-88df68f82edd2818-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-88df68f82edd2818-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-88df68f82edd2818-retry-user */ capabilities.users.getById(/* ir:node:fresh-88df68f82edd2818-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-88df68f82edd2818-retry-missing */ { error: /* ir:node:fresh-88df68f82edd2818-retry-missing-code */ "not_found_88df68f82edd2818" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-88df68f82edd2818-retry-found */ { ok: /* ir:node:fresh-88df68f82edd2818-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-88df68f82edd2818-missing */ { error: /* ir:node:fresh-88df68f82edd2818-missing-code */ "not_found_88df68f82edd2818" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-88df68f82edd2818-found */ { ok: /* ir:node:fresh-88df68f82edd2818-user-ref */ user };
        })());
  })();
}
