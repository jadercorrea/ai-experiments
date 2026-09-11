// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfeb333aed853ba04(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-feb333aed853ba04-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-feb333aed853ba04-normalizer */ rawId;
    return /* ir:node:fresh-feb333aed853ba04-validation */ (/* ir:node:fresh-feb333aed853ba04-is-empty */ (/* ir:node:fresh-feb333aed853ba04-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-feb333aed853ba04-invalid */ { error: /* ir:node:fresh-feb333aed853ba04-invalid-code */ "empty_identifier_feb333aed853ba04" })
      : (/* ir:node:fresh-feb333aed853ba04-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-feb333aed853ba04-get-user */ capabilities.users.getById(/* ir:node:fresh-feb333aed853ba04-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-feb333aed853ba04-missing */ { error: /* ir:node:fresh-feb333aed853ba04-missing-code */ "unknown_user_feb333aed853ba04" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-feb333aed853ba04-found */ { ok: /* ir:node:fresh-feb333aed853ba04-user-ref */ user };
        })());
  })();
}
