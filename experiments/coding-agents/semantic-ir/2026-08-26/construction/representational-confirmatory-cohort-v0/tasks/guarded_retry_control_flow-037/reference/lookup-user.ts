// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb7bd448413a1f3b9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b7bd448413a1f3b9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b7bd448413a1f3b9-normalizer */ (/* ir:node:fresh-b7bd448413a1f3b9-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b7bd448413a1f3b9-validation */ (/* ir:node:fresh-b7bd448413a1f3b9-is-empty */ (/* ir:node:fresh-b7bd448413a1f3b9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b7bd448413a1f3b9-invalid */ { error: /* ir:node:fresh-b7bd448413a1f3b9-invalid-code */ "invalid_input_b7bd448413a1f3b9" })
      : (/* ir:node:fresh-b7bd448413a1f3b9-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b7bd448413a1f3b9-get-user */ capabilities.users.getById(/* ir:node:fresh-b7bd448413a1f3b9-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b7bd448413a1f3b9-retry-guard */ (/* ir:node:fresh-b7bd448413a1f3b9-raw-equals-normalized */ (/* ir:node:fresh-b7bd448413a1f3b9-raw-for-guard */ rawId) === (/* ir:node:fresh-b7bd448413a1f3b9-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-b7bd448413a1f3b9-missing */ { error: /* ir:node:fresh-b7bd448413a1f3b9-missing-code */ "not_found_b7bd448413a1f3b9" })
              : (/* ir:node:fresh-b7bd448413a1f3b9-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-b7bd448413a1f3b9-retry-user */ capabilities.users.getById(/* ir:node:fresh-b7bd448413a1f3b9-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-b7bd448413a1f3b9-retry-missing */ { error: /* ir:node:fresh-b7bd448413a1f3b9-retry-missing-code */ "not_found_b7bd448413a1f3b9" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-b7bd448413a1f3b9-retry-found */ { ok: /* ir:node:fresh-b7bd448413a1f3b9-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b7bd448413a1f3b9-found */ { ok: /* ir:node:fresh-b7bd448413a1f3b9-user-ref */ user };
        })());
  })();
}
