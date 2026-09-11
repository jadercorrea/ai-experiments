// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1125da7c23f64f7e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1125da7c23f64f7e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1125da7c23f64f7e-normalizer */ (/* ir:node:fresh-1125da7c23f64f7e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1125da7c23f64f7e-validation */ (/* ir:node:fresh-1125da7c23f64f7e-is-empty */ (/* ir:node:fresh-1125da7c23f64f7e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1125da7c23f64f7e-invalid */ { error: /* ir:node:fresh-1125da7c23f64f7e-invalid-code */ "invalid_input_1125da7c23f64f7e" })
      : (/* ir:node:fresh-1125da7c23f64f7e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1125da7c23f64f7e-get-user */ capabilities.users.getById(/* ir:node:fresh-1125da7c23f64f7e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1125da7c23f64f7e-retry-guard */ (/* ir:node:fresh-1125da7c23f64f7e-raw-equals-normalized */ (/* ir:node:fresh-1125da7c23f64f7e-raw-for-guard */ rawId) === (/* ir:node:fresh-1125da7c23f64f7e-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-1125da7c23f64f7e-missing */ { error: /* ir:node:fresh-1125da7c23f64f7e-missing-code */ "not_found_1125da7c23f64f7e" })
              : (/* ir:node:fresh-1125da7c23f64f7e-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-1125da7c23f64f7e-retry-user */ capabilities.users.getById(/* ir:node:fresh-1125da7c23f64f7e-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-1125da7c23f64f7e-retry-missing */ { error: /* ir:node:fresh-1125da7c23f64f7e-retry-missing-code */ "not_found_1125da7c23f64f7e" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-1125da7c23f64f7e-retry-found */ { ok: /* ir:node:fresh-1125da7c23f64f7e-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1125da7c23f64f7e-found */ { ok: /* ir:node:fresh-1125da7c23f64f7e-user-ref */ user };
        })());
  })();
}
