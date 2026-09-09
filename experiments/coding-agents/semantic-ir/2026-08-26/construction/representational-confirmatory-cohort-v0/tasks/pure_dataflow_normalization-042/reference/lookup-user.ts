// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAcc380c5fca792f17(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-cc380c5fca792f17-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-cc380c5fca792f17-normalizer */ rawId;
    return /* ir:node:fresh-cc380c5fca792f17-validation */ (/* ir:node:fresh-cc380c5fca792f17-is-empty */ (/* ir:node:fresh-cc380c5fca792f17-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-cc380c5fca792f17-invalid */ { error: /* ir:node:fresh-cc380c5fca792f17-invalid-code */ "invalid_input_cc380c5fca792f17" })
      : (/* ir:node:fresh-cc380c5fca792f17-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-cc380c5fca792f17-get-user */ capabilities.users.getById(/* ir:node:fresh-cc380c5fca792f17-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-cc380c5fca792f17-missing */ { error: /* ir:node:fresh-cc380c5fca792f17-missing-code */ "not_found_cc380c5fca792f17" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-cc380c5fca792f17-found */ { ok: /* ir:node:fresh-cc380c5fca792f17-user-ref */ user };
        })());
  })();
}
