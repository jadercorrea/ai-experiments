// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf4092fb34aaffcc0(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f4092fb34aaffcc0-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f4092fb34aaffcc0-normalizer */ (/* ir:node:fresh-f4092fb34aaffcc0-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f4092fb34aaffcc0-validation */ (/* ir:node:fresh-f4092fb34aaffcc0-is-empty */ (/* ir:node:fresh-f4092fb34aaffcc0-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f4092fb34aaffcc0-invalid */ { error: /* ir:node:fresh-f4092fb34aaffcc0-invalid-code */ "invalid_input_f4092fb34aaffcc0" })
      : (/* ir:node:fresh-f4092fb34aaffcc0-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f4092fb34aaffcc0-get-user */ capabilities.users.getById(/* ir:node:fresh-f4092fb34aaffcc0-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f4092fb34aaffcc0-retry-guard */ (/* ir:node:fresh-f4092fb34aaffcc0-raw-equals-normalized */ (/* ir:node:fresh-f4092fb34aaffcc0-raw-for-guard */ rawId) === (/* ir:node:fresh-f4092fb34aaffcc0-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-f4092fb34aaffcc0-missing */ { error: /* ir:node:fresh-f4092fb34aaffcc0-missing-code */ "not_found_f4092fb34aaffcc0" })
              : (/* ir:node:fresh-f4092fb34aaffcc0-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-f4092fb34aaffcc0-retry-user */ capabilities.users.getById(/* ir:node:fresh-f4092fb34aaffcc0-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-f4092fb34aaffcc0-retry-missing */ { error: /* ir:node:fresh-f4092fb34aaffcc0-retry-missing-code */ "not_found_f4092fb34aaffcc0" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-f4092fb34aaffcc0-retry-found */ { ok: /* ir:node:fresh-f4092fb34aaffcc0-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f4092fb34aaffcc0-found */ { ok: /* ir:node:fresh-f4092fb34aaffcc0-user-ref */ user };
        })());
  })();
}
