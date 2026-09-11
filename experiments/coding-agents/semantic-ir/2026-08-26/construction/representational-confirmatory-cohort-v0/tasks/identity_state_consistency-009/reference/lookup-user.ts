// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAce321b734306227c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ce321b734306227c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ce321b734306227c-normalizer */ (/* ir:node:fresh-ce321b734306227c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ce321b734306227c-validation */ (/* ir:node:fresh-ce321b734306227c-is-empty */ (/* ir:node:fresh-ce321b734306227c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ce321b734306227c-invalid */ { error: /* ir:node:fresh-ce321b734306227c-invalid-code */ "invalid_input_ce321b734306227c" })
      : (/* ir:node:fresh-ce321b734306227c-user-match */ (/* ir:node:fresh-ce321b734306227c-reserved-equals */ (/* ir:node:fresh-ce321b734306227c-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-ce321b734306227c-reserved-literal */ "reserved-ce321b73"))
          ? (/* ir:node:fresh-ce321b734306227c-reserved-error */ { error: /* ir:node:fresh-ce321b734306227c-reserved-error-code */ "reserved_identifier_ce321b73" })
          : (/* ir:node:fresh-ce321b734306227c-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-ce321b734306227c-get-user */ capabilities.users.getById(/* ir:node:fresh-ce321b734306227c-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-ce321b734306227c-missing */ { error: /* ir:node:fresh-ce321b734306227c-missing-code */ "not_found_ce321b734306227c" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-ce321b734306227c-found */ { ok: /* ir:node:fresh-ce321b734306227c-user-ref */ user };
            })()));
  })();
}
