// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd8f0bba3b8f8a584(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d8f0bba3b8f8a584-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d8f0bba3b8f8a584-normalizer */ (/* ir:node:fresh-d8f0bba3b8f8a584-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d8f0bba3b8f8a584-validation */ (/* ir:node:fresh-d8f0bba3b8f8a584-is-empty */ (/* ir:node:fresh-d8f0bba3b8f8a584-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d8f0bba3b8f8a584-invalid */ { error: /* ir:node:fresh-d8f0bba3b8f8a584-invalid-code */ "invalid_input_d8f0bba3b8f8a584" })
      : (/* ir:node:fresh-d8f0bba3b8f8a584-user-match */ (/* ir:node:fresh-d8f0bba3b8f8a584-reserved-equals */ (/* ir:node:fresh-d8f0bba3b8f8a584-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-d8f0bba3b8f8a584-reserved-literal */ "reserved-d8f0bba3"))
          ? (/* ir:node:fresh-d8f0bba3b8f8a584-reserved-error */ { error: /* ir:node:fresh-d8f0bba3b8f8a584-reserved-error-code */ "reserved_identifier_d8f0bba3" })
          : (/* ir:node:fresh-d8f0bba3b8f8a584-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-d8f0bba3b8f8a584-get-user */ capabilities.users.getById(/* ir:node:fresh-d8f0bba3b8f8a584-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-d8f0bba3b8f8a584-missing */ { error: /* ir:node:fresh-d8f0bba3b8f8a584-missing-code */ "not_found_d8f0bba3b8f8a584" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-d8f0bba3b8f8a584-found */ { ok: /* ir:node:fresh-d8f0bba3b8f8a584-user-ref */ user };
            })()));
  })();
}
