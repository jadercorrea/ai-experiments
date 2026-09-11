// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA242689bdb22143e7(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-242689bdb22143e7-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-242689bdb22143e7-normalizer */ (/* ir:node:fresh-242689bdb22143e7-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-242689bdb22143e7-validation */ (/* ir:node:fresh-242689bdb22143e7-is-empty */ (/* ir:node:fresh-242689bdb22143e7-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-242689bdb22143e7-invalid */ { error: /* ir:node:fresh-242689bdb22143e7-invalid-code */ "invalid_input_242689bdb22143e7" })
      : (/* ir:node:fresh-242689bdb22143e7-user-match */ (/* ir:node:fresh-242689bdb22143e7-reserved-equals */ (/* ir:node:fresh-242689bdb22143e7-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-242689bdb22143e7-reserved-literal */ "reserved-242689bd"))
          ? (/* ir:node:fresh-242689bdb22143e7-reserved-error */ { error: /* ir:node:fresh-242689bdb22143e7-reserved-error-code */ "reserved_identifier_242689bd" })
          : (/* ir:node:fresh-242689bdb22143e7-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-242689bdb22143e7-get-user */ capabilities.users.getById(/* ir:node:fresh-242689bdb22143e7-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-242689bdb22143e7-missing */ { error: /* ir:node:fresh-242689bdb22143e7-missing-code */ "not_found_242689bdb22143e7" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-242689bdb22143e7-found */ { ok: /* ir:node:fresh-242689bdb22143e7-user-ref */ user };
            })()));
  })();
}
