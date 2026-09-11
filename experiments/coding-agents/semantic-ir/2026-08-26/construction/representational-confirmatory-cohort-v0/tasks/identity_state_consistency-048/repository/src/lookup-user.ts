// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0159060987c6c8da(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0159060987c6c8da-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0159060987c6c8da-normalizer */ (/* ir:node:fresh-0159060987c6c8da-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0159060987c6c8da-validation */ (/* ir:node:fresh-0159060987c6c8da-is-empty */ (/* ir:node:fresh-0159060987c6c8da-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0159060987c6c8da-invalid */ { error: /* ir:node:fresh-0159060987c6c8da-invalid-code */ "invalid_input_0159060987c6c8da" })
      : (/* ir:node:fresh-0159060987c6c8da-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0159060987c6c8da-get-user */ capabilities.users.getById(/* ir:node:fresh-0159060987c6c8da-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0159060987c6c8da-missing */ { error: /* ir:node:fresh-0159060987c6c8da-missing-code */ "not_found_0159060987c6c8da" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0159060987c6c8da-found */ { ok: /* ir:node:fresh-0159060987c6c8da-user-ref */ user };
        })());
  })();
}
