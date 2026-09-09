// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAcc2653d4024dba89(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-cc2653d4024dba89-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-cc2653d4024dba89-normalizer */ (/* ir:node:fresh-cc2653d4024dba89-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-cc2653d4024dba89-validation */ (/* ir:node:fresh-cc2653d4024dba89-is-empty */ (/* ir:node:fresh-cc2653d4024dba89-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-cc2653d4024dba89-invalid */ { error: /* ir:node:fresh-cc2653d4024dba89-invalid-code */ "invalid_input_cc2653d4024dba89" })
      : (/* ir:node:fresh-cc2653d4024dba89-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-cc2653d4024dba89-get-user */ capabilities.users.getById(/* ir:node:fresh-cc2653d4024dba89-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-cc2653d4024dba89-retry-guard */ (/* ir:node:fresh-cc2653d4024dba89-raw-equals-normalized */ (/* ir:node:fresh-cc2653d4024dba89-raw-for-guard */ rawId) === (/* ir:node:fresh-cc2653d4024dba89-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-cc2653d4024dba89-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-cc2653d4024dba89-retry-user */ capabilities.users.getById(/* ir:node:fresh-cc2653d4024dba89-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-cc2653d4024dba89-retry-missing */ { error: /* ir:node:fresh-cc2653d4024dba89-retry-missing-code */ "not_found_cc2653d4024dba89" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-cc2653d4024dba89-retry-found */ { ok: /* ir:node:fresh-cc2653d4024dba89-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-cc2653d4024dba89-missing */ { error: /* ir:node:fresh-cc2653d4024dba89-missing-code */ "not_found_cc2653d4024dba89" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-cc2653d4024dba89-found */ { ok: /* ir:node:fresh-cc2653d4024dba89-user-ref */ user };
        })());
  })();
}
