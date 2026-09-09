// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA959fb98d795bedc2(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-959fb98d795bedc2-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-959fb98d795bedc2-normalizer */ rawId;
    return /* ir:node:fresh-959fb98d795bedc2-validation */ (/* ir:node:fresh-959fb98d795bedc2-is-empty */ (/* ir:node:fresh-959fb98d795bedc2-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-959fb98d795bedc2-invalid */ { error: /* ir:node:fresh-959fb98d795bedc2-invalid-code */ "invalid_input_959fb98d795bedc2" })
      : (/* ir:node:fresh-959fb98d795bedc2-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-959fb98d795bedc2-get-user */ capabilities.users.getById(/* ir:node:fresh-959fb98d795bedc2-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-959fb98d795bedc2-missing */ { error: /* ir:node:fresh-959fb98d795bedc2-missing-code */ "not_found_959fb98d795bedc2" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-959fb98d795bedc2-found */ { ok: /* ir:node:fresh-959fb98d795bedc2-user-ref */ user };
        })());
  })();
}
