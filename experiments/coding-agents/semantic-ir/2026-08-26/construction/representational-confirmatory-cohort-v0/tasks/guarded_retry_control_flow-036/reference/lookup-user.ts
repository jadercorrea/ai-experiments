// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd0c90a13622f6036(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d0c90a13622f6036-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d0c90a13622f6036-normalizer */ (/* ir:node:fresh-d0c90a13622f6036-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d0c90a13622f6036-validation */ (/* ir:node:fresh-d0c90a13622f6036-is-empty */ (/* ir:node:fresh-d0c90a13622f6036-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d0c90a13622f6036-invalid */ { error: /* ir:node:fresh-d0c90a13622f6036-invalid-code */ "invalid_input_d0c90a13622f6036" })
      : (/* ir:node:fresh-d0c90a13622f6036-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d0c90a13622f6036-get-user */ capabilities.users.getById(/* ir:node:fresh-d0c90a13622f6036-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d0c90a13622f6036-retry-guard */ (/* ir:node:fresh-d0c90a13622f6036-raw-equals-normalized */ (/* ir:node:fresh-d0c90a13622f6036-raw-for-guard */ rawId) === (/* ir:node:fresh-d0c90a13622f6036-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-d0c90a13622f6036-missing */ { error: /* ir:node:fresh-d0c90a13622f6036-missing-code */ "not_found_d0c90a13622f6036" })
              : (/* ir:node:fresh-d0c90a13622f6036-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-d0c90a13622f6036-retry-user */ capabilities.users.getById(/* ir:node:fresh-d0c90a13622f6036-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-d0c90a13622f6036-retry-missing */ { error: /* ir:node:fresh-d0c90a13622f6036-retry-missing-code */ "not_found_d0c90a13622f6036" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-d0c90a13622f6036-retry-found */ { ok: /* ir:node:fresh-d0c90a13622f6036-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d0c90a13622f6036-found */ { ok: /* ir:node:fresh-d0c90a13622f6036-user-ref */ user };
        })());
  })();
}
