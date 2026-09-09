// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA123dc0809547e4ed(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-123dc0809547e4ed-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-123dc0809547e4ed-normalizer */ (/* ir:node:fresh-123dc0809547e4ed-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-123dc0809547e4ed-validation */ (/* ir:node:fresh-123dc0809547e4ed-is-empty */ (/* ir:node:fresh-123dc0809547e4ed-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-123dc0809547e4ed-invalid */ { error: /* ir:node:fresh-123dc0809547e4ed-invalid-code */ "invalid_input_123dc0809547e4ed" })
      : (/* ir:node:fresh-123dc0809547e4ed-user-match */ (/* ir:node:fresh-123dc0809547e4ed-reserved-equals */ (/* ir:node:fresh-123dc0809547e4ed-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-123dc0809547e4ed-reserved-literal */ "reserved-123dc080"))
          ? (/* ir:node:fresh-123dc0809547e4ed-reserved-error */ { error: /* ir:node:fresh-123dc0809547e4ed-reserved-error-code */ "reserved_identifier_123dc080" })
          : (/* ir:node:fresh-123dc0809547e4ed-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-123dc0809547e4ed-get-user */ capabilities.users.getById(/* ir:node:fresh-123dc0809547e4ed-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-123dc0809547e4ed-missing */ { error: /* ir:node:fresh-123dc0809547e4ed-missing-code */ "not_found_123dc0809547e4ed" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-123dc0809547e4ed-found */ { ok: /* ir:node:fresh-123dc0809547e4ed-user-ref */ user };
            })()));
  })();
}
