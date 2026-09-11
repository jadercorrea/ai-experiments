// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6ae1ca8672b500d0(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6ae1ca8672b500d0-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6ae1ca8672b500d0-normalizer */ (/* ir:node:fresh-6ae1ca8672b500d0-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-6ae1ca8672b500d0-validation */ (/* ir:node:fresh-6ae1ca8672b500d0-is-empty */ (/* ir:node:fresh-6ae1ca8672b500d0-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6ae1ca8672b500d0-invalid */ { error: /* ir:node:fresh-6ae1ca8672b500d0-invalid-code */ "invalid_input_6ae1ca8672b500d0" })
      : (/* ir:node:fresh-6ae1ca8672b500d0-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6ae1ca8672b500d0-get-user */ capabilities.users.getById(/* ir:node:fresh-6ae1ca8672b500d0-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6ae1ca8672b500d0-missing */ { error: /* ir:node:fresh-6ae1ca8672b500d0-missing-code */ "not_found_6ae1ca8672b500d0" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6ae1ca8672b500d0-found */ { ok: /* ir:node:fresh-6ae1ca8672b500d0-user-ref */ user };
        })());
  })();
}
