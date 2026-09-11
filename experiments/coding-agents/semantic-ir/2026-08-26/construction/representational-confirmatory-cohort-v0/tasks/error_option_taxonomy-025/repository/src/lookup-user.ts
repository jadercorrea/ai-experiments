// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1bedfb6542983ac2(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1bedfb6542983ac2-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1bedfb6542983ac2-normalizer */ rawId;
    return /* ir:node:fresh-1bedfb6542983ac2-validation */ (/* ir:node:fresh-1bedfb6542983ac2-is-empty */ (/* ir:node:fresh-1bedfb6542983ac2-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1bedfb6542983ac2-invalid */ { error: /* ir:node:fresh-1bedfb6542983ac2-invalid-code */ "invalid_input_1bedfb6542983ac2" })
      : (/* ir:node:fresh-1bedfb6542983ac2-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1bedfb6542983ac2-get-user */ capabilities.users.getById(/* ir:node:fresh-1bedfb6542983ac2-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1bedfb6542983ac2-missing */ { error: /* ir:node:fresh-1bedfb6542983ac2-missing-code */ "not_found_1bedfb6542983ac2" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1bedfb6542983ac2-found */ { ok: /* ir:node:fresh-1bedfb6542983ac2-user-ref */ user };
        })());
  })();
}
