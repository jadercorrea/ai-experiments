// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA8cddef88ef1fc807(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-8cddef88ef1fc807-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-8cddef88ef1fc807-normalizer */ (/* ir:node:fresh-8cddef88ef1fc807-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-8cddef88ef1fc807-validation */ (/* ir:node:fresh-8cddef88ef1fc807-is-empty */ (/* ir:node:fresh-8cddef88ef1fc807-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-8cddef88ef1fc807-invalid */ { error: /* ir:node:fresh-8cddef88ef1fc807-invalid-code */ "invalid_input_8cddef88ef1fc807" })
      : (/* ir:node:fresh-8cddef88ef1fc807-user-match */ (/* ir:node:fresh-8cddef88ef1fc807-reserved-equals */ (/* ir:node:fresh-8cddef88ef1fc807-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-8cddef88ef1fc807-reserved-literal */ "reserved-8cddef88"))
          ? (/* ir:node:fresh-8cddef88ef1fc807-reserved-error */ { error: /* ir:node:fresh-8cddef88ef1fc807-reserved-error-code */ "reserved_identifier_8cddef88" })
          : (/* ir:node:fresh-8cddef88ef1fc807-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-8cddef88ef1fc807-get-user */ capabilities.users.getById(/* ir:node:fresh-8cddef88ef1fc807-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-8cddef88ef1fc807-missing */ { error: /* ir:node:fresh-8cddef88ef1fc807-missing-code */ "not_found_8cddef88ef1fc807" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-8cddef88ef1fc807-found */ { ok: /* ir:node:fresh-8cddef88ef1fc807-user-ref */ user };
            })()));
  })();
}
