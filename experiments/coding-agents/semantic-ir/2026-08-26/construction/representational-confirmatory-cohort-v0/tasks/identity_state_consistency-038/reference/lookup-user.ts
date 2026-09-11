// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA8b864c6873d5fbea(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-8b864c6873d5fbea-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-8b864c6873d5fbea-normalizer */ (/* ir:node:fresh-8b864c6873d5fbea-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-8b864c6873d5fbea-validation */ (/* ir:node:fresh-8b864c6873d5fbea-is-empty */ (/* ir:node:fresh-8b864c6873d5fbea-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-8b864c6873d5fbea-invalid */ { error: /* ir:node:fresh-8b864c6873d5fbea-invalid-code */ "invalid_input_8b864c6873d5fbea" })
      : (/* ir:node:fresh-8b864c6873d5fbea-user-match */ (/* ir:node:fresh-8b864c6873d5fbea-reserved-equals */ (/* ir:node:fresh-8b864c6873d5fbea-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-8b864c6873d5fbea-reserved-literal */ "reserved-8b864c68"))
          ? (/* ir:node:fresh-8b864c6873d5fbea-reserved-error */ { error: /* ir:node:fresh-8b864c6873d5fbea-reserved-error-code */ "reserved_identifier_8b864c68" })
          : (/* ir:node:fresh-8b864c6873d5fbea-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-8b864c6873d5fbea-get-user */ capabilities.users.getById(/* ir:node:fresh-8b864c6873d5fbea-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-8b864c6873d5fbea-missing */ { error: /* ir:node:fresh-8b864c6873d5fbea-missing-code */ "not_found_8b864c6873d5fbea" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-8b864c6873d5fbea-found */ { ok: /* ir:node:fresh-8b864c6873d5fbea-user-ref */ user };
            })()));
  })();
}
