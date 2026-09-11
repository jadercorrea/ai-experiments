// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1cdcd7bc06ff8b25(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1cdcd7bc06ff8b25-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1cdcd7bc06ff8b25-normalizer */ (/* ir:node:fresh-1cdcd7bc06ff8b25-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1cdcd7bc06ff8b25-validation */ (/* ir:node:fresh-1cdcd7bc06ff8b25-is-empty */ (/* ir:node:fresh-1cdcd7bc06ff8b25-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1cdcd7bc06ff8b25-invalid */ { error: /* ir:node:fresh-1cdcd7bc06ff8b25-invalid-code */ "invalid_input_1cdcd7bc06ff8b25" })
      : (/* ir:node:fresh-1cdcd7bc06ff8b25-user-match */ (/* ir:node:fresh-1cdcd7bc06ff8b25-reserved-equals */ (/* ir:node:fresh-1cdcd7bc06ff8b25-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-1cdcd7bc06ff8b25-reserved-literal */ "reserved-1cdcd7bc"))
          ? (/* ir:node:fresh-1cdcd7bc06ff8b25-reserved-error */ { error: /* ir:node:fresh-1cdcd7bc06ff8b25-reserved-error-code */ "reserved_identifier_1cdcd7bc" })
          : (/* ir:node:fresh-1cdcd7bc06ff8b25-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-1cdcd7bc06ff8b25-get-user */ capabilities.users.getById(/* ir:node:fresh-1cdcd7bc06ff8b25-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-1cdcd7bc06ff8b25-missing */ { error: /* ir:node:fresh-1cdcd7bc06ff8b25-missing-code */ "not_found_1cdcd7bc06ff8b25" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-1cdcd7bc06ff8b25-found */ { ok: /* ir:node:fresh-1cdcd7bc06ff8b25-user-ref */ user };
            })()));
  })();
}
