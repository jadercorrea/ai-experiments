// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1acb3449ddff86ca(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1acb3449ddff86ca-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1acb3449ddff86ca-normalizer */ (/* ir:node:fresh-1acb3449ddff86ca-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1acb3449ddff86ca-validation */ (/* ir:node:fresh-1acb3449ddff86ca-is-empty */ (/* ir:node:fresh-1acb3449ddff86ca-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1acb3449ddff86ca-invalid */ { error: /* ir:node:fresh-1acb3449ddff86ca-invalid-code */ "invalid_input_1acb3449ddff86ca" })
      : (/* ir:node:fresh-1acb3449ddff86ca-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1acb3449ddff86ca-get-user */ capabilities.users.getById(/* ir:node:fresh-1acb3449ddff86ca-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1acb3449ddff86ca-missing */ { error: /* ir:node:fresh-1acb3449ddff86ca-missing-code */ "not_found_1acb3449ddff86ca" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1acb3449ddff86ca-found */ { ok: /* ir:node:fresh-1acb3449ddff86ca-user-ref */ user };
        })());
  })();
}
