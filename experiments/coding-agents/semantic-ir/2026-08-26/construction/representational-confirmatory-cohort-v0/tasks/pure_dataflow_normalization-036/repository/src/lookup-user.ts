// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA741aee3b929616e0(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-741aee3b929616e0-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-741aee3b929616e0-normalizer */ rawId;
    return /* ir:node:fresh-741aee3b929616e0-validation */ (/* ir:node:fresh-741aee3b929616e0-is-empty */ (/* ir:node:fresh-741aee3b929616e0-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-741aee3b929616e0-invalid */ { error: /* ir:node:fresh-741aee3b929616e0-invalid-code */ "invalid_input_741aee3b929616e0" })
      : (/* ir:node:fresh-741aee3b929616e0-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-741aee3b929616e0-get-user */ capabilities.users.getById(/* ir:node:fresh-741aee3b929616e0-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-741aee3b929616e0-missing */ { error: /* ir:node:fresh-741aee3b929616e0-missing-code */ "not_found_741aee3b929616e0" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-741aee3b929616e0-found */ { ok: /* ir:node:fresh-741aee3b929616e0-user-ref */ user };
        })());
  })();
}
