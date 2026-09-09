// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1df9addc7738a42f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1df9addc7738a42f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1df9addc7738a42f-normalizer */ (/* ir:node:fresh-1df9addc7738a42f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1df9addc7738a42f-validation */ (/* ir:node:fresh-1df9addc7738a42f-is-empty */ (/* ir:node:fresh-1df9addc7738a42f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1df9addc7738a42f-invalid */ { error: /* ir:node:fresh-1df9addc7738a42f-invalid-code */ "invalid_input_1df9addc7738a42f" })
      : (/* ir:node:fresh-1df9addc7738a42f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1df9addc7738a42f-get-user */ capabilities.users.getById(/* ir:node:fresh-1df9addc7738a42f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1df9addc7738a42f-missing */ { error: /* ir:node:fresh-1df9addc7738a42f-missing-code */ "not_found_1df9addc7738a42f" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1df9addc7738a42f-found */ { ok: /* ir:node:fresh-1df9addc7738a42f-user-ref */ user };
        })());
  })();
}
