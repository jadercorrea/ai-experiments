// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfdee443ebd7e0d67(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fdee443ebd7e0d67-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fdee443ebd7e0d67-normalizer */ rawId;
    return /* ir:node:fresh-fdee443ebd7e0d67-validation */ (/* ir:node:fresh-fdee443ebd7e0d67-is-empty */ (/* ir:node:fresh-fdee443ebd7e0d67-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fdee443ebd7e0d67-invalid */ { error: /* ir:node:fresh-fdee443ebd7e0d67-invalid-code */ "empty_identifier_fdee443ebd7e0d67" })
      : (/* ir:node:fresh-fdee443ebd7e0d67-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fdee443ebd7e0d67-get-user */ capabilities.users.getById(/* ir:node:fresh-fdee443ebd7e0d67-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fdee443ebd7e0d67-missing */ { error: /* ir:node:fresh-fdee443ebd7e0d67-missing-code */ "unknown_user_fdee443ebd7e0d67" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fdee443ebd7e0d67-found */ { ok: /* ir:node:fresh-fdee443ebd7e0d67-user-ref */ user };
        })());
  })();
}
