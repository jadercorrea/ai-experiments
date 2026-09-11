// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA97276b71aaac4056(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-97276b71aaac4056-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-97276b71aaac4056-normalizer */ (/* ir:node:fresh-97276b71aaac4056-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-97276b71aaac4056-validation */ (/* ir:node:fresh-97276b71aaac4056-is-empty */ (/* ir:node:fresh-97276b71aaac4056-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-97276b71aaac4056-invalid */ { error: /* ir:node:fresh-97276b71aaac4056-invalid-code */ "invalid_input_97276b71aaac4056" })
      : (/* ir:node:fresh-97276b71aaac4056-user-match */ (/* ir:node:fresh-97276b71aaac4056-reserved-equals */ (/* ir:node:fresh-97276b71aaac4056-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-97276b71aaac4056-reserved-literal */ "reserved-97276b71"))
          ? (/* ir:node:fresh-97276b71aaac4056-reserved-error */ { error: /* ir:node:fresh-97276b71aaac4056-reserved-error-code */ "reserved_identifier_97276b71" })
          : (/* ir:node:fresh-97276b71aaac4056-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-97276b71aaac4056-get-user */ capabilities.users.getById(/* ir:node:fresh-97276b71aaac4056-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-97276b71aaac4056-missing */ { error: /* ir:node:fresh-97276b71aaac4056-missing-code */ "not_found_97276b71aaac4056" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-97276b71aaac4056-found */ { ok: /* ir:node:fresh-97276b71aaac4056-user-ref */ user };
            })()));
  })();
}
