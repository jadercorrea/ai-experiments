// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA18925ad6a516c98a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-18925ad6a516c98a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-18925ad6a516c98a-normalizer */ (/* ir:node:fresh-18925ad6a516c98a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-18925ad6a516c98a-validation */ (/* ir:node:fresh-18925ad6a516c98a-is-empty */ (/* ir:node:fresh-18925ad6a516c98a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-18925ad6a516c98a-invalid */ { error: /* ir:node:fresh-18925ad6a516c98a-invalid-code */ "invalid_input_18925ad6a516c98a" })
      : (/* ir:node:fresh-18925ad6a516c98a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-18925ad6a516c98a-get-user */ capabilities.users.getById(/* ir:node:fresh-18925ad6a516c98a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-18925ad6a516c98a-retry-guard */ (/* ir:node:fresh-18925ad6a516c98a-raw-equals-normalized */ (/* ir:node:fresh-18925ad6a516c98a-raw-for-guard */ rawId) === (/* ir:node:fresh-18925ad6a516c98a-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-18925ad6a516c98a-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-18925ad6a516c98a-retry-user */ capabilities.users.getById(/* ir:node:fresh-18925ad6a516c98a-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-18925ad6a516c98a-retry-missing */ { error: /* ir:node:fresh-18925ad6a516c98a-retry-missing-code */ "not_found_18925ad6a516c98a" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-18925ad6a516c98a-retry-found */ { ok: /* ir:node:fresh-18925ad6a516c98a-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-18925ad6a516c98a-missing */ { error: /* ir:node:fresh-18925ad6a516c98a-missing-code */ "not_found_18925ad6a516c98a" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-18925ad6a516c98a-found */ { ok: /* ir:node:fresh-18925ad6a516c98a-user-ref */ user };
        })());
  })();
}
