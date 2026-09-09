// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5de2791e9822bc24(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5de2791e9822bc24-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5de2791e9822bc24-normalizer */ (/* ir:node:fresh-5de2791e9822bc24-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5de2791e9822bc24-validation */ (/* ir:node:fresh-5de2791e9822bc24-is-empty */ (/* ir:node:fresh-5de2791e9822bc24-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5de2791e9822bc24-invalid */ { error: /* ir:node:fresh-5de2791e9822bc24-invalid-code */ "invalid_input_5de2791e9822bc24" })
      : (/* ir:node:fresh-5de2791e9822bc24-user-match */ (/* ir:node:fresh-5de2791e9822bc24-reserved-equals */ (/* ir:node:fresh-5de2791e9822bc24-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-5de2791e9822bc24-reserved-literal */ "reserved-5de2791e"))
          ? (/* ir:node:fresh-5de2791e9822bc24-reserved-error */ { error: /* ir:node:fresh-5de2791e9822bc24-reserved-error-code */ "reserved_identifier_5de2791e" })
          : (/* ir:node:fresh-5de2791e9822bc24-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-5de2791e9822bc24-get-user */ capabilities.users.getById(/* ir:node:fresh-5de2791e9822bc24-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-5de2791e9822bc24-missing */ { error: /* ir:node:fresh-5de2791e9822bc24-missing-code */ "not_found_5de2791e9822bc24" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-5de2791e9822bc24-found */ { ok: /* ir:node:fresh-5de2791e9822bc24-user-ref */ user };
            })()));
  })();
}
