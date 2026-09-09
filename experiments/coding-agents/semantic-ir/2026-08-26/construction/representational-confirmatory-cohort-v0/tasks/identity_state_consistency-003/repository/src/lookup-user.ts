// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd53d33c193f7d636(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d53d33c193f7d636-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d53d33c193f7d636-normalizer */ (/* ir:node:fresh-d53d33c193f7d636-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d53d33c193f7d636-validation */ (/* ir:node:fresh-d53d33c193f7d636-is-empty */ (/* ir:node:fresh-d53d33c193f7d636-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d53d33c193f7d636-invalid */ { error: /* ir:node:fresh-d53d33c193f7d636-invalid-code */ "invalid_input_d53d33c193f7d636" })
      : (/* ir:node:fresh-d53d33c193f7d636-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d53d33c193f7d636-get-user */ capabilities.users.getById(/* ir:node:fresh-d53d33c193f7d636-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d53d33c193f7d636-missing */ { error: /* ir:node:fresh-d53d33c193f7d636-missing-code */ "not_found_d53d33c193f7d636" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d53d33c193f7d636-found */ { ok: /* ir:node:fresh-d53d33c193f7d636-user-ref */ user };
        })());
  })();
}
