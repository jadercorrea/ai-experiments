// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAab0560e4d916f8d0(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ab0560e4d916f8d0-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ab0560e4d916f8d0-normalizer */ rawId;
    return /* ir:node:fresh-ab0560e4d916f8d0-validation */ (/* ir:node:fresh-ab0560e4d916f8d0-is-empty */ (/* ir:node:fresh-ab0560e4d916f8d0-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ab0560e4d916f8d0-invalid */ { error: /* ir:node:fresh-ab0560e4d916f8d0-invalid-code */ "invalid_input_ab0560e4d916f8d0" })
      : (/* ir:node:fresh-ab0560e4d916f8d0-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ab0560e4d916f8d0-get-user */ capabilities.users.getById(/* ir:node:fresh-ab0560e4d916f8d0-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ab0560e4d916f8d0-missing */ { error: /* ir:node:fresh-ab0560e4d916f8d0-missing-code */ "not_found_ab0560e4d916f8d0" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ab0560e4d916f8d0-found */ { ok: /* ir:node:fresh-ab0560e4d916f8d0-user-ref */ user };
        })());
  })();
}
