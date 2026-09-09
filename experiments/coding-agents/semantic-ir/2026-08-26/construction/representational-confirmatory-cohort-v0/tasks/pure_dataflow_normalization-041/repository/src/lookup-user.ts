// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAab575bfc99a9bb45(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ab575bfc99a9bb45-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ab575bfc99a9bb45-normalizer */ (/* ir:node:fresh-ab575bfc99a9bb45-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ab575bfc99a9bb45-validation */ (/* ir:node:fresh-ab575bfc99a9bb45-is-empty */ (/* ir:node:fresh-ab575bfc99a9bb45-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ab575bfc99a9bb45-invalid */ { error: /* ir:node:fresh-ab575bfc99a9bb45-invalid-code */ "invalid_input_ab575bfc99a9bb45" })
      : (/* ir:node:fresh-ab575bfc99a9bb45-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ab575bfc99a9bb45-get-user */ capabilities.users.getById(/* ir:node:fresh-ab575bfc99a9bb45-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ab575bfc99a9bb45-missing */ { error: /* ir:node:fresh-ab575bfc99a9bb45-missing-code */ "not_found_ab575bfc99a9bb45" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ab575bfc99a9bb45-found */ { ok: /* ir:node:fresh-ab575bfc99a9bb45-user-ref */ user };
        })());
  })();
}
