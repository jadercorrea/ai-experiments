// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfeeb7480f51250e6(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-feeb7480f51250e6-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-feeb7480f51250e6-normalizer */ (/* ir:node:fresh-feeb7480f51250e6-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-feeb7480f51250e6-validation */ (/* ir:node:fresh-feeb7480f51250e6-is-empty */ (/* ir:node:fresh-feeb7480f51250e6-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-feeb7480f51250e6-invalid */ { error: /* ir:node:fresh-feeb7480f51250e6-invalid-code */ "invalid_input_feeb7480f51250e6" })
      : (/* ir:node:fresh-feeb7480f51250e6-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-feeb7480f51250e6-get-user */ capabilities.users.getById(/* ir:node:fresh-feeb7480f51250e6-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-feeb7480f51250e6-retry-guard */ (/* ir:node:fresh-feeb7480f51250e6-raw-equals-normalized */ (/* ir:node:fresh-feeb7480f51250e6-raw-for-guard */ rawId) === (/* ir:node:fresh-feeb7480f51250e6-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-feeb7480f51250e6-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-feeb7480f51250e6-retry-user */ capabilities.users.getById(/* ir:node:fresh-feeb7480f51250e6-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-feeb7480f51250e6-retry-missing */ { error: /* ir:node:fresh-feeb7480f51250e6-retry-missing-code */ "not_found_feeb7480f51250e6" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-feeb7480f51250e6-retry-found */ { ok: /* ir:node:fresh-feeb7480f51250e6-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-feeb7480f51250e6-missing */ { error: /* ir:node:fresh-feeb7480f51250e6-missing-code */ "not_found_feeb7480f51250e6" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-feeb7480f51250e6-found */ { ok: /* ir:node:fresh-feeb7480f51250e6-user-ref */ user };
        })());
  })();
}
