// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA916393f18145f01d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-916393f18145f01d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-916393f18145f01d-normalizer */ rawId;
    return /* ir:node:fresh-916393f18145f01d-validation */ (/* ir:node:fresh-916393f18145f01d-is-empty */ (/* ir:node:fresh-916393f18145f01d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-916393f18145f01d-invalid */ { error: /* ir:node:fresh-916393f18145f01d-invalid-code */ "empty_identifier_916393f18145f01d" })
      : (/* ir:node:fresh-916393f18145f01d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-916393f18145f01d-get-user */ capabilities.users.getById(/* ir:node:fresh-916393f18145f01d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-916393f18145f01d-missing */ { error: /* ir:node:fresh-916393f18145f01d-missing-code */ "unknown_user_916393f18145f01d" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-916393f18145f01d-found */ { ok: /* ir:node:fresh-916393f18145f01d-user-ref */ user };
        })());
  })();
}
