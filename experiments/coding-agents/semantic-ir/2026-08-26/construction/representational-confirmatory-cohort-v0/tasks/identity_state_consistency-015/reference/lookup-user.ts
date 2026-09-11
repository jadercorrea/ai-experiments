// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA429b0e02e09b62c2(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-429b0e02e09b62c2-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-429b0e02e09b62c2-normalizer */ (/* ir:node:fresh-429b0e02e09b62c2-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-429b0e02e09b62c2-validation */ (/* ir:node:fresh-429b0e02e09b62c2-is-empty */ (/* ir:node:fresh-429b0e02e09b62c2-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-429b0e02e09b62c2-invalid */ { error: /* ir:node:fresh-429b0e02e09b62c2-invalid-code */ "invalid_input_429b0e02e09b62c2" })
      : (/* ir:node:fresh-429b0e02e09b62c2-user-match */ (/* ir:node:fresh-429b0e02e09b62c2-reserved-equals */ (/* ir:node:fresh-429b0e02e09b62c2-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-429b0e02e09b62c2-reserved-literal */ "reserved-429b0e02"))
          ? (/* ir:node:fresh-429b0e02e09b62c2-reserved-error */ { error: /* ir:node:fresh-429b0e02e09b62c2-reserved-error-code */ "reserved_identifier_429b0e02" })
          : (/* ir:node:fresh-429b0e02e09b62c2-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-429b0e02e09b62c2-get-user */ capabilities.users.getById(/* ir:node:fresh-429b0e02e09b62c2-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-429b0e02e09b62c2-missing */ { error: /* ir:node:fresh-429b0e02e09b62c2-missing-code */ "not_found_429b0e02e09b62c2" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-429b0e02e09b62c2-found */ { ok: /* ir:node:fresh-429b0e02e09b62c2-user-ref */ user };
            })()));
  })();
}
