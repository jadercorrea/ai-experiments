// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc19d8b1933b4e996(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c19d8b1933b4e996-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c19d8b1933b4e996-normalizer */ (/* ir:node:fresh-c19d8b1933b4e996-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c19d8b1933b4e996-validation */ (/* ir:node:fresh-c19d8b1933b4e996-is-empty */ (/* ir:node:fresh-c19d8b1933b4e996-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c19d8b1933b4e996-invalid */ { error: /* ir:node:fresh-c19d8b1933b4e996-invalid-code */ "invalid_input_c19d8b1933b4e996" })
      : (/* ir:node:fresh-c19d8b1933b4e996-user-match */ (/* ir:node:fresh-c19d8b1933b4e996-reserved-equals */ (/* ir:node:fresh-c19d8b1933b4e996-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-c19d8b1933b4e996-reserved-literal */ "reserved-c19d8b19"))
          ? (/* ir:node:fresh-c19d8b1933b4e996-reserved-error */ { error: /* ir:node:fresh-c19d8b1933b4e996-reserved-error-code */ "reserved_identifier_c19d8b19" })
          : (/* ir:node:fresh-c19d8b1933b4e996-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-c19d8b1933b4e996-get-user */ capabilities.users.getById(/* ir:node:fresh-c19d8b1933b4e996-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-c19d8b1933b4e996-missing */ { error: /* ir:node:fresh-c19d8b1933b4e996-missing-code */ "not_found_c19d8b1933b4e996" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-c19d8b1933b4e996-found */ { ok: /* ir:node:fresh-c19d8b1933b4e996-user-ref */ user };
            })()));
  })();
}
