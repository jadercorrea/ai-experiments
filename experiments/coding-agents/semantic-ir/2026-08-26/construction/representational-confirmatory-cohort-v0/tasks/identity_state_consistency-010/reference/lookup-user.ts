// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb9cb0b25a7d2707f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b9cb0b25a7d2707f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b9cb0b25a7d2707f-normalizer */ (/* ir:node:fresh-b9cb0b25a7d2707f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b9cb0b25a7d2707f-validation */ (/* ir:node:fresh-b9cb0b25a7d2707f-is-empty */ (/* ir:node:fresh-b9cb0b25a7d2707f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b9cb0b25a7d2707f-invalid */ { error: /* ir:node:fresh-b9cb0b25a7d2707f-invalid-code */ "invalid_input_b9cb0b25a7d2707f" })
      : (/* ir:node:fresh-b9cb0b25a7d2707f-user-match */ (/* ir:node:fresh-b9cb0b25a7d2707f-reserved-equals */ (/* ir:node:fresh-b9cb0b25a7d2707f-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-b9cb0b25a7d2707f-reserved-literal */ "reserved-b9cb0b25"))
          ? (/* ir:node:fresh-b9cb0b25a7d2707f-reserved-error */ { error: /* ir:node:fresh-b9cb0b25a7d2707f-reserved-error-code */ "reserved_identifier_b9cb0b25" })
          : (/* ir:node:fresh-b9cb0b25a7d2707f-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-b9cb0b25a7d2707f-get-user */ capabilities.users.getById(/* ir:node:fresh-b9cb0b25a7d2707f-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-b9cb0b25a7d2707f-missing */ { error: /* ir:node:fresh-b9cb0b25a7d2707f-missing-code */ "not_found_b9cb0b25a7d2707f" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-b9cb0b25a7d2707f-found */ { ok: /* ir:node:fresh-b9cb0b25a7d2707f-user-ref */ user };
            })()));
  })();
}
