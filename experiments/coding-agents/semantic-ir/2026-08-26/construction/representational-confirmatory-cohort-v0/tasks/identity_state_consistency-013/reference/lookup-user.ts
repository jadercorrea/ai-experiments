// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA811bc766a6ab5219(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-811bc766a6ab5219-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-811bc766a6ab5219-normalizer */ (/* ir:node:fresh-811bc766a6ab5219-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-811bc766a6ab5219-validation */ (/* ir:node:fresh-811bc766a6ab5219-is-empty */ (/* ir:node:fresh-811bc766a6ab5219-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-811bc766a6ab5219-invalid */ { error: /* ir:node:fresh-811bc766a6ab5219-invalid-code */ "invalid_input_811bc766a6ab5219" })
      : (/* ir:node:fresh-811bc766a6ab5219-user-match */ (/* ir:node:fresh-811bc766a6ab5219-reserved-equals */ (/* ir:node:fresh-811bc766a6ab5219-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-811bc766a6ab5219-reserved-literal */ "reserved-811bc766"))
          ? (/* ir:node:fresh-811bc766a6ab5219-reserved-error */ { error: /* ir:node:fresh-811bc766a6ab5219-reserved-error-code */ "reserved_identifier_811bc766" })
          : (/* ir:node:fresh-811bc766a6ab5219-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-811bc766a6ab5219-get-user */ capabilities.users.getById(/* ir:node:fresh-811bc766a6ab5219-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-811bc766a6ab5219-missing */ { error: /* ir:node:fresh-811bc766a6ab5219-missing-code */ "not_found_811bc766a6ab5219" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-811bc766a6ab5219-found */ { ok: /* ir:node:fresh-811bc766a6ab5219-user-ref */ user };
            })()));
  })();
}
