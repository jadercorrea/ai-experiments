// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAca263fcd79d2cd77(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ca263fcd79d2cd77-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ca263fcd79d2cd77-normalizer */ rawId;
    return /* ir:node:fresh-ca263fcd79d2cd77-validation */ (/* ir:node:fresh-ca263fcd79d2cd77-is-empty */ (/* ir:node:fresh-ca263fcd79d2cd77-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ca263fcd79d2cd77-invalid */ { error: /* ir:node:fresh-ca263fcd79d2cd77-invalid-code */ "empty_identifier_ca263fcd79d2cd77" })
      : (/* ir:node:fresh-ca263fcd79d2cd77-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ca263fcd79d2cd77-get-user */ capabilities.users.getById(/* ir:node:fresh-ca263fcd79d2cd77-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ca263fcd79d2cd77-missing */ { error: /* ir:node:fresh-ca263fcd79d2cd77-missing-code */ "unknown_user_ca263fcd79d2cd77" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ca263fcd79d2cd77-found */ { ok: /* ir:node:fresh-ca263fcd79d2cd77-user-ref */ user };
        })());
  })();
}
