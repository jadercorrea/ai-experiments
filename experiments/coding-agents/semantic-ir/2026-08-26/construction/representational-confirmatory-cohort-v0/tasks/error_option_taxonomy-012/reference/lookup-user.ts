// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6130195e44397c9a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6130195e44397c9a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6130195e44397c9a-normalizer */ rawId;
    return /* ir:node:fresh-6130195e44397c9a-validation */ (/* ir:node:fresh-6130195e44397c9a-is-empty */ (/* ir:node:fresh-6130195e44397c9a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6130195e44397c9a-invalid */ { error: /* ir:node:fresh-6130195e44397c9a-invalid-code */ "empty_identifier_6130195e44397c9a" })
      : (/* ir:node:fresh-6130195e44397c9a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6130195e44397c9a-get-user */ capabilities.users.getById(/* ir:node:fresh-6130195e44397c9a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6130195e44397c9a-missing */ { error: /* ir:node:fresh-6130195e44397c9a-missing-code */ "unknown_user_6130195e44397c9a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6130195e44397c9a-found */ { ok: /* ir:node:fresh-6130195e44397c9a-user-ref */ user };
        })());
  })();
}
