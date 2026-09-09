// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb1f68736d308008f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b1f68736d308008f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b1f68736d308008f-normalizer */ (/* ir:node:fresh-b1f68736d308008f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b1f68736d308008f-validation */ (/* ir:node:fresh-b1f68736d308008f-is-empty */ (/* ir:node:fresh-b1f68736d308008f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b1f68736d308008f-invalid */ { error: /* ir:node:fresh-b1f68736d308008f-invalid-code */ "invalid_input_b1f68736d308008f" })
      : (/* ir:node:fresh-b1f68736d308008f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b1f68736d308008f-get-user */ capabilities.users.getById(/* ir:node:fresh-b1f68736d308008f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b1f68736d308008f-retry-guard */ (/* ir:node:fresh-b1f68736d308008f-raw-equals-normalized */ (/* ir:node:fresh-b1f68736d308008f-raw-for-guard */ rawId) === (/* ir:node:fresh-b1f68736d308008f-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-b1f68736d308008f-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-b1f68736d308008f-retry-user */ capabilities.users.getById(/* ir:node:fresh-b1f68736d308008f-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-b1f68736d308008f-retry-missing */ { error: /* ir:node:fresh-b1f68736d308008f-retry-missing-code */ "not_found_b1f68736d308008f" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-b1f68736d308008f-retry-found */ { ok: /* ir:node:fresh-b1f68736d308008f-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-b1f68736d308008f-missing */ { error: /* ir:node:fresh-b1f68736d308008f-missing-code */ "not_found_b1f68736d308008f" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b1f68736d308008f-found */ { ok: /* ir:node:fresh-b1f68736d308008f-user-ref */ user };
        })());
  })();
}
