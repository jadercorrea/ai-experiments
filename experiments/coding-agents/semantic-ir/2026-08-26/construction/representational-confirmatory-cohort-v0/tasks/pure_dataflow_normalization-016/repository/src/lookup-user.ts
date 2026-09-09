// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA61ef8990c2cdd5fc(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-61ef8990c2cdd5fc-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-61ef8990c2cdd5fc-normalizer */ (/* ir:node:fresh-61ef8990c2cdd5fc-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-61ef8990c2cdd5fc-validation */ (/* ir:node:fresh-61ef8990c2cdd5fc-is-empty */ (/* ir:node:fresh-61ef8990c2cdd5fc-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-61ef8990c2cdd5fc-invalid */ { error: /* ir:node:fresh-61ef8990c2cdd5fc-invalid-code */ "invalid_input_61ef8990c2cdd5fc" })
      : (/* ir:node:fresh-61ef8990c2cdd5fc-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-61ef8990c2cdd5fc-get-user */ capabilities.users.getById(/* ir:node:fresh-61ef8990c2cdd5fc-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-61ef8990c2cdd5fc-missing */ { error: /* ir:node:fresh-61ef8990c2cdd5fc-missing-code */ "not_found_61ef8990c2cdd5fc" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-61ef8990c2cdd5fc-found */ { ok: /* ir:node:fresh-61ef8990c2cdd5fc-user-ref */ user };
        })());
  })();
}
