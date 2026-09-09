// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA03a27ccd8e304c36(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-03a27ccd8e304c36-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-03a27ccd8e304c36-normalizer */ (/* ir:node:fresh-03a27ccd8e304c36-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-03a27ccd8e304c36-validation */ (/* ir:node:fresh-03a27ccd8e304c36-is-empty */ (/* ir:node:fresh-03a27ccd8e304c36-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-03a27ccd8e304c36-invalid */ { error: /* ir:node:fresh-03a27ccd8e304c36-invalid-code */ "invalid_input_03a27ccd8e304c36" })
      : (/* ir:node:fresh-03a27ccd8e304c36-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-03a27ccd8e304c36-get-user */ capabilities.users.getById(/* ir:node:fresh-03a27ccd8e304c36-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-03a27ccd8e304c36-retry-guard */ (/* ir:node:fresh-03a27ccd8e304c36-raw-equals-normalized */ (/* ir:node:fresh-03a27ccd8e304c36-raw-for-guard */ rawId) === (/* ir:node:fresh-03a27ccd8e304c36-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-03a27ccd8e304c36-missing */ { error: /* ir:node:fresh-03a27ccd8e304c36-missing-code */ "not_found_03a27ccd8e304c36" })
              : (/* ir:node:fresh-03a27ccd8e304c36-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-03a27ccd8e304c36-retry-user */ capabilities.users.getById(/* ir:node:fresh-03a27ccd8e304c36-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-03a27ccd8e304c36-retry-missing */ { error: /* ir:node:fresh-03a27ccd8e304c36-retry-missing-code */ "not_found_03a27ccd8e304c36" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-03a27ccd8e304c36-retry-found */ { ok: /* ir:node:fresh-03a27ccd8e304c36-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-03a27ccd8e304c36-found */ { ok: /* ir:node:fresh-03a27ccd8e304c36-user-ref */ user };
        })());
  })();
}
