// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf22aeff61a3028cd(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f22aeff61a3028cd-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f22aeff61a3028cd-normalizer */ rawId;
    return /* ir:node:fresh-f22aeff61a3028cd-validation */ (/* ir:node:fresh-f22aeff61a3028cd-is-empty */ (/* ir:node:fresh-f22aeff61a3028cd-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f22aeff61a3028cd-invalid */ { error: /* ir:node:fresh-f22aeff61a3028cd-invalid-code */ "empty_identifier_f22aeff61a3028cd" })
      : (/* ir:node:fresh-f22aeff61a3028cd-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f22aeff61a3028cd-get-user */ capabilities.users.getById(/* ir:node:fresh-f22aeff61a3028cd-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f22aeff61a3028cd-missing */ { error: /* ir:node:fresh-f22aeff61a3028cd-missing-code */ "unknown_user_f22aeff61a3028cd" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f22aeff61a3028cd-found */ { ok: /* ir:node:fresh-f22aeff61a3028cd-user-ref */ user };
        })());
  })();
}
