// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA75f2842e23fe47d1(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-75f2842e23fe47d1-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-75f2842e23fe47d1-normalizer */ (/* ir:node:fresh-75f2842e23fe47d1-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-75f2842e23fe47d1-validation */ (/* ir:node:fresh-75f2842e23fe47d1-is-empty */ (/* ir:node:fresh-75f2842e23fe47d1-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-75f2842e23fe47d1-invalid */ { error: /* ir:node:fresh-75f2842e23fe47d1-invalid-code */ "invalid_input_75f2842e23fe47d1" })
      : (/* ir:node:fresh-75f2842e23fe47d1-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-75f2842e23fe47d1-get-user */ capabilities.users.getById(/* ir:node:fresh-75f2842e23fe47d1-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-75f2842e23fe47d1-retry-guard */ (/* ir:node:fresh-75f2842e23fe47d1-raw-equals-normalized */ (/* ir:node:fresh-75f2842e23fe47d1-raw-for-guard */ rawId) === (/* ir:node:fresh-75f2842e23fe47d1-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-75f2842e23fe47d1-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-75f2842e23fe47d1-retry-user */ capabilities.users.getById(/* ir:node:fresh-75f2842e23fe47d1-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-75f2842e23fe47d1-retry-missing */ { error: /* ir:node:fresh-75f2842e23fe47d1-retry-missing-code */ "not_found_75f2842e23fe47d1" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-75f2842e23fe47d1-retry-found */ { ok: /* ir:node:fresh-75f2842e23fe47d1-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-75f2842e23fe47d1-missing */ { error: /* ir:node:fresh-75f2842e23fe47d1-missing-code */ "not_found_75f2842e23fe47d1" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-75f2842e23fe47d1-found */ { ok: /* ir:node:fresh-75f2842e23fe47d1-user-ref */ user };
        })());
  })();
}
