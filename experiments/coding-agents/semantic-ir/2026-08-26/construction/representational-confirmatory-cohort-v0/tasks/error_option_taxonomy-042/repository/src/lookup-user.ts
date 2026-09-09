// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAcf9b63646173091b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-cf9b63646173091b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-cf9b63646173091b-normalizer */ rawId;
    return /* ir:node:fresh-cf9b63646173091b-validation */ (/* ir:node:fresh-cf9b63646173091b-is-empty */ (/* ir:node:fresh-cf9b63646173091b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-cf9b63646173091b-invalid */ { error: /* ir:node:fresh-cf9b63646173091b-invalid-code */ "invalid_input_cf9b63646173091b" })
      : (/* ir:node:fresh-cf9b63646173091b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-cf9b63646173091b-get-user */ capabilities.users.getById(/* ir:node:fresh-cf9b63646173091b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-cf9b63646173091b-missing */ { error: /* ir:node:fresh-cf9b63646173091b-missing-code */ "not_found_cf9b63646173091b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-cf9b63646173091b-found */ { ok: /* ir:node:fresh-cf9b63646173091b-user-ref */ user };
        })());
  })();
}
