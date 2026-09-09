// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1989aa9bd2f4da5e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1989aa9bd2f4da5e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1989aa9bd2f4da5e-normalizer */ rawId;
    return /* ir:node:fresh-1989aa9bd2f4da5e-validation */ (/* ir:node:fresh-1989aa9bd2f4da5e-is-empty */ (/* ir:node:fresh-1989aa9bd2f4da5e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1989aa9bd2f4da5e-invalid */ { error: /* ir:node:fresh-1989aa9bd2f4da5e-invalid-code */ "invalid_input_1989aa9bd2f4da5e" })
      : (/* ir:node:fresh-1989aa9bd2f4da5e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1989aa9bd2f4da5e-get-user */ capabilities.users.getById(/* ir:node:fresh-1989aa9bd2f4da5e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1989aa9bd2f4da5e-missing */ { error: /* ir:node:fresh-1989aa9bd2f4da5e-missing-code */ "not_found_1989aa9bd2f4da5e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1989aa9bd2f4da5e-found */ { ok: /* ir:node:fresh-1989aa9bd2f4da5e-user-ref */ user };
        })());
  })();
}
