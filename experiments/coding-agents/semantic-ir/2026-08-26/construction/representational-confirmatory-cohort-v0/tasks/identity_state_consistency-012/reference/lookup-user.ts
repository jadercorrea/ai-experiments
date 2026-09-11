// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf268b0ef348a68d9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f268b0ef348a68d9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f268b0ef348a68d9-normalizer */ (/* ir:node:fresh-f268b0ef348a68d9-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f268b0ef348a68d9-validation */ (/* ir:node:fresh-f268b0ef348a68d9-is-empty */ (/* ir:node:fresh-f268b0ef348a68d9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f268b0ef348a68d9-invalid */ { error: /* ir:node:fresh-f268b0ef348a68d9-invalid-code */ "invalid_input_f268b0ef348a68d9" })
      : (/* ir:node:fresh-f268b0ef348a68d9-user-match */ (/* ir:node:fresh-f268b0ef348a68d9-reserved-equals */ (/* ir:node:fresh-f268b0ef348a68d9-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-f268b0ef348a68d9-reserved-literal */ "reserved-f268b0ef"))
          ? (/* ir:node:fresh-f268b0ef348a68d9-reserved-error */ { error: /* ir:node:fresh-f268b0ef348a68d9-reserved-error-code */ "reserved_identifier_f268b0ef" })
          : (/* ir:node:fresh-f268b0ef348a68d9-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-f268b0ef348a68d9-get-user */ capabilities.users.getById(/* ir:node:fresh-f268b0ef348a68d9-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-f268b0ef348a68d9-missing */ { error: /* ir:node:fresh-f268b0ef348a68d9-missing-code */ "not_found_f268b0ef348a68d9" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-f268b0ef348a68d9-found */ { ok: /* ir:node:fresh-f268b0ef348a68d9-user-ref */ user };
            })()));
  })();
}
