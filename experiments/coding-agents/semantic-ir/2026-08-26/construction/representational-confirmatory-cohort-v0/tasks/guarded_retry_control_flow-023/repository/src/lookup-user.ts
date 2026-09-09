// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0f7a8dccc7bceb73(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0f7a8dccc7bceb73-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0f7a8dccc7bceb73-normalizer */ (/* ir:node:fresh-0f7a8dccc7bceb73-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0f7a8dccc7bceb73-validation */ (/* ir:node:fresh-0f7a8dccc7bceb73-is-empty */ (/* ir:node:fresh-0f7a8dccc7bceb73-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0f7a8dccc7bceb73-invalid */ { error: /* ir:node:fresh-0f7a8dccc7bceb73-invalid-code */ "invalid_input_0f7a8dccc7bceb73" })
      : (/* ir:node:fresh-0f7a8dccc7bceb73-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0f7a8dccc7bceb73-get-user */ capabilities.users.getById(/* ir:node:fresh-0f7a8dccc7bceb73-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0f7a8dccc7bceb73-missing */ { error: /* ir:node:fresh-0f7a8dccc7bceb73-missing-code */ "not_found_0f7a8dccc7bceb73" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0f7a8dccc7bceb73-found */ { ok: /* ir:node:fresh-0f7a8dccc7bceb73-user-ref */ user };
        })());
  })();
}
