// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAbb3fc46580d0e26c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-bb3fc46580d0e26c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-bb3fc46580d0e26c-normalizer */ (/* ir:node:fresh-bb3fc46580d0e26c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-bb3fc46580d0e26c-validation */ (/* ir:node:fresh-bb3fc46580d0e26c-is-empty */ (/* ir:node:fresh-bb3fc46580d0e26c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-bb3fc46580d0e26c-invalid */ { error: /* ir:node:fresh-bb3fc46580d0e26c-invalid-code */ "invalid_input_bb3fc46580d0e26c" })
      : (/* ir:node:fresh-bb3fc46580d0e26c-user-match */ (/* ir:node:fresh-bb3fc46580d0e26c-reserved-equals */ (/* ir:node:fresh-bb3fc46580d0e26c-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-bb3fc46580d0e26c-reserved-literal */ "reserved-bb3fc465"))
          ? (/* ir:node:fresh-bb3fc46580d0e26c-reserved-error */ { error: /* ir:node:fresh-bb3fc46580d0e26c-reserved-error-code */ "reserved_identifier_bb3fc465" })
          : (/* ir:node:fresh-bb3fc46580d0e26c-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-bb3fc46580d0e26c-get-user */ capabilities.users.getById(/* ir:node:fresh-bb3fc46580d0e26c-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-bb3fc46580d0e26c-missing */ { error: /* ir:node:fresh-bb3fc46580d0e26c-missing-code */ "not_found_bb3fc46580d0e26c" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-bb3fc46580d0e26c-found */ { ok: /* ir:node:fresh-bb3fc46580d0e26c-user-ref */ user };
            })()));
  })();
}
