// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfe753c3493dde13d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fe753c3493dde13d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fe753c3493dde13d-normalizer */ (/* ir:node:fresh-fe753c3493dde13d-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-fe753c3493dde13d-validation */ (/* ir:node:fresh-fe753c3493dde13d-is-empty */ (/* ir:node:fresh-fe753c3493dde13d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fe753c3493dde13d-invalid */ { error: /* ir:node:fresh-fe753c3493dde13d-invalid-code */ "invalid_input_fe753c3493dde13d" })
      : (/* ir:node:fresh-fe753c3493dde13d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fe753c3493dde13d-get-user */ capabilities.users.getById(/* ir:node:fresh-fe753c3493dde13d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fe753c3493dde13d-missing */ { error: /* ir:node:fresh-fe753c3493dde13d-missing-code */ "not_found_fe753c3493dde13d" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fe753c3493dde13d-found */ { ok: /* ir:node:fresh-fe753c3493dde13d-user-ref */ user };
        })());
  })();
}
