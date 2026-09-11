// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA7d043c6a833408a4(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-7d043c6a833408a4-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-7d043c6a833408a4-normalizer */ (/* ir:node:fresh-7d043c6a833408a4-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-7d043c6a833408a4-validation */ (/* ir:node:fresh-7d043c6a833408a4-is-empty */ (/* ir:node:fresh-7d043c6a833408a4-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-7d043c6a833408a4-invalid */ { error: /* ir:node:fresh-7d043c6a833408a4-invalid-code */ "invalid_input_7d043c6a833408a4" })
      : (/* ir:node:fresh-7d043c6a833408a4-user-match */ (/* ir:node:fresh-7d043c6a833408a4-reserved-equals */ (/* ir:node:fresh-7d043c6a833408a4-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-7d043c6a833408a4-reserved-literal */ "reserved-7d043c6a"))
          ? (/* ir:node:fresh-7d043c6a833408a4-reserved-error */ { error: /* ir:node:fresh-7d043c6a833408a4-reserved-error-code */ "reserved_identifier_7d043c6a" })
          : (/* ir:node:fresh-7d043c6a833408a4-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-7d043c6a833408a4-get-user */ capabilities.users.getById(/* ir:node:fresh-7d043c6a833408a4-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-7d043c6a833408a4-missing */ { error: /* ir:node:fresh-7d043c6a833408a4-missing-code */ "not_found_7d043c6a833408a4" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-7d043c6a833408a4-found */ { ok: /* ir:node:fresh-7d043c6a833408a4-user-ref */ user };
            })()));
  })();
}
