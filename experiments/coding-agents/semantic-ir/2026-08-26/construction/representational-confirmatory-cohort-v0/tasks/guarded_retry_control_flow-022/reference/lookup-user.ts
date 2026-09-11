// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf44bf18a4c67f50c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f44bf18a4c67f50c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f44bf18a4c67f50c-normalizer */ (/* ir:node:fresh-f44bf18a4c67f50c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f44bf18a4c67f50c-validation */ (/* ir:node:fresh-f44bf18a4c67f50c-is-empty */ (/* ir:node:fresh-f44bf18a4c67f50c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f44bf18a4c67f50c-invalid */ { error: /* ir:node:fresh-f44bf18a4c67f50c-invalid-code */ "invalid_input_f44bf18a4c67f50c" })
      : (/* ir:node:fresh-f44bf18a4c67f50c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f44bf18a4c67f50c-get-user */ capabilities.users.getById(/* ir:node:fresh-f44bf18a4c67f50c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f44bf18a4c67f50c-retry-guard */ (/* ir:node:fresh-f44bf18a4c67f50c-raw-equals-normalized */ (/* ir:node:fresh-f44bf18a4c67f50c-raw-for-guard */ rawId) === (/* ir:node:fresh-f44bf18a4c67f50c-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-f44bf18a4c67f50c-missing */ { error: /* ir:node:fresh-f44bf18a4c67f50c-missing-code */ "not_found_f44bf18a4c67f50c" })
              : (/* ir:node:fresh-f44bf18a4c67f50c-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-f44bf18a4c67f50c-retry-user */ capabilities.users.getById(/* ir:node:fresh-f44bf18a4c67f50c-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-f44bf18a4c67f50c-retry-missing */ { error: /* ir:node:fresh-f44bf18a4c67f50c-retry-missing-code */ "not_found_f44bf18a4c67f50c" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-f44bf18a4c67f50c-retry-found */ { ok: /* ir:node:fresh-f44bf18a4c67f50c-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f44bf18a4c67f50c-found */ { ok: /* ir:node:fresh-f44bf18a4c67f50c-user-ref */ user };
        })());
  })();
}
