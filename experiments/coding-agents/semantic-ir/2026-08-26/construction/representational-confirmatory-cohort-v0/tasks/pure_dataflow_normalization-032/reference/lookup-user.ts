// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd07e7a453166db06(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d07e7a453166db06-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d07e7a453166db06-normalizer */ rawId;
    return /* ir:node:fresh-d07e7a453166db06-validation */ (/* ir:node:fresh-d07e7a453166db06-is-empty */ (/* ir:node:fresh-d07e7a453166db06-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d07e7a453166db06-invalid */ { error: /* ir:node:fresh-d07e7a453166db06-invalid-code */ "invalid_input_d07e7a453166db06" })
      : (/* ir:node:fresh-d07e7a453166db06-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d07e7a453166db06-get-user */ capabilities.users.getById(/* ir:node:fresh-d07e7a453166db06-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d07e7a453166db06-missing */ { error: /* ir:node:fresh-d07e7a453166db06-missing-code */ "not_found_d07e7a453166db06" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d07e7a453166db06-found */ { ok: /* ir:node:fresh-d07e7a453166db06-user-ref */ user };
        })());
  })();
}
