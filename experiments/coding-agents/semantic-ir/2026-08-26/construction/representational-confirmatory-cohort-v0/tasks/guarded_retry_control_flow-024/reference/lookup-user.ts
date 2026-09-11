// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAca56afe2f70afb8b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ca56afe2f70afb8b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ca56afe2f70afb8b-normalizer */ (/* ir:node:fresh-ca56afe2f70afb8b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ca56afe2f70afb8b-validation */ (/* ir:node:fresh-ca56afe2f70afb8b-is-empty */ (/* ir:node:fresh-ca56afe2f70afb8b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ca56afe2f70afb8b-invalid */ { error: /* ir:node:fresh-ca56afe2f70afb8b-invalid-code */ "invalid_input_ca56afe2f70afb8b" })
      : (/* ir:node:fresh-ca56afe2f70afb8b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ca56afe2f70afb8b-get-user */ capabilities.users.getById(/* ir:node:fresh-ca56afe2f70afb8b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ca56afe2f70afb8b-retry-guard */ (/* ir:node:fresh-ca56afe2f70afb8b-raw-equals-normalized */ (/* ir:node:fresh-ca56afe2f70afb8b-raw-for-guard */ rawId) === (/* ir:node:fresh-ca56afe2f70afb8b-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-ca56afe2f70afb8b-missing */ { error: /* ir:node:fresh-ca56afe2f70afb8b-missing-code */ "not_found_ca56afe2f70afb8b" })
              : (/* ir:node:fresh-ca56afe2f70afb8b-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-ca56afe2f70afb8b-retry-user */ capabilities.users.getById(/* ir:node:fresh-ca56afe2f70afb8b-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-ca56afe2f70afb8b-retry-missing */ { error: /* ir:node:fresh-ca56afe2f70afb8b-retry-missing-code */ "not_found_ca56afe2f70afb8b" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-ca56afe2f70afb8b-retry-found */ { ok: /* ir:node:fresh-ca56afe2f70afb8b-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ca56afe2f70afb8b-found */ { ok: /* ir:node:fresh-ca56afe2f70afb8b-user-ref */ user };
        })());
  })();
}
