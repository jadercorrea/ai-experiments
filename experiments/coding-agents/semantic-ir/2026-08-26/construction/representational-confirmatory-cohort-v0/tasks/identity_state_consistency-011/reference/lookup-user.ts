// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA28c9b43c96a3671f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-28c9b43c96a3671f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-28c9b43c96a3671f-normalizer */ (/* ir:node:fresh-28c9b43c96a3671f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-28c9b43c96a3671f-validation */ (/* ir:node:fresh-28c9b43c96a3671f-is-empty */ (/* ir:node:fresh-28c9b43c96a3671f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-28c9b43c96a3671f-invalid */ { error: /* ir:node:fresh-28c9b43c96a3671f-invalid-code */ "invalid_input_28c9b43c96a3671f" })
      : (/* ir:node:fresh-28c9b43c96a3671f-user-match */ (/* ir:node:fresh-28c9b43c96a3671f-reserved-equals */ (/* ir:node:fresh-28c9b43c96a3671f-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-28c9b43c96a3671f-reserved-literal */ "reserved-28c9b43c"))
          ? (/* ir:node:fresh-28c9b43c96a3671f-reserved-error */ { error: /* ir:node:fresh-28c9b43c96a3671f-reserved-error-code */ "reserved_identifier_28c9b43c" })
          : (/* ir:node:fresh-28c9b43c96a3671f-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-28c9b43c96a3671f-get-user */ capabilities.users.getById(/* ir:node:fresh-28c9b43c96a3671f-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-28c9b43c96a3671f-missing */ { error: /* ir:node:fresh-28c9b43c96a3671f-missing-code */ "not_found_28c9b43c96a3671f" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-28c9b43c96a3671f-found */ { ok: /* ir:node:fresh-28c9b43c96a3671f-user-ref */ user };
            })()));
  })();
}
