// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9db02e7e29480340(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9db02e7e29480340-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9db02e7e29480340-normalizer */ (/* ir:node:fresh-9db02e7e29480340-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9db02e7e29480340-validation */ (/* ir:node:fresh-9db02e7e29480340-is-empty */ (/* ir:node:fresh-9db02e7e29480340-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9db02e7e29480340-invalid */ { error: /* ir:node:fresh-9db02e7e29480340-invalid-code */ "invalid_input_9db02e7e29480340" })
      : (/* ir:node:fresh-9db02e7e29480340-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9db02e7e29480340-get-user */ capabilities.users.getById(/* ir:node:fresh-9db02e7e29480340-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9db02e7e29480340-missing */ { error: /* ir:node:fresh-9db02e7e29480340-missing-code */ "not_found_9db02e7e29480340" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9db02e7e29480340-found */ { ok: /* ir:node:fresh-9db02e7e29480340-user-ref */ user };
        })());
  })();
}
