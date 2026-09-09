// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA944d1d42edea3e5f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-944d1d42edea3e5f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-944d1d42edea3e5f-normalizer */ (/* ir:node:fresh-944d1d42edea3e5f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-944d1d42edea3e5f-validation */ (/* ir:node:fresh-944d1d42edea3e5f-is-empty */ (/* ir:node:fresh-944d1d42edea3e5f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-944d1d42edea3e5f-invalid */ { error: /* ir:node:fresh-944d1d42edea3e5f-invalid-code */ "invalid_input_944d1d42edea3e5f" })
      : (/* ir:node:fresh-944d1d42edea3e5f-user-match */ (/* ir:node:fresh-944d1d42edea3e5f-reserved-equals */ (/* ir:node:fresh-944d1d42edea3e5f-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-944d1d42edea3e5f-reserved-literal */ "reserved-944d1d42"))
          ? (/* ir:node:fresh-944d1d42edea3e5f-reserved-error */ { error: /* ir:node:fresh-944d1d42edea3e5f-reserved-error-code */ "reserved_identifier_944d1d42" })
          : (/* ir:node:fresh-944d1d42edea3e5f-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-944d1d42edea3e5f-get-user */ capabilities.users.getById(/* ir:node:fresh-944d1d42edea3e5f-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-944d1d42edea3e5f-missing */ { error: /* ir:node:fresh-944d1d42edea3e5f-missing-code */ "not_found_944d1d42edea3e5f" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-944d1d42edea3e5f-found */ { ok: /* ir:node:fresh-944d1d42edea3e5f-user-ref */ user };
            })()));
  })();
}
